"""
سرویس اعلان‌های مربوط به اشتراک
"""
import logging
from django.utils import timezone
from datetime import timedelta
from notifications.services import NotificationService
from notifications.models import NotificationPreference

logger = logging.getLogger(__name__)


class SubscriptionNotificationService:
    """سرویس ارسال اعلان‌های مربوط به اشتراک"""
    
    # Template codes
    TEMPLATE_SUBSCRIPTION_EXPIRING = 'subscription_expiring'
    TEMPLATE_SUBSCRIPTION_EXPIRED = 'subscription_expired'
    TEMPLATE_QUOTA_WARNING = 'quota_warning'
    TEMPLATE_QUOTA_EXCEEDED = 'quota_exceeded'
    TEMPLATE_SUBSCRIPTION_RENEWED = 'subscription_renewed'
    TEMPLATE_PAYMENT_SUCCESS = 'payment_success'
    TEMPLATE_PAYMENT_FAILED = 'payment_failed'
    
    @staticmethod
    def get_user_notification_channels(user) -> list:
        """
        دریافت کانال‌های فعال اعلان‌رسانی کاربر
        پیش‌فرض: همه کانال‌ها فعال
        """
        try:
            prefs = user.notification_preferences
        except NotificationPreference.DoesNotExist:
            # ایجاد تنظیمات پیش‌فرض با همه کانال‌ها فعال
            prefs = NotificationPreference.objects.create(user=user)
        
        channels = ['in_app']  # همیشه in_app فعال است
        
        if prefs.email_enabled and user.email:
            channels.append('email')
        if prefs.sms_enabled and user.phone_number:
            channels.append('sms')
        if prefs.push_enabled:
            channels.append('push')
        
        return channels
    
    @staticmethod
    def notify_subscription_expiring(subscription, days_remaining: int):
        """
        اعلان نزدیک شدن به انقضای اشتراک
        ارسال 7، 3 و 1 روز قبل از انقضا
        """
        user = subscription.user
        channels = SubscriptionNotificationService.get_user_notification_channels(user)
        
        context = {
            'user_name': user.get_full_name() or user.phone_number,
            'plan_name': subscription.plan.name,
            'days_remaining': days_remaining,
            'end_date': subscription.end_date.strftime('%Y/%m/%d'),
            'renewal_url': '/dashboard/subscription/renew',
        }
        
        try:
            NotificationService.create_notification(
                user=user,
                template_code=SubscriptionNotificationService.TEMPLATE_SUBSCRIPTION_EXPIRING,
                context=context,
                channels=channels,
                priority='high' if days_remaining <= 1 else 'normal'
            )
            logger.info(f"Subscription expiring notification sent to {user.phone_number}: {days_remaining} days")
        except Exception as e:
            logger.error(f"Failed to send expiring notification: {e}")
    
    @staticmethod
    def notify_subscription_expired(subscription):
        """اعلان انقضای اشتراک"""
        user = subscription.user
        channels = SubscriptionNotificationService.get_user_notification_channels(user)
        
        context = {
            'user_name': user.get_full_name() or user.phone_number,
            'plan_name': subscription.plan.name,
            'renewal_url': '/dashboard/subscription/plans',
        }
        
        try:
            NotificationService.create_notification(
                user=user,
                template_code=SubscriptionNotificationService.TEMPLATE_SUBSCRIPTION_EXPIRED,
                context=context,
                channels=channels,
                priority='high'
            )
            logger.info(f"Subscription expired notification sent to {user.phone_number}")
        except Exception as e:
            logger.error(f"Failed to send expired notification: {e}")
    
    @staticmethod
    def notify_quota_warning(user, usage_percentage: int, quota_type: str = 'daily'):
        """
        اعلان هشدار مصرف سهمیه
        ارسال وقتی 80% سهمیه استفاده شده
        """
        channels = SubscriptionNotificationService.get_user_notification_channels(user)
        
        subscription = user.subscriptions.filter(
            status='active',
            end_date__gt=timezone.now()
        ).first()
        
        if not subscription:
            return
        
        features = subscription.plan.features or {}
        
        if quota_type == 'daily':
            limit = features.get('max_queries_per_day', 10)
            limit_text = f'{limit} سوال در روز'
        else:
            limit = features.get('max_queries_per_month', 300)
            limit_text = f'{limit} سوال در ماه'
        
        context = {
            'user_name': user.get_full_name() or user.phone_number,
            'usage_percentage': usage_percentage,
            'quota_type': 'روزانه' if quota_type == 'daily' else 'ماهانه',
            'limit_text': limit_text,
            'upgrade_url': '/dashboard/subscription/upgrade',
        }
        
        try:
            NotificationService.create_notification(
                user=user,
                template_code=SubscriptionNotificationService.TEMPLATE_QUOTA_WARNING,
                context=context,
                channels=channels,
                priority='normal'
            )
            logger.info(f"Quota warning notification sent to {user.phone_number}: {usage_percentage}%")
        except Exception as e:
            logger.error(f"Failed to send quota warning notification: {e}")
    
    @staticmethod
    def notify_quota_exceeded(user, quota_type: str = 'daily'):
        """اعلان اتمام سهمیه"""
        channels = SubscriptionNotificationService.get_user_notification_channels(user)
        
        context = {
            'user_name': user.get_full_name() or user.phone_number,
            'quota_type': 'روزانه' if quota_type == 'daily' else 'ماهانه',
            'upgrade_url': '/dashboard/subscription/upgrade',
        }
        
        try:
            NotificationService.create_notification(
                user=user,
                template_code=SubscriptionNotificationService.TEMPLATE_QUOTA_EXCEEDED,
                context=context,
                channels=channels,
                priority='high'
            )
            logger.info(f"Quota exceeded notification sent to {user.phone_number}")
        except Exception as e:
            logger.error(f"Failed to send quota exceeded notification: {e}")
    
    @staticmethod
    def notify_subscription_renewed(subscription):
        """اعلان تمدید موفق اشتراک"""
        user = subscription.user
        channels = SubscriptionNotificationService.get_user_notification_channels(user)
        
        context = {
            'user_name': user.get_full_name() or user.phone_number,
            'plan_name': subscription.plan.name,
            'end_date': subscription.end_date.strftime('%Y/%m/%d'),
            'dashboard_url': '/dashboard',
        }
        
        try:
            NotificationService.create_notification(
                user=user,
                template_code=SubscriptionNotificationService.TEMPLATE_SUBSCRIPTION_RENEWED,
                context=context,
                channels=channels,
                priority='normal'
            )
            logger.info(f"Subscription renewed notification sent to {user.phone_number}")
        except Exception as e:
            logger.error(f"Failed to send renewed notification: {e}")
    
    @staticmethod
    def notify_payment_success(user, amount, plan_name):
        """اعلان پرداخت موفق"""
        channels = SubscriptionNotificationService.get_user_notification_channels(user)
        
        context = {
            'user_name': user.get_full_name() or user.phone_number,
            'amount': f'{amount:,.0f}',
            'plan_name': plan_name,
            'dashboard_url': '/dashboard',
        }
        
        try:
            NotificationService.create_notification(
                user=user,
                template_code=SubscriptionNotificationService.TEMPLATE_PAYMENT_SUCCESS,
                context=context,
                channels=channels,
                priority='normal'
            )
            logger.info(f"Payment success notification sent to {user.phone_number}")
        except Exception as e:
            logger.error(f"Failed to send payment success notification: {e}")
    
    @staticmethod
    def notify_payment_failed(user, amount, error_message):
        """اعلان پرداخت ناموفق"""
        channels = SubscriptionNotificationService.get_user_notification_channels(user)
        
        context = {
            'user_name': user.get_full_name() or user.phone_number,
            'amount': f'{amount:,.0f}',
            'error_message': error_message,
            'retry_url': '/dashboard/subscription/payment',
        }
        
        try:
            NotificationService.create_notification(
                user=user,
                template_code=SubscriptionNotificationService.TEMPLATE_PAYMENT_FAILED,
                context=context,
                channels=channels,
                priority='high'
            )
            logger.info(f"Payment failed notification sent to {user.phone_number}")
        except Exception as e:
            logger.error(f"Failed to send payment failed notification: {e}")


