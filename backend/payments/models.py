from django.db import models
from django.conf import settings
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
import uuid
import json
from decimal import Decimal
from subscriptions.models import Subscription, Plan


class PaymentGateway(models.TextChoices):
    """انواع درگاه پرداخت"""
    ZARINPAL = 'zarinpal', 'زرین‌پال'
    TEJARAT_TEST = 'tejarat_test', 'درگاه تست تجارت'
    STRIPE = 'stripe', 'Stripe'
    PAYPAL = 'paypal', 'PayPal'
    CRYPTO = 'crypto', 'Cryptocurrency'
    BANK_TRANSFER = 'bank_transfer', 'انتقال بانکی'
    CREDIT = 'credit', 'اعتبار حساب'


class PaymentStatus(models.TextChoices):
    """وضعیت‌های پرداخت"""
    PENDING = 'pending', 'در انتظار'
    PROCESSING = 'processing', 'در حال پردازش'
    SUCCESS = 'success', 'موفق'
    FAILED = 'failed', 'ناموفق'
    CANCELLED = 'cancelled', 'لغو شده'
    REFUNDED = 'refunded', 'بازگشت داده شده'
    PARTIALLY_REFUNDED = 'partially_refunded', 'بازگشت جزئی'


class Transaction(models.Model):
    """مدل تراکنش‌های مالی"""
    
    # شناسه‌ها
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    reference_id = models.CharField(
        max_length=100, 
        unique=True,
        help_text='شناسه مرجع تراکنش'
    )
    
    # کاربر و اشتراک
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='transactions',
        verbose_name='کاربر'
    )
    subscription = models.ForeignKey(
        Subscription,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='transactions',
        verbose_name='اشتراک'
    )
    plan = models.ForeignKey(
        Plan,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='پلن'
    )
    
    # مبلغ و ارز
    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        verbose_name='مبلغ'
    )
    currency = models.CharField(
        max_length=3,
        default='IRR',
        verbose_name='ارز',
        help_text='ISO 4217 currency code'
    )
    exchange_rate = models.DecimalField(
        max_digits=10,
        decimal_places=4,
        default=1,
        verbose_name='نرخ تبدیل'
    )
    
    # درگاه و وضعیت
    gateway = models.CharField(
        max_length=20,
        choices=PaymentGateway.choices,
        verbose_name='درگاه پرداخت'
    )
    status = models.CharField(
        max_length=20,
        choices=PaymentStatus.choices,
        default=PaymentStatus.PENDING,
        verbose_name='وضعیت'
    )
    
    # اطلاعات پرداخت
    gateway_transaction_id = models.CharField(
        max_length=255,
        blank=True,
        verbose_name='شناسه تراکنش درگاه'
    )
    gateway_response = models.JSONField(
        default=dict,
        blank=True,
        verbose_name='پاسخ درگاه'
    )
    
    # تخفیف
    discount_code = models.CharField(
        max_length=50,
        blank=True,
        verbose_name='کد تخفیف'
    )
    discount_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name='مبلغ تخفیف'
    )
    tax_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name='مالیات'
    )
    
    # فاکتور
    invoice_number = models.CharField(
        max_length=50,
        unique=True,
        blank=True,
        verbose_name='شماره فاکتور'
    )
    invoice_file = models.FileField(
        upload_to='invoices/%Y/%m/',
        blank=True,
        null=True,
        verbose_name='فایل فاکتور'
    )
    
    # توضیحات
    description = models.TextField(
        blank=True,
        verbose_name='توضیحات'
    )
    notes = models.TextField(
        blank=True,
        verbose_name='یادداشت داخلی'
    )
    
    # متادیتا
    metadata = models.JSONField(
        default=dict,
        blank=True,
        verbose_name='متادیتا'
    )
    ip_address = models.GenericIPAddressField(
        blank=True,
        null=True,
        verbose_name='آدرس IP'
    )
    user_agent = models.CharField(
        max_length=500,
        blank=True,
        verbose_name='User Agent'
    )
    
    # تاریخ‌ها
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='تاریخ ایجاد')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='تاریخ به‌روزرسانی')
    paid_at = models.DateTimeField(blank=True, null=True, verbose_name='تاریخ پرداخت')
    refunded_at = models.DateTimeField(blank=True, null=True, verbose_name='تاریخ بازگشت')
    
    class Meta:
        verbose_name = 'تراکنش'
        verbose_name_plural = 'تراکنش‌ها'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['reference_id']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"{self.reference_id} - {self.user.email} - {self.amount} {self.currency}"
    
    def save(self, *args, **kwargs):
        if not self.reference_id:
            self.reference_id = self.generate_reference_id()
        if not self.invoice_number and self.status == PaymentStatus.SUCCESS:
            self.invoice_number = self.generate_invoice_number()
        super().save(*args, **kwargs)
    
    def generate_reference_id(self):
        """تولید شناسه مرجع یکتا"""
        timestamp = timezone.now().strftime('%Y%m%d%H%M%S')
        random_str = uuid.uuid4().hex[:6].upper()
        return f"TRX-{timestamp}-{random_str}"
    
    def generate_invoice_number(self):
        """تولید شماره فاکتور"""
        year = timezone.now().year
        count = Transaction.objects.filter(
            invoice_number__isnull=False,
            created_at__year=year
        ).count() + 1
        return f"INV-{year}-{count:06d}"
    
    def get_final_amount(self):
        """محاسبه مبلغ نهایی با احتساب تخفیف و مالیات"""
        return self.amount - self.discount_amount + self.tax_amount


