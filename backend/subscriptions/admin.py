from django.contrib import admin
from django.utils.html import format_html
from django.utils import timezone
from .models import Plan, Subscription
from .usage import UsageLog


@admin.register(Plan)
class PlanAdmin(admin.ModelAdmin):
    list_display = ['name', 'plan_type', 'price', 'duration_days', 'max_queries_per_day', 'max_queries_per_month', 'max_organization_members', 'is_active', 'colored_status']
    list_filter = ['plan_type', 'is_active', 'created_at']
    search_fields = ['name', 'description']
    list_editable = ['price', 'duration_days', 'max_queries_per_day', 'max_queries_per_month', 'max_organization_members', 'is_active']
    ordering = ['plan_type', 'price']
    
    fieldsets = (
        ('اطلاعات پایه', {
            'fields': ('name', 'description', 'plan_type', 'price', 'duration_days', 'is_active')
        }),
        ('محدودیت‌های استفاده', {
            'fields': ('max_queries_per_day', 'max_queries_per_month'),
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
    
    def colored_status(self, obj):
        if obj.is_active:
            return format_html('<span style="color: green;">●</span> فعال')
        return format_html('<span style="color: red;">●</span> غیرفعال')
    colored_status.short_description = 'وضعیت'


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


@admin.register(UsageLog)
class UsageLogAdmin(admin.ModelAdmin):
    list_display = ['user_info', 'action_type', 'tokens_used', 'subscription_plan', 'created_at']
    list_filter = ['action_type', 'created_at']
    search_fields = ['user__email', 'user__phone_number', 'user__first_name', 'user__last_name']
    date_hierarchy = 'created_at'
    readonly_fields = ['id', 'user', 'subscription', 'action_type', 'tokens_used', 'metadata', 'ip_address', 'user_agent', 'created_at']
    
    def user_info(self, obj):
        return format_html(
            '<strong>{}</strong><br/><small>{}</small>',
            obj.user.get_full_name() or obj.user.email or obj.user.phone_number,
            obj.user.phone_number or obj.user.email
        )
    user_info.short_description = 'کاربر'
    
    def subscription_plan(self, obj):
        # اول از plan_name ذخیره شده استفاده کن (نام پلن در زمان ثبت)
        if obj.plan_name:
            return obj.plan_name
        # اگر نبود، از اشتراک فعلی بخوان (برای لاگ‌های قدیمی)
        if obj.subscription:
            return obj.subscription.plan.name
        return '-'
    subscription_plan.short_description = 'پلن'
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False
