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
    
    کاربران حقیقی (individual) -> پلن رایگان حقیقی
    کاربران حقوقی مالک سازمان (business owner) -> پلن رایگان حقوقی
    اعضای سازمان -> هیچ پلنی (از پلن مالک استفاده می‌کنند)
    """
    if not created or instance.is_superuser:
        return
    
    # اعضای سازمان نباید پلن شخصی بگیرند
    # آن‌ها از پلن مالک سازمان استفاده می‌کنند
    if instance.is_organization_member():
        logger.info(f"User {instance.phone_number} is organization member, no personal subscription created")
        return
    
    try:
        # انتخاب پلن رایگان بر اساس نوع کاربر
        user_type = instance.user_type
        
        # جستجوی پلن رایگان مناسب
        free_plan = Plan.objects.filter(
            plan_type=user_type,
            price=0,
            is_active=True
        ).first()
        
        if not free_plan:
            logger.warning(f"No free plan found for user type '{user_type}' for user {instance.phone_number}")
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


@receiver(post_save, sender=User)
def notify_admins_new_user(sender, instance, created, **kwargs):
    """
    ارسال پیامک به سوپر ادمین‌ها هنگام ثبت‌نام کاربر جدید
    """
    if not created or instance.is_superuser:
        return
    
    try:
        from notifications.services import NotificationService
        
        # پیدا کردن همه سوپر ادمین‌ها
        superusers = User.objects.filter(is_superuser=True, is_active=True)
        
        for admin in superusers:
            try:
                NotificationService.create_notification(
                    user=admin,
                    template_code='new_user_registered',
                    context={
                        'user_phone': instance.phone_number,
                        'user_name': instance.get_full_name() or instance.phone_number,
                    },
                    channels=['sms'],
                    priority='low'
                )
                logger.info(f"New user notification sent to admin {admin.phone_number}")
            except Exception as e:
                logger.error(f"Failed to notify admin {admin.phone_number}: {e}")
                
    except Exception as e:
        logger.error(f"Error notifying admins about new user {instance.phone_number}: {e}")
