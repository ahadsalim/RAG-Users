"""
URL های امور مالی
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    CurrencyListView, CurrencyDetailView, convert_currency,
    FinancialSettingsView, FinancialSettingsPublicView,
    InvoiceViewSet, UserInvoiceViewSet, TaxReportViewSet,
    FinancialDashboardView
)
from .admin_views import current_revenue_report_view

router = DefaultRouter()
router.register(r'invoices', InvoiceViewSet, basename='invoice')
router.register(r'user-invoices', UserInvoiceViewSet, basename='user-invoice')
router.register(r'tax-reports', TaxReportViewSet, basename='tax-report')

urlpatterns = [
    # Currency endpoints
    path('currencies/', CurrencyListView.as_view(), name='currency-list'),
    path('currencies/<int:pk>/', CurrencyDetailView.as_view(), name='currency-detail'),
    path('currencies/convert/', convert_currency, name='currency-convert'),
    
    # Settings
    path('settings/', FinancialSettingsView.as_view(), name='financial-settings'),
    path('settings/public/', FinancialSettingsPublicView.as_view(), name='financial-settings-public'),
    path('dashboard/', FinancialDashboardView.as_view(), name='financial-dashboard'),
    
    # Admin views
    path('admin/revenue-report/', current_revenue_report_view, name='revenue-report'),
    
    path('', include(router.urls)),
]
