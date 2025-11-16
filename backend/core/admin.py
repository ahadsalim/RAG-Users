"""
Override admin for third-party apps to add Persian names
This will be called from accounts/apps.py ready() method
"""
from django.apps import apps
from django.utils.translation import gettext_lazy as _


def setup_token_blacklist_persian():
    """Setup Persian names for token_blacklist app"""
    try:
        token_blacklist_app = apps.get_app_config('token_blacklist')
        token_blacklist_app.verbose_name = _('لیست سیاه توکن‌ها')
    except LookupError:
        pass

    try:
        from rest_framework_simplejwt.token_blacklist.models import OutstandingToken, BlacklistedToken
        
        OutstandingToken._meta.verbose_name = _('توکن فعال')
        OutstandingToken._meta.verbose_name_plural = _('توکن‌های فعال')
        
        BlacklistedToken._meta.verbose_name = _('توکن مسدود شده')
        BlacklistedToken._meta.verbose_name_plural = _('توکن‌های مسدود شده')
    except ImportError:
        pass
