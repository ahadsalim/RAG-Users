"""
Celery tasks for subscription management
تسک‌های زمان‌بندی شده برای مدیریت اشتراک‌ها
"""
import logging
from celery import shared_task
from .notification_service import SubscriptionScheduledTasks

logger = logging.getLogger(__name__)


@shared_task(name='subscriptions.tasks.check_expiring_subscriptions')
def check_expiring_subscriptions():
    """
    بررسی اشتراک‌های در حال انقضا
    ارسال اعلان 7، 3 و 1 روز قبل از انقضا
    """
    logger.info("Starting check_expiring_subscriptions task")
    try:
        SubscriptionScheduledTasks.check_expiring_subscriptions()
        logger.info("check_expiring_subscriptions completed successfully")
    except Exception as e:
        logger.error(f"check_expiring_subscriptions failed: {e}")
        raise


@shared_task(name='subscriptions.tasks.check_expired_subscriptions')
def check_expired_subscriptions():
    """
    بررسی و به‌روزرسانی اشتراک‌های منقضی شده
    تغییر وضعیت به expired و ارسال اعلان
    """
    logger.info("Starting check_expired_subscriptions task")
    try:
        SubscriptionScheduledTasks.check_expired_subscriptions()
        logger.info("check_expired_subscriptions completed successfully")
    except Exception as e:
        logger.error(f"check_expired_subscriptions failed: {e}")
        raise


@shared_task(name='subscriptions.tasks.check_quota_warnings')
def check_quota_warnings():
    """
    بررسی هشدارهای سهمیه
    ارسال اعلان وقتی 80% سهمیه استفاده شده
    """
    logger.info("Starting check_quota_warnings task")
    try:
        SubscriptionScheduledTasks.check_quota_warnings()
        logger.info("check_quota_warnings completed successfully")
    except Exception as e:
        logger.error(f"check_quota_warnings failed: {e}")
        raise


@shared_task(name='subscriptions.tasks.send_subscription_notification')
def send_subscription_notification(notification_type: str, subscription_id: str, **kwargs):
    """
    ارسال اعلان اشتراک به صورت async
    """
    from .models import Subscription
    from .notification_service import SubscriptionNotificationService
    
    logger.info(f"Sending {notification_type} notification for subscription {subscription_id}")
    
    try:
        subscription = Subscription.objects.get(id=subscription_id)
        
        if notification_type == 'renewed':
            SubscriptionNotificationService.notify_subscription_renewed(subscription)
        elif notification_type == 'expired':
            SubscriptionNotificationService.notify_subscription_expired(subscription)
        elif notification_type == 'expiring':
            days = kwargs.get('days_remaining', 3)
            SubscriptionNotificationService.notify_subscription_expiring(subscription, days)
        elif notification_type == 'payment_success':
            user = subscription.user
            amount = kwargs.get('amount', 0)
            plan_name = subscription.plan.name
            SubscriptionNotificationService.notify_payment_success(user, amount, plan_name)
        elif notification_type == 'payment_failed':
            user = subscription.user
            amount = kwargs.get('amount', 0)
            error_message = kwargs.get('error_message', 'خطای نامشخص')
            SubscriptionNotificationService.notify_payment_failed(user, amount, error_message)
        else:
            logger.warning(f"Unknown notification type: {notification_type}")
            
    except Subscription.DoesNotExist:
        logger.error(f"Subscription not found: {subscription_id}")
    except Exception as e:
        logger.error(f"Failed to send notification: {e}")
        raise
