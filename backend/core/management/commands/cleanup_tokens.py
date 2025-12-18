"""
Management command to cleanup old JWT tokens and inactive sessions.
Run this periodically via cron to keep the database clean.

Usage:
    python manage.py cleanup_tokens
    python manage.py cleanup_tokens --max-tokens-per-user 5
    python manage.py cleanup_tokens --session-days 30
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from rest_framework_simplejwt.token_blacklist.models import OutstandingToken, BlacklistedToken
from accounts.models import UserSession
from django.contrib.auth import get_user_model

User = get_user_model()


class Command(BaseCommand):
    help = 'Cleanup old JWT tokens and inactive sessions'

    def add_arguments(self, parser):
        parser.add_argument(
            '--max-tokens-per-user',
            type=int,
            default=3,
            help='Maximum number of tokens to keep per user (default: 3)'
        )
        parser.add_argument(
            '--session-days',
            type=int,
            default=30,
            help='Delete sessions older than this many days (default: 30)'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be deleted without actually deleting'
        )

    def handle(self, *args, **options):
        max_tokens = options['max_tokens_per_user']
        session_days = options['session_days']
        dry_run = options['dry_run']
        
        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN - No changes will be made'))
        
        total_tokens_deleted = 0
        total_sessions_deleted = 0
        
        # 1. Delete orphan tokens (tokens without user)
        orphan_tokens = OutstandingToken.objects.filter(user__isnull=True)
        orphan_count = orphan_tokens.count()
        if orphan_count > 0:
            if not dry_run:
                orphan_tokens.delete()
            self.stdout.write(f'Deleted {orphan_count} orphan tokens')
            total_tokens_deleted += orphan_count
        
        # 2. Delete expired tokens
        expired_tokens = OutstandingToken.objects.filter(expires_at__lt=timezone.now())
        expired_count = expired_tokens.count()
        if expired_count > 0:
            if not dry_run:
                # First blacklist them, then delete
                for token in expired_tokens:
                    try:
                        BlacklistedToken.objects.get_or_create(token=token)
                    except Exception:
                        pass
                expired_tokens.delete()
            self.stdout.write(f'Deleted {expired_count} expired tokens')
            total_tokens_deleted += expired_count
        
        # 3. Keep only max_tokens per user, delete older ones
        for user in User.objects.all():
            tokens = OutstandingToken.objects.filter(user=user).order_by('-created_at')
            tokens_to_delete = list(tokens[max_tokens:])
            if tokens_to_delete:
                count = len(tokens_to_delete)
                if not dry_run:
                    for token in tokens_to_delete:
                        try:
                            BlacklistedToken.objects.get_or_create(token=token)
                            token.delete()
                        except Exception:
                            pass
                self.stdout.write(f'User {user.username or user.phone_number}: deleted {count} old tokens')
                total_tokens_deleted += count
        
        # 4. Delete old inactive sessions
        cutoff_date = timezone.now() - timedelta(days=session_days)
        old_sessions = UserSession.objects.filter(
            is_active=False,
            last_activity__lt=cutoff_date
        )
        old_sessions_count = old_sessions.count()
        if old_sessions_count > 0:
            if not dry_run:
                old_sessions.delete()
            self.stdout.write(f'Deleted {old_sessions_count} old inactive sessions')
            total_sessions_deleted += old_sessions_count
        
        # 5. Delete expired sessions
        expired_sessions = UserSession.objects.filter(expires_at__lt=timezone.now())
        expired_sessions_count = expired_sessions.count()
        if expired_sessions_count > 0:
            if not dry_run:
                expired_sessions.update(is_active=False)
                expired_sessions.filter(last_activity__lt=cutoff_date).delete()
            self.stdout.write(f'Marked {expired_sessions_count} expired sessions as inactive')
        
        # Summary
        self.stdout.write(self.style.SUCCESS(
            f'\nCleanup complete: {total_tokens_deleted} tokens deleted, '
            f'{total_sessions_deleted} sessions deleted'
        ))
        
        # Show remaining counts
        remaining_tokens = OutstandingToken.objects.count()
        remaining_sessions = UserSession.objects.filter(is_active=True).count()
        self.stdout.write(f'Remaining: {remaining_tokens} tokens, {remaining_sessions} active sessions')
