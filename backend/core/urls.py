"""
URL Configuration اصلی پروژه app Platform
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework_simplejwt.views import TokenRefreshView
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView

# برای تنظیم عنوان پنل ادمین
admin.site.site_header = "پنل مدیریت پلتفرم مشاور"
admin.site.site_title = "مدیریت مشاور"
admin.site.index_title = "خوش آمدید به پنل مدیریت"

urlpatterns = [
    # Admin panel
    path('admin/', admin.site.urls),
    
    # API Documentation
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
    
    # API v1 endpoints
    path('api/v1/auth/', include('accounts.urls')),
    path('api/v1/auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/v1/', include('core.api_urls')),
    path('api/v1/chat/', include('chat.urls')),
    path('api/v1/subscriptions/', include('subscriptions.urls')),
    path('api/v1/payments/', include('payments.urls')),
    path('api/v1/consultants/', include('consultants.urls')),
    path('api/v1/notifications/', include('notifications.urls')),
    path('api/v1/analytics/', include('analytics.urls')),
    
    # WebSocket URLs (برای چت real-time)
    # این‌ها در asgi.py تنظیم می‌شوند
]

# Simple health check endpoint
from django.http import JsonResponse
from django.db import connection

def health_check(request):
    """بررسی سلامت سیستم"""
    try:
        connection.ensure_connection()
        db_status = 'ok'
    except Exception:
        db_status = 'error'
    
    return JsonResponse({
        'status': 'ok' if db_status == 'ok' else 'degraded',
        'database': db_status,
    })

urlpatterns.append(path('health/', health_check, name='health-check'))

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
