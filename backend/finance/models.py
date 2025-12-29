"""
مدل‌های امور مالی
"""
from django.db import models
from django.conf import settings
from django.utils import timezone
from django.core.validators import MinValueValidator
from django.utils.translation import gettext_lazy as _
from django.core.cache import cache
from decimal import Decimal
import uuid


class Currency(models.Model):
    """مدل ارز برای پشتیبانی چند ارزی"""
    
    code = models.CharField(max_length=3, unique=True, verbose_name=_('کد ارز'))
    name = models.CharField(max_length=50, verbose_name=_('نام ارز'))
    symbol = models.CharField(max_length=10, verbose_name=_('نماد'))
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
    is_base = models.BooleanField(
        default=False, 
        verbose_name=_('ارز پایه'),
        help_text=_('فقط یک ارز می‌تواند ارز پایه باشد. قیمت‌ها به این ارز ذخیره می‌شوند.')
    )
    is_default = models.BooleanField(
        default=False,
        verbose_name=_('ارز پیش‌فرض'),
        help_text=_('ارز پیش‌فرضی که برای کاربران جدید تنظیم می‌شود')
    )
    display_order = models.PositiveSmallIntegerField(default=0, verbose_name=_('ترتیب نمایش'))
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('ارز')
        verbose_name_plural = _('ارزها')
        ordering = ['display_order', 'code']
    
    def save(self, *args, **kwargs):
        if self.is_base:
            Currency.objects.filter(is_base=True).exclude(pk=self.pk).update(is_base=False)
        if self.is_default:
            Currency.objects.filter(is_default=True).exclude(pk=self.pk).update(is_default=False)
        super().save(*args, **kwargs)
        cache.delete('base_currency')
        cache.delete('default_currency')
    
    @classmethod
    def get_base_currency(cls):
        """دریافت ارز پایه (کش شده)"""
        base = cache.get('base_currency')
        if not base:
            base = cls.objects.filter(is_base=True, is_active=True).first()
            if base:
                cache.set('base_currency', base, 3600)
        return base
    
    @classmethod
    def get_default_currency(cls):
        """دریافت ارز پیش‌فرض برای کاربران جدید (کش شده)"""
        default = cache.get('default_currency')
        if not default:
            default = cls.objects.filter(is_default=True, is_active=True).first()
            if default:
                cache.set('default_currency', default, 3600)
        return default
    
    def __str__(self):
        return f"{self.name} ({self.code})"
    
    def format_price(self, amount):
        """فرمت‌بندی قیمت بر اساس تنظیمات ارز"""
        amount_float = float(amount) if isinstance(amount, Decimal) else amount
        
        if self.has_decimals and self.decimal_places > 0:
            return f"{amount_float:,.{self.decimal_places}f} {self.symbol}"
        else:
            return f"{int(amount_float):,} {self.symbol}"
    
    def convert_from_base(self, base_amount):
        """تبدیل مبلغ از ارز پایه به این ارز
        
        exchange_rate نشان می‌دهد چند واحد از ارز پایه برابر 1 واحد از این ارز است.
        مثال: اگر ارز پایه ریال باشد و exchange_rate تومان = 10، یعنی 10 ریال = 1 تومان
        پس برای تبدیل ریال به تومان باید تقسیم بر 10 کنیم.
        """
        if isinstance(base_amount, Decimal):
            return base_amount / Decimal(str(self.exchange_rate))
        return float(base_amount) / float(self.exchange_rate)
    
    def convert_to_base(self, amount):
        """تبدیل مبلغ از این ارز به ارز پایه
        
        برای تبدیل تومان به ریال باید ضرب در 10 کنیم.
        """
        if isinstance(amount, Decimal):
            return amount * Decimal(str(self.exchange_rate))
        return float(amount) * float(self.exchange_rate)


class PaymentGateway(models.Model):
    """تنظیمات درگاه پرداخت"""
    
    name = models.CharField(max_length=50, verbose_name=_('نام درگاه'))
    connected_account = models.CharField(max_length=50, blank=True, verbose_name=_('شماره حساب متصل'))
    merchant_id = models.CharField(max_length=255, blank=True, verbose_name=_('شناسه پذیرنده'))
    api_key = models.CharField(max_length=255, blank=True, verbose_name=_('کلید API'))
    api_secret = models.CharField(max_length=255, blank=True, verbose_name=_('رمز API'))
    
    is_active = models.BooleanField(default=True, verbose_name=_('فعال'))
    is_sandbox = models.BooleanField(default=False, verbose_name=_('حالت تست'))
    is_default = models.BooleanField(default=False, verbose_name=_('درگاه پیش‌فرض'))
    
    base_currency = models.ForeignKey(
        Currency,
        on_delete=models.PROTECT,
        related_name='base_for_gateways',
        null=True,
        blank=True,
        verbose_name=_('ارز مبنا'),
        help_text=_('ارزی که درگاه پرداخت مبالغ را بر اساس آن دریافت می‌کند')
    )
    
    supported_currencies = models.ManyToManyField(
        Currency,
        related_name='payment_gateways',
        blank=True,
        verbose_name=_('ارزهای پشتیبانی شده')
    )
    
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
        return self.name
    
    def save(self, *args, **kwargs):
        if self.is_default:
            # فقط یک درگاه می‌تواند پیش‌فرض باشد
            PaymentGateway.objects.filter(is_default=True).exclude(pk=self.pk).update(is_default=False)
        super().save(*args, **kwargs)
    
    @classmethod
    def get_default_gateway(cls):
        """دریافت درگاه پیش‌فرض"""
        return cls.objects.filter(is_default=True, is_active=True).first()


