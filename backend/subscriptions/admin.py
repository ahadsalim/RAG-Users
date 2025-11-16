from django.contrib import admin
from django.utils.html import format_html
from django.utils import timezone
from .models import Plan, Subscription


@admin.register(Plan)
class PlanAdmin(admin.ModelAdmin):
    list_display = ['name', 'price', 'duration_days', 'is_active']
    list_filter = ['is_active']
    search_fields = ['name', 'description']


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ['user', 'plan', 'status', 'start_date', 'end_date', 'auto_renew']
    list_filter = ['status', 'plan', 'auto_renew']
    search_fields = ['user__email']
    date_hierarchy = 'created_at'
    
    actions = ['activate_subscription', 'cancel_subscription']
    
    def activate_subscription(self, request, queryset):
        for sub in queryset:
            sub.activate()
        self.message_user(request, f'{queryset.count()} اشتراک فعال شد.')
    activate_subscription.short_description = 'فعال‌سازی'
    
    def cancel_subscription(self, request, queryset):
        for sub in queryset:
            sub.cancel()
        self.message_user(request, f'{queryset.count()} اشتراک لغو شد.')
    cancel_subscription.short_description = 'لغو اشتراک'
