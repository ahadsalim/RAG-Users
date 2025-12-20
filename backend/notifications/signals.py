"""
Signals for automatic notification preference creation
"""
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
import logging

logger = logging.getLogger(__name__)
User = get_user_model()


@receiver(post_save, sender=User)
def create_notification_preference(sender, instance, created, **kwargs):
    """
    ایجاد خودکار تنظیمات اعلان برای کاربران جدید
    """
    if created:
        from .models import NotificationPreference
        
        try:
            NotificationPreference.objects.get_or_create(user=instance)
            logger.info(f"NotificationPreference created for user {instance.phone_number}")
        except Exception as e:
            logger.error(f"Error creating NotificationPreference for user {instance.phone_number}: {e}")
