"""
ماژول اعلان‌ها (Notifications)

این ماژول شامل مدل‌های زیر است:

1. NotificationTemplate - قالب‌های اعلان (پیامک، ایمیل، پوش)
2. Notification - اعلان‌های ارسال شده به کاربران
3. NotificationPreference - تنظیمات اعلان هر کاربر
4. NotificationLog - لاگ ارسال اعلان‌ها
5. DeviceToken - توکن‌های دستگاه برای Push Notification

---

DeviceToken چیست؟
=================
برای ارسال Push Notification (نوتیفیکیشن روی گوشی/مرورگر) استفاده می‌شود.

مثال:
- کاربر اپ موبایل را نصب کرده و الان اپ بسته است
- می‌خواهید بهش پیام بدهید: "اشتراک شما فردا تمام می‌شود"
- بدون DeviceToken نمی‌توانید چون اپ بسته است
- با DeviceToken می‌توانید چون:
  1. وقتی کاربر اولین بار اپ را باز کرد، گوشی یک کد یکتا (توکن) از گوگل/اپل گرفت
  2. این کد در جدول DeviceToken ذخیره شد
  3. حالا این کد را به گوگل/اپل می‌دهید و می‌گویید: "این پیام را به این گوشی بفرست"
  4. گوگل/اپل پیام را به گوشی کاربر می‌رساند، حتی اگر اپ بسته باشد

پیش‌نیازها برای استفاده:
- اپلیکیشن موبایل یا PWA
- سرویس Firebase (برای اندروید) یا APNs (برای iOS)

اگر فقط وب‌سایت دارید و Push Notification نمی‌خواهید، این جدول خالی می‌ماند.
"""

from django.db import models
from django.conf import settings
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
import uuid
import json


class NotificationChannel(models.TextChoices):
    """کانال‌های ارسال اعلان"""
    EMAIL = 'email', 'ایمیل'
    SMS = 'sms', 'پیامک'
    PUSH = 'push', 'Push Notification'
    IN_APP = 'in_app', 'داخل برنامه'
    WEBSOCKET = 'websocket', 'WebSocket'


class NotificationPriority(models.TextChoices):
    """اولویت اعلان"""
    LOW = 'low', 'پایین'
    NORMAL = 'normal', 'عادی'
    HIGH = 'high', 'بالا'
    URGENT = 'urgent', 'فوری'


class NotificationCategory(models.TextChoices):
    """دسته‌بندی اعلان‌ها"""
    SYSTEM = 'system', 'سیستم'
    PAYMENT = 'payment', 'پرداخت'
    SUBSCRIPTION = 'subscription', 'اشتراک'
    CHAT = 'chat', 'چت'
    ACCOUNT = 'account', 'حساب کاربری'
    SECURITY = 'security', 'امنیت'
    MARKETING = 'marketing', 'بازاریابی'
    SUPPORT = 'support', 'پشتیبانی'


