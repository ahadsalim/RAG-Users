from django.db import models
from django.core.validators import MinValueValidator
from django.utils.translation import gettext_lazy as _
from django.core.cache import cache


class Currency(models.Model):
    """Currency model for multi-currency support"""
    
    code = models.CharField(max_length=3, unique=True, verbose_name=_('کد ارز'))  # e.g., IRR, USD, EUR
    name = models.CharField(max_length=50, verbose_name=_('نام ارز'))  # e.g., ریال ایران, دلار آمریکا
    symbol = models.CharField(max_length=10, verbose_name=_('نماد'))  # e.g., ﷼, $, €
    has_decimals = models.BooleanField(default=False, verbose_name=_('دارای اعشار'))
    decimal_places = models.PositiveSmallIntegerField(
        default=0, 
        verbose_name=_('تعداد ارقام اعشار'),
        help_text=_('تعداد ارقام اعشار (0 برای تومان/ریال، 2 برای دلار)')
    )
    exchange_rate = models.DecimalField(
        max_digits=15, 
        decimal_places=6,
        default=1,
        validators=[MinValueValidator(0)],
        verbose_name=_('نرخ تبدیل به واحد پایه'),
        help_text=_('نرخ تبدیل این ارز به واحد پایه سایت (1 = واحد پایه)')
    )
    is_active = models.BooleanField(default=True, verbose_name=_('فعال'))
    display_order = models.PositiveSmallIntegerField(default=0, verbose_name=_('ترتیب نمایش'))
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('ارز')
        verbose_name_plural = _('ارزها')
        ordering = ['display_order', 'code']
    
    def __str__(self):
        return f"{self.name} ({self.code})"
    
    def format_price(self, amount):
        """Format price according to currency settings"""
        from decimal import Decimal
        # تبدیل به float برای فرمت‌بندی
        amount_float = float(amount) if isinstance(amount, Decimal) else amount
        
        if self.has_decimals and self.decimal_places > 0:
            return f"{amount_float:,.{self.decimal_places}f} {self.symbol}"
        else:
            # Remove decimals for currencies like IRR, Toman
            return f"{int(amount_float):,} {self.symbol}"
    
    def convert_from_base(self, base_amount):
        """Convert amount from base currency to this currency"""
        from decimal import Decimal
        # تبدیل به Decimal برای دقت بالا
        if isinstance(base_amount, Decimal):
            return base_amount * Decimal(str(self.exchange_rate))
        return float(base_amount) * float(self.exchange_rate)


class PaymentGateway(models.Model):
    """Payment gateway configuration"""
    
    GATEWAY_TYPES = [
        ('zarinpal', _('زرین‌پال')),
        ('idpay', _('آیدی‌پی')),
        ('nextpay', _('نکست‌پی')),
        ('parsian', _('پارسیان')),
        ('mellat', _('ملت')),
        ('saman', _('سامان')),
        ('pasargad', _('پاسارگاد')),
        ('stripe', _('Stripe')),
        ('paypal', _('PayPal')),
    ]
    
    name = models.CharField(max_length=50, verbose_name=_('نام درگاه'))
    gateway_type = models.CharField(max_length=20, choices=GATEWAY_TYPES, verbose_name=_('نوع درگاه'))
    merchant_id = models.CharField(max_length=255, blank=True, verbose_name=_('شناسه پذیرنده'))
    api_key = models.CharField(max_length=255, blank=True, verbose_name=_('کلید API'))
    api_secret = models.CharField(max_length=255, blank=True, verbose_name=_('رمز API'))
    
    # Gateway settings
    is_active = models.BooleanField(default=True, verbose_name=_('فعال'))
    is_sandbox = models.BooleanField(default=False, verbose_name=_('حالت تست'))
    
    # Supported currencies
    supported_currencies = models.ManyToManyField(
        Currency,
        related_name='payment_gateways',
        blank=True,
        verbose_name=_('ارزهای پشتیبانی شده')
    )
    
    # Commission settings
    commission_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0)],
        verbose_name=_('درصد کارمزد')
    )
    
    display_order = models.PositiveSmallIntegerField(default=0, verbose_name=_('ترتیب نمایش'))
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('درگاه پرداخت')
        verbose_name_plural = _('درگاه‌های پرداخت')
        ordering = ['display_order', 'name']
    
    def __str__(self):
        return f"{self.name} ({self.get_gateway_type_display()})"


class SiteSettings(models.Model):
    """Site-wide settings (Singleton pattern)"""
    
    # Basic Info
    site_name = models.CharField(max_length=100, default='تجارت چت', verbose_name=_('نام سایت'))
    site_url = models.URLField(default='https://tejarat.chat', verbose_name=_('آدرس سایت'))
    site_description = models.TextField(blank=True, verbose_name=_('توضیحات سایت'))
    
    # Currency Settings
    base_currency = models.ForeignKey(
        Currency,
        on_delete=models.PROTECT,
        related_name='base_for_sites',
        null=True,
        blank=True,
        verbose_name=_('واحد پولی پایه'),
        help_text=_('واحد پولی پایه سایت (تومان، ریال، دلار و ...)')
    )
    
    # Payment Settings
    default_payment_gateway = models.ForeignKey(
        PaymentGateway,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='default_for_sites',
        verbose_name=_('درگاه پرداخت پیش‌فرض')
    )
    
    # Contact Info
    support_email = models.EmailField(blank=True, verbose_name=_('ایمیل پشتیبانی'))
    support_phone = models.CharField(max_length=20, blank=True, verbose_name=_('تلفن پشتیبانی'))
    
    # Social Media
    telegram_url = models.URLField(blank=True, verbose_name=_('آدرس تلگرام'))
    instagram_url = models.URLField(blank=True, verbose_name=_('آدرس اینستاگرام'))
    twitter_url = models.URLField(blank=True, verbose_name=_('آدرس توییتر'))
    
    # Maintenance
    maintenance_mode = models.BooleanField(default=False, verbose_name=_('حالت تعمیر و نگهداری'))
    maintenance_message = models.TextField(
        blank=True,
        verbose_name=_('پیام حالت تعمیر'),
        help_text=_('پیامی که در حالت تعمیر به کاربران نمایش داده می‌شود')
    )
    
    # Feature Flags
    allow_registration = models.BooleanField(default=True, verbose_name=_('امکان ثبت‌نام'))
    require_email_verification = models.BooleanField(default=True, verbose_name=_('الزام تأیید ایمیل'))
    enable_two_factor = models.BooleanField(default=True, verbose_name=_('فعال‌سازی احراز هویت دو مرحله‌ای'))
    
    # Timestamps
    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_('آخرین ویرایش توسط')
    )
    
    class Meta:
        verbose_name = _('تنظیمات سایت')
        verbose_name_plural = _('تنظیمات سایت')
    
    def __str__(self):
        return self.site_name
    
    def save(self, *args, **kwargs):
        # Ensure only one instance exists (Singleton pattern)
        self.pk = 1
        super().save(*args, **kwargs)
        # Clear cache when settings are updated
        cache.delete('site_settings')
    
    @classmethod
    def get_settings(cls):
        """Get site settings (cached)"""
        settings = cache.get('site_settings')
        if not settings:
            settings, _ = cls.objects.get_or_create(pk=1)
            cache.set('site_settings', settings, 3600)  # Cache for 1 hour
        return settings
    
    def delete(self, *args, **kwargs):
        # Prevent deletion of settings
        pass
