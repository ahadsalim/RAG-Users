from django.urls import path
from .views import SiteSettingsView, PaymentGatewayListView

urlpatterns = [
    # Site settings
    path('settings/', SiteSettingsView.as_view(), name='site-settings'),
    
    # Payment gateways (legacy - use /api/v1/finance/currencies/ instead)
    path('payment-gateways/', PaymentGatewayListView.as_view(), name='payment-gateway-list'),
]
