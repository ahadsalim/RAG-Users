"""
Django settings for app Platform - Intelligent Business Consulting System
"""

from pathlib import Path
from datetime import timedelta
from decouple import config, Csv
import os

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Security
SECRET_KEY = config('SECRET_KEY')
DEBUG = config('DEBUG', default=True, cast=bool)
ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='localhost,127.0.0.1', cast=Csv())

# Application definition
INSTALLED_APPS = [
    # Third-party admin
    'jazzmin',
    
    # Django apps
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    # Third-party apps
    'rest_framework',
    'rest_framework_simplejwt',
    'rest_framework_simplejwt.token_blacklist',
    'corsheaders',
    'channels',
    'drf_spectacular',
    'django_filters',
    
    # Local apps
    'core',
    'accounts',
    'subscriptions',
    'payments',
    'chat',
    'notifications',
    'analytics',
    'finance',
    'support',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'subscriptions.middleware.SubscriptionMiddleware',  # Check subscription limits
    'core.middleware.DynamicAdminTitleMiddleware',  # Dynamic admin title from SiteSettings
]

ROOT_URLCONF = 'core.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'django.template.context_processors.i18n',
            ],
        },
    },
]

WSGI_APPLICATION = 'core.wsgi.application'
ASGI_APPLICATION = 'core.asgi.application'

# Channels configuration
# Build Redis URL with password if provided
REDIS_PASSWORD = config('REDIS_PASSWORD', default='')
REDIS_HOST = config('REDIS_HOST', default='localhost')
REDIS_PORT = config('REDIS_PORT', default=6379, cast=int)

if REDIS_PASSWORD:
    CHANNEL_REDIS_URL = f"redis://:{REDIS_PASSWORD}@{REDIS_HOST}:{REDIS_PORT}/0"
else:
    CHANNEL_REDIS_URL = f"redis://{REDIS_HOST}:{REDIS_PORT}/0"

CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
            'hosts': [CHANNEL_REDIS_URL],
            'capacity': 1500,
            'expiry': 10,
        },
    },
}

# Database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': config('DB_NAME', default='app_db'),
        'USER': config('DB_USER', default='app_user'),
        'PASSWORD': config('DB_PASSWORD', default='secure_password'),
        'HOST': config('DB_HOST', default='localhost'),
        'PORT': config('DB_PORT', default='5432'),
        'OPTIONS': {
            'connect_timeout': 10,
        },
        'CONN_MAX_AGE': 600,
    }
}

# Redis Cache - use CACHE_URL from environment (includes password)
CACHE_URL_ENV = config('CACHE_URL', default=None)
if not CACHE_URL_ENV:
    # Fallback: build URL with password if provided
    if REDIS_PASSWORD:
        CACHE_URL_ENV = f"redis://:{REDIS_PASSWORD}@{REDIS_HOST}:{REDIS_PORT}/1"
    else:
        CACHE_URL_ENV = f"redis://{REDIS_HOST}:{REDIS_PORT}/1"

CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': CACHE_URL_ENV,
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            'IGNORE_EXCEPTIONS': False,  # Changed to False to see errors
        },
        'KEY_PREFIX': 'app',
        'TIMEOUT': 300,
    }
}

# Session configuration
SESSION_ENGINE = 'django.contrib.sessions.backends.db'
SESSION_COOKIE_AGE = 1209600  # 2 weeks

# Password validation (with Persian error messages)
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'accounts.validators.PersianUserAttributeSimilarityValidator'},
    {'NAME': 'accounts.validators.PersianMinimumLengthValidator', 'OPTIONS': {'min_length': 8}},
    {'NAME': 'accounts.validators.PersianCommonPasswordValidator'},
    {'NAME': 'accounts.validators.PersianNumericPasswordValidator'},
]

# Custom User Model
AUTH_USER_MODEL = 'accounts.User'

# Authentication Backends
AUTHENTICATION_BACKENDS = [
    'accounts.backends.PhoneOrEmailBackend',  # Custom backend for phone/email login
    'django.contrib.auth.backends.ModelBackend',  # Fallback to default
]

# Internationalization
LANGUAGE_CODE = 'fa-ir'
TIME_ZONE = 'Asia/Tehran'
USE_I18N = True
USE_L10N = True
USE_TZ = True

LANGUAGES = [
    ('fa', 'Persian'),
    ('en', 'English'),
]

LOCALE_PATHS = [
    BASE_DIR / 'locale',
]

