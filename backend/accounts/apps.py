from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class AccountsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'accounts'
    verbose_name = _('کاربران و حساب‌ها')
    
    def ready(self):
        """Setup Persian names for third-party apps"""
        from core.admin import setup_token_blacklist_persian
        setup_token_blacklist_persian()
