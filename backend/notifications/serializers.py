from rest_framework import serializers
from .models import (
    Notification, NotificationTemplate, NotificationPreference,
    DeviceToken, NotificationLog
)


class NotificationSerializer(serializers.ModelSerializer):
    """Serializer برای اعلان‌ها"""
    
    category_display = serializers.CharField(source='get_category_display', read_only=True)
    priority_display = serializers.CharField(source='get_priority_display', read_only=True)
    time_ago = serializers.SerializerMethodField()
    
    class Meta:
        model = Notification
        fields = [
            'id', 'title', 'body',
            'category', 'category_display',
            'priority', 'priority_display',
            'action_url', 'action_text',
            'is_read', 'read_at',
            'is_confirmed', 'confirmed_at',
            'created_at', 'expires_at',
            'time_ago'
        ]
        read_only_fields = [
            'id', 'created_at', 'read_at', 'confirmed_at'
        ]
    
    def get_time_ago(self, obj):
        """محاسبه زمان نسبی"""
        from django.utils import timezone
        from datetime import timedelta
        
        delta = timezone.now() - obj.created_at
        
        if delta < timedelta(minutes=1):
            return 'همین الان'
        elif delta < timedelta(hours=1):
            minutes = int(delta.total_seconds() / 60)
            return f'{minutes} دقیقه پیش'
        elif delta < timedelta(days=1):
            hours = int(delta.total_seconds() / 3600)
            return f'{hours} ساعت پیش'
        elif delta < timedelta(days=7):
            days = delta.days
            return f'{days} روز پیش'
        else:
            return obj.created_at.strftime('%Y-%m-%d')


class NotificationDetailSerializer(NotificationSerializer):
    """Serializer جزئیات کامل اعلان"""
    
    template_name = serializers.CharField(source='template.name', read_only=True)
    
    class Meta(NotificationSerializer.Meta):
        fields = NotificationSerializer.Meta.fields + [
            'template_name', 'channels',
            'sent_via_email', 'sent_via_sms', 'sent_via_push',
            'metadata', 'error_log'
        ]


class NotificationTemplateSerializer(serializers.ModelSerializer):
    """Serializer برای قالب‌های اعلان"""
    
    category_display = serializers.CharField(source='get_category_display', read_only=True)
    
    class Meta:
        model = NotificationTemplate
        fields = [
            'id', 'code', 'name', 'description',
            'category', 'category_display',
            'title_template', 'body_template',
            'email_subject_template', 'email_html_template', 'sms_template',
            'channels', 'default_priority',
            'action_url', 'action_text',
            'is_active', 'require_confirmation',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class NotificationPreferenceSerializer(serializers.ModelSerializer):
    """Serializer برای تنظیمات اعلان‌رسانی"""
    
    class Meta:
        model = NotificationPreference
        fields = [
            'user',
            'email_enabled', 'sms_enabled', 'push_enabled', 'in_app_enabled',
            'system_notifications', 'payment_notifications',
            'subscription_notifications', 'chat_notifications',
            'account_notifications', 'security_notifications',
            'marketing_notifications', 'support_notifications',
            'quiet_hours_enabled', 'quiet_hours_start', 'quiet_hours_end',
            'digest_enabled', 'digest_time',
            'custom_preferences',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['user', 'created_at', 'updated_at']


class DeviceTokenSerializer(serializers.ModelSerializer):
    """Serializer برای توکن‌های دستگاه"""
    
    device_type_display = serializers.CharField(source='get_device_type_display', read_only=True)
    
    class Meta:
        model = DeviceToken
        fields = [
            'id', 'token', 'device_type', 'device_type_display',
            'device_name', 'is_active',
            'last_used_at', 'created_at'
        ]
        read_only_fields = ['id', 'last_used_at', 'created_at']
        extra_kwargs = {
            'token': {'write_only': True}
        }


class RegisterDeviceSerializer(serializers.Serializer):
    """Serializer برای ثبت دستگاه"""
    
    token = serializers.CharField(max_length=500)
    device_type = serializers.ChoiceField(choices=DeviceToken.DEVICE_TYPES)
    device_name = serializers.CharField(max_length=100, required=False, allow_blank=True)


class SendNotificationSerializer(serializers.Serializer):
    """Serializer برای ارسال اعلان"""
    
    template_code = serializers.CharField(max_length=100)
    context = serializers.DictField()
    channels = serializers.ListField(
        child=serializers.CharField(),
        required=False
    )
    priority = serializers.ChoiceField(
        choices=['low', 'normal', 'high', 'urgent'],
        default='normal'
    )


class NotificationStatsSerializer(serializers.Serializer):
    """Serializer برای آمار اعلان‌ها"""
    
    total = serializers.IntegerField()
    unread = serializers.IntegerField()
    by_category = serializers.DictField()
    by_priority = serializers.DictField()
    recent = serializers.ListField()


class MarkAsReadSerializer(serializers.Serializer):
    """Serializer برای علامت‌گذاری به عنوان خوانده شده"""
    
    notification_ids = serializers.ListField(
        child=serializers.UUIDField(),
        required=False
    )
    mark_all = serializers.BooleanField(default=False)
