"""
سیستم دسترسی برای کارمندان
بر اساس StaffGroup و دسترسی‌های سفارشی
"""
from rest_framework import permissions


class IsStaffUser(permissions.BasePermission):
    """بررسی کارمند بودن کاربر"""
    
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        
        return request.user.is_staff


class IsSuperUser(permissions.BasePermission):
    """بررسی سوپر یوزر بودن"""
    
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        
        return request.user.is_superuser


class HasStaffPermission(permissions.BasePermission):
    """
    بررسی دسترسی خاص کارمند بر اساس StaffGroup
    استفاده: permission_classes = [HasStaffPermission('view_financial')]
    """
    
    def __init__(self, permission_code=None):
        self.permission_code = permission_code
    
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        
        # سوپر یوزر همه دسترسی‌ها را دارد
        if request.user.is_superuser:
            return True
        
        # کارمند نیست
        if not request.user.is_staff:
            return False
        
        # اگر permission_code مشخص نشده، فقط is_staff کافی است
        if not self.permission_code:
            return True
        
        # بررسی دسترسی در گروه‌های کارمندی
        return request.user.has_staff_permission(self.permission_code)


def staff_permission_factory(permission_code):
    """
    Factory برای ایجاد permission class با کد دسترسی خاص
    استفاده: permission_classes = [staff_permission_factory('view_financial')]
    """
    class StaffPermission(permissions.BasePermission):
        def has_permission(self, request, view):
            if not request.user.is_authenticated:
                return False
            
            if request.user.is_superuser:
                return True
            
            if not request.user.is_staff:
                return False
            
            return request.user.has_staff_permission(permission_code)
    
    return StaffPermission


# Permission classes آماده برای استفاده
class CanViewUsers(permissions.BasePermission):
    """دسترسی مشاهده کاربران"""
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        if request.user.is_superuser:
            return True
        return request.user.has_staff_permission('view_users')


class CanEditUsers(permissions.BasePermission):
    """دسترسی ویرایش کاربران"""
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        if request.user.is_superuser:
            return True
        return request.user.has_staff_permission('edit_users')


class CanViewFinancial(permissions.BasePermission):
    """دسترسی مشاهده امور مالی"""
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        if request.user.is_superuser:
            return True
        return request.user.has_staff_permission('view_financial')


class CanManageFinancial(permissions.BasePermission):
    """دسترسی مدیریت امور مالی"""
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        if request.user.is_superuser:
            return True
        return request.user.has_staff_permission('manage_financial')


class CanViewAnalytics(permissions.BasePermission):
    """دسترسی مشاهده گزارشات"""
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        if request.user.is_superuser:
            return True
        return request.user.has_staff_permission('view_analytics')


class CanExportData(permissions.BasePermission):
    """دسترسی خروجی داده"""
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        if request.user.is_superuser:
            return True
        return request.user.has_staff_permission('export_data')


class CanManageContent(permissions.BasePermission):
    """دسترسی مدیریت محتوا"""
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        if request.user.is_superuser:
            return True
        return request.user.has_staff_permission('manage_content')


class CanManageSubscriptions(permissions.BasePermission):
    """دسترسی مدیریت اشتراک‌ها"""
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        if request.user.is_superuser:
            return True
        return request.user.has_staff_permission('manage_subscriptions')


class CanViewLogs(permissions.BasePermission):
    """دسترسی مشاهده لاگ‌ها"""
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        if request.user.is_superuser:
            return True
        return request.user.has_staff_permission('view_logs')


class CanManageSupport(permissions.BasePermission):
    """دسترسی مدیریت پشتیبانی"""
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        if request.user.is_superuser:
            return True
        return request.user.has_staff_permission('manage_support')
