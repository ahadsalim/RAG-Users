"""
سیستم دسترسی برای پنل ادمین
"""
from rest_framework import permissions
from django.utils import timezone
from .models import AdminUser, AdminAction


class IsAdminUser(permissions.BasePermission):
    """بررسی کاربر ادمین بودن"""
    
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        
        # Superuser همیشه دسترسی دارد
        if request.user.is_superuser:
            return True
        
        # بررسی وجود پروفایل ادمین
        try:
            admin_user = request.user.admin_profile
            return admin_user.is_active
        except AdminUser.DoesNotExist:
            return False


class HasAdminPermission(permissions.BasePermission):
    """بررسی دسترسی خاص ادمین"""
    
    def __init__(self, permission_code):
        self.permission_code = permission_code
    
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        
        # Superuser همیشه دسترسی دارد
        if request.user.is_superuser:
            return True
        
        # بررسی دسترسی ادمین
        try:
            admin_user = request.user.admin_profile
            return admin_user.has_permission(self.permission_code)
        except AdminUser.DoesNotExist:
            return False


class RoleBasedPermission(permissions.BasePermission):
    """دسترسی بر اساس نقش"""
    
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        
        # Superuser همیشه دسترسی دارد
        if request.user.is_superuser:
            return True
        
        # دریافت نقش‌های مورد نیاز از view
        required_roles = getattr(view, 'required_roles', [])
        if not required_roles:
            return True  # اگر نقش خاصی نیاز نیست
        
        try:
            admin_user = request.user.admin_profile
            user_roles = admin_user.roles.filter(is_active=True).values_list('role_type', flat=True)
            
            # بررسی تطابق نقش‌ها
            return any(role in user_roles for role in required_roles)
        except AdminUser.DoesNotExist:
            return False


class IPRestrictionPermission(permissions.BasePermission):
    """محدودیت دسترسی بر اساس IP"""
    
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        
        # Superuser محدودیت IP ندارد
        if request.user.is_superuser:
            return True
        
        try:
            admin_user = request.user.admin_profile
            
            # اگر محدودیت IP تعریف نشده، دسترسی آزاد است
            if not admin_user.allowed_ips:
                return True
            
            # دریافت IP کاربر
            client_ip = self.get_client_ip(request)
            allowed_ips = admin_user.allowed_ips.strip().split('\n')
            
            return client_ip in allowed_ips
        except AdminUser.DoesNotExist:
            return False
    
    def get_client_ip(self, request):
        """دریافت IP واقعی کاربر"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class TimeRestrictionPermission(permissions.BasePermission):
    """محدودیت دسترسی بر اساس زمان"""
    
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        
        # Superuser محدودیت زمانی ندارد
        if request.user.is_superuser:
            return True
        
        try:
            admin_user = request.user.admin_profile
            
            # بررسی محدودیت زمانی
            if admin_user.access_start_time and admin_user.access_end_time:
                now = timezone.now().time()
                if not (admin_user.access_start_time <= now <= admin_user.access_end_time):
                    return False
            
            return True
        except AdminUser.DoesNotExist:
            return False


# Permission Classes ترکیبی
class AdminFullAccess(permissions.BasePermission):
    """دسترسی کامل ادمین"""
    
    def has_permission(self, request, view):
        return (
            IsAdminUser().has_permission(request, view) and
            IPRestrictionPermission().has_permission(request, view) and
            TimeRestrictionPermission().has_permission(request, view)
        )


class AdminReadOnly(permissions.BasePermission):
    """دسترسی فقط خواندنی ادمین"""
    
    def has_permission(self, request, view):
        if request.method not in permissions.SAFE_METHODS:
            return False
        
        return AdminFullAccess().has_permission(request, view)


# دکوراتور برای لاگ کردن اقدامات
def log_admin_action(action_type, model_name=None):
    """دکوراتور برای ثبت لاگ اقدامات ادمین"""
    
    def decorator(func):
        def wrapper(self, request, *args, **kwargs):
            # اجرای تابع اصلی
            response = func(self, request, *args, **kwargs)
            
            # ثبت لاگ
            try:
                admin_user = request.user.admin_profile
                
                # استخراج اطلاعات از response
                object_id = None
                object_repr = None
                if hasattr(response, 'data'):
                    data = response.data
                    if isinstance(data, dict):
                        object_id = data.get('id', '')
                        object_repr = str(data)[:500]
                
                AdminAction.objects.create(
                    admin_user=admin_user,
                    action_type=action_type,
                    model_name=model_name or self.__class__.__name__,
                    object_id=str(object_id) if object_id else '',
                    object_repr=object_repr or '',
                    description=f"{action_type} action performed",
                    ip_address=request.META.get('REMOTE_ADDR'),
                    user_agent=request.META.get('HTTP_USER_AGENT', ''),
                    metadata={
                        'method': request.method,
                        'path': request.path,
                        'query_params': dict(request.query_params) if hasattr(request, 'query_params') else {}
                    }
                )
            except Exception as e:
                # لاگ نباید باعث خطا در عملیات اصلی شود
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"Error logging admin action: {e}")
            
            return response
        
        return wrapper
    return decorator


class AdminActionLoggerMixin:
    """Mixin برای لاگ خودکار اقدامات در ViewSets"""
    
    def create(self, request, *args, **kwargs):
        response = super().create(request, *args, **kwargs)
        self._log_action('create', request, response)
        return response
    
    def update(self, request, *args, **kwargs):
        # ذخیره داده قبلی
        instance = self.get_object()
        before_data = self.get_serializer(instance).data
        
        response = super().update(request, *args, **kwargs)
        self._log_action('update', request, response, before_data=before_data)
        return response
    
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        before_data = self.get_serializer(instance).data
        
        response = super().destroy(request, *args, **kwargs)
        self._log_action('delete', request, None, before_data=before_data)
        return response
    
    def _log_action(self, action_type, request, response=None, before_data=None):
        """ثبت لاگ اقدام"""
        try:
            admin_user = request.user.admin_profile
            
            # استخراج اطلاعات
            model_name = self.get_serializer_class().__name__.replace('Serializer', '')
            object_id = ''
            object_repr = ''
            after_data = {}
            
            if response and hasattr(response, 'data'):
                data = response.data
                if isinstance(data, dict):
                    object_id = data.get('id', '')
                    after_data = data
                object_repr = str(data)[:500]
            
            AdminAction.objects.create(
                admin_user=admin_user,
                action_type=action_type,
                model_name=model_name,
                object_id=str(object_id) if object_id else '',
                object_repr=object_repr,
                before_data=before_data or {},
                after_data=after_data,
                ip_address=request.META.get('REMOTE_ADDR'),
                user_agent=request.META.get('HTTP_USER_AGENT', '')
            )
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error logging admin action: {e}")
