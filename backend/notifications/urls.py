from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = 'notifications'

router = DefaultRouter()
router.register(r'', views.NotificationViewSet, basename='notification')
router.register(r'devices', views.DeviceTokenViewSet, basename='device')
router.register(r'templates', views.NotificationTemplateViewSet, basename='template')

urlpatterns = [
    path('', include(router.urls)),
    path('preferences/', views.NotificationPreferenceView.as_view(), name='preferences'),
    path('send/', views.SendNotificationView.as_view(), name='send'),
    path('test/', views.TestNotificationView.as_view(), name='test'),
]
