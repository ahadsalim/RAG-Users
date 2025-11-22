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
def create_free_trial_subscription(sender, instance, created, **kwargs):
    """
    ایجاد خودکار اشتراک رایگان برای کاربران جدید
    """
    if created and not instance.is_superuser:
        try:
            # پیدا کردن پلن رایگان
            free_plan = Plan.objects.filter(
                name__icontains='free',
                is_active=True
            ).first()
            
            if not free_plan:
                # اگر پلن رایگان نبود، اولین پلن فعال را بگیر
                free_plan = Plan.objects.filter(is_active=True).first()
            
            if free_plan:
                # ایجاد اشتراک active برای 30 روز
                subscription = Subscription.objects.create(
                    user=instance,
                    plan=free_plan,
                    status='active',  # باید active باشد تا کاربر بتواند از سیستم استفاده کند
                    start_date=timezone.now(),
                    end_date=timezone.now() + timedelta(days=30),
                    auto_renew=False
                )
                logger.info(f"Free trial subscription created for user {instance.phone_number}: {subscription.id}")
            else:
                logger.warning(f"No subscription plan found to assign to new user {instance.phone_number}")
                
        except Exception as e:
            logger.error(f"Error creating subscription for user {instance.phone_number}: {e}")
