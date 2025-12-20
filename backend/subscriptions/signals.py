"""
Signals for automatic subscription management
"""
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
import logging

from .models import Subscription, Plan

User = get_user_model()
logger = logging.getLogger(__name__)


@receiver(post_save, sender=User)
def create_free_subscription(sender, instance, created, **kwargs):
    """
    ایجاد خودکار اشتراک رایگان برای کاربران جدید (غیر از سوپر ادمین)
    سوپر ادمین‌ها از طریق setup_initial_data پلن نامحدود دریافت می‌کنند
    """
    if not created or instance.is_superuser:
        return
    
    try:
        free_plan = Plan.objects.filter(name='رایگان', is_active=True).first()
        
        if not free_plan:
            logger.warning(f"No free plan found for new user {instance.phone_number}")
            return
        
        subscription = Subscription.objects.create(
            user=instance,
            plan=free_plan,
            status='active',
            start_date=timezone.now(),
            end_date=timezone.now() + timedelta(days=free_plan.duration_days),
            auto_renew=True
        )
        logger.info(f"Free subscription created for user {instance.phone_number}: {subscription.id}")
        
    except Exception as e:
        logger.error(f"Error creating subscription for user {instance.phone_number}: {e}")