class ZarinpalPayment(models.Model):
    """اطلاعات مختص پرداخت زرین‌پال"""
    
    transaction = models.OneToOneField(
        Transaction,
        on_delete=models.CASCADE,
        related_name='zarinpal_payment'
    )
    
    authority = models.CharField(
        max_length=100,
        unique=True,
        verbose_name='Authority'
    )
    
    card_hash = models.CharField(
        max_length=255,
        blank=True,
        verbose_name='هش کارت'
    )
    card_pan = models.CharField(
        max_length=20,
        blank=True,
        verbose_name='شماره کارت'
    )
    
    ref_id = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='Ref ID'
    )
    
    fee_type = models.CharField(
        max_length=20,
        blank=True,
        verbose_name='نوع کارمزد'
    )
    fee = models.IntegerField(
        default=0,
        verbose_name='کارمزد'
    )
    
    class Meta:
        verbose_name = 'پرداخت زرین‌پال'
        verbose_name_plural = 'پرداخت‌های زرین‌پال'


class StripePayment(models.Model):
    """اطلاعات مختص پرداخت Stripe"""
    
    transaction = models.OneToOneField(
        Transaction,
        on_delete=models.CASCADE,
        related_name='stripe_payment'
    )
    
    payment_intent_id = models.CharField(
        max_length=255,
        unique=True,
        verbose_name='Payment Intent ID'
    )
    
    charge_id = models.CharField(
        max_length=255,
        blank=True,
        verbose_name='Charge ID'
    )
    
    customer_id = models.CharField(
        max_length=255,
        blank=True,
        verbose_name='Customer ID'
    )
    
    payment_method_id = models.CharField(
        max_length=255,
        blank=True,
        verbose_name='Payment Method ID'
    )
    
    card_brand = models.CharField(
        max_length=50,
        blank=True,
        verbose_name='Card Brand'
    )
    card_last4 = models.CharField(
        max_length=4,
        blank=True,
        verbose_name='Card Last 4'
    )
    
    class Meta:
        verbose_name = 'پرداخت Stripe'
        verbose_name_plural = 'پرداخت‌های Stripe'


class TejaratTestPayment(models.Model):
    """اطلاعات مختص پرداخت درگاه تست تجارت"""
    
    transaction = models.OneToOneField(
        Transaction,
        on_delete=models.CASCADE,
        related_name='tejarat_test_payment'
    )
    
    token = models.CharField(
        max_length=255,
        unique=True,
        verbose_name='Token'
    )
    
    card_number = models.CharField(
        max_length=20,
        blank=True,
        verbose_name='شماره کارت'
    )
    
    tracking_code = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='کد پیگیری'
    )
    
    class Meta:
        verbose_name = 'پرداخت تست تجارت'
        verbose_name_plural = 'پرداخت‌های تست تجارت'


