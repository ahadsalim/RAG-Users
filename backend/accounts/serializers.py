from rest_framework import serializers
from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.password_validation import validate_password
from django.utils.translation import gettext_lazy as _
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from .models import User, Organization, UserSession, OrganizationInvitation
import re

User = get_user_model()


class CustomTokenObtainPairSerializer(serializers.Serializer):
    """Custom JWT token serializer supporting both email and phone_number login"""
    
    email = serializers.EmailField(required=False)
    phone_number = serializers.CharField(required=False)
    password = serializers.CharField(required=True, write_only=True)
    
    def validate(self, attrs):
        # Handle both email and phone_number login
        email = attrs.get('email')
        phone_number = attrs.get('phone_number')
        password = attrs.get('password')
        
        if not email and not phone_number:
            raise serializers.ValidationError(_('Either email or phone_number is required.'))
        
        # Find user by email or phone_number
        user = None
        if email:
            user = User.objects.filter(email=email).first()
        elif phone_number:
            user = User.objects.filter(phone_number=phone_number).first()
        
        # Validate credentials
        if not user or not user.check_password(password):
            raise serializers.ValidationError(_('Invalid credentials.'))
        
        # Check if account is locked
        if user.is_account_locked():
            raise serializers.ValidationError(_('Account is temporarily locked. Please try again later.'))
        
        # Generate JWT tokens
        from rest_framework_simplejwt.tokens import RefreshToken
        refresh = RefreshToken.for_user(user)
        
        # Add custom claims to tokens
        refresh['email'] = user.email
        refresh['username'] = user.username
        refresh['organization_id'] = str(user.organization.id) if user.organization else None
        
        data = {
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        }
        
        # Reset failed login attempts on successful login
        if user.failed_login_attempts > 0:
            user.failed_login_attempts = 0
            user.save(update_fields=['failed_login_attempts'])
        
        # Store user for view access
        self.user = user
        
        # Add user data
        data['user'] = {
            'id': str(user.id),
            'email': user.email,
            'username': user.username,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'phone_number': user.phone_number,
            'is_superuser': user.is_superuser,
            'is_staff': user.is_staff,
            'user_type': user.user_type,
            'company_name': user.company_name,
            'avatar': user.avatar.url if user.avatar else None,
            'organization': {
                'id': str(user.organization.id),
                'name': user.organization.name,
                'role': user.organization_role
            } if user.organization else None,
            'two_factor_enabled': user.two_factor_enabled,
            'language': user.language,
        }
        
        return data


class UserRegistrationSerializer(serializers.ModelSerializer):
    """User registration serializer"""
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    password_confirm = serializers.CharField(write_only=True, required=True)
    
    class Meta:
        model = User
        fields = [
            'email', 'username', 'password', 'password_confirm',
            'first_name', 'last_name', 'phone_number', 'user_type',
            'company_name', 'language', 'timezone', 'currency'
        ]
        extra_kwargs = {
            'email': {'required': False},
            'username': {'required': False},
            'phone_number': {'required': False},
        }
    
    def validate_email(self, value):
        if value and User.objects.filter(email=value).exists():
            raise serializers.ValidationError(_('کاربری با این ایمیل قبلاً ثبت‌نام کرده است.'))
        return value.lower() if value else None
    
    def validate_phone_number(self, value):
        if value and User.objects.filter(phone_number=value).exists():
            raise serializers.ValidationError(_('کاربری با این شماره تلفن قبلاً ثبت‌نام کرده است.'))
        
        # Validate phone format based on user type (will be checked in validate method)
        return value
    
    def validate_username(self, value):
        if value and User.objects.filter(username=value).exists():
            raise serializers.ValidationError(_('A user with this username already exists.'))
        if value and not re.match(r'^[\w.@+-]+$', value):
            raise serializers.ValidationError(_('Username can only contain letters, numbers, and @/./+/-/_ characters.'))
        return value
    
    def validate(self, attrs):
        # Check password match
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError({'password': _('رمز عبور و تکرار آن یکسان نیستند.')})
        
        user_type = attrs.get('user_type', 'individual')
        phone_number = attrs.get('phone_number', '')
        
        # For legal users (business), email is required
        if user_type == 'legal' or user_type == 'business':
            if not attrs.get('email'):
                raise serializers.ValidationError({'email': _('ایمیل برای حساب‌های حقوقی الزامی است.')})
            
            # For legal users, email IS the username (not a separate username)
            # Set username to None to avoid conflicts
            attrs['username'] = None
            
            # For legal users, phone is required (can be mobile or landline)
            if not phone_number:
                raise serializers.ValidationError({'phone_number': _('شماره تلفن الزامی است.')})
            
            # Validate phone format for legal users (mobile or landline)
            # Mobile: 09123456789 (11 digits starting with 09)
            # Landline: 02112345678 (11 digits starting with 0 + area code)
            if not re.match(r'^0\d{10}$', phone_number):
                raise serializers.ValidationError({
                    'phone_number': _('لطفا یک شماره تلفن معتبر وارد کنید (موبایل: 09123456789 یا ثابت: 02112345678)')
                })
        else:
            # For real users (individual), mobile phone is required
            if not phone_number:
                raise serializers.ValidationError({'phone_number': _('شماره موبایل برای حساب‌های حقیقی الزامی است.')})
            
            # Validate mobile format for individual users (must be mobile)
            if not re.match(r'^09\d{9}$', phone_number):
                raise serializers.ValidationError({
                    'phone_number': _('لطفا یک شماره موبایل معتبر ایرانی وارد کنید (مثال: 09123456789)')
                })
            
            # For individual users, username can be None (phone is the identifier)
            attrs['username'] = None
        
        return attrs
    
    def create(self, validated_data):
        validated_data.pop('password_confirm')
        user = User.objects.create_user(**validated_data)
        return user