class SubscriptionScheduledTasks:
    """تسک‌های زمان‌بندی شده برای اشتراک‌ها"""
    
    @staticmethod
    def check_expiring_subscriptions():
        """
        بررسی اشتراک‌های در حال انقضا
        باید روزانه اجرا شود
        """
        from .models import Subscription
        
        now = timezone.now()
        
        # اشتراک‌هایی که 7 روز دیگر منقضی می‌شوند
        seven_days = now + timedelta(days=7)
        expiring_7_days = Subscription.objects.filter(
            status='active',
            end_date__date=seven_days.date()
        )
        
        for sub in expiring_7_days:
            SubscriptionNotificationService.notify_subscription_expiring(sub, 7)
        
        # اشتراک‌هایی که 3 روز دیگر منقضی می‌شوند
        three_days = now + timedelta(days=3)
        expiring_3_days = Subscription.objects.filter(
            status='active',
            end_date__date=three_days.date()
        )
        
        for sub in expiring_3_days:
            SubscriptionNotificationService.notify_subscription_expiring(sub, 3)
        
        # اشتراک‌هایی که فردا منقضی می‌شوند
        one_day = now + timedelta(days=1)
        expiring_1_day = Subscription.objects.filter(
            status='active',
            end_date__date=one_day.date()
        )
        
        for sub in expiring_1_day:
            SubscriptionNotificationService.notify_subscription_expiring(sub, 1)
        
        logger.info(f"Checked expiring subscriptions: 7d={expiring_7_days.count()}, 3d={expiring_3_days.count()}, 1d={expiring_1_day.count()}")
    
    @staticmethod
    def check_expired_subscriptions():
        """
        بررسی و به‌روزرسانی اشتراک‌های منقضی شده
        باید روزانه اجرا شود
        """
        from .models import Subscription
        
        now = timezone.now()
        
        # اشتراک‌هایی که منقضی شده‌اند اما هنوز active هستند
        expired = Subscription.objects.filter(
            status='active',
            end_date__lt=now
        )
        
        for sub in expired:
            sub.status = 'expired'
            sub.save()
            SubscriptionNotificationService.notify_subscription_expired(sub)
        
        logger.info(f"Expired {expired.count()} subscriptions")
    
    @staticmethod
    def check_quota_warnings():
        """
        بررسی هشدارهای سهمیه
        باید هر ساعت اجرا شود
        """
        from .models import Subscription
        from .usage import UsageService
        
        now = timezone.now()
        
        # همه اشتراک‌های فعال
        active_subscriptions = Subscription.objects.filter(
            status='active',
            end_date__gt=now
        )
        
        for sub in active_subscriptions:
            user = sub.user
            quota_percentage = UsageService.get_quota_percentage(user)
            
            # هشدار 80% سهمیه روزانه
            if 80 <= quota_percentage['daily'] < 100:
                SubscriptionNotificationService.notify_quota_warning(user, quota_percentage['daily'], 'daily')
            
            # هشدار 80% سهمیه ماهانه
            if 80 <= quota_percentage['monthly'] < 100:
                SubscriptionNotificationService.notify_quota_warning(user, quota_percentage['monthly'], 'monthly')
        
        logger.info(f"Checked quota warnings for {active_subscriptions.count()} subscriptions")
