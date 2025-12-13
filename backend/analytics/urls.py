from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    DashboardSummaryView,
    ChartDataView,
    UserAnalyticsViewSet,
    RevenueAnalyticsViewSet,
    SystemMetricsViewSet,
    MetricsExportView
)

router = DefaultRouter()
router.register(r'users', UserAnalyticsViewSet, basename='user-analytics')
router.register(r'revenue', RevenueAnalyticsViewSet, basename='revenue-analytics')
router.register(r'system', SystemMetricsViewSet, basename='system-metrics')

app_name = 'analytics'

urlpatterns = [
    path('dashboard/', DashboardSummaryView.as_view(), name='dashboard'),
    path('charts/', ChartDataView.as_view(), name='charts'),
    path('export/', MetricsExportView.as_view(), name='export'),
    path('', include(router.urls)),
]