class FinancialSettings(models.Model):
    """تنظیمات مالی سایت - فقط یک رکورد"""
    
    # اطلاعات مالیاتی
    company_name = models.CharField(max_length=255, verbose_name='نام شرکت/فروشنده', default='تجارت چت')
    company_name_en = models.CharField(max_length=255, verbose_name='نام انگلیسی شرکت', blank=True)
    company_address = models.TextField(verbose_name='آدرس', blank=True)
    postal_code = models.CharField(max_length=20, verbose_name='کد پستی', blank=True)
    phone = models.CharField(max_length=20, verbose_name='تلفن', blank=True)
    national_id = models.CharField(max_length=20, verbose_name='شناسه ملی', blank=True)
    registration_number = models.CharField(max_length=20, verbose_name='شماره ثبت', blank=True)
    tax_rate = models.DecimalField(max_digits=5, decimal_places=2, default=10, verbose_name='درصد مالیات ارزش افزوده')
    
    # درگاه پرداخت پیش‌فرض
    default_payment_gateway = models.ForeignKey(
        PaymentGateway,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='default_for_settings',
        verbose_name='درگاه پرداخت پیش‌فرض'
    )
    
    # تنظیمات سامانه مودیان
    moadian_enabled = models.BooleanField(default=False, verbose_name='اتصال به سامانه مودیان')
    moadian_api_key = models.CharField(max_length=500, verbose_name='کلید API مودیان', blank=True)
    moadian_private_key = models.TextField(verbose_name='کلید خصوصی مودیان', blank=True)
    moadian_memory_id = models.CharField(max_length=100, verbose_name='شناسه حافظه مالیاتی', blank=True)
    moadian_fiscal_id = models.CharField(max_length=100, verbose_name='شناسه یکتای مالیاتی', blank=True)
    
    # تنظیمات صدور فاکتور
    auto_invoice_legal = models.BooleanField(default=True, verbose_name='صدور خودکار فاکتور برای حقوقی')
    auto_invoice_all = models.BooleanField(default=False, verbose_name='صدور فاکتور برای همه')
    invoice_prefix = models.CharField(max_length=10, default='INV', verbose_name='پیشوند شماره فاکتور')
    invoice_start_number = models.PositiveIntegerField(default=1000, verbose_name='شماره شروع فاکتور')
    
    # متادیتا
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'تنظیمات مالی'
        verbose_name_plural = 'تنظیمات مالی'
    
    def __str__(self):
        return f'تنظیمات مالی - {self.company_name}'
    
    @classmethod
    def get_settings(cls):
        """دریافت یا ایجاد تنظیمات"""
        settings, _ = cls.objects.get_or_create(pk=1)
        return settings


