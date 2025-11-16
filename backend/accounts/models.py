from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.core.validators import RegexValidator
import uuid
import pyotp
import qrcode
from io import BytesIO
import base64

# Validators
phone_validator = RegexValidator(
    regex=r'^(\+98|0)?9\d{9}$',
    message=_('Enter a valid Iranian phone number.')
)

national_id_validator = RegexValidator(
    regex=r'^\d{10}$',
    message=_('Enter a valid 10-digit national ID.')
)

economic_code_validator = RegexValidator(
    regex=r'^\d{14}$',
    message=_('Enter a valid 14-digit economic code.')
)


class CustomUserManager(BaseUserManager):
    """Custom user manager to handle phone or email authentication"""
    
    def create_user(self, email=None, phone_number=None, password=None, **extra_fields):
        """Create and save a regular user"""
        if not email and not phone_number:
            raise ValueError('Either email or phone_number must be provided')
        
        if email:
            email = self.normalize_email(email)
        
        # Generate a unique username if not provided
        if not extra_fields.get('username'):
            extra_fields['username'] = None
            
        user = self.model(email=email, phone_number=phone_number, **extra_fields)
        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()
        user.save(using=self._db)
        return user
    
    def create_superuser(self, email, password=None, **extra_fields):
        """Create and save a superuser"""
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        
        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')
        
        return self.create_user(email=email, password=password, **extra_fields)


