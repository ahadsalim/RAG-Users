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
    """
    if instance.rag_conversation_id:
        try:
            # دریافت JWT token کاربر
            # از آنجایی که در signal هستیم و دسترسی مستقیم به request نداریم،
            # باید از یک روش دیگر token را بگیریم
            
            # گزینه 1: استفاده از token ذخیره شده در user model (اگر وجود داشته باشد)
            # گزینه 2: تولید یک service token برای عملیات داخلی
            # گزینه 3: استفاده از API key سیستمی
            
            # برای الان از user token استفاده می‌کنیم (باید در model ذخیره شود)
            # یا می‌توانیم یک service token داشته باشیم
            
            from rest_framework_simplejwt.tokens import RefreshToken
            
            # تولید token برای کاربر
            refresh = RefreshToken.for_user(instance.user)
            access_token = str(refresh.access_token)
            
            # حذف از RAG Core (async call را در sync context اجرا می‌کنیم)
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
            
            success = loop.run_until_complete(
                core_service.delete_conversation(
                    conversation_id=instance.rag_conversation_id,
                    token=access_token
                )
            )
            
            if success:
                logger.info(f"✅ Conversation {instance.id} deleted from RAG Core: {instance.rag_conversation_id}")
            else:
                logger.warning(f"⚠️ Failed to delete conversation {instance.id} from RAG Core")
                
        except Exception as e:
            logger.error(f"❌ Error deleting conversation from RAG Core: {e}")
            # ادامه حذف در Django حتی اگر RAG Core خطا داد


@receiver(post_delete, sender=Conversation)
def log_conversation_deletion(sender, instance, **kwargs):
    """
    لاگ حذف conversation
    """
    logger.info(f"Conversation {instance.id} ({instance.title}) deleted by user {instance.user.email}")
