"""
Timezone utilities for converting UTC to user's timezone
"""
from django.utils import timezone
import pytz
from datetime import datetime


def convert_to_user_timezone(dt, user_timezone_code=None):
    """
    تبدیل datetime از UTC به timezone کاربر
    
    Args:
        dt: datetime object (aware or naive)
        user_timezone_code: کد timezone کاربر (مثل 'Asia/Tehran')
    
    Returns:
        datetime object در timezone کاربر
    """
    if not dt:
        return None
    
    # اگر timezone مشخص نشده، از تهران استفاده کن
    if not user_timezone_code:
        user_timezone_code = 'Asia/Tehran'
    
    try:
        user_tz = pytz.timezone(user_timezone_code)
    except:
        # اگر timezone نامعتبر بود، از تهران استفاده کن
        user_tz = pytz.timezone('Asia/Tehran')
    
    # اگر datetime naive است، فرض کن UTC است
    if timezone.is_naive(dt):
        dt = timezone.make_aware(dt, timezone.utc)
    
    # تبدیل به timezone کاربر
    return dt.astimezone(user_tz)


def get_user_timezone_code(user):
    """
    دریافت کد timezone کاربر
    
    Args:
        user: User object
    
    Returns:
        str: کد timezone (مثل 'Asia/Tehran')
    """
    if not user or not user.is_authenticated:
        return 'Asia/Tehran'
    
    # اگر کاربر timezone دارد
    if hasattr(user, 'timezone') and user.timezone:
        # اگر timezone یک ForeignKey است
        if hasattr(user.timezone, 'code'):
            return user.timezone.code
        # اگر timezone یک string است
        return str(user.timezone)
    
    return 'Asia/Tehran'


def format_datetime_for_user(dt, user, format_string='%Y/%m/%d %H:%M'):
    """
    فرمت کردن datetime برای نمایش به کاربر
    
    Args:
        dt: datetime object
        user: User object
        format_string: فرمت نمایش
    
    Returns:
        str: تاریخ و زمان فرمت شده
    """
    if not dt:
        return ''
    
    user_tz_code = get_user_timezone_code(user)
    user_dt = convert_to_user_timezone(dt, user_tz_code)
    
    return user_dt.strftime(format_string)


def format_datetime_jalali(dt, user):
    """
    فرمت کردن datetime به شمسی برای نمایش به کاربر
    
    Args:
        dt: datetime object
        user: User object
    
    Returns:
        str: تاریخ و زمان شمسی فرمت شده
    """
    if not dt:
        return ''
    
    try:
        import jdatetime
        user_tz_code = get_user_timezone_code(user)
        user_dt = convert_to_user_timezone(dt, user_tz_code)
        
        jalali = jdatetime.datetime.fromgregorian(datetime=user_dt)
        return jalali.strftime('%Y/%m/%d %H:%M')
    except:
        return format_datetime_for_user(dt, user)
