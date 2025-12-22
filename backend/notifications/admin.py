from django.contrib import admin
from django.utils.html import format_html
from django import forms
from .models import (
    NotificationTemplate, Notification, NotificationPreference,
    DeviceToken, NotificationLog
)


@admin.register(NotificationTemplate)
class NotificationTemplateAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'category', 'default_priority', 'is_active', 'channels_display', 'created_at']
    list_filter = ['category', 'default_priority', 'is_active', 'created_at']
    search_fields = ['name', 'code', 'title_template', 'body_template']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('اطلاعات پایه و محتوای قالب', {
            'fields': ('code', 'name', 'description', 'category', 'title_template', 'body_template')
        }),
        ('قالب‌های مخصوص', {
            'fields': ('email_subject_template', 'email_html_template', 'sms_template'),
            'classes': ('collapse',)
        }),
        ('تنظیمات', {
            'fields': ('channels', 'default_priority', 'is_active', 'require_confirmation')
        }),
        ('اقدام', {
            'fields': ('action_url', 'action_text')
        }),
        ('متادیتا', {
            'fields': ('metadata', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def formfield_for_dbfield(self, db_field, request, **kwargs):
        if db_field.name == 'description':
            kwargs['widget'] = forms.Textarea(attrs={'rows': 2, 'style': 'width: 100%;'})
        elif db_field.name == 'body_template':
            kwargs['widget'] = forms.Textarea(attrs={'rows': 2, 'style': 'width: 100%;'})
        return super().formfield_for_dbfield(db_field, request, **kwargs)
    
    def channels_display(self, obj):
        if obj.channels:
            return ', '.join(obj.channels)
        return '-'
    channels_display.short_description = 'کانال‌ها'


class NotificationLogInline(admin.TabularInline):
    model = NotificationLog
    extra = 0
    readonly_fields = ['channel', 'status', 'recipient', 'sent_at', 'error_message']
    can_delete = False
    
    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ['title', 'user', 'category', 'priority', 'is_read', 'channels_display', 'sent_status', 'created_at']
    list_filter = ['category', 'priority', 'is_read', 'created_at', 'sent_via_email', 'sent_via_sms', 'sent_via_push']
    search_fields = ['title', 'body', 'user__email']
    readonly_fields = ['created_at', 'read_at', 'confirmed_at']
    inlines = [NotificationLogInline]
    
    fieldsets = (
        ('گیرنده', {
            'fields': ('user', 'template')
        }),
        ('محتوا', {
            'fields': ('title', 'body', 'category', 'priority')
        }),
        ('اقدام', {
            'fields': ('action_url', 'action_text')
        }),
        ('وضعیت ارسال', {
            'fields': ('channels', 'sent_via_email', 'sent_via_sms', 'sent_via_push', 'sent_via_in_app')
        }),
        ('وضعیت خواندن', {
            'fields': ('is_read', 'read_at', 'is_confirmed', 'confirmed_at')
        }),
        ('اطلاعات اضافی', {
            'fields': ('metadata', 'error_log', 'created_at', 'expires_at'),
            'classes': ('collapse',)
        }),
    )
    
    def channels_display(self, obj):
        if obj.channels:
            return ', '.join(obj.channels)
        return '-'
    channels_display.short_description = 'کانال‌ها'
    
    def sent_status(self, obj):
        statuses = []
        if obj.sent_via_email:
            statuses.append('📧')
        if obj.sent_via_sms:
            statuses.append('💬')
        if obj.sent_via_push:
            statuses.append('🔔')
        if obj.sent_via_in_app:
            statuses.append('📱')
        return ' '.join(statuses) if statuses else '-'
    sent_status.short_description = 'ارسال شده'
    
    actions = ['mark_as_read', 'mark_as_unread']
    
    def mark_as_read(self, request, queryset):
        from django.utils import timezone
        count = queryset.update(is_read=True, read_at=timezone.now())
        self.message_user(request, f'{count} اعلان به عنوان خوانده شده علامت‌گذاری شد.')
    mark_as_read.short_description = 'علامت‌گذاری به عنوان خوانده شده'
    
    def mark_as_unread(self, request, queryset):
        count = queryset.update(is_read=False, read_at=None)
        self.message_user(request, f'{count} اعلان به عنوان خوانده نشده علامت‌گذاری شد.')
    mark_as_unread.short_description = 'علامت‌گذاری به عنوان خوانده نشده'


@admin.register(NotificationPreference)
class NotificationPreferenceAdmin(admin.ModelAdmin):
    list_display = ['get_user_display', 'email_enabled', 'sms_enabled', 'push_enabled', 'in_app_enabled', 'get_updated_at_jalali']
    list_filter = ['email_enabled', 'sms_enabled', 'push_enabled', 'in_app_enabled']
    search_fields = ['user__phone_number', 'user__email']
    readonly_fields = ['user_display', 'get_created_at_jalali', 'get_updated_at_jalali']
    
    fields = (
        'user_display',
        ('email_enabled', 'sms_enabled'),
        ('push_enabled', 'in_app_enabled'),
        ('system_notifications', 'payment_notifications'),
        ('subscription_notifications', 'chat_notifications'),
        ('account_notifications', 'security_notifications'),
        ('marketing_notifications', 'support_notifications'),
        ('get_created_at_jalali', 'get_updated_at_jalali'),
    )
    
    def get_user_display(self, obj):
        """نمایش نام کاربر در لیست"""
        return obj.user.get_full_name() or obj.user.phone_number
    get_user_display.short_description = 'کاربر'
    
    def user_display(self, obj):
        """نمایش نام کاربر در فرم"""
        return obj.user.get_full_name() or obj.user.phone_number
    user_display.short_description = 'کاربر'
    
    def get_created_at_jalali(self, obj):
        """تبدیل تاریخ ایجاد به شمسی"""
        from datetime import datetime
        import jdatetime
        if obj.created_at:
            jalali = jdatetime.datetime.fromgregorian(datetime=obj.created_at)
            return jalali.strftime('%Y/%m/%d - %H:%M')
        return '-'
    get_created_at_jalali.short_description = 'تاریخ ایجاد'
    
    def get_updated_at_jalali(self, obj):
        """تبدیل تاریخ به‌روزرسانی به شمسی"""
        from datetime import datetime
        import jdatetime
        if obj.updated_at:
            jalali = jdatetime.datetime.fromgregorian(datetime=obj.updated_at)
            return jalali.strftime('%Y/%m/%d - %H:%M')
        return '-'
    get_updated_at_jalali.short_description = 'آخرین به‌روزرسانی'


@admin.register(DeviceToken)
class DeviceTokenAdmin(admin.ModelAdmin):
    """
    توکن‌های دستگاه برای Push Notification
    برای توضیحات کامل فایل notifications/models.py را ببینید
    """
    list_display = ['user', 'device_type', 'device_name', 'is_active', 'last_used_at', 'created_at']
    list_filter = ['device_type', 'is_active', 'created_at']
    search_fields = ['user__email', 'device_name', 'token']
    readonly_fields = ['created_at', 'updated_at', 'last_used_at']
    
    fields = ['user', 'token', 'device_type', 'device_name', 'is_active', 'last_used_at', 'created_at', 'updated_at']
    
    def changelist_view(self, request, extra_context=None):
        from django.contrib import messages
        messages.info(request, '📱 توکن‌های دستگاه برای Push Notification استفاده می‌شود. برای توضیحات کامل فایل notifications/models.py را ببینید.')
        return super().changelist_view(request, extra_context=extra_context)


@admin.register(NotificationLog)
class NotificationLogAdmin(admin.ModelAdmin):
    list_display = ['notification', 'channel', 'recipient', 'status', 'sent_at', 'retry_count']
    list_filter = ['channel', 'status', 'created_at']
    search_fields = ['notification__title', 'recipient']
    readonly_fields = ['created_at', 'sent_at', 'delivered_at']
    
    fields = [
        'notification', 'channel', 'status', 'recipient',
        'provider_message_id', 'provider_response',
        'error_message', 'retry_count',
        'created_at', 'sent_at', 'delivered_at'
    ]
