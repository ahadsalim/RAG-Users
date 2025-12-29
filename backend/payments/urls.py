from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = 'payments'

router = DefaultRouter()
router.register(r'transactions', views.TransactionViewSet, basename='transaction')
router.register(r'wallet', views.WalletViewSet, basename='wallet')

urlpatterns = [
    path('', include(router.urls)),
    
    # Payment gateways list
    path('gateways/', views.PaymentGatewayListView.as_view(), name='gateway-list'),
    
    # Create payment (simplified endpoint)
    path('create/', views.TransactionViewSet.as_view({'post': 'create_payment'}), name='create-payment'),
    
    # Callbacks
    path('zarinpal/callback/', views.ZarinpalCallbackView.as_view(), name='zarinpal-callback'),
    path('zarinpal/wallet-callback/', views.ZarinpalCallbackView.as_view(), name='zarinpal-wallet-callback'),
    path('tejarat-test/callback/', views.TejaratTestCallbackView.as_view(), name='tejarat-test-callback'),
    path('stripe/webhook/', views.StripeWebhookView.as_view(), name='stripe-webhook'),
]
