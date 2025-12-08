from django.urls import path
from .views import (
    SiteSettingsView,
    CurrencyListView,
    PaymentGatewayListView,
    convert_currency
)

urlpatterns = [
    # Site settings
    path('settings/', SiteSettingsView.as_view(), name='site-settings'),
    
    # Currencies
    path('currencies/', CurrencyListView.as_view(), name='currency-list'),
    path('currencies/convert/', convert_currency, name='currency-convert'),
    
    # Payment gateways
    path('payment-gateways/', PaymentGatewayListView.as_view(), name='payment-gateway-list'),
]
