from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.cache import cache
import uuid


class SiteSettings(models.Model):
    """Site-wide settings (Singleton pattern)"""
    
    # Basic Info - All in one tab
    frontend_site_name = models.CharField(
        max_length=100, 
        default='تجارت چت', 
        verbose_name=_('نام سایت کاربران'),
        help_text=_('نام سایت که در فرانت‌اند نمایش داده می‌شود')
    )
    admin_site_name = models.CharField(
        max_length=100, 
        default='پنل مدیریت تجارت چت', 
        verbose_name=_('نام پنل مدیریت'),
        help_text=_('نام سایت که در پنل مدیریت نمایش داده می‌شود')
    )
    copyright_text = models.CharField(
        max_length=200, 
        default='تجارت چت © 2024', 
        verbose_name=_('متن کپی‌رایت'),
        help_text=_('متن کپی‌رایت که در پایین پنل مدیریت نمایش داده می‌شود')
    )
    
    # Contact Info (moved to main tab)
    support_email = models.EmailField(blank=True, verbose_name=_('ایمیل پشتیبانی'))
    support_phone = models.CharField(max_length=20, blank=True, verbose_name=_('تلفن پشتیبانی'))
    
    # Social Media (moved to main tab)
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
    
    # SMS Settings
    sms_signature = models.CharField(
        max_length=200,
        blank=True,
        verbose_name=_('امضای سایت در پیامک'),
        help_text=_('این متن به انتهای تمام پیامک‌ها (به جز OTP) اضافه می‌شود')
    )
    
    # License/Certificate Badges
    license_1_name = models.CharField(
        max_length=200,
        blank=True,
        verbose_name=_('نام مجوز 1'),
        help_text=_('مثال: نماد اعتماد الکترونیک')
    )
    license_1_logo_url = models.URLField(
        blank=True,
        verbose_name=_('URL لوگو مجوز 1'),
        help_text=_('آدرس لوگو یا بَج مجوز اول')
    )
    
    license_2_name = models.CharField(
        max_length=200,
        blank=True,
        verbose_name=_('نام مجوز 2'),
        help_text=_('مثال: مجوز وزارت ارتباطات')
    )
    license_2_logo_url = models.URLField(
        blank=True,
        verbose_name=_('URL لوگو مجوز 2'),
        help_text=_('آدرس لوگو یا بَج مجوز دوم')
    )
    
    license_3_name = models.CharField(
        max_length=200,
        blank=True,
        verbose_name=_('نام مجوز 3'),
        help_text=_('مثال: گواهینامه ISO')
    )
    license_3_logo_url = models.URLField(
        blank=True,
        verbose_name=_('URL لوگو مجوز 3'),
        help_text=_('آدرس لوگو یا بَج مجوز سوم')
    )
    
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
        return self.frontend_site_name
    
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
        """جلوگیری از حذف تنظیمات سایت"""
        raise ValueError("تنظیمات سایت قابل حذف نیست")


class Language(models.Model):
    """زبان‌های قابل انتخاب در سیستم"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, verbose_name=_('نام زبان'))
    code = models.CharField(max_length=10, unique=True, verbose_name=_('کد زبان'), help_text=_('مثال: fa, en, ar'))
    native_name = models.CharField(max_length=100, verbose_name=_('نام بومی'), help_text=_('مثال: فارسی، English'))
    is_rtl = models.BooleanField(default=False, verbose_name=_('راست به چپ'))
    is_active = models.BooleanField(default=True, verbose_name=_('فعال'))
    is_default = models.BooleanField(default=False, verbose_name=_('پیش‌فرض'))
    order = models.IntegerField(default=0, verbose_name=_('ترتیب نمایش'))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('تاریخ ایجاد'))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_('تاریخ به‌روزرسانی'))
    
    class Meta:
        verbose_name = _('زبان')
        verbose_name_plural = _('زبان‌ها')
        ordering = ['order', 'name']
    
    def __str__(self):
        return f"{self.native_name} ({self.code})"
    
    def save(self, *args, **kwargs):
        # اگر این زبان پیش‌فرض است، بقیه را غیرپیش‌فرض کن
        if self.is_default:
            Language.objects.exclude(pk=self.pk).update(is_default=False)
        super().save(*args, **kwargs)


class Timezone(models.Model):
    """مناطق زمانی قابل انتخاب در سیستم"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, verbose_name=_('نام منطقه زمانی'))
    code = models.CharField(max_length=50, unique=True, verbose_name=_('کد منطقه'), help_text=_('مثال: Asia/Tehran'))
    utc_offset = models.CharField(max_length=10, verbose_name=_('اختلاف با UTC'), help_text=_('مثال: +03:30, -05:00'))
    display_name = models.CharField(max_length=150, verbose_name=_('نام نمایشی'), help_text=_('مثال: تهران (UTC+03:30)'))
    is_active = models.BooleanField(default=True, verbose_name=_('فعال'))
    is_default = models.BooleanField(default=False, verbose_name=_('پیش‌فرض'))
    order = models.IntegerField(default=0, verbose_name=_('ترتیب نمایش'))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('تاریخ ایجاد'))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_('تاریخ به‌روزرسانی'))
    
    class Meta:
        verbose_name = _('منطقه زمانی')
        verbose_name_plural = _('مناطق زمانی')
        ordering = ['order', 'utc_offset']
    
    def __str__(self):
        return self.display_name
    
    def save(self, *args, **kwargs):
        # اگر این منطقه پیش‌فرض است، بقیه را غیرپیش‌فرض کن
        if self.is_default:
            Timezone.objects.exclude(pk=self.pk).update(is_default=False)
        super().save(*args, **kwargs)
