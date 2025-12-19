"""
URL های امور مالی
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    FinancialSettingsView, FinancialSettingsPublicView,
    InvoiceViewSet, UserInvoiceViewSet, TaxReportViewSet,
    FinancialDashboardView
)

router = DefaultRouter()
router.register(r'invoices', InvoiceViewSet, basename='invoice')
router.register(r'user-invoices', UserInvoiceViewSet, basename='user-invoice')
router.register(r'tax-reports', TaxReportViewSet, basename='tax-report')

urlpatterns = [
    path('settings/', FinancialSettingsView.as_view(), name='financial-settings'),
    path('settings/public/', FinancialSettingsPublicView.as_view(), name='financial-settings-public'),
    path('dashboard/', FinancialDashboardView.as_view(), name='financial-dashboard'),
    path('', include(router.urls)),
]
