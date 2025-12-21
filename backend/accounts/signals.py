"""
Signal handlers for accounts app
"""
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def set_default_currency_for_new_user(sender, instance, created, **kwargs):
    """
    تنظیم ارز پیش‌فرض برای کاربران جدید
    """
    if created and not instance.preferred_currency:
        from finance.models import Currency
        
        # دریافت ارز پیش‌فرض
        default_currency = Currency.get_default_currency()
        
        if default_currency:
            instance.preferred_currency = default_currency
            instance.save(update_fields=['preferred_currency'])