class NotificationTemplate(models.Model):
    """قالب‌های اعلان"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # شناسه و نام
    code = models.CharField(
        max_length=100,
        unique=True,
        verbose_name='کد قالب',
        help_text='مثال: payment_success, subscription_expired'
    )
    name = models.CharField(
        max_length=200,
        verbose_name='نام قالب'
    )
    description = models.TextField(
        blank=True,
        verbose_name='توضیحات'
    )
    
    # دسته‌بندی
    category = models.CharField(
        max_length=20,
        choices=NotificationCategory.choices,
        default=NotificationCategory.SYSTEM,
        verbose_name='دسته‌بندی'
    )
    
    # محتوای قالب
    title_template = models.CharField(
        max_length=200,
        verbose_name='قالب عنوان',
        help_text='می‌توانید از متغیرها استفاده کنید: {{user_name}}, {{amount}}, ...'
    )
    body_template = models.TextField(
        verbose_name='قالب متن',
        help_text='می‌توانید از متغیرها استفاده کنید'
    )
    
    # قالب‌های مخصوص هر کانال
    email_subject_template = models.CharField(
        max_length=200,
        blank=True,
        verbose_name='قالب موضوع ایمیل'
    )
    email_html_template = models.TextField(
        blank=True,
        verbose_name='قالب HTML ایمیل'
    )
    sms_template = models.CharField(
        max_length=500,
        blank=True,
        verbose_name='قالب پیامک',
        help_text='محدودیت 500 کاراکتر'
    )
    
    # کانال‌های فعال
    channels = models.JSONField(
        default=list,
        verbose_name='کانال‌های ارسال',
        help_text='لیست کانال‌های فعال: ["email", "sms", "push", "in_app"]'
    )
    
    # اولویت پیش‌فرض
    default_priority = models.CharField(
        max_length=10,
        choices=NotificationPriority.choices,
        default=NotificationPriority.NORMAL,
        verbose_name='اولویت پیش‌فرض'
    )
    
    # لینک اقدام
    action_url = models.CharField(
        max_length=500,
        blank=True,
        verbose_name='URL اقدام',
        help_text='لینکی که کاربر با کلیک به آن هدایت می‌شود'
    )
    action_text = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='متن دکمه اقدام'
    )
    
    # تنظیمات
    is_active = models.BooleanField(default=True, verbose_name='فعال')
    require_confirmation = models.BooleanField(
        default=False,
        verbose_name='نیاز به تایید',
        help_text='آیا کاربر باید تایید کند که این اعلان را دریافت کرده؟'
    )
    
    # متادیتا
    metadata = models.JSONField(
        default=dict,
        blank=True,
        verbose_name='متادیتا'
    )
    
    # تاریخ‌ها
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='تاریخ ایجاد')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='تاریخ به‌روزرسانی')
    
    class Meta:
        verbose_name = 'قالب اعلان'
        verbose_name_plural = 'قالب‌های اعلان'
        ordering = ['category', 'name']
    
    def __str__(self):
        return f"{self.name} ({self.code})"
    
    def render(self, context):
        """رندر کردن قالب با context"""
        from django.template import Context, Template
        
        title = Template(self.title_template).render(Context(context))
        body = Template(self.body_template).render(Context(context))
        
        rendered = {
            'title': title,
            'body': body,
            'action_url': Template(self.action_url).render(Context(context)) if self.action_url else '',
            'action_text': self.action_text
        }
        
        # رندر کردن قالب‌های مخصوص هر کانال
        if self.email_subject_template:
            rendered['email_subject'] = Template(self.email_subject_template).render(Context(context))
        if self.email_html_template:
            rendered['email_html'] = Template(self.email_html_template).render(Context(context))
        if self.sms_template:
            rendered['sms_text'] = Template(self.sms_template).render(Context(context))
        
        return rendered


class Notification(models.Model):
    """اعلان‌های ارسال شده"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # گیرنده
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notifications',
        verbose_name='کاربر'
    )
    
    # قالب
    template = models.ForeignKey(
        NotificationTemplate,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='قالب'
    )
    
    # محتوا
    title = models.CharField(max_length=200, verbose_name='عنوان')
    body = models.TextField(verbose_name='متن')
    
    # دسته‌بندی و اولویت
    category = models.CharField(
        max_length=20,
        choices=NotificationCategory.choices,
        default=NotificationCategory.SYSTEM,
        verbose_name='دسته‌بندی'
    )
    priority = models.CharField(
        max_length=10,
        choices=NotificationPriority.choices,
        default=NotificationPriority.NORMAL,
        verbose_name='اولویت'
    )
    
    # لینک اقدام
    action_url = models.CharField(
        max_length=500,
        blank=True,
        verbose_name='لینک اقدام'
    )
    action_text = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='متن دکمه'
    )
    
    # کانال‌های ارسال
    channels = models.JSONField(
        default=list,
        verbose_name='کانال‌های ارسال'
    )
    
    # وضعیت ارسال
    sent_via_email = models.BooleanField(default=False, verbose_name='ارسال شده از ایمیل')
    sent_via_sms = models.BooleanField(default=False, verbose_name='ارسال شده از پیامک')
    sent_via_push = models.BooleanField(default=False, verbose_name='ارسال شده از Push')
    sent_via_in_app = models.BooleanField(default=True, verbose_name='ارسال شده در برنامه')
    
    # وضعیت خواندن
    is_read = models.BooleanField(default=False, verbose_name='خوانده شده')
    read_at = models.DateTimeField(null=True, blank=True, verbose_name='زمان خواندن')
    
    # تایید
    is_confirmed = models.BooleanField(default=False, verbose_name='تایید شده')
    confirmed_at = models.DateTimeField(null=True, blank=True, verbose_name='زمان تایید')
    
    # داده‌های اضافی
    metadata = models.JSONField(
        default=dict,
        blank=True,
        verbose_name='متادیتا'
    )
    
    # خطاها
    error_log = models.JSONField(
        default=dict,
        blank=True,
        verbose_name='لاگ خطاها'
    )
    
    # تاریخ‌ها
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='زمان ایجاد')
    expires_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='زمان انقضا'
    )
    
    class Meta:
        verbose_name = 'اعلان'
        verbose_name_plural = 'اعلان‌ها'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'is_read', 'created_at']),
            models.Index(fields=['category', 'created_at']),
            models.Index(fields=['-created_at']),
        ]
    
    def __str__(self):
        return f"{self.title} - {self.user.email}"
    
    def mark_as_read(self):
        """علامت‌گذاری به عنوان خوانده شده"""
        if not self.is_read:
            self.is_read = True
            self.read_at = timezone.now()
            self.save(update_fields=['is_read', 'read_at'])
    
    def mark_as_confirmed(self):
        """علامت‌گذاری به عنوان تایید شده"""
        if not self.is_confirmed:
            self.is_confirmed = True
            self.confirmed_at = timezone.now()
            self.save(update_fields=['is_confirmed', 'confirmed_at'])


