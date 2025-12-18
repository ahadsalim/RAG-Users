from django.contrib import admin
from django.utils.html import format_html
from django.utils import timezone
from django.db.models import Sum
from django import forms
from .models import Plan, Subscription, UserUsageReport
from .usage import ModelUsageLog
from core.models import Currency


class PlanAdminForm(forms.ModelForm):
    """فرم سفارشی برای نمایش قیمت با جداکننده هزارگان"""
    
    class Meta:
        model = Plan
        fields = '__all__'
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Get base currency name for label
        base_currency = Currency.get_base_currency()
        currency_name = base_currency.name if base_currency else 'ارز پایه'
        
        # Update price field label and help text
        self.fields['price'].label = f'قیمت ({currency_name})'
        self.fields['price'].help_text = f'قیمت را به {currency_name} وارد کنید'
        
        # Add thousand separator widget
        self.fields['price'].widget.attrs.update({
            'style': 'direction: ltr; text-align: left;',
            'class': 'vIntegerField',
        })


@admin.register(Plan)
class PlanAdmin(admin.ModelAdmin):
    form = PlanAdminForm
    list_display = ['name', 'plan_type', 'formatted_price', 'duration_days', 'max_queries_per_day', 'max_queries_per_month', 'max_active_sessions', 'max_organization_members', 'is_active', 'colored_status']
    list_filter = ['plan_type', 'is_active', 'created_at']
    search_fields = ['name', 'description']
    list_editable = ['duration_days', 'max_queries_per_day', 'max_queries_per_month', 'max_active_sessions', 'max_organization_members', 'is_active']
    ordering = ['plan_type', 'price']
    
    def get_fieldsets(self, request, obj=None):
        base_currency = Currency.get_base_currency()
        currency_name = base_currency.name if base_currency else 'ارز پایه'
        
        return (
            ('اطلاعات پایه', {
                'fields': ('name', 'description', 'plan_type', 'price', 'duration_days', 'is_active'),
                'description': f'قیمت را به {currency_name} وارد کنید.'
            }),
            ('محدودیت‌های استفاده', {
                'fields': ('max_queries_per_day', 'max_queries_per_month', 'max_active_sessions'),
            }),
            ('تنظیمات سازمانی (فقط برای پلن‌های حقوقی)', {
                'fields': ('max_organization_members',),
                'description': 'حداکثر تعداد اعضای سازمان برای پلن‌های حقوقی'
            }),
            ('ویژگی‌های اضافی', {
                'fields': ('features',),
                'classes': ('collapse',),
                'description': 'تنظیمات JSON اضافی. مثال: {"gpt_3_5_access": true, "gpt_4_access": false}'
            }),
        )
    
    def formatted_price(self, obj):
        """Display price with currency formatting"""
        return obj.get_price_display()
    formatted_price.short_description = 'قیمت'
    
    def colored_status(self, obj):
        if obj.is_active:
            return format_html('<span style="color: green;">●</span> فعال')
        return format_html('<span style="color: red;">●</span> غیرفعال')
    colored_status.short_description = 'وضعیت'
    
    class Media:
        css = {
            'all': ('admin/css/plan_admin.css',)
        }


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ['user_info', 'plan', 'colored_status', 'start_date', 'end_date', 'days_remaining', 'auto_renew']
    list_filter = ['status', 'plan', 'auto_renew', 'created_at']
    search_fields = ['user__email', 'user__phone_number', 'user__first_name', 'user__last_name']
    date_hierarchy = 'created_at'
    list_editable = ['auto_renew']
    readonly_fields = ['created_at', 'updated_at', 'days_remaining']
    
    fieldsets = (
        ('اطلاعات کاربر', {
            'fields': ('user', 'plan')
        }),
        ('وضعیت اشتراک', {
            'fields': ('status', 'start_date', 'end_date', 'auto_renew')
        }),
        ('اطلاعات سیستمی', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['activate_subscription', 'cancel_subscription', 'extend_subscription']
    
    def user_info(self, obj):
        return format_html(
            '<strong>{}</strong><br/><small>{}</small>',
            obj.user.get_full_name() or obj.user.email,
            obj.user.phone_number or obj.user.email
        )
    user_info.short_description = 'کاربر'
    
    def colored_status(self, obj):
        colors = {
            'active': 'green',
            'expired': 'red',
            'cancelled': 'gray',
            'pending': 'orange',
        }
        color = colors.get(obj.status, 'gray')
        status_fa = dict(obj.STATUS_CHOICES).get(obj.status, obj.status)
        return format_html('<span style="color: {};">●</span> {}', color, status_fa)
    colored_status.short_description = 'وضعیت'
    
    def days_remaining(self, obj):
        if obj.status == 'active' and obj.end_date:
            delta = obj.end_date - timezone.now()
            days = delta.days
            if days > 0:
                return format_html('<span style="color: green;">{} روز</span>', days)
            else:
                return format_html('<span style="color: red;">منقضی شده</span>')
        return '-'
    days_remaining.short_description = 'باقیمانده'
    
    def activate_subscription(self, request, queryset):
        count = 0
        for sub in queryset:
            sub.activate()
            count += 1
        self.message_user(request, f'{count} اشتراک فعال شد.')
    activate_subscription.short_description = 'فعال‌سازی اشتراک'
    
    def cancel_subscription(self, request, queryset):
        count = 0
        for sub in queryset:
            sub.cancel()
            count += 1
        self.message_user(request, f'{count} اشتراک لغو شد.')
    cancel_subscription.short_description = 'لغو اشتراک'
    
    def extend_subscription(self, request, queryset):
        from datetime import timedelta
        count = 0
        for sub in queryset:
            sub.end_date = sub.end_date + timedelta(days=30)
            sub.save()
            count += 1
        self.message_user(request, f'{count} اشتراک 30 روز تمدید شد.')
    extend_subscription.short_description = 'تمدید 30 روزه'


@admin.register(ModelUsageLog)
class ModelUsageLogAdmin(admin.ModelAdmin):
    """گزارش مصرف مدل‌ها - لاگ هر درخواست به مدل‌های AI"""
    list_display = ['user_info', 'action_type', 'input_tokens', 'output_tokens', 'subscription_plan', 'created_at']
    list_filter = ['action_type', 'created_at']
    search_fields = ['user__email', 'user__phone_number', 'user__first_name', 'user__last_name']
    date_hierarchy = 'created_at'
    readonly_fields = ['id', 'user', 'subscription', 'action_type', 'input_tokens', 'output_tokens', 'metadata', 'ip_address', 'user_agent', 'created_at']
    
    def user_info(self, obj):
        return format_html(
            '<strong>{}</strong><br/><small>{}</small>',
            obj.user.get_full_name() or obj.user.email or obj.user.phone_number,
            obj.user.phone_number or obj.user.email
        )
    user_info.short_description = 'کاربر'
    
    def subscription_plan(self, obj):
        if obj.plan_name:
            return obj.plan_name
        if obj.subscription:
            return obj.subscription.plan.name
        return '-'
    subscription_plan.short_description = 'پلن'
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False


@admin.register(UserUsageReport)
class UserUsageReportAdmin(admin.ModelAdmin):
    """گزارش مصرف کاربران - خلاصه مصرف هر کاربر"""
    
    list_display = ['user_info', 'plan_name', 'input_tokens_display', 'output_tokens_display', 
                    'remaining_queries', 'remaining_days', 'date_joined']
    list_filter = ['plan', 'status']
    search_fields = ['user__email', 'user__phone_number', 'user__first_name', 'user__last_name']
    ordering = ['-user__date_joined']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user', 'plan')
    
    def user_info(self, obj):
        return format_html(
            '<strong>{}</strong><br/><small>{}</small>',
            obj.user.get_full_name() or obj.user.phone_number,
            obj.user.phone_number or obj.user.email
        )
    user_info.short_description = 'کاربر'
    
    def plan_name(self, obj):
        return obj.plan.name if obj.plan else '-'
    plan_name.short_description = 'پلن'
    
    def input_tokens_display(self, obj):
        tokens = ModelUsageLog.objects.filter(user=obj.user).aggregate(
            total=Sum('input_tokens')
        )
        return tokens['total'] or 0
    input_tokens_display.short_description = 'توکن ورودی'
    
    def output_tokens_display(self, obj):
        tokens = ModelUsageLog.objects.filter(user=obj.user).aggregate(
            total=Sum('output_tokens')
        )
        return tokens['total'] or 0
    output_tokens_display.short_description = 'توکن خروجی'
    
    def remaining_queries(self, obj):
        if obj.status != 'active':
            return '-'
        from .usage import UsageService
        monthly_used = UsageService.get_monthly_usage(obj.user, obj)
        max_monthly = obj.plan.max_queries_per_month or 300
        remaining = max(0, max_monthly - monthly_used)
        return f'{remaining} از {max_monthly}'
    remaining_queries.short_description = 'مانده سوال'
    
    def remaining_days(self, obj):
        if obj.status != 'active' or not obj.end_date:
            return '-'
        delta = obj.end_date - timezone.now()
        days = max(0, delta.days)
        if days > 0:
            return format_html('<span style="color: green;">{} روز</span>', days)
        return format_html('<span style="color: red;">منقضی</span>')
    remaining_days.short_description = 'مانده روز'
    
    def date_joined(self, obj):
        try:
            import jdatetime
            import pytz
            dt = obj.user.date_joined
            tehran_tz = pytz.timezone('Asia/Tehran')
            if dt.tzinfo:
                dt = dt.astimezone(tehran_tz)
            j_date = jdatetime.datetime.fromgregorian(datetime=dt)
            return j_date.strftime('%Y/%m/%d')
        except Exception:
            return obj.user.date_joined.strftime('%Y/%m/%d')
    date_joined.short_description = 'تاریخ عضویت'
    date_joined.admin_order_field = 'user__date_joined'
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return False
