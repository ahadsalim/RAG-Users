"""
Django Admin configuration for admin_panel app
"""
from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from django.utils.html import format_html
from .models import Role, AdminUser, AdminAction, AdminDashboardWidget, AdminNotification


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    """Role Admin"""
    
    list_display = ['name', 'role_type', 'priority', 'is_active', 'is_default', 'created_at']
    list_filter = ['role_type', 'is_active', 'is_default', 'created_at']
    search_fields = ['name', 'description']
    ordering = ['-priority', 'name']
    
    fieldsets = (
        (_('اطلاعات پایه'), {
            'fields': ('name', 'role_type', 'description', 'priority')
        }),
        (_('دسترسی‌های کاربران'), {
            'fields': (
                'can_view_all_users', 'can_edit_users', 'can_delete_users'
            )
        }),
        (_('دسترسی‌های مالی'), {
            'fields': ('can_view_financial', 'can_manage_financial')
        }),
        (_('دسترسی‌های سیستم'), {
            'fields': (
                'can_view_analytics', 'can_export_data', 
                'can_manage_content', 'can_manage_system', 'can_view_logs'
            )
        }),
        (_('دسترسی‌های Django'), {
            'fields': ('permissions',),
            'classes': ('collapse',)
        }),
        (_('تنظیمات'), {
            'fields': ('is_active', 'is_default', 'created_by')
        }),
    )
    
    filter_horizontal = ['permissions']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(AdminUser)
class AdminUserAdmin(admin.ModelAdmin):
    """Admin User Admin"""
    
    list_display = ['user', 'get_roles', 'department', 'employee_id', 'is_active', 'last_activity']
    list_filter = ['is_active', 'department', 'created_at']
    search_fields = ['user__email', 'user__phone_number', 'user__first_name', 'user__last_name', 'employee_id']
    ordering = ['-created_at']
    
    fieldsets = (
        (_('کاربر'), {
            'fields': ('user',)
        }),
        (_('نقش‌ها'), {
            'fields': ('roles',)
        }),
        (_('اطلاعات شغلی'), {
            'fields': ('department', 'employee_id')
        }),
        (_('محدودیت‌های دسترسی'), {
            'fields': ('access_start_time', 'access_end_time', 'allowed_ips'),
            'classes': ('collapse',)
        }),
        (_('وضعیت'), {
            'fields': ('is_active', 'last_activity')
        }),
    )
    
    filter_horizontal = ['roles']
    readonly_fields = ['last_activity', 'created_at', 'updated_at']
    
    def get_roles(self, obj):
        roles = obj.roles.filter(is_active=True)
        if roles.exists():
            role_list = ', '.join([role.name for role in roles])
            return format_html('<span style="color: #0066cc;">{}</span>', role_list)
        return '-'
    get_roles.short_description = _('نقش‌ها')


@admin.register(AdminAction)
class AdminActionAdmin(admin.ModelAdmin):
    """Admin Action Log Admin"""
    
    list_display = ['admin_user', 'action_type', 'model_name', 'object_repr', 'ip_address', 'created_at']
    list_filter = ['action_type', 'model_name', 'created_at']
    search_fields = ['admin_user__user__email', 'model_name', 'object_repr', 'description', 'ip_address']
    ordering = ['-created_at']
    date_hierarchy = 'created_at'
    
    fieldsets = (
        (_('ادمین و عملیات'), {
            'fields': ('admin_user', 'action_type', 'model_name')
        }),
        (_('شیء'), {
            'fields': ('object_id', 'object_repr')
        }),
        (_('تغییرات'), {
            'fields': ('before_data', 'after_data', 'description'),
            'classes': ('collapse',)
        }),
        (_('اطلاعات درخواست'), {
            'fields': ('ip_address', 'user_agent', 'metadata'),
            'classes': ('collapse',)
        }),
        (_('تاریخ'), {
            'fields': ('created_at',)
        }),
    )
    
    readonly_fields = ['created_at']
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False


@admin.register(AdminDashboardWidget)
class AdminDashboardWidgetAdmin(admin.ModelAdmin):
    """Admin Dashboard Widget Admin"""
    
    list_display = ['title', 'widget_type', 'position_x', 'position_y', 'width', 'height', 'is_active', 'is_default']
    list_filter = ['widget_type', 'is_active', 'is_default', 'created_at']
    search_fields = ['title', 'required_permission']
    ordering = ['position_y', 'position_x']
    
    fieldsets = (
        (_('اطلاعات پایه'), {
            'fields': ('title', 'widget_type')
        }),
        (_('تنظیمات'), {
            'fields': ('config', 'required_permission', 'roles')
        }),
        (_('موقعیت و اندازه'), {
            'fields': ('position_x', 'position_y', 'width', 'height')
        }),
        (_('وضعیت'), {
            'fields': ('is_active', 'is_default')
        }),
    )
    
    filter_horizontal = ['roles']


@admin.register(AdminNotification)
class AdminNotificationAdmin(admin.ModelAdmin):
    """Admin Notification Admin"""
    
    list_display = ['title', 'notification_type', 'admin_user', 'broadcast', 'is_read', 'created_at']
    list_filter = ['notification_type', 'is_read', 'broadcast', 'created_at']
    search_fields = ['title', 'message', 'admin_user__user__email']
    ordering = ['-created_at']
    date_hierarchy = 'created_at'
    
    fieldsets = (
        (_('گیرنده'), {
            'fields': ('admin_user', 'roles', 'broadcast')
        }),
        (_('محتوا'), {
            'fields': ('title', 'message', 'notification_type')
        }),
        (_('اقدام'), {
            'fields': ('action_url', 'action_text'),
            'classes': ('collapse',)
        }),
        (_('وضعیت'), {
            'fields': ('is_read', 'read_at')
        }),
        (_('تاریخ‌ها'), {
            'fields': ('created_at', 'expires_at')
        }),
    )
    
    filter_horizontal = ['roles']
    readonly_fields = ['created_at', 'read_at']
