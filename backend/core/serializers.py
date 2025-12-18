from rest_framework import serializers
from .models import Currency, PaymentGateway, SiteSettings


class CurrencySerializer(serializers.ModelSerializer):
    """Serializer for Currency model"""
    
    class Meta:
        model = Currency
        fields = [
            'id', 'code', 'name', 'symbol', 'has_decimals', 
            'decimal_places', 'exchange_rate', 'is_active', 'display_order'
        ]
        read_only_fields = ['id']


class PaymentGatewaySerializer(serializers.ModelSerializer):
    """Serializer for PaymentGateway model"""
    supported_currencies = CurrencySerializer(many=True, read_only=True)
    
    class Meta:
        model = PaymentGateway
        fields = [
            'id', 'name', 'gateway_type', 'is_active', 'is_sandbox',
            'supported_currencies', 'commission_percentage', 'display_order'
        ]
        read_only_fields = ['id']


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
