from django.db import models
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
import uuid
import json

User = get_user_model()


class Conversation(models.Model):
    """محلی conversation tracking که با RAG Core همگام می‌شود"""
    RESPONSE_MODE_CHOICES = [
        ('simple_explanation', _('توضیح ساده')),
        ('legal_reference', _('ارجاع قانونی دقیق')),
        ('action_checklist', _('چک‌لیست اقدام')),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='conversations')
    organization = models.ForeignKey('accounts.Organization', on_delete=models.SET_NULL, null=True, blank=True)
    
    # شناسه conversation در سیستم RAG Core
    rag_conversation_id = models.CharField(max_length=255, blank=True, db_index=True)
    
    # متادیتا
    title = models.CharField(max_length=255, default=_('گفتگوی جدید'))
    description = models.TextField(blank=True)
    tags = models.JSONField(default=list, blank=True)
    
    # تنظیمات
    default_response_mode = models.CharField(
        max_length=20,
        choices=RESPONSE_MODE_CHOICES,
        default='simple_explanation'
    )
    
    # سازماندهی
    folder = models.ForeignKey('ConversationFolder', on_delete=models.SET_NULL, null=True, blank=True)
    is_pinned = models.BooleanField(default=False)
    is_archived = models.BooleanField(default=False)
    is_shared = models.BooleanField(default=False)
    share_token = models.CharField(max_length=64, blank=True, unique=True, null=True)
    
    # آمار
    message_count = models.IntegerField(default=0)
    token_usage = models.IntegerField(default=0)
    last_message_at = models.DateTimeField(null=True, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-last_message_at', '-created_at']
        indexes = [
            models.Index(fields=['user', '-last_message_at']),
            models.Index(fields=['rag_conversation_id']),
        ]
        verbose_name = _('گفتگو')
        verbose_name_plural = _('گفتگوها')
    
    def __str__(self):
        return f"{self.title} - {self.user.email}"


class Message(models.Model):
    """پیام‌های فردی در گفتگوها"""
    ROLE_CHOICES = [
        ('user', _('کاربر')),
        ('assistant', _('دستیار')),
        ('system', _('سیستم')),
    ]
    
    STATUS_CHOICES = [
        ('pending', _('در انتظار')),
        ('processing', _('در حال پردازش')),
        ('completed', _('تکمیل شده')),
        ('failed', _('خطا')),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='messages')
    
    # شناسه پیام در RAG Core
    rag_message_id = models.CharField(max_length=255, blank=True, db_index=True)
    
    # محتوا
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    content = models.TextField()
    
    # حالت پاسخ (برای پیام‌های کاربر)
    response_mode = models.CharField(
        max_length=20,
        choices=Conversation.RESPONSE_MODE_CHOICES,
        blank=True
    )
    
    # منابع (برای پاسخ‌های دستیار)
    sources = models.JSONField(default=list, blank=True)
    chunks = models.JSONField(default=list, blank=True)
    
    # متادیتا اضافی (برای ذخیره file_analysis و سایر اطلاعات)
    metadata = models.JSONField(default=dict, blank=True)
    
    # وضعیت
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    error_message = models.TextField(blank=True)
    
    # آمار
    tokens = models.IntegerField(default=0)
    processing_time_ms = models.IntegerField(default=0)
    model_used = models.CharField(max_length=50, blank=True)
    cached = models.BooleanField(default=False)
    
    # بازخورد کاربر
    rating = models.IntegerField(null=True, blank=True)  # 1-5
    feedback_type = models.CharField(max_length=50, blank=True)
    feedback_text = models.TextField(blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['conversation', 'created_at']),
            models.Index(fields=['rag_message_id']),
        ]
        verbose_name = _('پیام')
        verbose_name_plural = _('پیام‌ها')
    
    def __str__(self):
        return f"{self.role}: {self.content[:50]}..."


