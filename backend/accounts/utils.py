"""
Utility functions for accounts app
"""
from django.core.mail import send_mail
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django.template.loader import render_to_string
from user_agents import parse
import requests
import logging

logger = logging.getLogger('app')


def get_client_ip(request):
    """Get client IP address from request"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def get_user_agent_info(request):
    """Extract device and browser info from user agent"""
    user_agent_string = request.META.get('HTTP_USER_AGENT', '')
    user_agent = parse(user_agent_string)
    
    return {
        'device_type': 'mobile' if user_agent.is_mobile else 'tablet' if user_agent.is_tablet else 'desktop',
        'device_name': f"{user_agent.device.brand or 'Unknown'} {user_agent.device.model or ''}".strip(),
        'browser': f"{user_agent.browser.family} {user_agent.browser.version_string}",
        'os': f"{user_agent.os.family} {user_agent.os.version_string}"
    }


def send_email_verification(user):
    """Send email verification link to user"""
    try:
        # Generate verification token (you should implement a proper token generation)
        import secrets
        token = secrets.token_urlsafe(32)
        
        # Store token in cache or database
        from django.core.cache import cache
        cache_key = f"email_verify_{user.id}"
        cache.set(cache_key, token, 86400)  # 24 hours
        
        # Construct verification link (using backend API endpoint)
        verification_link = f"{settings.FRONTEND_URL}/api/v1/auth/verify-email/?token={token}&user={user.id}"
        
        # Send email
        subject = _('تایید ایمیل - سامانه تجارت چت')
        message = render_to_string('emails/verify_email.txt', {
            'user': user,
            'verification_link': verification_link
        })
        html_message = render_to_string('emails/verify_email.html', {
            'user': user,
            'verification_link': verification_link
        })
        
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            html_message=html_message,
            fail_silently=False
        )
        
        logger.info(f"Email verification sent to {user.email}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to send email verification to {user.email}: {str(e)}")
        return False


def send_otp_bale(phone_number, otp_code):
    """Send OTP via Bale Messenger"""
    try:
        import requests
        from decouple import config
        
        # Get Bale credentials
        client_id = config('BALE_USERNAME', default=None)
        client_secret = config('BALE_PASSWORD', default=None)
        
        if not client_id or not client_secret:
            logger.warning("Bale credentials not configured")
            return False
        
        # Get access token
        token_url = "https://safir.bale.ai/api/v2/auth/token"
        token_data = {
            'grant_type': 'client_credentials',
            'client_id': client_id,
            'client_secret': client_secret,
            'scope': 'read'
        }
        token_response = requests.post(token_url, data=token_data, timeout=10)
        token_response.raise_for_status()
        access_token = token_response.json().get('access_token')
        
        if not access_token:
            logger.error("Failed to get Bale access token")
            return False
        
        # Format phone number (remove leading 0 and add 98)
        formatted_phone = phone_number
        if phone_number.startswith('0'):
            formatted_phone = '98' + phone_number[1:]
        elif not phone_number.startswith('98'):
            formatted_phone = '98' + phone_number
        
        # Send OTP via Bale
        otp_url = "https://safir.bale.ai/api/v2/send_otp"
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }
        otp_data = {
            'phone': formatted_phone,
            'otp': int(otp_code)
        }
        
        otp_response = requests.post(otp_url, json=otp_data, headers=headers, timeout=10)
        otp_response.raise_for_status()
        
        logger.info(f"✅ OTP sent to {phone_number} via Bale Messenger: {otp_code}")
        print(f"\n{'='*50}\n✅ Bale OTP SENT\n🔐 CODE: {otp_code}\n📱 Phone: {phone_number}\n{'='*50}\n")
        return True
        
    except requests.exceptions.Timeout:
        logger.error(f"Bale API timeout for {phone_number}")
        return False
    except requests.exceptions.RequestException as e:
        logger.error(f"Bale API error for {phone_number}: {str(e)}")
        if hasattr(e, 'response') and e.response is not None:
            logger.error(f"Response: {e.response.text}")
        return False
    except Exception as e:
        logger.error(f"Failed to send OTP via Bale to {phone_number}: {str(e)}")
        return False


def send_otp_sms(phone_number, otp_code):
    """Send OTP via SMS using Kavenegar Verify API"""
    import requests
    from decouple import config
    
    try:
        # Get Kavenegar API key
        api_key = config('KAVENEGAR_API_KEY', default=None)
        template_name = 'otp'  # نام الگوی تعریف شده در کاوه نگار
        
        if not api_key or api_key == 'your-kavenegar-api-key':
            logger.warning("Kavenegar API key not configured - logging OTP instead")
            logger.info(f"⚠️ OTP for {phone_number}: {otp_code}")
            print(f"\n{'='*50}\n🔐 OTP CODE: {otp_code}\n📱 Phone: {phone_number}\n{'='*50}\n")
            return True
        
        # ارسال از طریق Verify API (اعتبارسنجی)
        url = f'https://api.kavenegar.com/v1/{api_key}/verify/lookup.json'
        
        params = {
            'receptor': phone_number,
            'token': otp_code,
            'template': template_name,
        }
        
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        
        result = response.json()
        
        if result.get('return', {}).get('status') == 200:
            logger.info(f"OTP SMS sent to {phone_number} via Kavenegar Verify API")
            return True
        else:
            logger.error(f"Kavenegar API error: {result}")
            raise Exception(f"API returned status {result.get('return', {}).get('status')}")
        
    except Exception as e:
        logger.error(f"Failed to send OTP SMS to {phone_number}: {str(e)}")
        # In development, log the OTP for testing
        logger.info(f"⚠️ OTP for {phone_number}: {otp_code}")
        print(f"\n{'='*50}\n🔐 OTP CODE: {otp_code}\n📱 Phone: {phone_number}\n❌ Error: {str(e)}\n{'='*50}\n")
        return False


def send_password_reset_email(user, reset_token):
    """Send password reset email"""
    try:
        reset_link = f"{settings.FRONTEND_URL}/auth/reset-password?token={reset_token}&user={user.id}"
        
        logger.info(f"Generated reset link: {reset_link}")
        logger.info(f"Token being sent: {reset_token}")
        
        subject = 'درخواست بازیابی رمز عبور - تجارت چت'
        message = render_to_string('emails/password_reset.txt', {
            'user': user,
            'reset_link': reset_link
        })
        html_message = render_to_string('emails/password_reset.html', {
            'user': user,
            'reset_link': reset_link
        })
        
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            html_message=html_message,
            fail_silently=False
        )
        
        logger.info(f"Password reset email sent to {user.email}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to send password reset email to {user.email}: {str(e)}")
        return False


def verify_national_id(national_id):
    """
    Verify Iranian national ID (code melli)
    Returns True if valid, False otherwise
    """
    if not national_id or len(national_id) != 10:
        return False
    
    try:
        # Check if all characters are digits
        if not national_id.isdigit():
            return False
        
        # Iranian national ID validation algorithm
        check = int(national_id[9])
        sum = 0
        for i in range(9):
            sum += int(national_id[i]) * (10 - i)
        
        remainder = sum % 11
        
        if remainder < 2:
            return check == remainder
        else:
            return check == (11 - remainder)
            
    except Exception:
        return False


def verify_economic_code(economic_code):
    """
    Verify Iranian economic code (14 digits)
    This is a placeholder - implement actual verification if API is available
    """
    if not economic_code or len(economic_code) != 14:
        return False
    
    return economic_code.isdigit()


def get_location_from_ip(ip_address):
    """
    Get approximate location from IP address
    Uses a free IP geolocation service
    """
    try:
        # Using ipapi.co free service
        response = requests.get(f"https://ipapi.co/{ip_address}/json/", timeout=5)
        if response.status_code == 200:
            data = response.json()
            return f"{data.get('city', 'Unknown')}, {data.get('country_name', 'Unknown')}"
    except Exception as e:
        logger.error(f"Failed to get location for IP {ip_address}: {str(e)}")
    
    return "Unknown"


def generate_invoice_number():
    """Generate unique invoice number"""
    from datetime import datetime
    import random
    
    # Format: INV-YYYYMMDD-XXXXXX
    date_part = datetime.now().strftime('%Y%m%d')
    random_part = ''.join(random.choices('0123456789', k=6))
    
    return f"INV-{date_part}-{random_part}"


def calculate_jalali_date(gregorian_date):
    """Convert Gregorian date to Jalali (Persian) date"""
    try:
        import jdatetime
        return jdatetime.date.fromgregorian(date=gregorian_date)
    except ImportError:
        logger.warning("jdatetime not installed, returning Gregorian date")
        return gregorian_date


def format_persian_number(number):
    """Convert English numbers to Persian numbers"""
    persian_digits = '۰۱۲۳۴۵۶۷۸۹'
    english_digits = '0123456789'
    
    translation_table = str.maketrans(english_digits, persian_digits)
    return str(number).translate(translation_table)


def format_currency(amount, currency='IRR'):
    """Format amount as currency"""
    if currency == 'IRR':
        # Format as Rial with Persian digits
        formatted = f"{amount:,.0f}"
        formatted = format_persian_number(formatted)
        return f"{formatted} ریال"
    elif currency == 'USD':
        return f"${amount:,.2f}"
    else:
        return f"{amount:,.2f} {currency}"