class UserProfileSerializer(serializers.ModelSerializer):
    """User profile serializer"""
    organization = serializers.SerializerMethodField()
    sessions_count = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = [
            'id', 'email', 'username', 'first_name', 'last_name',
            'phone_number', 'phone_verified', 'email_verified',
            'avatar', 'bio', 'user_type', 'national_id', 'national_id_verified',
            'company_name', 'economic_code', 'organization', 'organization_role',
            'language', 'timezone', 'currency', 'chat_context',
            'two_factor_enabled', 'max_concurrent_sessions',
            'email_notifications', 'sms_notifications', 'push_notifications',
            'is_superuser', 'is_staff',
            'created_at', 'updated_at', 'last_seen', 'sessions_count'
        ]
        read_only_fields = [
            'id', 'email_verified', 'phone_verified', 'national_id_verified',
            'two_factor_enabled', 'is_superuser', 'is_staff',
            'created_at', 'updated_at', 'last_seen'
        ]
    
    def get_organization(self, obj):
        if obj.organization:
            return {
                'id': str(obj.organization.id),
                'name': obj.organization.name,
                'slug': obj.organization.slug,
                'logo': obj.organization.logo.url if obj.organization.logo else None,
            }
        return None
    
    def get_sessions_count(self, obj):
        return obj.sessions.filter(is_active=True).count()


class PasswordChangeSerializer(serializers.Serializer):
    """Password change serializer"""
    old_password = serializers.CharField(required=True, write_only=True)
    new_password = serializers.CharField(required=True, write_only=True, validators=[validate_password])
    new_password_confirm = serializers.CharField(required=True, write_only=True)
    
    def validate_old_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError(_('Old password is incorrect.'))
        return value
    
    def validate(self, attrs):
        if attrs['new_password'] != attrs['new_password_confirm']:
            raise serializers.ValidationError({'new_password': _('New passwords do not match.')})
        return attrs
    
    def save(self):
        user = self.context['request'].user
        user.set_password(self.validated_data['new_password'])
        user.save()
        return user


class PasswordResetRequestSerializer(serializers.Serializer):
    """Password reset request serializer"""
    email = serializers.EmailField(required=True)
    
    def validate_email(self, value):
        if not User.objects.filter(email=value).exists():
            # Don't reveal if email exists or not for security
            pass
        return value.lower()
    
    def save(self):
        from .utils import send_password_reset_email
        import secrets
        from django.core.cache import cache
        import logging
        
        logger = logging.getLogger(__name__)
        email = self.validated_data['email']
        try:
            user = User.objects.get(email=email)
            
            # Generate reset token
            reset_token = secrets.token_urlsafe(32)
            
            # Store token in cache (valid for 1 hour)
            cache_key = f"password_reset_{user.id}"
            cache.set(cache_key, reset_token, 3600)
            
            # Verify token was stored
            stored_token = cache.get(cache_key)
            logger.info(f"Password reset token generated for {user.email}")
            logger.info(f"Cache key: {cache_key}")
            logger.info(f"Token stored: {stored_token == reset_token}")
            logger.info(f"Token value: {reset_token}")
            
            # Send email
            send_password_reset_email(user, reset_token)
        except User.DoesNotExist:
            # Don't reveal if email exists or not
            logger.warning(f"Password reset requested for non-existent email: {email}")
            pass


