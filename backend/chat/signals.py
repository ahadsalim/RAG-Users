"""
Signals برای همگام‌سازی با RAG Core
"""
from django.db.models.signals import post_delete, pre_delete
from django.dispatch import receiver
import logging

from .models import Conversation, Message
from .core_service import RAGCoreService

logger = logging.getLogger(__name__)


@receiver(pre_delete, sender=Conversation)
def delete_conversation_from_rag_core(sender, instance, **kwargs):
    """
    حذف conversation از RAG Core قبل از حذف از دیتابیس
    """
    if instance.rag_conversation_id:
        try:
            # حذف از RAG Core
            rag_service = RAGCoreService()
            # TODO: باید endpoint حذف conversation در RAG Core اضافه شود
            # rag_service.delete_conversation(instance.rag_conversation_id)
            
            logger.info(f"Conversation {instance.id} deleted from RAG Core: {instance.rag_conversation_id}")
        except Exception as e:
            logger.error(f"Error deleting conversation from RAG Core: {e}")
            # ادامه حذف در Django حتی اگر RAG Core خطا داد


@receiver(post_delete, sender=Conversation)
def log_conversation_deletion(sender, instance, **kwargs):
    """
    لاگ حذف conversation
    """
    logger.info(f"Conversation {instance.id} ({instance.title}) deleted by user {instance.user.email}")
