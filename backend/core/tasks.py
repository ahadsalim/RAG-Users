"""
Celery tasks for core functionality
تسک‌های زمان‌بندی شده برای عملیات اصلی سیستم
"""
import logging
from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task(name='core.tasks.cleanup_tokens_and_sessions')
def cleanup_tokens_and_sessions():
    """
    پاکسازی توکن‌ها و session های قدیمی
    - حذف توکن‌های منقضی شده
    - نگه داشتن حداکثر 3 توکن برای هر کاربر
    - حذف session های غیرفعال قدیمی‌تر از 30 روز
    """
    from django.utils import timezone
    from datetime import timedelta
    from rest_framework_simplejwt.token_blacklist.models import OutstandingToken, BlacklistedToken
    from accounts.models import UserSession
    from django.contrib.auth import get_user_model
    
    User = get_user_model()
    max_tokens_per_user = 3
    session_days = 30
    
    logger.info("Starting cleanup_tokens_and_sessions task")
    
    total_tokens_deleted = 0
    total_sessions_deleted = 0
    
    try:
        # 1. Delete orphan tokens (tokens without user)
        orphan_tokens = OutstandingToken.objects.filter(user__isnull=True)
        orphan_count = orphan_tokens.count()
        if orphan_count > 0:
            orphan_tokens.delete()
            total_tokens_deleted += orphan_count
            logger.info(f"Deleted {orphan_count} orphan tokens")
        
        # 2. Delete expired tokens
        expired_tokens = OutstandingToken.objects.filter(expires_at__lt=timezone.now())
        expired_count = expired_tokens.count()
        if expired_count > 0:
            for token in expired_tokens:
                try:
                    BlacklistedToken.objects.get_or_create(token=token)
                except Exception:
                    pass
            expired_tokens.delete()
            total_tokens_deleted += expired_count
            logger.info(f"Deleted {expired_count} expired tokens")
        
        # 3. Keep only max_tokens per user, delete older ones
        for user in User.objects.all():
            tokens = OutstandingToken.objects.filter(user=user).order_by('-created_at')
            tokens_to_delete = list(tokens[max_tokens_per_user:])
            if tokens_to_delete:
                count = len(tokens_to_delete)
                for token in tokens_to_delete:
                    try:
                        BlacklistedToken.objects.get_or_create(token=token)
                        token.delete()
                    except Exception:
                        pass
                total_tokens_deleted += count
                logger.info(f"User {user.username or user.phone_number}: deleted {count} old tokens")
        
        # 4. Delete old inactive sessions
        cutoff_date = timezone.now() - timedelta(days=session_days)
        old_sessions = UserSession.objects.filter(
            is_active=False,
            last_activity__lt=cutoff_date
        )
        old_sessions_count = old_sessions.count()
        if old_sessions_count > 0:
            old_sessions.delete()
            total_sessions_deleted += old_sessions_count
            logger.info(f"Deleted {old_sessions_count} old inactive sessions")
        
        # 5. Mark expired sessions as inactive
        expired_sessions = UserSession.objects.filter(expires_at__lt=timezone.now(), is_active=True)
        expired_sessions_count = expired_sessions.count()
        if expired_sessions_count > 0:
            expired_sessions.update(is_active=False)
            logger.info(f"Marked {expired_sessions_count} expired sessions as inactive")
        
        logger.info(f"cleanup_tokens_and_sessions completed: {total_tokens_deleted} tokens, {total_sessions_deleted} sessions deleted")
        
    except Exception as e:
        logger.error(f"cleanup_tokens_and_sessions failed: {e}")
        raise
    
    return {
        'tokens_deleted': total_tokens_deleted,
        'sessions_deleted': total_sessions_deleted
    }


@shared_task(name='core.tasks.cleanup_old_files')
def cleanup_old_files():
    """
    پاکسازی فایل‌های موقت قدیمی از MinIO
    فایل‌های قدیمی‌تر از 24 ساعت حذف می‌شوند
    """
    import subprocess
    
    logger.info("Starting cleanup_old_files task")
    
    try:
        result = subprocess.run(
            ['python3', '/srv/cleanup_old_files.py', '--hours', '24'],
            capture_output=True,
            text=True,
            timeout=300
        )
        
        if result.returncode == 0:
            logger.info(f"cleanup_old_files completed: {result.stdout}")
        else:
            logger.error(f"cleanup_old_files failed: {result.stderr}")
            
    except FileNotFoundError:
        logger.warning("cleanup_old_files.py not found, skipping")
    except Exception as e:
        logger.error(f"cleanup_old_files failed: {e}")
        raise
