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


class UsageLog(models.Model):
    """لاگ مصرف کاربران"""
    
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
        related_name='usage_logs',
        verbose_name='کاربر'
    )
    subscription = models.ForeignKey(
        'subscriptions.Subscription',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='usage_logs',
        verbose_name='اشتراک'
    )
    
    # نوع عملیات
    action_type = models.CharField(
        max_length=20,
        choices=ACTION_TYPES,
        default='query',
        verbose_name='نوع عملیات'
    )
    
    # مصرف
    tokens_used = models.IntegerField(default=0, verbose_name='توکن مصرفی')
    
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
        verbose_name = 'لاگ مصرف'
        verbose_name_plural = 'لاگ‌های مصرف'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'action_type', 'created_at']),
            models.Index(fields=['subscription', 'created_at']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"{self.user} - {self.action_type} - {self.created_at}"


class UsageService:
    """سرویس مدیریت مصرف"""
    
    @staticmethod
    def log_usage(
        user,
        action_type: str = 'query',
        tokens_used: int = 0,
        subscription=None,
        metadata: dict = None,
        ip_address: str = None,
        user_agent: str = None
    ) -> UsageLog:
        """ثبت یک مصرف جدید"""
        
        # اگر subscription ارسال نشده، اشتراک فعال کاربر را پیدا کن
        if subscription is None:
            subscription = user.subscriptions.filter(
                status='active',
                end_date__gt=timezone.now()
            ).first()
        
        log = UsageLog.objects.create(
            user=user,
            subscription=subscription,
            action_type=action_type,
            tokens_used=tokens_used,
            metadata=metadata or {},
            ip_address=ip_address,
            user_agent=user_agent or ''
        )
        
        logger.info(f"Usage logged: {user} - {action_type} - {tokens_used} tokens")
        return log
    
    @staticmethod
    def get_daily_usage(user, date=None) -> int:
        """تعداد query های یک روز خاص"""
        if date is None:
            date = timezone.now().date()
        
        return UsageLog.objects.filter(
            user=user,
            action_type='query',
            created_at__date=date
        ).count()
    
    @staticmethod
    def get_monthly_usage(user, year=None, month=None) -> int:
        """تعداد query های یک ماه خاص"""
        now = timezone.now()
        if year is None:
            year = now.year
        if month is None:
            month = now.month
        
        return UsageLog.objects.filter(
            user=user,
            action_type='query',
            created_at__year=year,
            created_at__month=month
        ).count()
    
    @staticmethod
    def get_tokens_used_today(user) -> int:
        """توکن‌های مصرفی امروز"""
        today = timezone.now().date()
        
        result = UsageLog.objects.filter(
            user=user,
            created_at__date=today
        ).aggregate(total=Sum('tokens_used'))
        
        return result['total'] or 0
    
    @staticmethod
    def get_tokens_used_month(user, year=None, month=None) -> int:
        """توکن‌های مصرفی این ماه"""
        now = timezone.now()
        if year is None:
            year = now.year
        if month is None:
            month = now.month
        
        result = UsageLog.objects.filter(
            user=user,
            created_at__year=year,
            created_at__month=month
        ).aggregate(total=Sum('tokens_used'))
        
        return result['total'] or 0
    
    @staticmethod
    def get_usage_stats(user, days: int = 30) -> dict:
        """آمار مصرف کاربر در N روز اخیر"""
        
        start_date = timezone.now() - timedelta(days=days)
        
        # آمار کلی
        logs = UsageLog.objects.filter(
            user=user,
            created_at__gte=start_date
        )
        
        total_queries = logs.filter(action_type='query').count()
        total_tokens = logs.aggregate(total=Sum('tokens_used'))['total'] or 0
        
        # آمار روزانه
        daily_stats = logs.filter(action_type='query').annotate(
            date=TruncDate('created_at')
        ).values('date').annotate(
            count=Count('id'),
            tokens=Sum('tokens_used')
        ).order_by('date')
        
        return {
            'total_queries': total_queries,
            'total_tokens': total_tokens,
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
        
        # مصرف فعلی
        daily_used = UsageService.get_daily_usage(user)
        monthly_used = UsageService.get_monthly_usage(user)
        
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
        
        daily_used = UsageService.get_daily_usage(user)
        monthly_used = UsageService.get_monthly_usage(user)
        
        return {
            'daily': min(100, int((daily_used / max_daily) * 100)) if max_daily > 0 else 0,
            'monthly': min(100, int((monthly_used / max_monthly) * 100)) if max_monthly > 0 else 0,
        }