class Organization(models.Model):
    """Organization model for team management"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255, verbose_name=_('Organization Name'))
    slug = models.SlugField(max_length=255, unique=True)
    logo = models.ImageField(upload_to='organizations/logos/', blank=True, null=True)
    
    # Legal Information
    company_name = models.CharField(max_length=255, blank=True, verbose_name=_('Company Legal Name'))
    economic_code = models.CharField(
        max_length=14, 
        blank=True, 
        validators=[economic_code_validator],
        verbose_name=_('Economic Code')
    )
    national_id = models.CharField(
        max_length=11, 
        blank=True,
        verbose_name=_('Company National ID')
    )
    registration_number = models.CharField(max_length=50, blank=True)
    
    # Contact Information
    address = models.TextField(blank=True)
    postal_code = models.CharField(max_length=10, blank=True)
    phone = models.CharField(max_length=15, blank=True, validators=[phone_validator])
    
    # Settings
    allowed_email_domains = models.TextField(
        blank=True,
        help_text=_('Comma-separated list of allowed email domains for auto-join')
    )
    max_members = models.IntegerField(default=10)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('Organization')
        verbose_name_plural = _('Organizations')
        ordering = ['-created_at']
    
    def __str__(self):
        return self.name


class User(AbstractUser):
    """Custom User model with extended fields"""
    
    USER_TYPE_CHOICES = [
        ('individual', _('Individual')),
        ('business', _('Business')),
    ]
    
    LANGUAGE_CHOICES = [
        ('fa', _('Persian')),
        ('en', _('English')),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Override username to allow null/blank since we use email as USERNAME_FIELD
    username = models.CharField(max_length=150, blank=True, null=True, unique=True)
    
    # Override email to allow null/blank for phone-only users
    email = models.EmailField(unique=True, blank=True, null=True, verbose_name=_('Email Address'))
    phone_number = models.CharField(
        max_length=15, 
        unique=True,
        validators=[phone_validator],
        verbose_name=_('Phone Number')
    )
    phone_verified = models.BooleanField(default=False)
    email_verified = models.BooleanField(default=False)
    
    # Profile Information
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    bio = models.TextField(blank=True, max_length=500)
    user_type = models.CharField(max_length=20, choices=USER_TYPE_CHOICES, default='individual')
    
    # Legal/Business Information
    national_id = models.CharField(
        max_length=10, 
        blank=True, 
        validators=[national_id_validator],
        verbose_name=_('National ID')
    )
    national_id_verified = models.BooleanField(default=False)
    company_name = models.CharField(max_length=255, blank=True)
    economic_code = models.CharField(
        max_length=14, 
        blank=True, 
        validators=[economic_code_validator]
    )
    
    # Organization
    organization = models.ForeignKey(
        Organization, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='members'
    )
    organization_role = models.CharField(
        max_length=20,
        choices=[
            ('owner', _('Owner')),
            ('admin', _('Admin')),
            ('member', _('Member')),
        ],
        blank=True
    )
    
    # Settings & Preferences
    language = models.CharField(max_length=5, choices=LANGUAGE_CHOICES, default='fa')
    timezone = models.CharField(max_length=50, default='Asia/Tehran')
    currency = models.CharField(max_length=3, default='IRR')
    
    # Chat Context/Memory
    chat_context = models.JSONField(
        default=dict,
        blank=True,
        help_text=_('User preferences and context for chat interactions')
    )
    
    # 2FA
    two_factor_enabled = models.BooleanField(default=False)
    totp_secret = models.CharField(max_length=32, blank=True)
    backup_codes = models.JSONField(default=list, blank=True)
    
    # Session Management
    max_concurrent_sessions = models.IntegerField(default=3)
    
    # Security
    last_password_change = models.DateTimeField(null=True, blank=True)
    failed_login_attempts = models.IntegerField(default=0)
    locked_until = models.DateTimeField(null=True, blank=True)
    
    # API Access
    api_key = models.CharField(max_length=64, blank=True, null=True, unique=True)
    api_key_created_at = models.DateTimeField(null=True, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_seen = models.DateTimeField(null=True, blank=True)
    
    # Notifications
    email_notifications = models.BooleanField(default=True)
    sms_notifications = models.BooleanField(default=True)
    push_notifications = models.BooleanField(default=True)
    
    # Use custom manager
    objects = CustomUserManager()
    
    USERNAME_FIELD = 'phone_number'
    REQUIRED_FIELDS = []
    
    class Meta:
        verbose_name = _('User')
        verbose_name_plural = _('Users')
        ordering = ['-created_at']
    
    def __str__(self):
        return self.phone_number or self.email or str(self.id)
    
    def generate_totp_secret(self):
        """Generate a new TOTP secret for 2FA"""
        self.totp_secret = pyotp.random_base32()
        self.save(update_fields=['totp_secret'])
        return self.totp_secret
    
    def get_totp_uri(self):
        """Get TOTP URI for QR code generation"""
        if not self.totp_secret:
            self.generate_totp_secret()
        return pyotp.totp.TOTP(self.totp_secret).provisioning_uri(
            name=self.email,
            issuer_name='app Platform'
        )
    
    def generate_qr_code(self):
        """Generate QR code for TOTP setup"""
        uri = self.get_totp_uri()
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(uri)
        qr.make(fit=True)
        img = qr.make_image(fill_color='black', back_color='white')
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        img_str = base64.b64encode(buffer.getvalue()).decode()
        return f"data:image/png;base64,{img_str}"
    
    def verify_totp(self, token):
        """Verify TOTP token"""
        if not self.totp_secret:
            return False
        totp = pyotp.TOTP(self.totp_secret)
        return totp.verify(token, valid_window=1)
    
    def generate_api_key(self):
        """Generate a new API key for the user"""
        import secrets
        self.api_key = secrets.token_urlsafe(48)
        self.api_key_created_at = timezone.now()
        self.save(update_fields=['api_key', 'api_key_created_at'])
        return self.api_key
    
    def is_account_locked(self):
        """Check if account is temporarily locked"""
        if self.locked_until and self.locked_until > timezone.now():
            return True
        return False
    
    def lock_account(self, duration_minutes=30):
        """Lock account for specified duration"""
        from datetime import timedelta
        self.locked_until = timezone.now() + timedelta(minutes=duration_minutes)
        self.save(update_fields=['locked_until'])
    
    def unlock_account(self):
        """Unlock account"""
        self.failed_login_attempts = 0
        self.locked_until = None
        self.save(update_fields=['failed_login_attempts', 'locked_until'])


class UserSession(models.Model):
    """Track user sessions for security"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sessions')
    session_key = models.CharField(max_length=255, unique=True, blank=False, null=False)
    
    # Device Information
    device_type = models.CharField(max_length=50, blank=True)
    device_name = models.CharField(max_length=255, blank=True)
    browser = models.CharField(max_length=50, blank=True)
    os = models.CharField(max_length=50, blank=True)
    
    # Network Information
    ip_address = models.GenericIPAddressField()
    location = models.CharField(max_length=255, blank=True)
    
    # Token Information
    refresh_token = models.TextField(blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    last_activity = models.DateTimeField(auto_now=True)
    expires_at = models.DateTimeField()
    
    # Status
    is_active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['-last_activity']
        verbose_name = _('User Session')
        verbose_name_plural = _('User Sessions')
    
    def __str__(self):
        return f"{self.user.email} - {self.device_name or 'Unknown Device'}"


class OrganizationInvitation(models.Model):
    """Invitations for joining organizations"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='invitations')
    email = models.EmailField()
    invited_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='sent_invitations')
    role = models.CharField(
        max_length=20,
        choices=[
            ('admin', _('Admin')),
            ('member', _('Member')),
        ],
        default='member'
    )
    token = models.CharField(max_length=64, unique=True)
    
    # Status
    accepted = models.BooleanField(default=False)
    accepted_at = models.DateTimeField(null=True, blank=True)
    accepted_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='accepted_invitations')
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    
    class Meta:
        unique_together = ['organization', 'email']
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Invitation for {self.email} to {self.organization.name}"
    
    def is_expired(self):
        return timezone.now() > self.expires_at


class AuditLog(models.Model):
    """Audit log for sensitive operations"""
    ACTION_CHOICES = [
        ('login', _('Login')),
        ('logout', _('Logout')),
        ('password_change', _('Password Change')),
        ('password_reset', _('Password Reset')),
        ('2fa_enabled', _('2FA Enabled')),
        ('2fa_disabled', _('2FA Disabled')),
        ('api_key_generated', _('API Key Generated')),
        ('profile_updated', _('Profile Updated')),
        ('organization_created', _('Organization Created')),
        ('organization_joined', _('Organization Joined')),
        ('organization_left', _('Organization Left')),
        ('payment_made', _('Payment Made')),
        ('subscription_changed', _('Subscription Changed')),
        ('admin_action', _('Admin Action')),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='audit_logs')
    action = models.CharField(max_length=50, choices=ACTION_CHOICES)
    details = models.JSONField(default=dict)
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField(blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['user', '-timestamp']),
            models.Index(fields=['action', '-timestamp']),
        ]
    
    def __str__(self):
        return f"{self.user.email if self.user else 'Unknown'} - {self.action} - {self.timestamp}"
