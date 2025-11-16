"""
Serializers برای ماژول چت
"""
from rest_framework import serializers
from django.utils.translation import gettext_lazy as _
from .models import (
    Conversation, Message, ConversationFolder, 
    ChatTemplate, SharedConversation, MessageAttachment
)


class MessageAttachmentSerializer(serializers.ModelSerializer):
    """Serializer برای پیوست‌های پیام"""
    
    class Meta:
        model = MessageAttachment
        fields = [
            'id', 'file', 'file_name', 'file_size', 'file_type',
            'mime_type', 'thumbnail', 'extracted_text', 'extraction_status',
            'created_at'
        ]
        read_only_fields = ['id', 'thumbnail', 'extracted_text', 'extraction_status']


class MessageSerializer(serializers.ModelSerializer):
    """Serializer برای پیام‌ها"""
    attachments = MessageAttachmentSerializer(many=True, read_only=True)
    
    class Meta:
        model = Message
        fields = [
            'id', 'conversation', 'rag_message_id', 'role', 'content',
            'response_mode', 'sources', 'chunks', 'status', 'error_message',
            'tokens', 'processing_time_ms', 'model_used', 'cached',
            'rating', 'feedback_type', 'feedback_text',
            'attachments', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'rag_message_id', 'sources', 'chunks', 'status',
            'error_message', 'tokens', 'processing_time_ms', 'model_used',
            'cached', 'created_at', 'updated_at'
        ]


class ConversationSerializer(serializers.ModelSerializer):
    """Serializer برای گفتگوها"""
    last_message = serializers.SerializerMethodField()
    unread_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Conversation
        fields = [
            'id', 'user', 'organization', 'rag_conversation_id', 'title',
            'description', 'tags', 'default_response_mode', 'folder',
            'is_pinned', 'is_archived', 'is_shared', 'share_token',
            'message_count', 'token_usage', 'last_message_at',
            'last_message', 'unread_count', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'user', 'organization', 'rag_conversation_id',
            'share_token', 'message_count', 'token_usage', 'last_message_at',
            'created_at', 'updated_at'
        ]
    
    def get_last_message(self, obj):
        """دریافت آخرین پیام گفتگو"""
        last_msg = obj.messages.order_by('-created_at').first()
        if last_msg:
            return {
                'role': last_msg.role,
                'content': last_msg.content[:100] + '...' if len(last_msg.content) > 100 else last_msg.content,
                'created_at': last_msg.created_at
            }
        return None
    
    def get_unread_count(self, obj):
        """تعداد پیام‌های خوانده نشده"""
        # این باید بر اساس last_seen کاربر محاسبه شود
        return 0


class ConversationDetailSerializer(ConversationSerializer):
    """Serializer جزئیات گفتگو با پیام‌ها"""
    messages = MessageSerializer(many=True, read_only=True)
    
    class Meta(ConversationSerializer.Meta):
        fields = ConversationSerializer.Meta.fields + ['messages']


