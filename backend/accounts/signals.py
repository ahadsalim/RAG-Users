"""
Signal handlers for accounts app
"""
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def set_default_currency_and_timezone_for_new_user(sender, instance, created, **kwargs):
    """
    تنظیم ارز و منطقه زمانی پیش‌فرض برای کاربران جدید
    """
    if created:
        update_fields = []
        
        # تنظیم ارز پیش‌فرض
        if not instance.preferred_currency:
            from finance.models import Currency
            default_currency = Currency.get_default_currency()
            if default_currency:
                instance.preferred_currency = default_currency
                update_fields.append('preferred_currency')
        
        # تنظیم منطقه زمانی پیش‌فرض (تهران)
        if not instance.timezone:
            from core.models import Timezone
            tehran = Timezone.objects.filter(code='Asia/Tehran').first()
            if tehran:
                instance.timezone = tehran
                update_fields.append('timezone')
        
        if update_fields:
            instance.save(update_fields=update_fields)
