"""
مدل و سرویس‌های مدیریت مصرف کاربران
"""
from django.db import models
from django.conf import settings
from django.utils import timezone
from django.db.models import Sum, Count
from django.db.models.functions import TruncDate
from datetime import timedelta
import uuid
import logging

logger = logging.getLogger(__name__)


class ModelUsageLog(models.Model):
    """گزارش مصرف مدل‌ها - لاگ هر درخواست به مدل‌های AI"""
    
    ACTION_TYPES = [
        ('query', 'سوال'),
        ('file_upload', 'آپلود فایل'),
        ('file_download', 'دانلود فایل'),
        ('api_call', 'فراخوانی API'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # کاربر و اشتراک
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='model_usage_logs',
        verbose_name='کاربر'
    )
    subscription = models.ForeignKey(
        'subscriptions.Subscription',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='model_usage_logs',
        verbose_name='اشتراک'
    )
    
    # نوع عملیات
    action_type = models.CharField(
        max_length=20,
        choices=ACTION_TYPES,
        default='query',
        verbose_name='نوع عملیات'
    )
    
    # مصرف توکن - تفکیک ورودی و خروجی
    input_tokens = models.IntegerField(default=0, verbose_name='توکن ورودی')
    output_tokens = models.IntegerField(default=0, verbose_name='توکن خروجی')
    
    # نام پلن در زمان ثبت (برای گزارش‌گیری)
    plan_name = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='نام پلن',
        help_text='نام پلن در زمان ثبت لاگ'
    )
    
    # متادیتا
    metadata = models.JSONField(
        default=dict,
        blank=True,
        verbose_name='متادیتا',
        help_text='اطلاعات اضافی مثل model_used, conversation_id, etc.'
    )
    
    # اطلاعات درخواست
    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
        verbose_name='آدرس IP'
    )
    user_agent = models.CharField(
        max_length=500,
        blank=True,
        verbose_name='User Agent'
    )
    
    # تاریخ
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='زمان ایجاد')
    
    class Meta:
        verbose_name = 'گزارش مصرف مدل'
        verbose_name_plural = 'گزارش مصرف مدل‌ها'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'action_type', 'created_at']),
            models.Index(fields=['subscription', 'created_at']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"{self.user} - {self.action_type} - {self.created_at}"
    
    @property
    def total_tokens(self):
        """مجموع توکن‌های ورودی و خروجی"""
        return self.input_tokens + self.output_tokens


# Alias for backward compatibility
UsageLog = ModelUsageLog


class UsageService:
    """سرویس مدیریت مصرف"""
    
    @staticmethod
    def log_usage(
        user,
        action_type: str = 'query',
        input_tokens: int = 0,
        output_tokens: int = 0,
        tokens_used: int = 0,  # backward compatibility
        subscription=None,
        metadata: dict = None,
        ip_address: str = None,
        user_agent: str = None
    ) -> ModelUsageLog:
        """ثبت یک مصرف جدید"""
        
        # اگر subscription ارسال نشده، اشتراک فعال کاربر را پیدا کن
        if subscription is None:
            subscription = user.subscriptions.filter(
                status='active',
                end_date__gt=timezone.now()
            ).first()
        
        # نام پلن در زمان ثبت
        plan_name = ''
        if subscription and subscription.plan:
            plan_name = subscription.plan.name
        
        # backward compatibility: اگر tokens_used داده شده ولی input/output نه
        if tokens_used > 0 and input_tokens == 0 and output_tokens == 0:
            input_tokens = tokens_used
        
        log = ModelUsageLog.objects.create(
            user=user,
            subscription=subscription,
            action_type=action_type,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            plan_name=plan_name,
            metadata=metadata or {},
            ip_address=ip_address,
            user_agent=user_agent or ''
        )
        
        logger.info(f"Usage logged: {user} - {action_type} - {input_tokens}+{output_tokens} tokens")
        return log
    
    @staticmethod
    def get_daily_usage(user, subscription=None, date=None) -> int:
        """تعداد query های یک روز خاص برای اشتراک فعلی"""
        if date is None:
            date = timezone.now().date()
        
        queryset = UsageLog.objects.filter(
            user=user,
            action_type='query',
            created_at__date=date
        )
        
        # فقط مصرف اشتراک فعلی را بشمار
        if subscription:
            queryset = queryset.filter(subscription=subscription)
        
        return queryset.count()
    
    @staticmethod
    def get_monthly_usage(user, subscription=None) -> int:
        """تعداد query های اشتراک فعلی (از تاریخ شروع اشتراک)"""
        
        # اگر اشتراک داده نشده، اشتراک فعال را پیدا کن
        if subscription is None:
            subscription = user.subscriptions.filter(
                status__in=['active', 'trial'],
                end_date__gt=timezone.now()
            ).first()
        
        if not subscription:
            return 0
        
        # مصرف از تاریخ شروع اشتراک
        return UsageLog.objects.filter(
            user=user,
            action_type='query',
            subscription=subscription,
            created_at__gte=subscription.start_date
        ).count()
    
    @staticmethod
    def get_tokens_used_today(user) -> dict:
        """توکن‌های مصرفی امروز"""
        today = timezone.now().date()
        
        result = ModelUsageLog.objects.filter(
            user=user,
            created_at__date=today
        ).aggregate(
            input_total=Sum('input_tokens'),
            output_total=Sum('output_tokens')
        )
        
        return {
            'input': result['input_total'] or 0,
            'output': result['output_total'] or 0,
            'total': (result['input_total'] or 0) + (result['output_total'] or 0)
        }
    
    @staticmethod
    def get_tokens_used_month(user, year=None, month=None) -> dict:
        """توکن‌های مصرفی این ماه"""
        now = timezone.now()
        if year is None:
            year = now.year
        if month is None:
            month = now.month
        
        result = ModelUsageLog.objects.filter(
            user=user,
            created_at__year=year,
            created_at__month=month
        ).aggregate(
            input_total=Sum('input_tokens'),
            output_total=Sum('output_tokens')
        )
        
        return {
            'input': result['input_total'] or 0,
            'output': result['output_total'] or 0,
            'total': (result['input_total'] or 0) + (result['output_total'] or 0)
        }
    
    @staticmethod
    def get_usage_stats(user, days: int = 30) -> dict:
        """آمار مصرف کاربر در N روز اخیر"""
        
        start_date = timezone.now() - timedelta(days=days)
        
        # آمار کلی
        logs = ModelUsageLog.objects.filter(
            user=user,
            created_at__gte=start_date
        )
        
        total_queries = logs.filter(action_type='query').count()
        token_totals = logs.aggregate(
            input_total=Sum('input_tokens'),
            output_total=Sum('output_tokens')
        )
        
        # آمار روزانه
        daily_stats = logs.filter(action_type='query').annotate(
            date=TruncDate('created_at')
        ).values('date').annotate(
            count=Count('id'),
            input_tokens=Sum('input_tokens'),
            output_tokens=Sum('output_tokens')
        ).order_by('date')
        
        return {
            'total_queries': total_queries,
            'total_input_tokens': token_totals['input_total'] or 0,
            'total_output_tokens': token_totals['output_total'] or 0,
            'total_tokens': (token_totals['input_total'] or 0) + (token_totals['output_total'] or 0),
            'daily_stats': list(daily_stats),
            'period_days': days
        }
    
    @staticmethod
    def check_quota(user, subscription=None) -> tuple:
        """
        بررسی سهمیه کاربر
        
        Returns:
            tuple: (can_query: bool, message: str, usage_info: dict)
        """
        
        # دریافت اشتراک فعال
        if subscription is None:
            subscription = user.subscriptions.filter(
                status='active',
                end_date__gt=timezone.now()
            ).first()
        
        if not subscription:
            return False, 'اشتراک فعالی ندارید', {}
        
        # دریافت محدودیت‌ها از پلن
        features = subscription.plan.features or {}
        max_daily = features.get('max_queries_per_day', 10)
        max_monthly = features.get('max_queries_per_month', 300)
        
        # مصرف فعلی - فقط برای اشتراک فعلی
        daily_used = UsageService.get_daily_usage(user, subscription)
        monthly_used = UsageService.get_monthly_usage(user, subscription)
        
        usage_info = {
            'daily_used': daily_used,
            'daily_limit': max_daily,
            'daily_remaining': max(0, max_daily - daily_used),
            'monthly_used': monthly_used,
            'monthly_limit': max_monthly,
            'monthly_remaining': max(0, max_monthly - monthly_used),
        }
        
        # بررسی محدودیت روزانه
        if daily_used >= max_daily:
            return False, f'سهمیه روزانه شما ({max_daily} سوال) تمام شده است', usage_info
        
        # بررسی محدودیت ماهانه
        if monthly_used >= max_monthly:
            return False, f'سهمیه ماهانه شما ({max_monthly} سوال) تمام شده است', usage_info
        
        return True, 'OK', usage_info
    
    @staticmethod
    def get_quota_percentage(user) -> dict:
        """درصد مصرف سهمیه"""
        
        subscription = user.subscriptions.filter(
            status='active',
            end_date__gt=timezone.now()
        ).first()
        
        if not subscription:
            return {'daily': 0, 'monthly': 0}
        
        features = subscription.plan.features or {}
        max_daily = features.get('max_queries_per_day', 10)
        max_monthly = features.get('max_queries_per_month', 300)
        
        daily_used = UsageService.get_daily_usage(user, subscription)
        monthly_used = UsageService.get_monthly_usage(user, subscription)
        
        return {
            'daily': min(100, int((daily_used / max_daily) * 100)) if max_daily > 0 else 0,
            'monthly': min(100, int((monthly_used / max_monthly) * 100)) if max_monthly > 0 else 0,
        }
