"""
Signals برای همگام‌سازی با RAG Core
"""
from django.db.models.signals import post_delete, pre_delete
from django.dispatch import receiver
import logging
import asyncio

from .models import Conversation, Message
from .core_service import core_service

logger = logging.getLogger(__name__)


@receiver(pre_delete, sender=Conversation)
def delete_conversation_from_rag_core(sender, instance, **kwargs):
    """
    حذف conversation از RAG Core قبل از حذف از دیتابیس
    اگر حذف از Core ناموفق باشد، حذف از Django هم متوقف می‌شود
    """
    if instance.rag_conversation_id:
        from rest_framework_simplejwt.tokens import RefreshToken
        from django.db import transaction
        
        # تولید token برای کاربر
        refresh = RefreshToken.for_user(instance.user)
        access_token = str(refresh.access_token)
        
        # حذف از RAG Core (async call را در sync context اجرا می‌کنیم)
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        try:
            success = loop.run_until_complete(
                core_service.delete_conversation(
                    conversation_id=instance.rag_conversation_id,
                    token=access_token
                )
            )
            
            if success:
                logger.info(f"✅ Conversation {instance.id} deleted from RAG Core: {instance.rag_conversation_id}")
            else:
                # اگر حذف از Core ناموفق بود، exception بفرست تا حذف از Django متوقف شود
                error_msg = f"Failed to delete conversation {instance.id} from RAG Core. Aborting Django deletion."
                logger.error(f"❌ {error_msg}")
                raise Exception(error_msg)
                
        except Exception as e:
            # هر خطایی که رخ دهد، حذف از Django را متوقف می‌کنیم
            error_msg = f"Error deleting conversation {instance.id} from RAG Core: {e}. Aborting Django deletion."
            logger.error(f"❌ {error_msg}")
            raise Exception(error_msg) from e


@receiver(post_delete, sender=Conversation)
def log_conversation_deletion(sender, instance, **kwargs):
    """
    لاگ حذف conversation
    """
    logger.info(f"Conversation {instance.id} ({instance.title}) deleted by user {instance.user.email}")
