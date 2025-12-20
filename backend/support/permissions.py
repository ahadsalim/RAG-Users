from rest_framework import permissions


class IsStaffOrReadOnly(permissions.BasePermission):
    """
    فقط کارشناسان می‌توانند تغییر دهند
    """
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user and request.user.is_staff


class IsTicketOwnerOrStaff(permissions.BasePermission):
    """
    فقط صاحب تیکت یا کارشناسان دسترسی دارند
    """
    def has_object_permission(self, request, view, obj):
        # کارشناسان دسترسی کامل دارند
        if request.user.is_staff:
            return True
        
        # صاحب تیکت فقط می‌تواند تیکت خود را ببیند
        return obj.user == request.user


class IsDepartmentAgent(permissions.BasePermission):
    """
    فقط کارشناسان دپارتمان مربوطه دسترسی دارند
    """
    def has_object_permission(self, request, view, obj):
        if request.user.is_superuser:
            return True
        
        if not request.user.is_staff:
            return False
        
        # بررسی عضویت در دپارتمان
        if hasattr(obj, 'department') and obj.department:
            return request.user in obj.department.agents.all()
        
        return True


class CanManageTicket(permissions.BasePermission):
    """
    دسترسی مدیریت تیکت
    """
    def has_object_permission(self, request, view, obj):
        user = request.user
        
        # سوپر یوزر همه دسترسی‌ها را دارد
        if user.is_superuser:
            return True
        
        # کاربر عادی فقط می‌تواند تیکت خود را ببیند
        if not user.is_staff:
            return obj.user == user
        
        # کارشناس تخصیص داده شده
        if obj.assigned_to == user:
            return True
        
        # کارشناس دپارتمان
        if obj.department and user in obj.department.agents.all():
            return True
        
        # مدیر دپارتمان
        if obj.department and obj.department.manager == user:
            return True
        
        return False
