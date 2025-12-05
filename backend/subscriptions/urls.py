from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'plans', views.PlanViewSet, basename='plan')
router.register(r'subscriptions', views.SubscriptionViewSet, basename='subscription')

urlpatterns = [
    path('', include(router.urls)),
    path('usage/', views.UsageView.as_view(), name='usage'),
    path('usage/stats/', views.UsageStatsView.as_view(), name='usage-stats'),
    path('reports/', views.UsageReportView.as_view(), name='usage-report'),
    path('reports/export/', views.UsageReportExportView.as_view(), name='usage-report-export'),
    path('reports/admin/', views.AdminReportView.as_view(), name='admin-report'),
]