# Static files
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [BASE_DIR / 'static']

# Media files
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# REST Framework configuration
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
        'rest_framework.renderers.BrowsableAPIRenderer',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ],
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle'
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '100/hour',
        'user': '1000/hour'
    },
    'DATETIME_FORMAT': '%Y-%m-%d %H:%M:%S',
    'DATE_FORMAT': '%Y-%m-%d',
}

# JWT Settings
JWT_SECRET_KEY = config('JWT_SECRET_KEY', default=SECRET_KEY)
JWT_ALGORITHM = config('JWT_ALGORITHM', default='HS256')
JWT_ACCESS_TOKEN_LIFETIME = config('JWT_ACCESS_TOKEN_LIFETIME', default=60, cast=int)  # minutes
JWT_REFRESH_TOKEN_LIFETIME = config('JWT_REFRESH_TOKEN_LIFETIME', default=1440, cast=int)  # minutes

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=JWT_ACCESS_TOKEN_LIFETIME),
    'REFRESH_TOKEN_LIFETIME': timedelta(minutes=JWT_REFRESH_TOKEN_LIFETIME),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'UPDATE_LAST_LOGIN': True,
    'ALGORITHM': JWT_ALGORITHM,
    'SIGNING_KEY': JWT_SECRET_KEY,  # استفاده از کلید JWT جداگانه برای هماهنگی با سیستم مرکزی
    'VERIFYING_KEY': None,
    'AUTH_HEADER_TYPES': ('Bearer',),
    'USER_ID_FIELD': 'id',
    'USER_ID_CLAIM': 'sub',  # استاندارد JWT برای Core API compatibility
    'AUTH_TOKEN_CLASSES': ('accounts.tokens.CustomAccessToken',),  # استفاده از custom token
    'TOKEN_TYPE_CLAIM': 'type',  # Core API expects 'type' not 'token_type'
    'JTI_CLAIM': 'jti',
}

# CORS Configuration
CORS_ALLOWED_ORIGINS = config(
    'CORS_ALLOWED_ORIGINS',
    default='http://localhost:3000,http://127.0.0.1:3000,https://tejarat.chat,http://tejarat.chat,https://admin.tejarat.chat',
    cast=Csv()
)
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_ALL_ORIGINS = False  # Security: Only allow specified origins
CORS_ALLOW_HEADERS = [
    'accept',
    'accept-encoding',
    'authorization',
    'content-type',
    'dnt',
    'origin',
    'user-agent',
    'x-csrftoken',
    'x-requested-with',
]

# Email Configuration
EMAIL_BACKEND = config('EMAIL_BACKEND', default='django.core.mail.backends.smtp.EmailBackend')
EMAIL_HOST = config('EMAIL_HOST', default='smtp.gmail.com')
EMAIL_PORT = config('EMAIL_PORT', default=587, cast=int)
EMAIL_USE_TLS = config('EMAIL_USE_TLS', default=True, cast=bool)
EMAIL_HOST_USER = config('EMAIL_HOST_USER', default='')
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD', default='')
DEFAULT_FROM_EMAIL = config('DEFAULT_FROM_EMAIL', default='noreply@tejarat.chat')
FRONTEND_URL = config('FRONTEND_URL', default='https://tejarat.chat')

# Celery Configuration
CELERY_BROKER_URL = f"redis://{config('REDIS_HOST', default='localhost')}:{config('REDIS_PORT', default=6379)}/0"
CELERY_RESULT_BACKEND = CELERY_BROKER_URL
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = TIME_ZONE
CELERY_TASK_TRACK_STARTED = True
CELERY_TASK_TIME_LIMIT = 30 * 60

# Celery Beat Schedule - تسک‌های زمان‌بندی شده
from celery.schedules import crontab

CELERY_BEAT_SCHEDULE = {
    # بررسی اشتراک‌های در حال انقضا - هر روز ساعت 9 صبح
    'check-expiring-subscriptions': {
        'task': 'subscriptions.tasks.check_expiring_subscriptions',
        'schedule': crontab(hour=9, minute=0),
    },
    # بررسی اشتراک‌های منقضی شده - هر روز ساعت 0:30
    'check-expired-subscriptions': {
        'task': 'subscriptions.tasks.check_expired_subscriptions',
        'schedule': crontab(hour=0, minute=30),
    },
    # بررسی هشدارهای سهمیه - هر 6 ساعت
    'check-quota-warnings': {
        'task': 'subscriptions.tasks.check_quota_warnings',
        'schedule': crontab(hour='*/6', minute=0),
    },
    # پاکسازی توکن‌ها و session های قدیمی - هر شب ساعت 3 صبح
    'cleanup-tokens-and-sessions': {
        'task': 'core.tasks.cleanup_tokens_and_sessions',
        'schedule': crontab(hour=3, minute=0),
    },
    # پاکسازی فایل‌های موقت - هر شب ساعت 2 صبح
    'cleanup-old-files': {
        'task': 'core.tasks.cleanup_old_files',
        'schedule': crontab(hour=2, minute=0),
    },
}

