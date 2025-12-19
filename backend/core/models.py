from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.cache import cache


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
    
    # Payment Settings
    default_payment_gateway = models.ForeignKey(
        'finance.PaymentGateway',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='default_for_sites',
        verbose_name=_('درگاه پرداخت پیش‌فرض')
    )
    
    # Maintenance
    maintenance_mode = models.BooleanField(default=False, verbose_name=_('حالت تعمیر و نگهداری'))
    maintenance_message = models.TextField(
        blank=True,
        verbose_name=_('پیام حالت تعمیر'),
        help_text=_('پیامی که در حالت تعمیر به کاربران نمایش داده می‌شود')
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
