"""
Override admin for third-party apps to add Persian names
This will be called from accounts/apps.py ready() method
"""
from django.contrib import admin
from django.apps import apps
from django.utils.translation import gettext_lazy as _
from .models import Currency, PaymentGateway, SiteSettings


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


@admin.register(Currency)
class CurrencyAdmin(admin.ModelAdmin):
    """Admin for Currency model"""
    list_display = [
        'code', 'name', 'symbol', 'is_base', 'has_decimals', 'decimal_places', 
        'exchange_rate_display', 'is_active', 'display_order'
    ]
    list_editable = ['is_active', 'is_base', 'display_order']
    list_filter = ['is_active', 'has_decimals', 'is_base']
    search_fields = ['code', 'name']
    ordering = ['display_order', 'code']
    
    def exchange_rate_display(self, obj):
        """Display exchange rate with max 2 decimal places"""
        if obj.exchange_rate == int(obj.exchange_rate):
            return f"{int(obj.exchange_rate):,}"
        return f"{float(obj.exchange_rate):,.2f}"
    exchange_rate_display.short_description = _('نرخ تبدیل به واحد پایه')
    
    fieldsets = (
        (_('اطلاعات پایه'), {
            'fields': ('code', 'name', 'symbol', 'display_order')
        }),
        (_('تنظیمات اعشار'), {
            'fields': ('has_decimals', 'decimal_places'),
            'description': _('برای تومان و ریال، "دارای اعشار" را خاموش کنید')
        }),
        (_('نرخ تبدیل'), {
            'fields': ('exchange_rate',),
            'description': _('نرخ تبدیل این ارز به واحد پایه سایت (1 = واحد پایه)')
        }),
        (_('وضعیت'), {
            'fields': ('is_active', 'is_base'),
            'description': _('فقط یک ارز می‌تواند ارز پایه باشد')
        }),
    )


@admin.register(PaymentGateway)
class PaymentGatewayAdmin(admin.ModelAdmin):
    """Admin for PaymentGateway model"""
    list_display = [
        'name', 'gateway_type', 'is_active', 'is_sandbox', 
        'commission_percentage', 'display_order'
    ]
    list_editable = ['is_active', 'is_sandbox', 'display_order']
    list_filter = ['gateway_type', 'is_active', 'is_sandbox']
    search_fields = ['name', 'merchant_id']
    filter_horizontal = ['supported_currencies']
    ordering = ['display_order', 'name']
    
    fieldsets = (
        (_('اطلاعات پایه'), {
            'fields': ('name', 'gateway_type', 'display_order')
        }),
        (_('اطلاعات API'), {
            'fields': ('merchant_id', 'api_key', 'api_secret'),
            'classes': ('collapse',),
            'description': _('اطلاعات احراز هویت درگاه پرداخت')
        }),
        (_('تنظیمات'), {
            'fields': ('is_active', 'is_sandbox', 'commission_percentage', 'supported_currencies')
        }),
    )


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
        (_('اطلاعات پایه سایت'), {
            'fields': ('site_name', 'site_url', 'site_description')
        }),
        (_('تنظیمات مالی'), {
            'fields': ('base_currency', 'default_payment_gateway'),
            'description': _('واحد پولی و درگاه پرداخت پیش‌فرض سایت')
        }),
        (_('اطلاعات تماس'), {
            'fields': ('support_email', 'support_phone'),
            'classes': ('collapse',)
        }),
        (_('شبکه‌های اجتماعی'), {
            'fields': ('telegram_url', 'instagram_url', 'twitter_url'),
            'classes': ('collapse',)
        }),
        (_('حالت تعمیر و نگهداری'), {
            'fields': ('maintenance_mode', 'maintenance_message'),
            'classes': ('collapse',)
        }),
        (_('تنظیمات امنیتی'), {
            'fields': ('allow_registration', 'require_email_verification', 'enable_two_factor'),
            'classes': ('collapse',)
        }),
    )
    
    def save_model(self, request, obj, form, change):
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)