class Invoice(models.Model):
    """فاکتور"""
    
    STATUS_CHOICES = [
        ('draft', 'پیش‌نویس'),
        ('issued', 'صادر شده'),
        ('paid', 'پرداخت شده'),
        ('cancelled', 'لغو شده'),
        ('sent_to_tax', 'ارسال به مالیات'),
        ('tax_confirmed', 'تایید مالیات'),
        ('tax_rejected', 'رد مالیات'),
    ]
    
    TYPE_CHOICES = [
        ('sale', 'فروش'),
        ('return', 'برگشت از فروش'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    invoice_number = models.CharField(max_length=50, unique=True, verbose_name='شماره فاکتور')
    
    # خریدار
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, verbose_name='خریدار')
    buyer_name = models.CharField(max_length=255, verbose_name='نام خریدار')
    buyer_national_id = models.CharField(max_length=20, verbose_name='کد ملی/شناسه ملی', blank=True)
    buyer_economic_code = models.CharField(max_length=20, verbose_name='کد اقتصادی خریدار', blank=True)
    buyer_address = models.TextField(verbose_name='آدرس خریدار', blank=True)
    buyer_postal_code = models.CharField(max_length=20, verbose_name='کد پستی خریدار', blank=True)
    buyer_phone = models.CharField(max_length=20, verbose_name='تلفن خریدار', blank=True)
    is_legal_buyer = models.BooleanField(default=False, verbose_name='خریدار حقوقی')
    
    # مبالغ
    subtotal = models.DecimalField(max_digits=15, decimal_places=0, verbose_name='جمع قبل از مالیات')
    tax_rate = models.DecimalField(max_digits=5, decimal_places=2, verbose_name='درصد مالیات')
    tax_amount = models.DecimalField(max_digits=15, decimal_places=0, verbose_name='مبلغ مالیات')
    discount = models.DecimalField(max_digits=15, decimal_places=0, default=0, verbose_name='تخفیف')
    total = models.DecimalField(max_digits=15, decimal_places=0, verbose_name='جمع کل')
    
    # وضعیت
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft', verbose_name='وضعیت')
    invoice_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='sale', verbose_name='نوع فاکتور')
    
    # ارتباط با پرداخت (Transaction)
    payment = models.ForeignKey(
        'payments.Transaction',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='پرداخت مرتبط'
    )
    
    # اطلاعات مالیاتی
    tax_id = models.CharField(max_length=100, verbose_name='شناسه یکتای مالیاتی', blank=True)
    tax_serial = models.CharField(max_length=100, verbose_name='سریال مالیاتی', blank=True)
    sent_to_tax_at = models.DateTimeField(null=True, blank=True, verbose_name='تاریخ ارسال به مالیات')
    tax_response = models.JSONField(null=True, blank=True, verbose_name='پاسخ سامانه مالیات')
    
    # تاریخ‌ها
    issue_date = models.DateTimeField(default=timezone.now, verbose_name='تاریخ صدور')
    due_date = models.DateTimeField(null=True, blank=True, verbose_name='تاریخ سررسید')
    paid_at = models.DateTimeField(null=True, blank=True, verbose_name='تاریخ پرداخت')
    
    # یادداشت
    notes = models.TextField(blank=True, verbose_name='یادداشت')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'فاکتور'
        verbose_name_plural = 'فاکتورها'
        ordering = ['-created_at']
    
    def __str__(self):
        return f'{self.invoice_number} - {self.buyer_name}'
    
    @classmethod
    def generate_invoice_number(cls):
        """تولید شماره فاکتور یکتا"""
        settings = FinancialSettings.get_settings()
        prefix = settings.invoice_prefix
        
        last_invoice = cls.objects.filter(
            invoice_number__startswith=prefix
        ).order_by('-created_at').first()
        
        if last_invoice:
            try:
                last_num = int(last_invoice.invoice_number.replace(prefix, ''))
                new_num = last_num + 1
            except ValueError:
                new_num = settings.invoice_start_number
        else:
            new_num = settings.invoice_start_number
        
        return f'{prefix}{new_num}'


class InvoiceItem(models.Model):
    """آیتم فاکتور"""
    
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name='items', verbose_name='فاکتور')
    description = models.CharField(max_length=500, verbose_name='شرح')
    quantity = models.PositiveIntegerField(default=1, verbose_name='تعداد')
    unit_price = models.DecimalField(max_digits=15, decimal_places=0, verbose_name='قیمت واحد')
    discount = models.DecimalField(max_digits=15, decimal_places=0, default=0, verbose_name='تخفیف')
    tax_rate = models.DecimalField(max_digits=5, decimal_places=2, verbose_name='درصد مالیات')
    tax_amount = models.DecimalField(max_digits=15, decimal_places=0, verbose_name='مبلغ مالیات')
    total = models.DecimalField(max_digits=15, decimal_places=0, verbose_name='جمع')
    
    # کد کالا/خدمات (برای سامانه مالیات)
    service_code = models.CharField(max_length=20, blank=True, verbose_name='کد خدمات')
    
    class Meta:
        verbose_name = 'آیتم فاکتور'
        verbose_name_plural = 'آیتم‌های فاکتور'
    
    def __str__(self):
        return f'{self.description} - {self.total}'


class TaxReport(models.Model):
    """گزارش مالیاتی"""
    
    PERIOD_CHOICES = [
        ('monthly', 'ماهانه'),
        ('quarterly', 'فصلی'),
        ('yearly', 'سالانه'),
    ]
    
    STATUS_CHOICES = [
        ('draft', 'پیش‌نویس'),
        ('submitted', 'ارسال شده'),
        ('confirmed', 'تایید شده'),
        ('rejected', 'رد شده'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    period_type = models.CharField(max_length=20, choices=PERIOD_CHOICES, verbose_name='نوع دوره')
    period_start = models.DateField(verbose_name='شروع دوره')
    period_end = models.DateField(verbose_name='پایان دوره')
    
    total_sales = models.DecimalField(max_digits=20, decimal_places=0, default=0, verbose_name='کل فروش')
    total_tax = models.DecimalField(max_digits=20, decimal_places=0, default=0, verbose_name='کل مالیات')
    invoice_count = models.PositiveIntegerField(default=0, verbose_name='تعداد فاکتور')
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft', verbose_name='وضعیت')
    submitted_at = models.DateTimeField(null=True, blank=True, verbose_name='تاریخ ارسال')
    
    notes = models.TextField(blank=True, verbose_name='یادداشت')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'گزارش مالیاتی'
        verbose_name_plural = 'گزارشات مالیاتی'
        ordering = ['-period_start']
    
    def __str__(self):
        return f'{self.get_period_type_display()} - {self.period_start} تا {self.period_end}'