class PasswordResetConfirmSerializer(serializers.Serializer):
    """Password reset confirmation serializer"""
    token = serializers.CharField(required=True)
    user_id = serializers.UUIDField(required=True)
    new_password = serializers.CharField(required=True, write_only=True, validators=[validate_password])
    new_password_confirm = serializers.CharField(required=True, write_only=True)
    
    def validate(self, attrs):
        import logging
        logger = logging.getLogger(__name__)
        
        if attrs['new_password'] != attrs['new_password_confirm']:
            raise serializers.ValidationError({'new_password': _('Passwords do not match.')})
        
        # Validate token
        from django.core.cache import cache
        user_id = attrs['user_id']
        token = attrs['token']
        
        cache_key = f"password_reset_{user_id}"
        cached_token = cache.get(cache_key)
        
        logger.info(f"Validating reset token for user: {user_id}")
        logger.info(f"Received token: {token}")
        logger.info(f"Cached token: {cached_token}")
        logger.info(f"Tokens match: {cached_token == token}")
        
        if not cached_token or cached_token != token:
            logger.error(f"Token validation failed! Cached: {cached_token}, Received: {token}")
            raise serializers.ValidationError({'token': _('Invalid or expired reset token.')})
        
        return attrs
    
    def save(self):
        from django.core.cache import cache
        import logging
        
        logger = logging.getLogger(__name__)
        user_id = self.validated_data['user_id']
        new_password = self.validated_data['new_password']
        
        try:
            user = User.objects.get(id=user_id)
            logger.info(f"Resetting password for user: {user.email}")
            
            # Reset password
            user.set_password(new_password)
            
            # Unlock account and reset failed login attempts
            user.locked_until = None
            user.failed_login_attempts = 0
            
            user.save(update_fields=['password', 'locked_until', 'failed_login_attempts'])
            
            logger.info(f"Password successfully reset for user: {user.email}")
            logger.info(f"Account unlocked and failed login attempts reset")
            
            # Delete used token
            cache_key = f"password_reset_{user_id}"
            cache.delete(cache_key)
            logger.info(f"Reset token deleted for user: {user.email}")
            
        except User.DoesNotExist:
            logger.error(f"User not found with ID: {user_id}")
            raise serializers.ValidationError({'user_id': _('User not found.')})


class TwoFactorSetupSerializer(serializers.Serializer):
    """Two-factor authentication setup serializer"""
    password = serializers.CharField(required=True, write_only=True)
    
    def validate_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError(_('Password is incorrect.'))
        return value


class TwoFactorVerifySerializer(serializers.Serializer):
    """Two-factor authentication verification serializer"""
    token = serializers.CharField(required=True, max_length=6, min_length=6)
    
    def validate_token(self, value):
        if not value.isdigit():
            raise serializers.ValidationError(_('Token must contain only digits.'))
        return value


class OrganizationSerializer(serializers.ModelSerializer):
    """Organization serializer"""
    members_count = serializers.SerializerMethodField()
    owner = serializers.SerializerMethodField()
    
    class Meta:
        model = Organization
        fields = [
            'id', 'name', 'slug', 'logo', 'company_name', 'economic_code',
            'national_id', 'registration_number', 'address', 'postal_code',
            'phone', 'allowed_email_domains', 'max_members', 'members_count',
            'owner', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'slug', 'created_at', 'updated_at']
    
    def get_members_count(self, obj):
        return obj.members.count()
    
    def get_owner(self, obj):
        owner = obj.members.filter(organization_role='owner').first()
        if owner:
            return {
                'id': str(owner.id),
                'email': owner.email,
                'name': f"{owner.first_name} {owner.last_name}".strip() or owner.username
            }
        return None


class OrganizationInvitationSerializer(serializers.ModelSerializer):
    """Organization invitation serializer"""
    organization_name = serializers.CharField(source='organization.name', read_only=True)
    invited_by_name = serializers.SerializerMethodField()
    
    class Meta:
        model = OrganizationInvitation
        fields = [
            'id', 'organization', 'organization_name', 'email', 'role',
            'invited_by', 'invited_by_name', 'created_at', 'expires_at'
        ]
        read_only_fields = ['id', 'token', 'created_at', 'expires_at']
    
    def get_invited_by_name(self, obj):
        if obj.invited_by:
            return f"{obj.invited_by.first_name} {obj.invited_by.last_name}".strip() or obj.invited_by.username
        return None


class UserSessionSerializer(serializers.ModelSerializer):
    """User session serializer"""
    is_current = serializers.SerializerMethodField()
    
    class Meta:
        model = UserSession
        fields = [
            'id', 'device_type', 'device_name', 'browser', 'os',
            'ip_address', 'location', 'created_at', 'last_activity',
            'is_active', 'is_current'
        ]
        read_only_fields = ['id', 'created_at', 'last_activity']
    
    def get_is_current(self, obj):
        request = self.context.get('request')
        if request and hasattr(request, 'session'):
            return obj.session_key == request.session.session_key
        return False


class PhoneVerificationSerializer(serializers.Serializer):
    """Phone number verification serializer"""
    phone_number = serializers.CharField(required=True)
    
    def validate_phone_number(self, value):
        # Iranian phone number validation
        import re
        pattern = r'^(\+98|0)?9\d{9}$'
        if not re.match(pattern, value):
            raise serializers.ValidationError(_('Enter a valid Iranian phone number.'))
        
        # Normalize phone number
        if value.startswith('+98'):
            value = value[3:]
        elif value.startswith('0'):
            value = value[1:]
        
        return f"+98{value}"


class OTPVerificationSerializer(serializers.Serializer):
    """OTP verification serializer"""
    phone_number = serializers.CharField(required=True)
    otp_code = serializers.CharField(required=True, max_length=6, min_length=6)
    
    def validate_otp_code(self, value):
        if not value.isdigit():
            raise serializers.ValidationError(_('OTP code must contain only digits.'))
        return value