class CryptoPayment(models.Model):
    """اطلاعات مختص پرداخت رمزارز"""
    
    CRYPTO_CURRENCIES = [
        ('BTC', 'Bitcoin'),
        ('ETH', 'Ethereum'),
        ('USDT', 'Tether'),
        ('USDC', 'USD Coin'),
        ('BNB', 'Binance Coin'),
    ]
    
    NETWORKS = [
        ('bitcoin', 'Bitcoin Network'),
        ('ethereum', 'Ethereum Network'),
        ('bsc', 'Binance Smart Chain'),
        ('tron', 'Tron Network'),
        ('polygon', 'Polygon Network'),
    ]
    
    transaction = models.OneToOneField(
        Transaction,
        on_delete=models.CASCADE,
        related_name='crypto_payment'
    )
    
    cryptocurrency = models.CharField(
        max_length=10,
        choices=CRYPTO_CURRENCIES,
        verbose_name='رمزارز'
    )
    
    network = models.CharField(
        max_length=20,
        choices=NETWORKS,
        verbose_name='شبکه'
    )
    
    wallet_address = models.CharField(
        max_length=255,
        verbose_name='آدرس کیف پول مقصد'
    )
    
    from_address = models.CharField(
        max_length=255,
        blank=True,
        verbose_name='آدرس کیف پول مبدا'
    )
    
    tx_hash = models.CharField(
        max_length=255,
        unique=True,
        blank=True,
        verbose_name='Transaction Hash'
    )
    
    amount_crypto = models.DecimalField(
        max_digits=20,
        decimal_places=8,
        verbose_name='مقدار رمزارز'
    )
    
    confirmations = models.IntegerField(
        default=0,
        verbose_name='تعداد تاییدیه'
    )
    
    required_confirmations = models.IntegerField(
        default=3,
        verbose_name='تاییدیه‌های مورد نیاز'
    )
    
    class Meta:
        verbose_name = 'پرداخت رمزارز'
        verbose_name_plural = 'پرداخت‌های رمزارز'


class Wallet(models.Model):
    """کیف پول کاربران برای اعتبار حساب"""
    
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='wallet',
        verbose_name='کاربر'
    )
    
    balance = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        verbose_name='موجودی'
    )
    
    currency = models.CharField(
        max_length=3,
        default='IRR',
        verbose_name='ارز'
    )
    
    is_active = models.BooleanField(
        default=True,
        verbose_name='فعال'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'کیف پول'
        verbose_name_plural = 'کیف پول‌ها'
    
    def __str__(self):
        return f"{self.user.email} - {self.balance} {self.currency}"
    
    def add_credit(self, amount, description=''):
        """افزودن اعتبار"""
        self.balance += Decimal(str(amount))
        self.save()
        
        WalletTransaction.objects.create(
            wallet=self,
            transaction_type='credit',
            amount=amount,
            description=description,
            balance_after=self.balance
        )
        return self.balance
    
    def deduct_credit(self, amount, description=''):
        """کسر اعتبار"""
        if self.balance < amount:
            raise ValueError('موجودی کافی نیست')
        
        self.balance -= Decimal(str(amount))
        self.save()
        
        WalletTransaction.objects.create(
            wallet=self,
            transaction_type='debit',
            amount=amount,
            description=description,
            balance_after=self.balance
        )
        return self.balance


class WalletTransaction(models.Model):
    """تراکنش‌های کیف پول"""
    
    TRANSACTION_TYPES = [
        ('credit', 'واریز'),
        ('debit', 'برداشت'),
    ]
    
    wallet = models.ForeignKey(
        Wallet,
        on_delete=models.CASCADE,
        related_name='transactions',
        verbose_name='کیف پول'
    )
    
    transaction_type = models.CharField(
        max_length=10,
        choices=TRANSACTION_TYPES,
        verbose_name='نوع تراکنش'
    )
    
    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        verbose_name='مبلغ'
    )
    
    balance_after = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        verbose_name='موجودی پس از تراکنش'
    )
    
    description = models.TextField(
        blank=True,
        verbose_name='توضیحات'
    )
    
    related_transaction = models.ForeignKey(
        Transaction,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='تراکنش مرتبط'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'تراکنش کیف پول'
        verbose_name_plural = 'تراکنش‌های کیف پول'
        ordering = ['-created_at']