class ConversationFolder(models.Model):
    """پوشه‌ها برای سازماندهی گفتگوها"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='conversation_folders')
    name = models.CharField(max_length=255)
    color = models.CharField(max_length=7, default='#3B82F6')  # Hex color
    icon = models.CharField(max_length=50, default='folder')
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='children')
    order = models.IntegerField(default=0)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['order', 'name']
        unique_together = ['user', 'name', 'parent']
        verbose_name = _('پوشه گفتگو')
        verbose_name_plural = _('پوشه‌های گفتگو')
    
    def __str__(self):
        return self.name


class ChatTemplate(models.Model):
    """قالب‌های پیش‌تعریف برای شروع گفتگو"""
    CATEGORY_CHOICES = [
        ('legal', _('حقوقی')),
        ('business', _('کسب‌وکار')),
        ('tax', _('مالیاتی')),
        ('insurance', _('بیمه')),
        ('labor', _('کار و استخدام')),
        ('contract', _('قراردادها')),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=255)
    description = models.TextField()
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    prompt_template = models.TextField()
    variables = models.JSONField(default=list)  # لیست متغیرهایی که کاربر باید پر کند
    icon = models.CharField(max_length=50, default='template')
    is_active = models.BooleanField(default=True)
    usage_count = models.IntegerField(default=0)
    
    # دسترسی
    is_public = models.BooleanField(default=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='chat_templates')
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-usage_count', 'category', 'title']
        verbose_name = _('قالب چت')
        verbose_name_plural = _('قالب‌های چت')
    
    def __str__(self):
        return f"{self.title} ({self.get_category_display()})"


class SharedConversation(models.Model):
    """گفتگوهای به اشتراک گذاشته شده"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='shares')
    shared_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='shared_conversations')
    share_token = models.CharField(max_length=64, unique=True)
    
    # تنظیمات اشتراک
    allow_copy = models.BooleanField(default=True)
    allow_export = models.BooleanField(default=False)
    password_protected = models.BooleanField(default=False)
    password_hash = models.CharField(max_length=255, blank=True)
    
    # انقضا
    expires_at = models.DateTimeField(null=True, blank=True)
    max_views = models.IntegerField(null=True, blank=True)
    view_count = models.IntegerField(default=0)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    last_viewed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = _('گفتگوی اشتراکی')
        verbose_name_plural = _('گفتگوهای اشتراکی')
    
    def is_expired(self):
        if self.expires_at and timezone.now() > self.expires_at:
            return True
        if self.max_views and self.view_count >= self.max_views:
            return True
        return False
    
    def __str__(self):
        return f"Share: {self.conversation.title}"


class MessageAttachment(models.Model):
    """فایل‌های پیوست پیام‌ها"""
    ATTACHMENT_TYPE_CHOICES = [
        ('document', _('سند')),
        ('image', _('تصویر')),
        ('pdf', _('PDF')),
        ('spreadsheet', _('صفحه گسترده')),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    message = models.ForeignKey(Message, on_delete=models.CASCADE, related_name='attachments')
    
    file = models.CharField(max_length=500)  # MinIO object key یا مسیر فایل
    file_name = models.CharField(max_length=500)  # افزایش برای نام فایل‌های طولانی
    file_size = models.IntegerField()  # in bytes
    file_type = models.CharField(max_length=20, choices=ATTACHMENT_TYPE_CHOICES)
    mime_type = models.CharField(max_length=200)  # افزایش برای mime type های طولانی
    
    # برای تصاویر
    thumbnail = models.ImageField(upload_to='chat/thumbnails/%Y/%m/', blank=True, null=True)
    
    # OCR یا استخراج متن
    extracted_text = models.TextField(blank=True)
    extraction_status = models.CharField(max_length=20, default='pending')
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['created_at']
        verbose_name = _('پیوست پیام')
        verbose_name_plural = _('پیوست‌های پیام')
    
    def __str__(self):
        return f"{self.file_name} - {self.message.id}"
