"""
پنل مدیریت امور مالی
"""
from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from .models import Currency, PaymentGateway, FinancialSettings, Invoice, InvoiceItem, TaxReport


@admin.register(Currency)
class CurrencyAdmin(admin.ModelAdmin):
    """مدیریت ارزها"""
    list_display = [
        'code', 'name', 'symbol', 'is_base_display', 'has_decimals', 'decimal_places', 
        'exchange_rate_display', 'is_active', 'display_order'
    ]
    list_editable = ['is_active', 'display_order']
    list_filter = ['is_active', 'has_decimals', 'is_base']
    search_fields = ['code', 'name']
    ordering = ['display_order', 'code']
    
    def is_base_display(self, obj):
        if obj.is_base:
            return format_html('<span style="color: green; font-weight: bold;">✓</span>')
        return ''
    is_base_display.short_description = _('پایه')
    
    def exchange_rate_display(self, obj):
        if obj.exchange_rate == int(obj.exchange_rate):
            return f"{int(obj.exchange_rate):,}"
        return f"{float(obj.exchange_rate):,.2f}"
    exchange_rate_display.short_description = _('نرخ تبدیل')
    
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
    """مدیریت درگاه‌های پرداخت"""
    list_display = [
        'name', 'is_active', 'is_sandbox', 
        'commission_percentage', 'display_order'
    ]
    list_editable = ['is_active', 'is_sandbox', 'display_order']
    list_filter = ['is_active', 'is_sandbox']
    search_fields = ['name', 'merchant_id']
    filter_horizontal = ['supported_currencies']
    ordering = ['display_order', 'name']
    
    fieldsets = (
        (_('درگاه پرداخت'), {
            'fields': (
                'name', 
                'connected_account',
                'merchant_id', 
                'api_key', 
                'api_secret',
                'is_active', 
                'is_sandbox', 
                'commission_percentage', 
                'display_order',
                'supported_currencies',
            )
        }),
    )


@admin.register(FinancialSettings)
class FinancialSettingsAdmin(admin.ModelAdmin):
    """مدیریت تنظیمات مالی"""
    
    fieldsets = (
        ('اطلاعات مالیاتی', {
            'fields': (
                'company_name', 'company_name_en', 'company_address',
                'postal_code', 'phone', 'national_id', 'registration_number', 'tax_rate'
            )
        }),
        ('درگاه پرداخت', {
            'fields': ('default_payment_gateway',)
        }),
        ('سامانه مودیان', {
            'fields': (
                'moadian_enabled', 'moadian_api_key', 'moadian_private_key',
                'moadian_memory_id', 'moadian_fiscal_id'
            ),
            'classes': ('collapse',)
        }),
        ('تنظیمات فاکتور', {
            'fields': (
                'auto_invoice_legal', 'auto_invoice_all',
                'invoice_prefix', 'invoice_start_number'
            )
        }),
    )
    
    def has_add_permission(self, request):
        # فقط یک رکورد مجاز است
        return not FinancialSettings.objects.exists()
    
    def has_delete_permission(self, request, obj=None):
        return False


class InvoiceItemInline(admin.TabularInline):
    """آیتم‌های فاکتور"""
    model = InvoiceItem
    extra = 0
    readonly_fields = ['tax_amount', 'total']


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    """مدیریت فاکتورها"""
    
    list_display = [
        'invoice_number', 'buyer_name', 'is_legal_buyer', 'total_display',
        'status_badge', 'issue_date', 'tax_status'
    ]
    list_filter = ['status', 'is_legal_buyer', 'invoice_type', 'issue_date']
    search_fields = ['invoice_number', 'buyer_name', 'buyer_national_id']
    readonly_fields = ['invoice_number', 'created_at', 'updated_at', 'tax_id', 'tax_serial']
    date_hierarchy = 'issue_date'
    inlines = [InvoiceItemInline]
    
    fieldsets = (
        ('اطلاعات فاکتور', {
            'fields': ('invoice_number', 'invoice_type', 'status', 'issue_date', 'due_date')
        }),
        ('اطلاعات خریدار', {
            'fields': (
                'user', 'buyer_name', 'is_legal_buyer', 'buyer_national_id',
                'buyer_economic_code', 'buyer_address', 'buyer_postal_code', 'buyer_phone'
            )
        }),
        ('مبالغ', {
            'fields': ('subtotal', 'tax_rate', 'tax_amount', 'discount', 'total')
        }),
        ('پرداخت', {
            'fields': ('payment', 'paid_at')
        }),
        ('اطلاعات مالیاتی', {
            'fields': ('tax_id', 'tax_serial', 'sent_to_tax_at', 'tax_response'),
            'classes': ('collapse',)
        }),
        ('یادداشت', {
            'fields': ('notes',),
            'classes': ('collapse',)
        }),
    )
    
    def total_display(self, obj):
        return f'{obj.total:,.0f} تومان'
    total_display.short_description = 'مبلغ کل'
    
    def status_badge(self, obj):
        colors = {
            'draft': 'gray',
            'issued': 'blue',
            'paid': 'green',
            'cancelled': 'red',
            'sent_to_tax': 'orange',
            'tax_confirmed': 'green',
            'tax_rejected': 'red',
        }
        color = colors.get(obj.status, 'gray')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; border-radius: 4px;">{}</span>',
            color, obj.get_status_display()
        )
    status_badge.short_description = 'وضعیت'
    
    def tax_status(self, obj):
        if obj.tax_id:
            return format_html('<span style="color: green;">✓ ارسال شده</span>')
        return format_html('<span style="color: gray;">-</span>')
    tax_status.short_description = 'مالیات'
    
    actions = ['send_to_tax', 'mark_as_paid']
    
    def send_to_tax(self, request, queryset):
        # TODO: پیاده‌سازی ارسال به سامانه مالیات
        self.message_user(request, 'این قابلیت در حال توسعه است')
    send_to_tax.short_description = 'ارسال به سامانه مالیات'
    
    def mark_as_paid(self, request, queryset):
        queryset.update(status='paid')
        self.message_user(request, f'{queryset.count()} فاکتور پرداخت شده علامت‌گذاری شد')
    mark_as_paid.short_description = 'علامت‌گذاری به عنوان پرداخت شده'


@admin.register(TaxReport)
class TaxReportAdmin(admin.ModelAdmin):
    """مدیریت گزارشات مالیاتی"""
    
    list_display = ['period_type', 'period_start', 'period_end', 'total_sales_display', 'total_tax_display', 'invoice_count', 'status']
    list_filter = ['period_type', 'status']
    readonly_fields = ['total_sales', 'total_tax', 'invoice_count']
    
    def total_sales_display(self, obj):
        return f'{obj.total_sales:,.0f} تومان'
    total_sales_display.short_description = 'کل فروش'
    
    def total_tax_display(self, obj):
        return f'{obj.total_tax:,.0f} تومان'
    total_tax_display.short_description = 'کل مالیات'
