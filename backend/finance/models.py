"""
مدل‌های امور مالی
"""
from django.db import models
from django.conf import settings
from django.utils import timezone
import uuid


class FinancialSettings(models.Model):
    """تنظیمات مالی سایت - فقط یک رکورد"""
    
    # اطلاعات فروشنده
    company_name = models.CharField(max_length=255, verbose_name='نام شرکت/فروشنده', default='تجارت چت')
    company_name_en = models.CharField(max_length=255, verbose_name='نام انگلیسی شرکت', blank=True)
    company_address = models.TextField(verbose_name='آدرس', blank=True)
    postal_code = models.CharField(max_length=20, verbose_name='کد پستی', blank=True)
    phone = models.CharField(max_length=20, verbose_name='تلفن', blank=True)
    fax = models.CharField(max_length=20, verbose_name='فکس', blank=True)
    email = models.EmailField(verbose_name='ایمیل', blank=True)
    website = models.URLField(verbose_name='وب‌سایت', blank=True)
    
    # اطلاعات مالیاتی
    economic_code = models.CharField(max_length=20, verbose_name='کد اقتصادی', blank=True)
    national_id = models.CharField(max_length=20, verbose_name='شناسه ملی', blank=True)
    registration_number = models.CharField(max_length=20, verbose_name='شماره ثبت', blank=True)
    tax_rate = models.DecimalField(max_digits=5, decimal_places=2, default=10, verbose_name='درصد مالیات ارزش افزوده')
    
    # درگاه پرداخت پیش‌فرض
    default_payment_gateway = models.CharField(
        max_length=50,
        blank=True,
        verbose_name='درگاه پرداخت پیش‌فرض',
        help_text='نام درگاه پرداخت پیش‌فرض (مثلاً zarinpal)'
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
