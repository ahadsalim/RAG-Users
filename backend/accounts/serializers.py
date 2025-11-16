from rest_framework import serializers
from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.password_validation import validate_password
from django.utils.translation import gettext_lazy as _
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from .models import User, Organization, UserSession, OrganizationInvitation
import re

User = get_user_model()


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """Custom JWT token serializer with additional claims"""
    
    def validate(self, attrs):
        data = super().validate(attrs)
        
        # Check if account is locked
        if self.user.is_account_locked():
            raise serializers.ValidationError(_('Account is temporarily locked. Please try again later.'))
        
        # Reset failed login attempts on successful login
        if self.user.failed_login_attempts > 0:
            self.user.failed_login_attempts = 0
            self.user.save(update_fields=['failed_login_attempts'])
        
        # Add custom claims
        data['user'] = {
            'id': str(self.user.id),
            'email': self.user.email,
            'username': self.user.username,
            'first_name': self.user.first_name,
            'last_name': self.user.last_name,
            'avatar': self.user.avatar.url if self.user.avatar else None,
            'organization': {
                'id': str(self.user.organization.id),
                'name': self.user.organization.name,
                'role': self.user.organization_role
            } if self.user.organization else None,
            'two_factor_enabled': self.user.two_factor_enabled,
            'language': self.user.language,
        }
        
        return data
    
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        
        # Add custom claims to token
        token['email'] = user.email
        token['username'] = user.username
        token['organization_id'] = str(user.organization.id) if user.organization else None
        
        return token


class UserRegistrationSerializer(serializers.ModelSerializer):
    """User registration serializer"""
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    password_confirm = serializers.CharField(write_only=True, required=True)
    
    class Meta:
        model = User
        fields = [
            'email', 'username', 'password', 'password_confirm',
            'first_name', 'last_name', 'phone_number', 'user_type',
            'language', 'timezone', 'currency'
        ]
        extra_kwargs = {
            'email': {'required': True},
            'username': {'required': True},
        }
    
    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError(_('A user with this email already exists.'))
        return value.lower()
    
    def validate_username(self, value):
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError(_('A user with this username already exists.'))
        if not re.match(r'^[\w.@+-]+$', value):
            raise serializers.ValidationError(_('Username can only contain letters, numbers, and @/./+/-/_ characters.'))
        return value
    
    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError({'password': _('Passwords do not match.')})
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
            'created_at', 'updated_at', 'last_seen', 'sessions_count'
        ]
        read_only_fields = [
            'id', 'email_verified', 'phone_verified', 'national_id_verified',
            'two_factor_enabled', 'created_at', 'updated_at', 'last_seen'
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


class PasswordResetConfirmSerializer(serializers.Serializer):
    """Password reset confirmation serializer"""
    token = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True, write_only=True, validators=[validate_password])
    new_password_confirm = serializers.CharField(required=True, write_only=True)
    
    def validate(self, attrs):
        if attrs['new_password'] != attrs['new_password_confirm']:
            raise serializers.ValidationError({'new_password': _('Passwords do not match.')})
        return attrs


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
