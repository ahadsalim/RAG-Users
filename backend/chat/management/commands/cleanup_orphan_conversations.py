"""
Management command to cleanup orphan conversations in Core RAG
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
import asyncio
from rest_framework_simplejwt.tokens import RefreshToken

from chat.models import Conversation
from chat.core_service import core_service

User = get_user_model()


class Command(BaseCommand):
    help = 'Cleanup orphan conversations that exist in Core but not in local DB'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be deleted without actually deleting',
        )
    
    def handle(self, *args, **options):
        dry_run = options['dry_run']
        
        if dry_run:
            self.stdout.write(self.style.WARNING('🔍 DRY RUN MODE - No actual deletions will occur'))
        
        self.stdout.write('Finding conversations with rag_conversation_id...')
        
        # پیدا کردن تمام conversation هایی که rag_conversation_id دارند
        conversations = Conversation.objects.exclude(rag_conversation_id='').exclude(rag_conversation_id__isnull=True)
        
        self.stdout.write(f'Found {conversations.count()} conversations with RAG IDs')
        
        deleted_count = 0
        error_count = 0
        
        for conv in conversations:
            try:
                # تولید token برای کاربر
                refresh = RefreshToken.for_user(conv.user)
                access_token = str(refresh.access_token)
                
                # حذف از Core
                loop = asyncio.get_event_loop()
                success = loop.run_until_complete(
                    core_service.delete_conversation(
                        conversation_id=conv.rag_conversation_id,
                        token=access_token
                    )
                )
                
                if success:
                    if dry_run:
                        self.stdout.write(
                            self.style.SUCCESS(
                                f'  [DRY RUN] Would delete: {conv.rag_conversation_id} ({conv.title})'
                            )
                        )
                    else:
                        self.stdout.write(
                            self.style.SUCCESS(
                                f'  ✓ Deleted from Core: {conv.rag_conversation_id} ({conv.title})'
                            )
                        )
                    deleted_count += 1
                else:
                    self.stdout.write(
                        self.style.ERROR(
                            f'  ✗ Failed: {conv.rag_conversation_id} ({conv.title})'
                        )
                    )
                    error_count += 1
                    
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(
                        f'  ✗ Error for {conv.rag_conversation_id}: {e}'
                    )
                )
                error_count += 1
        
        self.stdout.write('')
        if dry_run:
            self.stdout.write(
                self.style.SUCCESS(
                    f'DRY RUN: Would delete {deleted_count} conversations, {error_count} errors'
                )
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(
                    f'Done! Deleted {deleted_count} conversations, {error_count} errors'
                )
            )
