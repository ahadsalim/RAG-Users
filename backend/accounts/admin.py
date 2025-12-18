"""
Django Admin configuration for accounts app
"""
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _
from django.utils.html import format_html
from .models import User, Organization, UserSession, OrganizationInvitation, AuditLog, StaffGroup


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Custom User Admin"""
    
    list_display = [
        'phone_number', 'email', 'get_full_name', 'user_type', 
        'organization_role', 'is_staff', 'is_superuser', 
        'is_active', 'phone_verified', 'get_created_at_display'
    ]
    list_filter = [
        'user_type', 'is_staff', 'is_superuser', 'is_active', 
        'phone_verified', 'email_verified', 'organization_role', 'created_at'
    ]
    search_fields = ['phone_number', 'email', 'first_name', 'last_name', 'national_id', 'company_name']
    ordering = ['-created_at']
    
    fieldsets = (
        (_('اطلاعات ورود'), {
            'fields': ('phone_number', 'email', 'password_change_link')
        }),
        (_('اطلاعات شخصی'), {
            'fields': ('first_name', 'last_name', 'avatar', 'bio', 'user_type', 'national_id', 'national_id_verified')
        }),
        (_('اطلاعات تجاری'), {
            'fields': ('company_name', 'economic_code', 'organization', 'organization_role'),
            'classes': ('collapse',)
        }),
        (_('دسترسی‌ها'), {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'staff_groups'),
        }),
        (_('تنظیمات'), {
            'fields': ('language', 'timezone', 'currency'),
            'classes': ('collapse',)
        }),
        (_('امنیت'), {
            'fields': ('two_factor_enabled', 'phone_verified', 'email_verified', 'last_password_change', 'failed_login_attempts', 'locked_until'),
            'classes': ('collapse',)
        }),
        (_('اعلان‌ها'), {
            'fields': ('email_notifications', 'sms_notifications', 'push_notifications'),
            'classes': ('collapse',)
        }),
        (_('تاریخ‌ها'), {
            'fields': ('last_login_display', 'created_at_display', 'updated_at_display', 'last_seen_display'),
            'classes': ('collapse',)
        }),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('phone_number', 'email', 'password1', 'password2', 'first_name', 'last_name', 'user_type', 'is_staff', 'is_superuser'),
        }),
    )
    
    readonly_fields = [
        'password_change_link', 
        'created_at_display', 'updated_at_display', 'last_login_display', 'last_seen_display',
        'last_password_change'
    ]
    filter_horizontal = ['staff_groups']
    
    def get_full_name(self, obj):
        return obj.get_full_name() or '-'
    get_full_name.short_description = _('نام کامل')
    
    def password_change_link(self, obj):
        if obj.pk:
            from django.urls import reverse
            from django.utils.html import format_html
            url = reverse('admin:auth_user_password_change', args=[obj.pk])
            return format_html('<a href="{}" class="button">تغییر رمز عبور</a>', url)
        return '-'
    password_change_link.short_description = _('رمز عبور')
    
    def get_created_at_display(self, obj):
        return self._format_jalali_datetime(obj.created_at)
    get_created_at_display.short_description = _('تاریخ ایجاد')
    get_created_at_display.admin_order_field = 'created_at'
    
    def created_at_display(self, obj):
        return self._format_jalali_datetime(obj.created_at)
    created_at_display.short_description = _('تاریخ ایجاد')
    
    def updated_at_display(self, obj):
        return self._format_jalali_datetime(obj.updated_at)
    updated_at_display.short_description = _('تاریخ به‌روزرسانی')
    
    def last_login_display(self, obj):
        return self._format_jalali_datetime(obj.last_login) if obj.last_login else '-'
    last_login_display.short_description = _('آخرین ورود')
    
    def last_seen_display(self, obj):
        return self._format_jalali_datetime(obj.last_seen) if obj.last_seen else '-'
    last_seen_display.short_description = _('آخرین بازدید')
    
    def _format_jalali_datetime(self, dt):
        """Convert datetime to Jalali (Persian) format"""
        if not dt:
            return '-'
        try:
            from datetime import datetime
            import jdatetime
            import pytz
            # Convert to Tehran timezone
            from django.utils import timezone as tz
            if tz.is_aware(dt):
                tehran_tz = pytz.timezone('Asia/Tehran')
                dt = dt.astimezone(tehran_tz)
            
            # Convert to Jalali
            j_date = jdatetime.datetime.fromgregorian(datetime=dt)
            return j_date.strftime('%Y/%m/%d - %H:%M:%S')
        except Exception as e:
            return str(dt)


@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    """Organization Admin"""
    
    list_display = ['name', 'slug', 'company_name', 'member_count', 'max_members', 'created_at']
    list_filter = ['created_at']
    search_fields = ['name', 'slug', 'company_name', 'economic_code', 'national_id']
    ordering = ['-created_at']
    prepopulated_fields = {'slug': ('name',)}
    
    fieldsets = (
        (_('اطلاعات پایه'), {
            'fields': ('name', 'slug', 'logo')
        }),
        (_('اطلاعات قانونی'), {
            'fields': ('company_name', 'economic_code', 'national_id', 'registration_number')
        }),
        (_('اطلاعات تماس'), {
            'fields': ('address', 'postal_code', 'phone')
        }),
        (_('تنظیمات'), {
            'fields': ('allowed_email_domains', 'max_members')
        }),
        (_('تاریخ‌ها'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['created_at', 'updated_at']
    
    def member_count(self, obj):
        count = obj.members.count()
        return format_html('<strong>{}</strong> عضو', count)
    member_count.short_description = _('تعداد اعضا')


@admin.register(UserSession)
class UserSessionAdmin(admin.ModelAdmin):
    """User Session Admin"""
    
    list_display = ['user', 'device_type', 'ip_address', 'is_active', 'created_at', 'last_activity']
    list_filter = ['device_type', 'is_active', 'created_at']
    search_fields = ['user__email', 'user__phone_number', 'ip_address', 'user_agent']
    ordering = ['-last_activity']
    date_hierarchy = 'created_at'
    
    fieldsets = (
        (_('کاربر'), {
            'fields': ('user',)
        }),
        (_('اطلاعات دستگاه'), {
            'fields': ('device_type', 'device_name', 'browser', 'os', 'ip_address', 'user_agent')
        }),
        (_('وضعیت'), {
            'fields': ('is_active', 'last_activity')
        }),
        (_('تاریخ‌ها'), {
            'fields': ('created_at', 'expires_at'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['created_at']


@admin.register(OrganizationInvitation)
class OrganizationInvitationAdmin(admin.ModelAdmin):
    """Organization Invitation Admin"""
    
    list_display = ['email', 'organization', 'role', 'accepted', 'invited_by', 'created_at', 'expires_at']
    list_filter = ['accepted', 'role', 'created_at']
    search_fields = ['email', 'organization__name', 'invited_by__email']
    ordering = ['-created_at']
    date_hierarchy = 'created_at'
    
    fieldsets = (
        (_('دعوت‌نامه'), {
            'fields': ('organization', 'email', 'role', 'invited_by')
        }),
        (_('وضعیت'), {
            'fields': ('accepted', 'accepted_by', 'token')
        }),
        (_('تاریخ‌ها'), {
            'fields': ('created_at', 'expires_at', 'accepted_at'),
        }),
    )
    
    readonly_fields = ['token', 'created_at', 'accepted_at']


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    """Audit Log Admin"""
    
    list_display = ['user', 'action', 'ip_address', 'timestamp']
    list_filter = ['action', 'timestamp']
    search_fields = ['user__email', 'user__phone_number', 'ip_address']
    ordering = ['-timestamp']
    date_hierarchy = 'timestamp'
    
    fieldsets = (
        (_('کاربر و عملیات'), {
            'fields': ('user', 'action')
        }),
        (_('جزئیات'), {
            'fields': ('details',)
        }),
        (_('اطلاعات درخواست'), {
            'fields': ('ip_address', 'user_agent')
        }),
        (_('تاریخ'), {
            'fields': ('timestamp',)
        }),
    )
    
    readonly_fields = ['timestamp']
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False


@admin.register(StaffGroup)
class StaffGroupAdmin(admin.ModelAdmin):
    """Staff Group Admin - گروه‌های کارمندی"""
    
    list_display = ['name', 'get_permissions_count', 'member_count', 'priority', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'description']
    ordering = ['-priority', 'name']
    
    fieldsets = (
        (_('اطلاعات پایه'), {
            'fields': ('name', 'description', 'priority', 'is_active')
        }),
        (_('دسترسی‌های کاربران'), {
            'fields': ('can_view_users', 'can_edit_users', 'can_delete_users')
        }),
        (_('دسترسی‌های مالی'), {
            'fields': ('can_view_financial', 'can_manage_financial')
        }),
        (_('دسترسی‌های سیستم'), {
            'fields': (
                'can_view_analytics', 'can_export_data', 
                'can_manage_content', 'can_manage_subscriptions',
                'can_view_logs', 'can_manage_support'
            )
        }),
    )
    
    readonly_fields = ['created_at', 'updated_at']
    
    def get_permissions_count(self, obj):
        count = len(obj.get_permissions_list())
        return format_html('<strong>{}</strong> دسترسی', count)
    get_permissions_count.short_description = _('تعداد دسترسی‌ها')
    
    def member_count(self, obj):
        count = obj.members.filter(is_staff=True).count()
        return format_html('<strong>{}</strong> کارمند', count)
    member_count.short_description = _('تعداد اعضا')