# Payment Gateways
ZARINPAL_MERCHANT_ID = config('ZARINPAL_MERCHANT_ID', default='')
ZARINPAL_SANDBOX = config('ZARINPAL_SANDBOX', default=True, cast=bool)

STRIPE_PUBLIC_KEY = config('STRIPE_PUBLIC_KEY', default='')
STRIPE_SECRET_KEY = config('STRIPE_SECRET_KEY', default='')

# Crypto Rates API (برای دریافت نرخ لحظه‌ای رمزارزها)
CRYPTO_RATES_API_URL = config('CRYPTO_RATES_API_URL', default='')

# RAG Core API Configuration (moved to end of file)

# Security Settings
SECURE_SSL_REDIRECT = config('SECURE_SSL_REDIRECT', default=False, cast=bool)
SESSION_COOKIE_SECURE = config('SESSION_COOKIE_SECURE', default=False, cast=bool)
CSRF_COOKIE_SECURE = config('CSRF_COOKIE_SECURE', default=False, cast=bool)
CSRF_TRUSTED_ORIGINS = [
    'http://admin.tejarat.chat',
    'https://admin.tejarat.chat',
    'http://tejarat.chat',
    'https://tejarat.chat',
    'http://89.251.8.95',
]
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'

# Logging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose'
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': config('DJANGO_LOG_LEVEL', default='INFO'),
            'propagate': False,
        },
        'django.request': {
            'handlers': ['console'],
            'level': 'ERROR',
            'propagate': False,
        },
        'app': {
            'handlers': ['console'],
            'level': 'DEBUG' if DEBUG else 'INFO',
            'propagate': False,
        },
    },
}
# os.makedirs(BASE_DIR / 'logs', exist_ok=True)

# ===========================
# SMS & Messaging Configuration
# ===========================
# Kavenegar (SMS)
KAVENEGAR_API_KEY = config('KAVENEGAR_API_KEY', default='')
KAVENEGAR_SENDER = config('KAVENEGAR_SENDER', default='')

# Bale Messenger (OTP)
BALE_USERNAME = config('BALE_USERNAME', default='')
BALE_PASSWORD = config('BALE_PASSWORD', default='')

# OTP Configuration
OTP_EXPIRE_SECONDS = config('OTP_EXPIRE_SECONDS', default=120, cast=int)

# ===========================
# Core RAG API Configuration (deprecated - use RAG_CORE_BASE_URL instead)
# ===========================
# These are kept for backward compatibility with celery tasks
CORE_API_URL = config('CORE_API_URL', default=config('RAG_CORE_BASE_URL', default=''))
CORE_API_KEY = config('CORE_API_KEY', default=config('RAG_CORE_API_KEY', default=''))

