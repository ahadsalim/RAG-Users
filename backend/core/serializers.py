from rest_framework import serializers
from .models import SiteSettings


class SiteSettingsSerializer(serializers.ModelSerializer):
    """Serializer for SiteSettings model"""
    
    class Meta:
        model = SiteSettings
        fields = [
            'frontend_site_name', 'admin_site_name',
            'support_email', 'support_phone',
            'telegram_url', 'instagram_url', 'twitter_url',
            'maintenance_mode', 'maintenance_message',
            'license_1_name', 'license_1_logo_url',
            'license_2_name', 'license_2_logo_url',
            'license_3_name', 'license_3_logo_url',
        ]
