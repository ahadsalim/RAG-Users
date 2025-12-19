"""
Override admin for third-party apps to add Persian names
This will be called from accounts/apps.py ready() method
"""
from django.contrib import admin
from django.contrib.auth.models import Group
from django.apps import apps
from django.utils.translation import gettext_lazy as _
from .models import SiteSettings

# Unregister Django's default Group model (we use custom StaffGroup in accounts)
admin.site.unregister(Group)


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


@admin.register(SiteSettings)
class SiteSettingsAdmin(admin.ModelAdmin):
    """Admin for SiteSettings model (Singleton)"""
    
    def has_add_permission(self, request):
        # Prevent adding more than one instance
        return not SiteSettings.objects.exists()
    
    def has_delete_permission(self, request, obj=None):
        # Prevent deletion of settings
        return False
    
    fieldsets = (
        (_('تنظیمات سایت'), {
            'fields': (
                'frontend_site_name', 
                'admin_site_name',
                'copyright_text',
                'support_email', 
                'support_phone',
                'telegram_url', 
                'instagram_url', 
                'twitter_url',
                'default_payment_gateway',
                'maintenance_mode', 
                'maintenance_message',
            )
        }),
    )
    
    def save_model(self, request, obj, form, change):
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)
