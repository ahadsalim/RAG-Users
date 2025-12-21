"""
Middleware to activate user's timezone
"""
from django.utils import timezone
import pytz


class TimezoneMiddleware:
    """
    Middleware برای فعال‌سازی timezone کاربر
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # دریافت timezone کاربر
        if request.user.is_authenticated:
            user_timezone = self.get_user_timezone(request.user)
            if user_timezone:
                timezone.activate(user_timezone)
        else:
            # برای کاربران مهمان، از تهران استفاده کن
            timezone.activate(pytz.timezone('Asia/Tehran'))
        
        response = self.get_response(request)
        
        # بازگشت به timezone پیش‌فرض
        timezone.deactivate()
        
        return response
    
    def get_user_timezone(self, user):
        """دریافت timezone کاربر"""
        try:
            if hasattr(user, 'timezone') and user.timezone:
                # اگر timezone یک ForeignKey است
                if hasattr(user.timezone, 'code'):
                    return pytz.timezone(user.timezone.code)
                # اگر timezone یک string است
                return pytz.timezone(str(user.timezone))
        except:
            pass
        
        return pytz.timezone('Asia/Tehran')
