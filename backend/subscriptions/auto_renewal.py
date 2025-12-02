"""
سرویس تمدید خودکار اشتراک
"""
import logging
from django.utils import timezone
from django.db import transaction
from datetime import timedelta
from decimal import Decimal

logger = logging.getLogger(__name__)


class AutoRenewalService:
    """سرویس تمدید خودکار اشتراک‌ها"""
    
    @staticmethod
    def process_auto_renewals():
        """
        پردازش تمدید خودکار اشتراک‌ها
        باید روزانه اجرا شود
        """
        from .models import Subscription
        from .notification_service import SubscriptionNotificationService
        
        now = timezone.now()
        
        # اشتراک‌هایی که:
        # 1. auto_renew فعال است
        # 2. فردا یا امروز منقضی می‌شوند
        # 3. هنوز active هستند
        tomorrow = now + timedelta(days=1)
        
        subscriptions_to_renew = Subscription.objects.filter(
            auto_renew=True,
            status='active',
            end_date__lte=tomorrow,
            end_date__gte=now
        )
        
        renewed_count = 0
        failed_count = 0
        
        for subscription in subscriptions_to_renew:
            try:
                success = AutoRenewalService.renew_subscription(subscription)
                if success:
                    renewed_count += 1
                else:
                    failed_count += 1
            except Exception as e:
                logger.error(f"Auto-renewal failed for subscription {subscription.id}: {e}")
                failed_count += 1
        
        logger.info(f"Auto-renewal completed: {renewed_count} renewed, {failed_count} failed")
        return renewed_count, failed_count
    
    @staticmethod
    @transaction.atomic
    def renew_subscription(subscription) -> bool:
        """
        تمدید یک اشتراک
        
        Returns:
            bool: True اگر تمدید موفق بود
        """
        from .notification_service import SubscriptionNotificationService
        from payments.models import Wallet, Transaction
        
        user = subscription.user
        plan = subscription.plan
        
        # بررسی قیمت پلن
        if plan.price <= 0:
            # پلن رایگان - تمدید بدون پرداخت
            return AutoRenewalService._extend_subscription(subscription)
        
        # بررسی موجودی کیف پول
        try:
            wallet = user.wallet
        except Wallet.DoesNotExist:
            logger.warning(f"No wallet for user {user.phone_number}")
            SubscriptionNotificationService.notify_payment_failed(
                user, plan.price, 'کیف پول یافت نشد'
            )
            return False
        
        if wallet.balance < plan.price:
            logger.warning(f"Insufficient balance for user {user.phone_number}: {wallet.balance} < {plan.price}")
            SubscriptionNotificationService.notify_payment_failed(
                user, plan.price, 'موجودی کیف پول کافی نیست'
            )
            return False
        
        # کسر از کیف پول
        try:
            wallet.withdraw(
                amount=plan.price,
                description=f'تمدید خودکار اشتراک {plan.name}'
            )
        except Exception as e:
            logger.error(f"Wallet withdrawal failed: {e}")
            SubscriptionNotificationService.notify_payment_failed(
                user, plan.price, str(e)
            )
            return False
        
        # ثبت تراکنش
        Transaction.objects.create(
            user=user,
            amount=plan.price,
            transaction_type='subscription',
            status='completed',
            description=f'تمدید خودکار اشتراک {plan.name}',
            metadata={
                'subscription_id': str(subscription.id),
                'plan_id': str(plan.id),
                'auto_renewal': True
            }
        )
        
        # تمدید اشتراک
        success = AutoRenewalService._extend_subscription(subscription)
        
        if success:
            # ارسال اعلان موفقیت
            SubscriptionNotificationService.notify_subscription_renewed(subscription)
            SubscriptionNotificationService.notify_payment_success(user, plan.price, plan.name)
        
        return success
    
    @staticmethod
    def _extend_subscription(subscription) -> bool:
        """تمدید تاریخ انقضای اشتراک"""
        try:
            plan = subscription.plan
            
            # محاسبه تاریخ جدید
            if subscription.end_date > timezone.now():
                # اگر هنوز منقضی نشده، از تاریخ انقضا اضافه کن
                new_end_date = subscription.end_date + timedelta(days=plan.duration_days)
            else:
                # اگر منقضی شده، از الان اضافه کن
                new_end_date = timezone.now() + timedelta(days=plan.duration_days)
            
            subscription.end_date = new_end_date
            subscription.status = 'active'
            subscription.save()
            
            logger.info(f"Subscription {subscription.id} extended to {new_end_date}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to extend subscription {subscription.id}: {e}")
            return False
    
    @staticmethod
    def enable_auto_renewal(subscription) -> bool:
        """فعال‌سازی تمدید خودکار"""
        subscription.auto_renew = True
        subscription.save(update_fields=['auto_renew'])
        logger.info(f"Auto-renewal enabled for subscription {subscription.id}")
        return True
    
    @staticmethod
    def disable_auto_renewal(subscription) -> bool:
        """غیرفعال‌سازی تمدید خودکار"""
        subscription.auto_renew = False
        subscription.save(update_fields=['auto_renew'])
        logger.info(f"Auto-renewal disabled for subscription {subscription.id}")
        return True
    
    @staticmethod
    def check_renewal_eligibility(subscription) -> dict:
        """
        بررسی امکان تمدید خودکار
        
        Returns:
            dict: اطلاعات وضعیت تمدید
        """
        from payments.models import Wallet
        
        user = subscription.user
        plan = subscription.plan
        
        result = {
            'can_renew': False,
            'auto_renew_enabled': subscription.auto_renew,
            'plan_price': plan.price,
            'wallet_balance': Decimal('0'),
            'balance_sufficient': False,
            'days_until_expiry': 0,
            'message': ''
        }
        
        # روزهای باقیمانده
        if subscription.end_date:
            delta = subscription.end_date - timezone.now()
            result['days_until_expiry'] = max(0, delta.days)
        
        # بررسی پلن رایگان
        if plan.price <= 0:
            result['can_renew'] = True
            result['balance_sufficient'] = True
            result['message'] = 'پلن رایگان - تمدید بدون پرداخت'
            return result
        
        # بررسی کیف پول
        try:
            wallet = user.wallet
            result['wallet_balance'] = wallet.balance
            result['balance_sufficient'] = wallet.balance >= plan.price
            
            if result['balance_sufficient']:
                result['can_renew'] = True
                result['message'] = 'موجودی کافی برای تمدید'
            else:
                result['message'] = f'موجودی کافی نیست. نیاز به {plan.price - wallet.balance:,.0f} ریال شارژ'
                
        except Wallet.DoesNotExist:
            result['message'] = 'کیف پول یافت نشد'
        
        return result