class NotificationPreference(models.Model):
    """تنظیمات اعلان‌رسانی کاربر"""
    
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        primary_key=True,
        related_name='notification_preferences',
        verbose_name='کاربر'
    )
    
    # فعال‌سازی کلی کانال‌ها
    email_enabled = models.BooleanField(default=True, verbose_name='ایمیل فعال')
    sms_enabled = models.BooleanField(default=True, verbose_name='پیامک فعال')
    push_enabled = models.BooleanField(default=True, verbose_name='Push فعال')
    in_app_enabled = models.BooleanField(default=True, verbose_name='داخل برنامه فعال')
    
    # تنظیمات بر اساس دسته
    system_notifications = models.BooleanField(default=True, verbose_name='اعلان‌های سیستمی')
    payment_notifications = models.BooleanField(default=True, verbose_name='اعلان‌های پرداخت')
    subscription_notifications = models.BooleanField(default=True, verbose_name='اعلان‌های اشتراک')
    chat_notifications = models.BooleanField(default=True, verbose_name='اعلان‌های چت')
    account_notifications = models.BooleanField(default=True, verbose_name='اعلان‌های حساب')
    security_notifications = models.BooleanField(default=True, verbose_name='اعلان‌های امنیتی')
    marketing_notifications = models.BooleanField(default=False, verbose_name='اعلان‌های بازاریابی')
    support_notifications = models.BooleanField(default=True, verbose_name='اعلان‌های پشتیبانی')
    
    # تاریخ‌ها
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'تنظیمات اعلان'
        verbose_name_plural = 'تنظیمات اعلان‌رسانی'
    
    def __str__(self):
        return f"Preferences for {self.user.phone_number}"
    
    def is_channel_enabled(self, channel):
        """بررسی فعال بودن یک کانال"""
        channel_map = {
            'email': self.email_enabled,
            'sms': self.sms_enabled,
            'push': self.push_enabled,
            'in_app': self.in_app_enabled,
        }
        return channel_map.get(channel, False)
    
    def is_category_enabled(self, category):
        """بررسی فعال بودن یک دسته"""
        category_map = {
            'system': self.system_notifications,
            'payment': self.payment_notifications,
            'subscription': self.subscription_notifications,
            'chat': self.chat_notifications,
            'account': self.account_notifications,
            'security': self.security_notifications,
            'marketing': self.marketing_notifications,
            'support': self.support_notifications,
        }
        return category_map.get(category, True)


class DeviceToken(models.Model):
    """توکن‌های دستگاه برای Push Notification"""
    
    DEVICE_TYPES = [
        ('ios', 'iOS'),
        ('android', 'Android'),
        ('web', 'Web'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='device_tokens',
        verbose_name='کاربر'
    )
    
    token = models.CharField(
        max_length=500,
        unique=True,
        verbose_name='توکن دستگاه'
    )
    
    device_type = models.CharField(
        max_length=10,
        choices=DEVICE_TYPES,
        verbose_name='نوع دستگاه'
    )
    
    device_name = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='نام دستگاه'
    )
    
    is_active = models.BooleanField(default=True, verbose_name='فعال')
    
    last_used_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='آخرین استفاده'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'توکن دستگاه'
        verbose_name_plural = 'توکن‌های دستگاه'
        indexes = [
            models.Index(fields=['user', 'is_active']),
        ]
    
    def __str__(self):
        return f"{self.user.email} - {self.device_type}"


class NotificationLog(models.Model):
    """لاگ ارسال اعلان‌ها"""
    
    STATUS_CHOICES = [
        ('pending', 'در انتظار'),
        ('sent', 'ارسال شده'),
        ('delivered', 'تحویل داده شده'),
        ('failed', 'ناموفق'),
        ('bounced', 'برگشت خورده'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    notification = models.ForeignKey(
        Notification,
        on_delete=models.CASCADE,
        related_name='logs',
        verbose_name='اعلان'
    )
    
    channel = models.CharField(
        max_length=20,
        choices=NotificationChannel.choices,
        verbose_name='کانال'
    )
    
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        verbose_name='وضعیت'
    )
    
    # اطلاعات ارسال
    recipient = models.CharField(
        max_length=255,
        verbose_name='گیرنده',
        help_text='ایمیل، شماره تلفن، یا توکن دستگاه'
    )
    
    # پاسخ سرویس
    provider_response = models.JSONField(
        default=dict,
        blank=True,
        verbose_name='پاسخ سرویس‌دهنده'
    )
    
    provider_message_id = models.CharField(
        max_length=255,
        blank=True,
        verbose_name='شناسه پیام نزد سرویس‌دهنده'
    )
    
    # خطا
    error_message = models.TextField(
        blank=True,
        verbose_name='پیام خطا'
    )
    
    # تلاش مجدد
    retry_count = models.IntegerField(default=0, verbose_name='تعداد تلاش مجدد')
    
    # تاریخ‌ها
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='زمان ایجاد')
    sent_at = models.DateTimeField(null=True, blank=True, verbose_name='زمان ارسال')
    delivered_at = models.DateTimeField(null=True, blank=True, verbose_name='زمان تحویل')
    
    class Meta:
        verbose_name = 'لاگ اعلان'
        verbose_name_plural = 'لاگ اعلان‌ها'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['notification', 'channel']),
            models.Index(fields=['status', 'created_at']),
        ]
    
    def __str__(self):
        return f"{self.notification.title} - {self.channel} - {self.status}"
