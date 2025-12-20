from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.utils import timezone
from .models import (
    TicketDepartment, TicketCategory, Ticket, TicketMessage,
    TicketAttachment, TicketForward, TicketHistory, CannedResponse,
    TicketTag, SLAPolicy
)

User = get_user_model()


class UserMinimalSerializer(serializers.ModelSerializer):
    """سریالایزر کوچک برای نمایش کاربر"""
    full_name = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = ['id', 'full_name', 'phone_number', 'email', 'avatar', 'is_staff']
    
    def get_full_name(self, obj):
        if obj.first_name and obj.last_name:
            return f"{obj.first_name} {obj.last_name}"
        elif obj.first_name:
            return obj.first_name
        elif obj.last_name:
            return obj.last_name
        return obj.phone_number or obj.email or str(obj.id)


class TicketDepartmentSerializer(serializers.ModelSerializer):
    """سریالایزر دپارتمان"""
    manager_info = UserMinimalSerializer(source='manager', read_only=True)
    agents_count = serializers.SerializerMethodField()
    open_tickets_count = serializers.SerializerMethodField()
    
    class Meta:
        model = TicketDepartment
        fields = [
            'id', 'name', 'description', 'email', 'manager', 'manager_info',
            'is_active', 'is_public', 'auto_assign', 'priority',
            'default_response_time', 'default_resolution_time',
            'agents_count', 'open_tickets_count',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_agents_count(self, obj):
        return obj.agents.filter(is_active=True).count()
    
    def get_open_tickets_count(self, obj):
        return obj.tickets.filter(status__in=['open', 'in_progress', 'waiting']).count()


class TicketDepartmentListSerializer(serializers.ModelSerializer):
    """سریالایزر لیست دپارتمان (برای کاربران)"""
    class Meta:
        model = TicketDepartment
        fields = ['id', 'name', 'description']


class TicketCategorySerializer(serializers.ModelSerializer):
    """سریالایزر دسته‌بندی"""
    children = serializers.SerializerMethodField()
    parent_name = serializers.CharField(source='parent.name', read_only=True)
    
    class Meta:
        model = TicketCategory
        fields = [
            'id', 'name', 'description', 'icon', 'color',
            'default_department', 'default_priority', 'parent', 'parent_name',
            'is_active', 'order', 'children', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_children(self, obj):
        children = obj.children.filter(is_active=True)
        return TicketCategorySerializer(children, many=True).data


class TicketCategoryListSerializer(serializers.ModelSerializer):
    """سریالایزر لیست دسته‌بندی (برای کاربران)"""
    class Meta:
        model = TicketCategory
        fields = ['id', 'name', 'description', 'icon', 'color', 'default_priority']


class TicketAttachmentSerializer(serializers.ModelSerializer):
    """سریالایزر پیوست"""
    uploaded_by_info = UserMinimalSerializer(source='uploaded_by', read_only=True)
    file_url = serializers.SerializerMethodField()
    
    class Meta:
        model = TicketAttachment
        fields = [
            'id', 'ticket', 'message', 'uploaded_by', 'uploaded_by_info',
            'file', 'file_url', 'file_name', 'file_size', 'mime_type', 'created_at'
        ]
        read_only_fields = ['id', 'uploaded_by', 'file_name', 'file_size', 'mime_type', 'created_at']
    
    def get_file_url(self, obj):
        request = self.context.get('request')
        if obj.file and request:
            return request.build_absolute_uri(obj.file.url)
        return None


class TicketMessageSerializer(serializers.ModelSerializer):
    """سریالایزر پیام تیکت"""
    sender_info = UserMinimalSerializer(source='sender', read_only=True)
    attachments = TicketAttachmentSerializer(many=True, read_only=True)
    
    class Meta:
        model = TicketMessage
        fields = [
            'id', 'ticket', 'sender', 'sender_info', 'content',
            'message_type', 'is_staff_reply', 'attachments',
            'metadata', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'sender', 'is_staff_reply', 'created_at', 'updated_at']


class TicketMessageCreateSerializer(serializers.ModelSerializer):
    """سریالایزر ایجاد پیام"""
    attachments = serializers.ListField(
        child=serializers.FileField(),
        required=False,
        write_only=True
    )
    
    class Meta:
        model = TicketMessage
        fields = ['content', 'message_type', 'attachments']
    
    def create(self, validated_data):
        attachments_data = validated_data.pop('attachments', [])
        message = TicketMessage.objects.create(**validated_data)
        
        for file in attachments_data:
            TicketAttachment.objects.create(
                message=message,
                ticket=message.ticket,
                uploaded_by=message.sender,
                file=file,
                file_name=file.name,
                file_size=file.size,
                mime_type=file.content_type or 'application/octet-stream'
            )
        
        return message


class TicketHistorySerializer(serializers.ModelSerializer):
    """سریالایزر تاریخچه"""
    user_info = UserMinimalSerializer(source='user', read_only=True)
    action_display = serializers.CharField(source='get_action_display', read_only=True)
    
    class Meta:
        model = TicketHistory
        fields = [
            'id', 'ticket', 'user', 'user_info', 'action', 'action_display',
            'old_value', 'new_value', 'description', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class TicketForwardSerializer(serializers.ModelSerializer):
    """سریالایزر فوروارد"""
    from_agent_info = UserMinimalSerializer(source='from_agent', read_only=True)
    to_agent_info = UserMinimalSerializer(source='to_agent', read_only=True)
    to_department_info = TicketDepartmentListSerializer(source='to_department', read_only=True)
    
    class Meta:
        model = TicketForward
        fields = [
            'id', 'ticket', 'from_agent', 'from_agent_info',
            'to_agent', 'to_agent_info', 'to_department', 'to_department_info',
            'reason', 'created_at'
        ]
        read_only_fields = ['id', 'from_agent', 'created_at']


class TicketSerializer(serializers.ModelSerializer):
    """سریالایزر کامل تیکت"""
    user_info = UserMinimalSerializer(source='user', read_only=True)
    assigned_to_info = UserMinimalSerializer(source='assigned_to', read_only=True)
    category_info = TicketCategoryListSerializer(source='category', read_only=True)
    department_info = TicketDepartmentListSerializer(source='department', read_only=True)
    messages = TicketMessageSerializer(many=True, read_only=True)
    attachments = TicketAttachmentSerializer(many=True, read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    priority_display = serializers.CharField(source='get_priority_display', read_only=True)
    source_display = serializers.CharField(source='get_source_display', read_only=True)
    is_sla_breached = serializers.SerializerMethodField()
    messages_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Ticket
        fields = [
            'id', 'ticket_number', 'user', 'user_info', 'organization',
            'subject', 'description', 'category', 'category_info',
            'department', 'department_info', 'status', 'status_display',
            'priority', 'priority_display', 'source', 'source_display',
            'assigned_to', 'assigned_to_info', 'tags',
            'response_due', 'resolution_due', 'first_response_at', 'resolved_at',
            'satisfaction_rating', 'satisfaction_feedback',
            'user_read', 'staff_read', 'is_sla_breached', 'messages_count',
            'messages', 'attachments',
            'created_at', 'updated_at', 'closed_at'
        ]
        read_only_fields = [
            'id', 'ticket_number', 'user', 'first_response_at', 'resolved_at',
            'user_read', 'staff_read', 'created_at', 'updated_at', 'closed_at'
        ]
    
    def get_is_sla_breached(self, obj):
        return obj.is_sla_breached()
    
    def get_messages_count(self, obj):
        return obj.messages.count()


class TicketListSerializer(serializers.ModelSerializer):
    """سریالایزر لیست تیکت‌ها"""
    user_info = UserMinimalSerializer(source='user', read_only=True)
    assigned_to_info = UserMinimalSerializer(source='assigned_to', read_only=True)
    category_name = serializers.CharField(source='category.name', read_only=True)
    department_name = serializers.CharField(source='department.name', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    priority_display = serializers.CharField(source='get_priority_display', read_only=True)
    is_sla_breached = serializers.SerializerMethodField()
    messages_count = serializers.SerializerMethodField()
    last_message_at = serializers.SerializerMethodField()
    
    class Meta:
        model = Ticket
        fields = [
            'id', 'ticket_number', 'user_info', 'subject',
            'category_name', 'department_name',
            'status', 'status_display', 'priority', 'priority_display',
            'assigned_to_info', 'is_sla_breached', 'messages_count',
            'user_read', 'staff_read', 'last_message_at',
            'created_at', 'updated_at'
        ]
    
    def get_is_sla_breached(self, obj):
        return obj.is_sla_breached()
    
    def get_messages_count(self, obj):
        return obj.messages.count()
    
    def get_last_message_at(self, obj):
        last_message = obj.messages.order_by('-created_at').first()
        if last_message:
            return last_message.created_at
        return obj.created_at


class TicketCreateSerializer(serializers.ModelSerializer):
    """سریالایزر ایجاد تیکت"""
    attachments = serializers.ListField(
        child=serializers.FileField(),
        required=False,
        write_only=True
    )
    
    class Meta:
        model = Ticket
        fields = [
            'subject', 'description', 'category', 'department',
            'priority', 'attachments'
        ]
    
    def create(self, validated_data):
        attachments_data = validated_data.pop('attachments', [])
        user = self.context['request'].user
        
        # تنظیم دپارتمان از دسته‌بندی اگر مشخص نشده
        if not validated_data.get('department') and validated_data.get('category'):
            validated_data['department'] = validated_data['category'].default_department
        
        # تنظیم اولویت از دسته‌بندی اگر مشخص نشده
        if not validated_data.get('priority') and validated_data.get('category'):
            validated_data['priority'] = validated_data['category'].default_priority
        
        # تنظیم سازمان کاربر
        validated_data['user'] = user
        if user.organization:
            validated_data['organization'] = user.organization
        
        ticket = Ticket.objects.create(**validated_data)
        
        # تخصیص خودکار به کارشناس
        if ticket.department and ticket.department.auto_assign:
            agent = ticket.department.get_agent_with_least_tickets()
            if agent:
                ticket.assigned_to = agent
                ticket.save(update_fields=['assigned_to'])
        
        # ذخیره پیوست‌ها
        for file in attachments_data:
            TicketAttachment.objects.create(
                ticket=ticket,
                uploaded_by=user,
                file=file,
                file_name=file.name,
                file_size=file.size,
                mime_type=file.content_type or 'application/octet-stream'
            )
        
        # ثبت در تاریخچه
        TicketHistory.objects.create(
            ticket=ticket,
            user=user,
            action='created',
            description=f'تیکت #{ticket.ticket_number} ایجاد شد'
        )
        
        return ticket


class TicketUpdateSerializer(serializers.ModelSerializer):
    """سریالایزر به‌روزرسانی تیکت (برای کارشناسان)"""
    
    class Meta:
        model = Ticket
        fields = [
            'status', 'priority', 'category', 'department',
            'assigned_to', 'tags', 'response_due', 'resolution_due'
        ]
    
    def update(self, instance, validated_data):
        user = self.context['request'].user
        
        # ثبت تغییرات در تاریخچه
        for field, new_value in validated_data.items():
            old_value = getattr(instance, field)
            if old_value != new_value:
                action = f'{field}_changed'
                if field == 'status':
                    action = 'status_changed'
                elif field == 'priority':
                    action = 'priority_changed'
                elif field == 'assigned_to':
                    action = 'assigned'
                elif field == 'department':
                    action = 'department_changed'
                elif field == 'category':
                    action = 'category_changed'
                
                TicketHistory.objects.create(
                    ticket=instance,
                    user=user,
                    action=action,
                    old_value={'value': str(old_value)},
                    new_value={'value': str(new_value)}
                )
        
        return super().update(instance, validated_data)


class TicketRatingSerializer(serializers.ModelSerializer):
    """سریالایزر امتیازدهی تیکت"""
    
    class Meta:
        model = Ticket
        fields = ['satisfaction_rating', 'satisfaction_feedback']
    
    def validate_satisfaction_rating(self, value):
        if value < 1 or value > 5:
            raise serializers.ValidationError('امتیاز باید بین 1 تا 5 باشد')
        return value


class CannedResponseSerializer(serializers.ModelSerializer):
    """سریالایزر پاسخ آماده"""
    created_by_info = UserMinimalSerializer(source='created_by', read_only=True)
    category_name = serializers.CharField(source='category.name', read_only=True)
    department_name = serializers.CharField(source='department.name', read_only=True)
    
    class Meta:
        model = CannedResponse
        fields = [
            'id', 'title', 'content', 'category', 'category_name',
            'department', 'department_name', 'created_by', 'created_by_info',
            'is_public', 'is_active', 'usage_count',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_by', 'usage_count', 'created_at', 'updated_at']


class TicketTagSerializer(serializers.ModelSerializer):
    """سریالایزر تگ"""
    
    class Meta:
        model = TicketTag
        fields = ['id', 'name', 'color', 'description', 'is_active', 'created_at']
        read_only_fields = ['id', 'created_at']


class SLAPolicySerializer(serializers.ModelSerializer):
    """سریالایزر سیاست SLA"""
    department_name = serializers.CharField(source='department.name', read_only=True)
    category_name = serializers.CharField(source='category.name', read_only=True)
    priority_display = serializers.CharField(source='get_priority_display', read_only=True)
    
    class Meta:
        model = SLAPolicy
        fields = [
            'id', 'name', 'description', 'priority', 'priority_display',
            'department', 'department_name', 'category', 'category_name',
            'response_time', 'resolution_time', 'business_hours_only',
            'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class TicketStatsSerializer(serializers.Serializer):
    """سریالایزر آمار تیکت‌ها"""
    total_tickets = serializers.IntegerField()
    open_tickets = serializers.IntegerField()
    in_progress_tickets = serializers.IntegerField()
    waiting_tickets = serializers.IntegerField()
    resolved_tickets = serializers.IntegerField()
    closed_tickets = serializers.IntegerField()
    sla_breached = serializers.IntegerField()
    avg_response_time = serializers.DurationField(allow_null=True)
    avg_resolution_time = serializers.DurationField(allow_null=True)
    satisfaction_avg = serializers.FloatField(allow_null=True)


class ForwardTicketSerializer(serializers.Serializer):
    """سریالایزر فوروارد تیکت"""
    to_agent = serializers.UUIDField(required=False)
    to_department = serializers.UUIDField(required=False)
    reason = serializers.CharField(required=False, allow_blank=True)
    
    def validate(self, data):
        if not data.get('to_agent') and not data.get('to_department'):
            raise serializers.ValidationError('باید کارشناس یا دپارتمان مقصد مشخص شود')
        return data
