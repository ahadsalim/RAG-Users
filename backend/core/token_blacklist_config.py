"""
Custom AppConfig for rest_framework_simplejwt.token_blacklist
to provide Persian verbose name
"""
from rest_framework_simplejwt.token_blacklist.apps import TokenBlacklistConfig as BaseTokenBlacklistConfig
from django.utils.translation import gettext_lazy as _


class TokenBlacklistConfig(BaseTokenBlacklistConfig):
    """Custom config with Persian name"""
    verbose_name = _('لیست سیاه توکن‌ها')
