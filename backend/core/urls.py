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
    path('api/v1/chat/', include('chat.urls')),
    path('api/v1/subscriptions/', include('subscriptions.urls')),
    path('api/v1/payments/', include('payments.urls')),
    path('api/v1/consultants/', include('consultants.urls')),
    path('api/v1/notifications/', include('notifications.urls')),
    path('api/v1/analytics/', include('analytics.urls')),
    
    # Health checks - TODO: Install django-health-check package
    # path('health/', include('health_check.urls')),
    
    # WebSocket URLs (برای چت real-time)
    # این‌ها در asgi.py تنظیم می‌شوند
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
