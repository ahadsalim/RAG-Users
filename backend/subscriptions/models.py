from django.db import models
from django.conf import settings
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
import uuid


class Plan(models.Model):
    """مدل پلن اشتراک"""
    
    PLAN_TYPE_CHOICES = [
        ('individual', _('حقیقی')),
        ('business', _('حقوقی')),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(_("نام پلن"), max_length=100)
    description = models.TextField(_("توضیحات"), blank=True)
    plan_type = models.CharField(_("نوع پلن"), max_length=20, choices=PLAN_TYPE_CHOICES, default='individual')
    
    # قیمت همیشه در واحد پایه (Base Currency) ذخیره می‌شود
    price = models.DecimalField(_("قیمت"), max_digits=15, decimal_places=0, help_text=_('قیمت به ارز پایه سایت'))
    
    duration_days = models.IntegerField(_("مدت به روز"), default=30)
    max_queries_per_day = models.IntegerField(_("سوال/روز"), default=10)
    max_queries_per_month = models.IntegerField(_("سوال/ماه"), default=200)
    max_active_sessions = models.IntegerField(_("حداکثر جلسات فعال"), default=3, help_text=_("حداکثر تعداد دستگاه‌های همزمان"))
    max_organization_members = models.IntegerField(_("حداکثر اعضای سازمان"), default=1, help_text=_("فقط برای پلن‌های حقوقی"))
    features = models.JSONField(_("ویژگی‌ها"), default=dict, blank=True)
    is_active = models.BooleanField(_("فعال"), default=True)
    created_at = models.DateTimeField(_("تاریخ ایجاد"), auto_now_add=True)
    updated_at = models.DateTimeField(_("تاریخ به‌روزرسانی"), auto_now=True)
    
    class Meta:
        verbose_name = _("پلن")
        verbose_name_plural = _("پلن‌ها")
        ordering = ['price']
    
    def __str__(self):
        return self.name
    
    def get_formatted_price(self, target_currency=None):
        """Get formatted price based on currency settings
        
        Args:
            target_currency: ارز مورد نظر برای نمایش (اختیاری)
        
        Returns:
            قیمت فرمت شده با واحد ارز
        """
        from finance.models import Currency
        
        if target_currency is None:
            # Use base currency
            target_currency = Currency.get_base_currency()
        
        if target_currency:
            # Price is already in base currency, convert to target if different
            if target_currency.is_base:
                # No conversion needed
                return target_currency.format_price(self.price)
            else:
                # Convert from base to target currency
                converted_price = target_currency.convert_from_base(self.price)
                return target_currency.format_price(converted_price)
        else:
            # Fallback to plain price
            return f"{int(self.price):,}"
    
    def get_price_display(self):
        """Get price display for admin (in base currency)"""
        from finance.models import Currency
        base = Currency.get_base_currency()
        if base:
            return base.format_price(self.price)
        return f"{int(self.price):,}"
    
    def get_final_price(self):
        """محاسبه قیمت نهایی با احتساب مالیات
        
        Returns:
            Decimal: قیمت نهایی شامل مالیات
        """
        from finance.models import FinancialSettings
        from decimal import Decimal
        
        # دریافت تنظیمات مالی
        financial_settings = FinancialSettings.get_settings()
        tax_rate = financial_settings.tax_rate if financial_settings else Decimal('10')
        
        # محاسبه مالیات
        tax_amount = (self.price * tax_rate) / Decimal('100')
        
        # قیمت نهایی = قیمت پایه + مالیات
        final_price = self.price + tax_amount
        
        return final_price


class Subscription(models.Model):
    """مدل اشتراک کاربر"""
    
    STATUS_CHOICES = [
        ('active', _('فعال')),
        ('expired', _('منقضی شده')),
        ('cancelled', _('لغو شده')),
        ('pending', _('در انتظار')),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='subscriptions',
        verbose_name=_("کاربر")
    )
    plan = models.ForeignKey(
        Plan,
        on_delete=models.PROTECT,
        related_name='subscriptions',
        verbose_name=_("پلن")
    )
    status = models.CharField(_("وضعیت"), max_length=20, choices=STATUS_CHOICES, default='pending')
    start_date = models.DateTimeField(_("تاریخ شروع"), default=timezone.now)
    end_date = models.DateTimeField(_("تاریخ پایان"))
    auto_renew = models.BooleanField(_("تمدید خودکار"), default=False)
    created_at = models.DateTimeField(_("تاریخ ایجاد"), auto_now_add=True)
    updated_at = models.DateTimeField(_("تاریخ به‌روزرسانی"), auto_now=True)
    
    class Meta:
        verbose_name = _("اشتراک کاربر")
        verbose_name_plural = _("اشتراک کاربران")
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.email} - {self.plan.name}"
    
    @property
    def is_active(self):
        """بررسی فعال بودن اشتراک"""
        return self.status == 'active' and self.end_date > timezone.now()
    
    def activate(self):
        """فعال‌سازی اشتراک"""
        self.status = 'active'
        self.save()
    
    def cancel(self):
        """لغو اشتراک"""
        self.status = 'cancelled'
        self.auto_renew = False
        self.save()
    
    def renew(self):
        """تمدید اشتراک"""
        from datetime import timedelta
        self.status = 'active'
        self.start_date = timezone.now()
        self.end_date = timezone.now() + timedelta(days=self.plan.duration_days)
        self.save()
    
    def can_query(self):
        """
        بررسی اینکه آیا کاربر می‌تواند query بفرستد
        
        Returns:
            tuple: (can_query: bool, message: str)
        """
        # بررسی فعال بودن اشتراک
        if not self.is_active:
            return False, "اشتراک شما منقضی شده است"
        
        # دریافت محدودیت‌ها از features
        features = self.plan.features or {}
        max_queries_per_day = features.get('max_queries_per_day', 10)
        max_queries_per_month = features.get('max_queries_per_month', self.plan.max_queries_per_month or 200)
        
        # بررسی محدودیت روزانه - استفاده از UsageService برای یکسان‌سازی با UI
        daily_used = self.queries_used_today
        if daily_used >= max_queries_per_day:
            return False, f"محدودیت روزانه ({max_queries_per_day} سوال) تمام شده است"
        
        # بررسی محدودیت ماهانه
        monthly_used = self.queries_used_month
        if monthly_used >= max_queries_per_month:
            return False, f"محدودیت ماهانه ({max_queries_per_month} سوال) تمام شده است"
        
        return True, "OK"
    
    @property
    def queries_used_today(self):
        """تعداد query های امروز - از UsageLog"""
        from .usage import UsageService
        return UsageService.get_daily_usage(self.user, self)
    
    @property
    def queries_used_month(self):
        """تعداد query های این ماه - از UsageLog"""
        from .usage import UsageService
        return UsageService.get_monthly_usage(self.user, self)


class UserUsageReport(Subscription):
    """Proxy model برای گزارش مصرف کاربران"""
    
    class Meta:
        proxy = True
        verbose_name = 'گزارش مصرف کاربر'
        verbose_name_plural = 'گزارش مصرف کاربران'