class ConversationFolderSerializer(serializers.ModelSerializer):
    """Serializer برای پوشه‌های گفتگو"""
    conversations_count = serializers.SerializerMethodField()
    
    class Meta:
        model = ConversationFolder
        fields = [
            'id', 'name', 'color', 'icon', 'parent', 'order',
            'conversations_count', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_conversations_count(self, obj):
        return obj.conversation_set.count()


class ChatTemplateSerializer(serializers.ModelSerializer):
    """Serializer برای قالب‌های چت"""
    category_display = serializers.CharField(source='get_category_display', read_only=True)
    
    class Meta:
        model = ChatTemplate
        fields = [
            'id', 'title', 'description', 'category', 'category_display',
            'prompt_template', 'variables', 'icon', 'is_active',
            'usage_count', 'is_public', 'created_by', 'created_at'
        ]
        read_only_fields = ['id', 'usage_count', 'created_at']


class SharedConversationSerializer(serializers.ModelSerializer):
    """Serializer برای گفتگوهای اشتراکی"""
    conversation_title = serializers.CharField(source='conversation.title', read_only=True)
    
    class Meta:
        model = SharedConversation
        fields = [
            'id', 'conversation', 'conversation_title', 'share_token',
            'allow_copy', 'allow_export', 'password_protected',
            'expires_at', 'max_views', 'view_count',
            'created_at', 'last_viewed_at'
        ]
        read_only_fields = [
            'id', 'share_token', 'view_count', 'created_at', 'last_viewed_at'
        ]


class QueryRequestSerializer(serializers.Serializer):
    """Serializer برای درخواست پرسش"""
    query = serializers.CharField(required=True, min_length=3, max_length=5000)
    conversation_id = serializers.UUIDField(required=False, allow_null=True)
    response_mode = serializers.ChoiceField(
        choices=['simple_explanation', 'legal_reference', 'action_checklist'],
        default='simple_explanation'
    )
    max_results = serializers.IntegerField(default=5, min_value=1, max_value=20)
    use_cache = serializers.BooleanField(default=True)
    use_reranking = serializers.BooleanField(default=True)
    stream = serializers.BooleanField(default=False)
    
    # فیلترهای جستجو (اختیاری)
    filters = serializers.JSONField(required=False, default=dict)
    
    # تنظیمات LLM (اختیاری)
    llm_config = serializers.JSONField(required=False, default=dict)
    
    # Context اضافی
    context = serializers.JSONField(required=False, default=dict)
    
    def validate_query(self, value):
        """اعتبارسنجی متن سوال"""
        # حذف فضاهای خالی اضافی
        value = value.strip()
        
        # بررسی طول
        if len(value) < 3:
            raise serializers.ValidationError(_('سوال باید حداقل 3 کاراکتر داشته باشد'))
        
        if len(value) > 5000:
            raise serializers.ValidationError(_('سوال نباید بیشتر از 5000 کاراکتر باشد'))
        
        return value
    
    def validate_filters(self, value):
        """اعتبارسنجی فیلترها"""
        allowed_filters = [
            'document_type', 'jurisdiction', 'authority', 'date_range'
        ]
        
        for key in value.keys():
            if key not in allowed_filters:
                raise serializers.ValidationError(
                    f'فیلتر {key} مجاز نیست'
                )
        
        return value
    
    def validate_llm_config(self, value):
        """اعتبارسنجی تنظیمات LLM"""
        if 'temperature' in value:
            temp = value['temperature']
            if not (0 <= temp <= 2):
                raise serializers.ValidationError(
                    'temperature باید بین 0 و 2 باشد'
                )
        
        if 'max_tokens' in value:
            tokens = value['max_tokens']
            if not (100 <= tokens <= 8192):
                raise serializers.ValidationError(
                    'max_tokens باید بین 100 و 8192 باشد'
                )
        
        return value


class QueryResponseSerializer(serializers.Serializer):
    """Serializer برای پاسخ پرسش"""
    answer = serializers.CharField()
    sources = serializers.ListField(child=serializers.CharField())
    chunks = serializers.ListField(child=serializers.JSONField())
    metadata = serializers.JSONField()
    user_info = serializers.JSONField()
    conversation_id = serializers.UUIDField()
    message_id = serializers.UUIDField()


class MessageFeedbackSerializer(serializers.Serializer):
    """Serializer برای بازخورد پیام"""
    message_id = serializers.UUIDField(required=True)
    rating = serializers.IntegerField(min_value=1, max_value=5, required=False)
    feedback_type = serializers.ChoiceField(
        choices=['helpful', 'unhelpful', 'incorrect', 'incomplete'],
        required=False
    )
    feedback_text = serializers.CharField(max_length=1000, required=False)
    suggested_response = serializers.CharField(max_length=5000, required=False)
    
    def validate(self, attrs):
        """حداقل یکی از فیلدهای بازخورد باید پر شود"""
        if not any([
            attrs.get('rating'),
            attrs.get('feedback_type'),
            attrs.get('feedback_text'),
            attrs.get('suggested_response')
        ]):
            raise serializers.ValidationError(
                _('حداقل یکی از موارد بازخورد را وارد کنید')
            )
        return attrs


class ConversationExportSerializer(serializers.Serializer):
    """Serializer برای export گفتگو"""
    format = serializers.ChoiceField(
        choices=['json', 'pdf', 'docx', 'txt'],
        default='pdf'
    )
    include_sources = serializers.BooleanField(default=True)
    include_metadata = serializers.BooleanField(default=False)
    include_timestamps = serializers.BooleanField(default=True)


class BulkConversationActionSerializer(serializers.Serializer):
    """Serializer برای عملیات گروهی روی گفتگوها"""
    conversation_ids = serializers.ListField(
        child=serializers.UUIDField(),
        min_length=1,
        max_length=50
    )
    action = serializers.ChoiceField(
        choices=['archive', 'unarchive', 'delete', 'move_to_folder', 'tag']
    )
    folder_id = serializers.UUIDField(required=False)  # برای move_to_folder
    tags = serializers.ListField(
        child=serializers.CharField(max_length=50),
        required=False
    )  # برای tag action