# ===========================
# Jazzmin Admin Configuration
# ===========================
JAZZMIN_SETTINGS = {
    # Title
    "site_title": "مشاور هوشمند کسب و کار",
    "site_header": "مشاور هوشمند کسب و کار",
    "site_brand": "مشاور هوشمند",
    "site_logo": "images/logo-small.png",
    "login_logo": "images/logo-medium.png",
    "login_logo_dark": None,
    "site_logo_classes": "img-fluid",
    "site_icon": "images/favicon.ico",
    "welcome_sign": "خوش آمدید به پنل مدیریت",
    "copyright": "مشاور هوشمند کسب و کار © 2024",
    "search_model": "auth.User",
    "user_avatar": None,
    
    # Top Menu
    "topmenu_links": [
        {"name": "صفحه اصلی", "url": "admin:index", "permissions": ["auth.view_user"]},
        {"name": "پشتیبانی", "url": "https://tejarat.chat", "new_window": True},
        {"model": "auth.User"},
    ],
    
    # User Menu
    "usermenu_links": [
        {"model": "auth.user"}
    ],
    
    # Side Menu
    "show_sidebar": True,
    "navigation_expanded": True,
    "hide_apps": [],
    "hide_models": [],
    "order_with_respect_to": ["accounts", "admin_panel", "chat", "subscriptions", "payments", "finance", "notifications", "analytics"],
    
    # Icons
    "icons": {
        "auth": "fas fa-users-cog",
        "auth.user": "fas fa-user",
        "auth.Group": "fas fa-users",
        "accounts": "fas fa-users",
        "accounts.User": "fas fa-user-circle",
        "accounts.Organization": "fas fa-building",
        "accounts.UserSession": "fas fa-laptop",
        "accounts.OrganizationInvitation": "fas fa-envelope",
        "accounts.AuditLog": "fas fa-history",
        "admin_panel": "fas fa-user-shield",
        "admin_panel.Role": "fas fa-user-tag",
        "admin_panel.AdminUser": "fas fa-user-shield",
        "admin_panel.AdminAction": "fas fa-clipboard-list",
        "admin_panel.AdminDashboardWidget": "fas fa-th",
        "admin_panel.AdminNotification": "fas fa-bell",
        "chat.Conversation": "fas fa-comments",
        "chat.Message": "fas fa-comment",
        "subscriptions.Subscription": "fas fa-crown",
        "subscriptions.SubscriptionPlan": "fas fa-clipboard-list",
        "payments.Payment": "fas fa-credit-card",
        "finance": "fas fa-file-invoice-dollar",
        "finance.FinancialSettings": "fas fa-cog",
        "finance.Invoice": "fas fa-file-invoice",
        "finance.TaxReport": "fas fa-chart-pie",
        "notifications.Notification": "fas fa-bell",
        "analytics.Analytics": "fas fa-chart-line",
        "support": "fas fa-headset",
        "support.Ticket": "fas fa-ticket-alt",
        "support.TicketDepartment": "fas fa-building",
        "support.TicketCategory": "fas fa-tags",
        "support.TicketMessage": "fas fa-comment-dots",
        "support.CannedResponse": "fas fa-reply-all",
        "support.TicketTag": "fas fa-tag",
        "support.SLAPolicy": "fas fa-clock",
    },
    
    # UI Tweaks
    "custom_css": "admin/css/custom_rtl.css",
    "custom_js": None,
    "use_google_fonts_cdn": True,
    "show_ui_builder": False,
    
    "changeform_format": "horizontal_tabs",
    "changeform_format_overrides": {"auth.user": "collapsible", "auth.group": "vertical_tabs"},
    
    # Language
    "language_chooser": False,
}

JAZZMIN_UI_TWEAKS = {
    "navbar_small_text": False,
    "footer_small_text": False,
    "body_small_text": False,
    "brand_small_text": False,
    "brand_colour": "navbar-info",
    "accent": "accent-primary",
    "navbar": "navbar-dark",
    "no_navbar_border": False,
    "navbar_fixed": True,
    "layout_boxed": False,
    "footer_fixed": False,
    "sidebar_fixed": True,
    "sidebar": "sidebar-dark-info",
    "sidebar_nav_small_text": False,
    "sidebar_disable_expand": False,
    "sidebar_nav_child_indent": False,
    "sidebar_nav_compact_style": False,
    "sidebar_nav_legacy_style": False,
    "sidebar_nav_flat_style": False,
    "theme": "default",
    "dark_mode_theme": None,
    "button_classes": {
        "primary": "btn-primary",
        "secondary": "btn-secondary",
        "info": "btn-info",
        "warning": "btn-warning",
        "danger": "btn-danger",
        "success": "btn-success"
    }
}

# S3 Configuration
S3_ENDPOINT_URL = config('S3_ENDPOINT_URL', default='')
S3_ACCESS_KEY_ID = config('S3_ACCESS_KEY_ID', default='')
S3_SECRET_ACCESS_KEY = config('S3_SECRET_ACCESS_KEY', default='')
S3_TEMP_BUCKET = config('S3_TEMP_BUCKET', default='')
S3_USE_SSL = config('S3_USE_SSL', default=True, cast=bool)
S3_REGION = config('S3_REGION', default='us-east-1')

# RAG Core Configuration
RAG_CORE_BASE_URL = config('RAG_CORE_BASE_URL', default='')
RAG_CORE_API_KEY = config('RAG_CORE_API_KEY', default='')
RAG_CORE_TIMEOUT = config('RAG_CORE_TIMEOUT', default=60, cast=int)  # seconds
