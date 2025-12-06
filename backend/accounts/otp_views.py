"""
OTP-based authentication views for real users
"""
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.utils import timezone
from datetime import timedelta
import random
import logging
import uuid

from .models import UserSession, AuditLog
from .utils import send_otp_sms, send_otp_bale, get_client_ip, get_user_agent_info

logger = logging.getLogger('app')
User = get_user_model()


class SendOTPView(APIView):
    """Send OTP to phone number for authentication"""
    permission_classes = []
    
    def post(self, request):
        phone_number = request.data.get('phone_number', '').strip()
        method = request.data.get('method', 'sms').lower()  # 'sms' or 'bale'
        
        if not phone_number:
            return Response({
                'message': 'شماره موبایل الزامی است'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Validate phone number format
        if not phone_number.startswith('09') or len(phone_number) != 11:
            return Response({
                'message': 'شماره موبایل باید با 09 شروع شده و 11 رقم باشد'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Check rate limiting
        rate_limit_key = f"otp_rate_limit_{phone_number}"
        if cache.get(rate_limit_key):
            return Response({
                'message': 'لطفا 2 دقیقه صبر کنید و مجدد تلاش کنید'
            }, status=status.HTTP_429_TOO_MANY_REQUESTS)
        
        # Generate 6-digit OTP
        otp_code = str(random.randint(100000, 999999))
        
        # Store OTP in cache for 5 minutes
        cache_key = f"otp_{phone_number}"
        cache.set(cache_key, otp_code, 300)  # 5 minutes
        
        # Set rate limit (2 minutes)
        cache.set(rate_limit_key, True, 120)
        
        # Send OTP via selected method
        try:
            if method == 'bale':
                success = send_otp_bale(phone_number, otp_code)
                if not success:
                    # Fallback to SMS if Bale fails
                    logger.warning(f"Bale failed for {phone_number}, falling back to SMS")
                    send_otp_sms(phone_number, otp_code)
                    method_used = 'sms'
                else:
                    method_used = 'bale'
            else:
                send_otp_sms(phone_number, otp_code)
                method_used = 'sms'
            
            logger.info(f"OTP sent to {phone_number} via {method_used}: {otp_code}")  # Remove in production
        except Exception as e:
            logger.error(f"Error sending OTP to {phone_number}: {str(e)}")
            return Response({
                'message': 'خطا در ارسال کد تایید'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        # Log attempt
        AuditLog.objects.create(
            user=None,
            action='otp_sent',
            details={'phone_number': phone_number, 'method': method_used},
            ip_address=get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )
        
        return Response({
            'message': 'کد تایید برای شما ارسال شد',
            'method': method_used,
            'expires_in': 300  # seconds
        }, status=status.HTTP_200_OK)


class VerifyOTPView(APIView):
    """Verify OTP and login/register user"""
    permission_classes = []
    
    def post(self, request):
        phone_number = request.data.get('phone_number', '').strip()
        otp_code = request.data.get('otp_code', '').strip()
        
        if not phone_number or not otp_code:
            return Response({
                'message': 'شماره موبایل و کد تایید الزامی است'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Get OTP from cache
        cache_key = f"otp_{phone_number}"
        stored_otp = cache.get(cache_key)
        
        if not stored_otp:
            return Response({
                'message': 'کد تایید منقضی شده است. لطفا مجدد درخواست کنید'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if stored_otp != otp_code:
            # Log failed attempt
            AuditLog.objects.create(
                user=None,
                action='otp_verify_failed',
                details={'phone_number': phone_number},
                ip_address=get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', '')
            )
            
            return Response({
                'message': 'کد تایید اشتباه است'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # OTP is valid, delete it
        cache.delete(cache_key)
        
        # Get or create user
        user, created = User.objects.get_or_create(
            phone_number=phone_number,
            defaults={
                'user_type': 'individual',  # حقیقی - phone login
                'is_active': True,
                'phone_verified': True,
            }
        )
        
        if not created:
            # Update phone verified status
            user.phone_verified = True
            user.save(update_fields=['phone_verified'])
        
        # Generate JWT tokens
        refresh = RefreshToken.for_user(user)
        
        # Generate a unique session key
        # Always use UUID for API/mobile logins since they don't have browser sessions
        session_key = str(uuid.uuid4())
        
        # Create session record with unique session_key
        session = UserSession.objects.create(
            user=user,
            session_key=session_key,
            ip_address=get_client_ip(request),
            **get_user_agent_info(request),
            expires_at=timezone.now() + timedelta(days=30),  # 30 days for mobile login
            refresh_token=str(refresh)
        )
        
        # Log successful login
        AuditLog.objects.create(
            user=user,
            action='otp_login_success' if not created else 'otp_register_success',
            details={'phone_number': phone_number},
            ip_address=get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )
        
        return Response({
            'access': str(refresh.access_token),
            'refresh': str(refresh),
            'user': {
                'id': str(user.id),
                'email': user.email or '',
                'username': user.username,
                'first_name': user.first_name or '',
                'last_name': user.last_name or '',
                'phone_number': user.phone_number,
                'is_superuser': user.is_superuser,
                'is_staff': user.is_staff,
                'user_type': user.user_type,
                'company_name': user.company_name or '',
                'avatar': user.avatar.url if user.avatar else None,
                'organization': {
                    'id': str(user.organization.id),
                    'name': user.organization.name,
                    'role': user.organization_role
                } if user.organization else None,
                'two_factor_enabled': user.two_factor_enabled,
                'language': user.language,
            },
            'message': 'ورود موفقیت‌آمیز بود' if not created else 'ثبت‌نام و ورود موفقیت‌آمیز بود'
        }, status=status.HTTP_200_OK)
