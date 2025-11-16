from rest_framework import status, generics, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.core.cache import cache
from datetime import timedelta
import random
import string
import logging

from .models import User, Organization, UserSession, OrganizationInvitation, AuditLog
from .serializers import (
    CustomTokenObtainPairSerializer,
    UserRegistrationSerializer,
    UserProfileSerializer,
    PasswordChangeSerializer,
    PasswordResetRequestSerializer,
    PasswordResetConfirmSerializer,
    TwoFactorSetupSerializer,
    TwoFactorVerifySerializer,
    OrganizationSerializer,
    OrganizationInvitationSerializer,
    UserSessionSerializer,
    PhoneVerificationSerializer,
    OTPVerificationSerializer
)
from .utils import send_otp_sms, send_email_verification, get_client_ip, get_user_agent_info

logger = logging.getLogger('app')
User = get_user_model()


class CustomTokenObtainPairView(TokenObtainPairView):
    """Custom JWT token obtain view with 2FA support"""
    serializer_class = CustomTokenObtainPairSerializer
    
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        
        try:
            serializer.is_valid(raise_exception=True)
        except Exception as e:
            # Log failed login attempt
            email = request.data.get('email', '')
            if email:
                try:
                    user = User.objects.get(email=email)
                    user.failed_login_attempts += 1
                    if user.failed_login_attempts >= 5:
                        user.lock_account(30)  # Lock for 30 minutes
                    user.save(update_fields=['failed_login_attempts', 'locked_until'])
                except User.DoesNotExist:
                    pass
            
            # Log to audit
            AuditLog.objects.create(
                user=None,
                action='login',
                details={'email': email, 'success': False, 'error': str(e)},
                ip_address=get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', '')
            )
            
            return Response(
                {'error': str(e)},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        # Check if 2FA is enabled
        user = serializer.user
        if user.two_factor_enabled:
            # Store tokens temporarily and require 2FA verification
            cache_key = f"2fa_pending_{user.id}"
            cache.set(cache_key, serializer.validated_data, 300)  # 5 minutes
            
            return Response({
                'requires_2fa': True,
                'user_id': str(user.id),
                'message': _('Please enter your 2FA code.')
            }, status=status.HTTP_200_OK)
        
        # Create session record
        session = UserSession.objects.create(
            user=user,
            session_key=request.session.session_key or '',
            ip_address=get_client_ip(request),
            **get_user_agent_info(request),
            expires_at=timezone.now() + timedelta(days=7),
            refresh_token=serializer.validated_data.get('refresh', '')
        )
        
        # Log successful login
        AuditLog.objects.create(
            user=user,
            action='login',
            details={'success': True, 'session_id': str(session.id)},
            ip_address=get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )
        
        # Update last login
        user.last_login = timezone.now()
        user.save(update_fields=['last_login'])
        
        return Response(serializer.validated_data, status=status.HTTP_200_OK)


class TwoFactorVerifyView(APIView):
    """Verify 2FA code and complete login"""
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        user_id = request.data.get('user_id')
        token = request.data.get('token')
        
        if not user_id or not token:
            return Response(
                {'error': _('User ID and token are required.')},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response(
                {'error': _('Invalid user ID.')},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Verify TOTP token
        if not user.verify_totp(token):
            return Response(
                {'error': _('Invalid or expired 2FA code.')},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Retrieve cached tokens
        cache_key = f"2fa_pending_{user_id}"
        token_data = cache.get(cache_key)
        
        if not token_data:
            return Response(
                {'error': _('2FA session expired. Please login again.')},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Clear cache
        cache.delete(cache_key)
        
        # Create session record
        session = UserSession.objects.create(
            user=user,
            session_key=request.session.session_key or '',
            ip_address=get_client_ip(request),
            **get_user_agent_info(request),
            expires_at=timezone.now() + timedelta(days=7),
            refresh_token=token_data.get('refresh', '')
        )
        
        # Log successful 2FA verification
        AuditLog.objects.create(
            user=user,
            action='login',
            details={'success': True, '2fa_verified': True, 'session_id': str(session.id)},
            ip_address=get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )
        
        return Response(token_data, status=status.HTTP_200_OK)


class UserRegistrationView(generics.CreateAPIView):
    """User registration endpoint"""
    serializer_class = UserRegistrationSerializer
    permission_classes = [permissions.AllowAny]
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        
        # Send verification email
        send_email_verification(user)
        
        # Generate tokens
        refresh = RefreshToken.for_user(user)
        
        # Create session
        session = UserSession.objects.create(
            user=user,
            session_key=request.session.session_key or '',
            ip_address=get_client_ip(request),
            **get_user_agent_info(request),
            expires_at=timezone.now() + timedelta(days=7),
            refresh_token=str(refresh)
        )
        
        # Log registration
        AuditLog.objects.create(
            user=user,
            action='registration',
            details={'email': user.email},
            ip_address=get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )
        
        return Response({
            'user': UserProfileSerializer(user).data,
            'tokens': {
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            },
            'message': _('Registration successful. Please check your email to verify your account.')
        }, status=status.HTTP_201_CREATED)


class UserProfileView(generics.RetrieveUpdateAPIView):
    """Get and update user profile"""
    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_object(self):
        return self.request.user
    
    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        
        # Log profile update
        AuditLog.objects.create(
            user=request.user,
            action='profile_updated',
            details={'fields': list(request.data.keys())},
            ip_address=get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )
        
        return Response(serializer.data)


class PasswordChangeView(APIView):
    """Change user password"""
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        serializer = PasswordChangeSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        
        # Update last password change
        user.last_password_change = timezone.now()
        user.save(update_fields=['last_password_change'])
        
        # Invalidate all sessions except current
        UserSession.objects.filter(user=user).exclude(
            session_key=request.session.session_key
        ).update(is_active=False)
        
        # Log password change
        AuditLog.objects.create(
            user=user,
            action='password_change',
            details={'success': True},
            ip_address=get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )
        
        return Response({
            'message': _('Password changed successfully.')
        }, status=status.HTTP_200_OK)


class TwoFactorSetupView(APIView):
    """Setup 2FA for user"""
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        serializer = TwoFactorSetupSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        
        user = request.user
        
        # Generate TOTP secret
        secret = user.generate_totp_secret()
        qr_code = user.generate_qr_code()
        
        # Generate backup codes
        backup_codes = [''.join(random.choices(string.digits, k=8)) for _ in range(10)]
        user.backup_codes = backup_codes
        user.save(update_fields=['backup_codes'])
        
        return Response({
            'secret': secret,
            'qr_code': qr_code,
            'backup_codes': backup_codes,
            'message': _('Scan the QR code with your authenticator app and verify with a code.')
        }, status=status.HTTP_200_OK)


class TwoFactorEnableView(APIView):
    """Enable 2FA after verification"""
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        serializer = TwoFactorVerifySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        user = request.user
        token = serializer.validated_data['token']
        
        # Verify token
        if not user.verify_totp(token):
            return Response(
                {'error': _('Invalid verification code.')},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Enable 2FA
        user.two_factor_enabled = True
        user.save(update_fields=['two_factor_enabled'])
        
        # Log 2FA enablement
        AuditLog.objects.create(
            user=user,
            action='2fa_enabled',
            details={'success': True},
            ip_address=get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )
        
        return Response({
            'message': _('Two-factor authentication enabled successfully.')
        }, status=status.HTTP_200_OK)


class TwoFactorDisableView(APIView):
    """Disable 2FA"""
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        password = request.data.get('password')
        
        if not password:
            return Response(
                {'error': _('Password is required.')},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        user = request.user
        
        if not user.check_password(password):
            return Response(
                {'error': _('Password is incorrect.')},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Disable 2FA
        user.two_factor_enabled = False
        user.totp_secret = ''
        user.backup_codes = []
        user.save(update_fields=['two_factor_enabled', 'totp_secret', 'backup_codes'])
        
        # Log 2FA disablement
        AuditLog.objects.create(
            user=user,
            action='2fa_disabled',
            details={'success': True},
            ip_address=get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )
        
        return Response({
            'message': _('Two-factor authentication disabled successfully.')
        }, status=status.HTTP_200_OK)


class UserSessionViewSet(ModelViewSet):
    """Manage user sessions"""
    serializer_class = UserSessionSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return UserSession.objects.filter(
            user=self.request.user,
            is_active=True
        ).order_by('-last_activity')
    
    @action(detail=True, methods=['post'])
    def revoke(self, request, pk=None):
        """Revoke a specific session"""
        session = self.get_object()
        
        # Don't allow revoking current session
        if session.session_key == request.session.session_key:
            return Response(
                {'error': _('Cannot revoke current session.')},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        session.is_active = False
        session.save(update_fields=['is_active'])
        
        # Blacklist the refresh token
        if session.refresh_token:
            try:
                token = RefreshToken(session.refresh_token)
                token.blacklist()
            except Exception:
                pass
        
        return Response({
            'message': _('Session revoked successfully.')
        }, status=status.HTTP_200_OK)
    
    @action(detail=False, methods=['post'])
    def revoke_all(self, request):
        """Revoke all sessions except current"""
        sessions = UserSession.objects.filter(
            user=request.user,
            is_active=True
        ).exclude(session_key=request.session.session_key)
        
        # Blacklist all refresh tokens
        for session in sessions:
            if session.refresh_token:
                try:
                    token = RefreshToken(session.refresh_token)
                    token.blacklist()
                except Exception:
                    pass
        
        sessions.update(is_active=False)
        
        return Response({
            'message': _('All other sessions revoked successfully.')
        }, status=status.HTTP_200_OK)


class PhoneVerificationView(APIView):
    """Send OTP for phone verification"""
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        serializer = PhoneVerificationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        phone_number = serializer.validated_data['phone_number']
        
        # Generate OTP
        otp = ''.join(random.choices(string.digits, k=6))
        
        # Store OTP in cache (5 minutes expiry)
        cache_key = f"otp_{request.user.id}_{phone_number}"
        cache.set(cache_key, otp, 300)
        
        # Send OTP via SMS
        send_otp_sms(phone_number, otp)
        
        return Response({
            'message': _('OTP sent successfully.'),
            'phone_number': phone_number
        }, status=status.HTTP_200_OK)


class OTPVerificationView(APIView):
    """Verify OTP and update phone number"""
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        serializer = OTPVerificationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        phone_number = serializer.validated_data['phone_number']
        otp_code = serializer.validated_data['otp_code']
        
        # Retrieve OTP from cache
        cache_key = f"otp_{request.user.id}_{phone_number}"
        cached_otp = cache.get(cache_key)
        
        if not cached_otp:
            return Response(
                {'error': _('OTP expired or invalid.')},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if cached_otp != otp_code:
            return Response(
                {'error': _('Invalid OTP code.')},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Update user's phone number
        user = request.user
        user.phone_number = phone_number
        user.phone_verified = True
        user.save(update_fields=['phone_number', 'phone_verified'])
        
        # Clear OTP from cache
        cache.delete(cache_key)
        
        return Response({
            'message': _('Phone number verified successfully.')
        }, status=status.HTTP_200_OK)


class LogoutView(APIView):
    """Logout user and blacklist token"""
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        try:
            # Get refresh token from request
            refresh_token = request.data.get('refresh_token')
            if refresh_token:
                token = RefreshToken(refresh_token)
                token.blacklist()
            
            # Invalidate current session
            session = UserSession.objects.filter(
                user=request.user,
                session_key=request.session.session_key
            ).first()
            if session:
                session.is_active = False
                session.save(update_fields=['is_active'])
            
            # Log logout
            AuditLog.objects.create(
                user=request.user,
                action='logout',
                details={'success': True},
                ip_address=get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', '')
            )
            
            return Response({
                'message': _('Logged out successfully.')
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
