"""
URL Configuration برای ماژول accounts
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView

from .views import (
    CustomTokenObtainPairView,
    TwoFactorVerifyView,
    UserRegistrationView,
    UserProfileView,
    PasswordChangeView,
    PasswordResetRequestView,
    PasswordResetConfirmView,
    TwoFactorSetupView,
    TwoFactorEnableView,
    TwoFactorDisableView,
    UserSessionViewSet,
    PhoneVerificationView,
    OTPVerificationView,
    EmailVerificationView,
    LogoutView
)
from .otp_views import SendOTPView, VerifyOTPView
from .settings_views import user_settings

router = DefaultRouter()
router.register(r'sessions', UserSessionViewSet, basename='session')

app_name = 'accounts'

urlpatterns = [
    # Authentication
    path('register/', UserRegistrationView.as_view(), name='register'),
    path('login/', CustomTokenObtainPairView.as_view(), name='login'),
    path('login/2fa/', TwoFactorVerifyView.as_view(), name='2fa-verify'),
    path('logout/', LogoutView.as_view(), name='logout'),
    
    # OTP Login (for real users)
    path('send-otp/', SendOTPView.as_view(), name='send-otp'),
    path('verify-otp/', VerifyOTPView.as_view(), name='verify-otp'),
    
    # Email Verification
    path('verify-email/', EmailVerificationView.as_view(), name='verify-email'),
    
    # Profile
    path('profile/', UserProfileView.as_view(), name='profile'),
    path('password/change/', PasswordChangeView.as_view(), name='password-change'),
    path('forgot-password/', PasswordResetRequestView.as_view(), name='password-reset-request'),
    path('reset-password/', PasswordResetConfirmView.as_view(), name='password-reset-confirm'),
    
    # Settings
    path('settings/', user_settings, name='settings'),
    
    # 2FA
    path('2fa/setup/', TwoFactorSetupView.as_view(), name='2fa-setup'),
    path('2fa/enable/', TwoFactorEnableView.as_view(), name='2fa-enable'),
    path('2fa/disable/', TwoFactorDisableView.as_view(), name='2fa-disable'),
    
    # Phone Verification
    path('phone/verify/', PhoneVerificationView.as_view(), name='phone-verify'),
    path('phone/otp/', OTPVerificationView.as_view(), name='otp-verify'),
    
    # Sessions Management
    path('', include(router.urls)),
]
