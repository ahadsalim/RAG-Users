"""
Celery tasks for chat module
تسک‌های پس‌زمینه برای ماژول چت
"""
import logging
from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task(name='chat.tasks.log_audit')
def log_audit(user_id, action, details, ip_address, user_agent):
    """ثبت AuditLog در پس‌زمینه"""
    try:
        from accounts.models import AuditLog
        from django.contrib.auth import get_user_model
        User = get_user_model()
        
        user = User.objects.get(id=user_id)
        AuditLog.objects.create(
            user=user,
            action=action,
            details=details,
            ip_address=ip_address or '0.0.0.0',
            user_agent=user_agent or ''
        )
    except Exception as e:
        logger.error(f"Failed to log audit: {e}")


@shared_task(name='chat.tasks.update_conversation_stats')
def update_conversation_stats(conversation_id):
    """به‌روزرسانی آمار conversation در پس‌زمینه"""
    try:
        from chat.models import Conversation
        from django.utils import timezone
        from django.db.models import Count
        
        conversation = Conversation.objects.get(id=conversation_id)
        conversation.message_count = conversation.messages.filter(role='user').count()
        conversation.token_usage = conversation.messages.aggregate(
            total=Count('tokens')
        )['total'] or 0
        conversation.last_message_at = timezone.now()
        conversation.save(update_fields=['message_count', 'token_usage', 'last_message_at'])
    except Exception as e:
        logger.error(f"Failed to update conversation stats: {e}")
