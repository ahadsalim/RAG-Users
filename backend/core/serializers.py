from rest_framework import serializers
from .models import SiteSettings
from finance.serializers import PaymentGatewaySerializer


class SiteSettingsSerializer(serializers.ModelSerializer):
    """Serializer for SiteSettings model"""
    default_payment_gateway = PaymentGatewaySerializer(read_only=True)
    
    class Meta:
        model = SiteSettings
        fields = [
            'frontend_site_name', 'admin_site_name',
            'default_payment_gateway',
            'support_email', 'support_phone',
            'telegram_url', 'instagram_url', 'twitter_url',
            'maintenance_mode', 'maintenance_message',
        ]
