from django.db import models
from django.conf import settings
from django.utils import timezone
from django.db.models import Sum, Count, Avg, Q, F
from decimal import Decimal
import uuid
from datetime import datetime, timedelta


class MetricType(models.TextChoices):
    """انواع متریک‌ها"""
    USER_REGISTRATION = 'user_registration', 'ثبت‌نام کاربران'
    USER_LOGIN = 'user_login', 'ورود کاربران'
    QUERY_COUNT = 'query_count', 'تعداد کوئری'
    TOKEN_USAGE = 'token_usage', 'مصرف توکن'
    REVENUE = 'revenue', 'درآمد'
    SUBSCRIPTION = 'subscription', 'اشتراک'
    PAYMENT = 'payment', 'پرداخت'
    API_USAGE = 'api_usage', 'استفاده از API'
    ERROR_RATE = 'error_rate', 'نرخ خطا'
    RESPONSE_TIME = 'response_time', 'زمان پاسخ'


class DailyMetric(models.Model):
    """آمار روزانه"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    date = models.DateField(verbose_name='تاریخ', db_index=True)
    metric_type = models.CharField(
        max_length=30,
        choices=MetricType.choices,
        verbose_name='نوع متریک',
        db_index=True
    )
    
    # مقادیر
    count = models.IntegerField(default=0, verbose_name='تعداد')
    sum_value = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0,
        verbose_name='مجموع'
    )
    avg_value = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        verbose_name='میانگین'
    )
    min_value = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name='حداقل'
    )
    max_value = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name='حداکثر'
    )
    
    # متادیتا
    metadata = models.JSONField(
        default=dict,
        blank=True,
        verbose_name='متادیتا'
    )
    
    # تاریخ‌ها
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'متریک روزانه'
        verbose_name_plural = 'متریک‌های روزانه'
        unique_together = ['date', 'metric_type']
        ordering = ['-date', 'metric_type']
        indexes = [
            models.Index(fields=['date', 'metric_type']),
        ]
    
    def __str__(self):
        return f"{self.date} - {self.get_metric_type_display()}: {self.count}"
    
    @classmethod
    def record_metric(cls, metric_type, value=1, date=None):
        """ثبت یک متریک"""
        if date is None:
            date = timezone.now().date()
        
        metric, created = cls.objects.get_or_create(
            date=date,
            metric_type=metric_type,
            defaults={'count': 0, 'sum_value': 0}
        )
        
        # به‌روزرسانی مقادیر
        metric.count += 1
        metric.sum_value += Decimal(str(value))
        
        # محاسبه میانگین
        if metric.count > 0:
            metric.avg_value = metric.sum_value / metric.count
        
        # به‌روزرسانی min/max
        if metric.min_value is None or value < metric.min_value:
            metric.min_value = Decimal(str(value))
        if metric.max_value is None or value > metric.max_value:
            metric.max_value = Decimal(str(value))
        
        metric.save()
        return metric


class UserAnalytics(models.Model):
    """تحلیل رفتار کاربران"""
    
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        primary_key=True,
        related_name='analytics',
        verbose_name='کاربر'
    )
    
    # آمار کلی
    total_queries = models.IntegerField(default=0, verbose_name='کل کوئری‌ها')
    total_tokens = models.BigIntegerField(default=0, verbose_name='کل توکن‌ها')
    total_conversations = models.IntegerField(default=0, verbose_name='کل مکالمات')
    total_spent = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        verbose_name='کل هزینه'
    )
    
    # آمار زمانی
    last_query_at = models.DateTimeField(null=True, blank=True, verbose_name='آخرین کوئری')
    last_payment_at = models.DateTimeField(null=True, blank=True, verbose_name='آخرین پرداخت')
    active_days = models.IntegerField(default=0, verbose_name='روزهای فعال')
    
    # میانگین‌ها
    avg_queries_per_day = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        default=0,
        verbose_name='میانگین کوئری روزانه'
    )
    avg_tokens_per_query = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name='میانگین توکن هر کوئری'
    )
    avg_response_time = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        default=0,
        verbose_name='میانگین زمان پاسخ (ثانیه)'
    )
    
    # رتبه‌بندی
    engagement_score = models.IntegerField(
        default=0,
        verbose_name='امتیاز تعامل',
        help_text='0-100'
    )
    value_score = models.IntegerField(
        default=0,
        verbose_name='امتیاز ارزش',
        help_text='0-100'
    )
    
    # تنظیمات
    preferred_model = models.CharField(
        max_length=50,
        blank=True,
        verbose_name='مدل ترجیحی'
    )
    preferred_response_mode = models.CharField(
        max_length=50,
        blank=True,
        verbose_name='حالت پاسخ ترجیحی'
    )
    
    # متادیتا
    metadata = models.JSONField(
        default=dict,
        blank=True,
        verbose_name='متادیتا'
    )
    
    # تاریخ‌ها
    first_activity = models.DateTimeField(null=True, blank=True, verbose_name='اولین فعالیت')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'تحلیل کاربر'
        verbose_name_plural = 'تحلیل کاربران'
    
    def __str__(self):
        return f"{self.user.email} Analytics"
    
    def update_query_stats(self, tokens=0, response_time=0):
        """به‌روزرسانی آمار کوئری"""
        self.total_queries += 1
        self.total_tokens += tokens
        self.last_query_at = timezone.now()
        
        # محاسبه میانگین‌ها
        if self.total_queries > 0:
            self.avg_tokens_per_query = self.total_tokens / self.total_queries
        
        # به‌روزرسانی زمان پاسخ
        if response_time > 0:
            if self.avg_response_time == 0:
                self.avg_response_time = Decimal(str(response_time))
            else:
                # میانگین متحرک
                self.avg_response_time = (
                    self.avg_response_time * Decimal('0.9') +
                    Decimal(str(response_time)) * Decimal('0.1')
                )
        
        self.calculate_scores()
        self.save()
    
    def calculate_scores(self):
        """محاسبه امتیازات"""
        # امتیاز تعامل (بر اساس فعالیت)
        if self.total_queries > 0:
            days_since_registration = (timezone.now() - self.created_at).days or 1
            activity_rate = min(100, (self.total_queries / days_since_registration) * 10)
            recency_score = 100 if self.last_query_at and (
                timezone.now() - self.last_query_at
            ).days < 7 else 50
            self.engagement_score = int((activity_rate + recency_score) / 2)
        
        # امتیاز ارزش (بر اساس هزینه)
        if self.total_spent > 0:
            self.value_score = min(100, int(self.total_spent / 1000000 * 100))  # 1M = 100


class RevenueAnalytics(models.Model):
    """تحلیل درآمد"""
    
    PERIOD_CHOICES = [
        ('daily', 'روزانه'),
        ('weekly', 'هفتگی'),
        ('monthly', 'ماهانه'),
        ('quarterly', 'فصلی'),
        ('yearly', 'سالانه'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    period_type = models.CharField(
        max_length=20,
        choices=PERIOD_CHOICES,
        verbose_name='نوع دوره'
    )
    period_start = models.DateField(verbose_name='شروع دوره')
    period_end = models.DateField(verbose_name='پایان دوره')
    
    # درآمد
    total_revenue = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0,
        verbose_name='کل درآمد'
    )
    subscription_revenue = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0,
        verbose_name='درآمد اشتراک'
    )
    one_time_revenue = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0,
        verbose_name='درآمد یکباره'
    )
    
    # تعداد تراکنش‌ها
    total_transactions = models.IntegerField(default=0, verbose_name='کل تراکنش‌ها')
    successful_transactions = models.IntegerField(default=0, verbose_name='تراکنش‌های موفق')
    failed_transactions = models.IntegerField(default=0, verbose_name='تراکنش‌های ناموفق')
    
    # کاربران
    new_customers = models.IntegerField(default=0, verbose_name='مشتریان جدید')
    returning_customers = models.IntegerField(default=0, verbose_name='مشتریان بازگشتی')
    
    # میانگین‌ها
    avg_transaction_value = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        verbose_name='میانگین ارزش تراکنش'
    )
    avg_customer_value = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        verbose_name='میانگین ارزش مشتری'
    )
    
    # نرخ‌ها
    conversion_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        verbose_name='نرخ تبدیل (%)'
    )
    churn_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        verbose_name='نرخ ریزش (%)'
    )
    growth_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        verbose_name='نرخ رشد (%)'
    )
    
    # تحلیل درگاه‌ها
    gateway_breakdown = models.JSONField(
        default=dict,
        verbose_name='تفکیک درگاه‌ها'
    )
    
    # تحلیل پلن‌ها
    plan_breakdown = models.JSONField(
        default=dict,
        verbose_name='تفکیک پلن‌ها'
    )
    
    # متادیتا
    metadata = models.JSONField(
        default=dict,
        blank=True,
        verbose_name='متادیتا'
    )
    
    # تاریخ‌ها
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'تحلیل درآمد'
        verbose_name_plural = 'تحلیل‌های درآمد'
        unique_together = ['period_type', 'period_start', 'period_end']
        ordering = ['-period_start']
        indexes = [
            models.Index(fields=['period_type', 'period_start']),
        ]
    
    def __str__(self):
        return f"{self.get_period_type_display()} - {self.period_start} to {self.period_end}"
    
    @classmethod
    def calculate_for_period(cls, period_type, start_date, end_date):
        """محاسبه آمار برای یک دوره"""
        from payments.models import Transaction, PaymentStatus
        from subscriptions.models import Subscription
        
        # دریافت تراکنش‌های دوره
        transactions = Transaction.objects.filter(
            created_at__date__gte=start_date,
            created_at__date__lte=end_date
        )
        
        # محاسبات اصلی
        total_revenue = transactions.filter(
            status=PaymentStatus.SUCCESS
        ).aggregate(total=Sum('amount'))['total'] or 0
        
        successful = transactions.filter(status=PaymentStatus.SUCCESS).count()
        failed = transactions.filter(status=PaymentStatus.FAILED).count()
        
        # ایجاد یا به‌روزرسانی
        analytics, created = cls.objects.update_or_create(
            period_type=period_type,
            period_start=start_date,
            period_end=end_date,
            defaults={
                'total_revenue': total_revenue,
                'total_transactions': transactions.count(),
                'successful_transactions': successful,
                'failed_transactions': failed,
                'conversion_rate': (successful / (successful + failed) * 100) if (successful + failed) > 0 else 0,
                'avg_transaction_value': total_revenue / successful if successful > 0 else 0
            }
        )
        
        return analytics


class SystemMetrics(models.Model):
    """متریک‌های سیستم"""
    
    timestamp = models.DateTimeField(
        default=timezone.now,
        verbose_name='زمان',
        db_index=True
    )
    
    # منابع سیستم
    cpu_usage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        verbose_name='مصرف CPU (%)'
    )
    memory_usage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        verbose_name='مصرف RAM (%)'
    )
    disk_usage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        verbose_name='مصرف دیسک (%)'
    )
    
    # کارایی
    active_connections = models.IntegerField(
        default=0,
        verbose_name='اتصالات فعال'
    )
    request_per_second = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name='درخواست در ثانیه'
    )
    avg_response_time = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name='میانگین زمان پاسخ (ms)'
    )
    
    # خطاها
    error_count = models.IntegerField(
        default=0,
        verbose_name='تعداد خطا'
    )
    error_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        verbose_name='نرخ خطا (%)'
    )
    
    # Queue
    queue_size = models.IntegerField(
        default=0,
        verbose_name='اندازه صف'
    )
    queue_processing_time = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name='زمان پردازش صف (ms)'
    )
    
    # Cache
    cache_hit_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        verbose_name='نرخ Cache Hit (%)'
    )
    
    class Meta:
        verbose_name = 'متریک سیستم'
        verbose_name_plural = 'متریک‌های سیستم'
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['-timestamp']),
        ]
    
    def __str__(self):
        return f"System Metrics - {self.timestamp}"
