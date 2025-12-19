from rest_framework import generics, permissions
from rest_framework.response import Response
from .models import SiteSettings
from .serializers import SiteSettingsSerializer
from finance.models import PaymentGateway
from finance.serializers import PaymentGatewaySerializer


class SiteSettingsView(generics.RetrieveAPIView):
    """Get site settings"""
    permission_classes = [permissions.AllowAny]
    serializer_class = SiteSettingsSerializer
    
    def get_object(self):
        return SiteSettings.get_settings()


class PaymentGatewayListView(generics.ListAPIView):
    """List all active payment gateways"""
    permission_classes = [permissions.AllowAny]
    serializer_class = PaymentGatewaySerializer
    queryset = PaymentGateway.objects.filter(is_active=True)
