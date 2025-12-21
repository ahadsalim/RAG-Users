from django.db import models
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
import uuid
import secrets

User = get_user_model()


class TicketDepartment(models.Model):
    """
    دپارتمان‌های پشتیبانی
    مثال: فنی، مالی، فروش، عمومی
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, unique=True, verbose_name=_('نام دپارتمان'))
    description = models.TextField(blank=True, verbose_name=_('توضیحات'))
    email = models.EmailField(blank=True, verbose_name=_('ایمیل دپارتمان'))
    
    # مدیر دپارتمان
    manager = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='managed_departments',
        verbose_name=_('مدیر دپارتمان'),
        limit_choices_to={'is_staff': True}
    )
    
    # کارمندان این دپارتمان
    agents = models.ManyToManyField(
        User,
        blank=True,
        related_name='support_departments',
        verbose_name=_('کارشناسان'),
        limit_choices_to={'is_staff': True}
    )
    
    # تنظیمات
    is_active = models.BooleanField(default=True, verbose_name=_('فعال'))
    is_public = models.BooleanField(default=True, verbose_name=_('قابل مشاهده برای کاربران'))
    auto_assign = models.BooleanField(default=True, verbose_name=_('تخصیص خودکار'))
    priority = models.IntegerField(default=0, verbose_name=_('اولویت نمایش'))
    
    # SLA پیش‌فرض (به ساعت)
    default_response_time = models.IntegerField(
        default=24,
        verbose_name=_('زمان پاسخ‌دهی پیش‌فرض (ساعت)')
    )
    default_resolution_time = models.IntegerField(
        default=72,
        verbose_name=_('زمان حل مشکل پیش‌فرض (ساعت)')
    )
    
    # تاریخ‌ها
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('تاریخ ایجاد'))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_('تاریخ به‌روزرسانی'))
    
    class Meta:
        verbose_name = _('دپارتمان پشتیبانی')
        verbose_name_plural = _('دپارتمان‌های پشتیبانی')
        ordering = ['-priority', 'name']
    
    def __str__(self):
        return self.name
    
    def get_available_agents(self):
        """دریافت کارشناسان فعال این دپارتمان"""
        return self.agents.filter(is_active=True)
    
    def get_agent_with_least_tickets(self):
        """دریافت کارشناس با کمترین تیکت باز"""
        from django.db.models import Count
        agents = self.get_available_agents().annotate(
            open_tickets=Count('assigned_tickets', filter=models.Q(
                assigned_tickets__status__in=['open', 'in_progress', 'waiting']
            ))
        ).order_by('open_tickets')
        return agents.first()


class TicketCategory(models.Model):
    """
    دسته‌بندی تیکت‌ها
    مثال: مشکل فنی، سوال، پیشنهاد، شکایت
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, verbose_name=_('نام دسته‌بندی'))
    description = models.TextField(blank=True, verbose_name=_('توضیحات'))
    icon = models.CharField(max_length=50, default='tag', verbose_name=_('آیکون'))
    color = models.CharField(max_length=7, default='#3B82F6', verbose_name=_('رنگ'))
    
    # دپارتمان پیش‌فرض
    default_department = models.ForeignKey(
        TicketDepartment,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='categories',
        verbose_name=_('دپارتمان پیش‌فرض')
    )
    
    # اولویت پیش‌فرض
    PRIORITY_CHOICES = [
        ('low', _('کم')),
        ('medium', _('متوسط')),
        ('high', _('بالا')),
        ('urgent', _('فوری')),
    ]
    default_priority = models.CharField(
        max_length=10,
        choices=PRIORITY_CHOICES,
        default='medium',
        verbose_name=_('اولویت پیش‌فرض')
    )
    
    # سلسله مراتب
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='children',
        verbose_name=_('دسته‌بندی والد')
    )
    
    is_active = models.BooleanField(default=True, verbose_name=_('فعال'))
    order = models.IntegerField(default=0, verbose_name=_('ترتیب'))
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('تاریخ ایجاد'))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_('تاریخ به‌روزرسانی'))
    
    class Meta:
        verbose_name = _('دسته‌بندی تیکت')
        verbose_name_plural = _('دسته‌بندی‌های تیکت')
        ordering = ['order', 'name']
    
    def __str__(self):
        if self.parent:
            return f"{self.parent.name} > {self.name}"
        return self.name


class Ticket(models.Model):
    """
    مدل اصلی تیکت پشتیبانی
    """
    STATUS_CHOICES = [
        ('open', _('باز')),
        ('in_progress', _('در حال بررسی')),
        ('waiting', _('در انتظار پاسخ کاربر')),
        ('answered', _('پاسخ داده شده')),
        ('closed', _('بسته شده')),
    ]
    
    PRIORITY_CHOICES = [
        ('low', _('کم')),
        ('medium', _('متوسط')),
        ('high', _('بالا')),
        ('urgent', _('فوری')),
    ]
    
    SOURCE_CHOICES = [
        ('web', _('وب‌سایت')),
        ('email', _('ایمیل')),
        ('phone', _('تلفن')),
        ('chat', _('چت')),
        ('api', _('API')),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # شماره تیکت (قابل خواندن)
    ticket_number = models.CharField(
        max_length=20,
        unique=True,
        verbose_name=_('شماره تیکت'),
        editable=False
    )
    
    # کاربر ایجادکننده
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='tickets',
        verbose_name=_('کاربر')
    )
    
    # سازمان (اگر کاربر حقوقی باشد)
    organization = models.ForeignKey(
        'accounts.Organization',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='tickets',
        verbose_name=_('سازمان')
    )
    
    # اطلاعات اصلی
    subject = models.CharField(max_length=255, verbose_name=_('موضوع'))
    description = models.TextField(verbose_name=_('توضیحات'))
    
    # دسته‌بندی و دپارتمان
    category = models.ForeignKey(
        TicketCategory,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='tickets',
        verbose_name=_('دسته‌بندی')
    )
    department = models.ForeignKey(
        TicketDepartment,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='tickets',
        verbose_name=_('دپارتمان')
    )
    
    # وضعیت و اولویت
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='open',
        verbose_name=_('وضعیت')
    )
    priority = models.CharField(
        max_length=10,
        choices=PRIORITY_CHOICES,
        default='medium',
        verbose_name=_('اولویت')
    )
    
    # منبع تیکت
    source = models.CharField(
        max_length=20,
        choices=SOURCE_CHOICES,
        default='web',
        verbose_name=_('منبع')
    )
    
    # تخصیص به کارشناس
    assigned_to = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_tickets',
        verbose_name=_('کارشناس مسئول'),
        limit_choices_to={'is_staff': True}
    )
    
    # تگ‌ها
    tags = models.JSONField(default=list, blank=True, verbose_name=_('تگ‌ها'))
    
    # SLA
    response_due = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_('مهلت پاسخ‌دهی')
    )
    resolution_due = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_('مهلت حل مشکل')
    )
    first_response_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_('زمان اولین پاسخ')
    )
    resolved_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_('زمان حل مشکل')
    )
    
    # امتیاز رضایت کاربر
    satisfaction_rating = models.IntegerField(
        null=True,
        blank=True,
        verbose_name=_('امتیاز رضایت'),
        help_text=_('از 1 تا 5')
    )
    satisfaction_feedback = models.TextField(
        blank=True,
        verbose_name=_('بازخورد رضایت')
    )
    
    # متادیتا
    metadata = models.JSONField(default=dict, blank=True, verbose_name=_('متادیتا'))
    
    # آیا کاربر پاسخ جدید خوانده؟
    user_read = models.BooleanField(default=True, verbose_name=_('خوانده شده توسط کاربر'))
    staff_read = models.BooleanField(default=False, verbose_name=_('خوانده شده توسط کارشناس'))
    
    # تاریخ‌ها
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('تاریخ ایجاد'))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_('تاریخ به‌روزرسانی'))
    closed_at = models.DateTimeField(null=True, blank=True, verbose_name=_('تاریخ بسته شدن'))
    
    class Meta:
        verbose_name = _('تیکت')
        verbose_name_plural = _('تیکت‌ها')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['assigned_to', 'status']),
            models.Index(fields=['department', 'status']),
            models.Index(fields=['ticket_number']),
            models.Index(fields=['status', '-priority', '-created_at']),
        ]
    
    def __str__(self):
        return f"#{self.ticket_number} - {self.subject}"
    
    def save(self, *args, **kwargs):
        if not self.ticket_number:
            self.ticket_number = self.generate_ticket_number()
        
        # تنظیم SLA در صورت عدم وجود
        if not self.response_due and self.department:
            self.response_due = timezone.now() + timezone.timedelta(
                hours=self.department.default_response_time
            )
        if not self.resolution_due and self.department:
            self.resolution_due = timezone.now() + timezone.timedelta(
                hours=self.department.default_resolution_time
            )
        
        # تنظیم تاریخ بسته شدن
        if self.status == 'closed' and not self.closed_at:
            self.closed_at = timezone.now()
        elif self.status != 'closed':
            self.closed_at = None
        
        # تنظیم تاریخ حل شدن
        if self.status in ['resolved', 'closed'] and not self.resolved_at:
            self.resolved_at = timezone.now()
        
        super().save(*args, **kwargs)
    
    @staticmethod
    def generate_ticket_number():
        """تولید شماره تیکت یکتا"""
        from datetime import datetime
        prefix = datetime.now().strftime('%y%m')
        random_part = secrets.token_hex(3).upper()
        return f"TK{prefix}{random_part}"
    
    def is_sla_breached(self):
        """بررسی نقض SLA"""
        now = timezone.now()
        if self.response_due and not self.first_response_at and now > self.response_due:
            return True
        if self.resolution_due and not self.resolved_at and now > self.resolution_due:
            return True
        return False
    
    def get_response_time(self):
        """محاسبه زمان پاسخ‌دهی"""
        if self.first_response_at:
            return self.first_response_at - self.created_at
        return None
    
    def get_resolution_time(self):
        """محاسبه زمان حل مشکل"""
        if self.resolved_at:
            return self.resolved_at - self.created_at
        return None


class TicketMessage(models.Model):
    """
    پیام‌های تیکت (مکالمات)
    """
    MESSAGE_TYPE_CHOICES = [
        ('reply', _('پاسخ')),
        ('note', _('یادداشت داخلی')),
        ('question', _('سوال از کاربر')),
        ('send_to', _('ارسال به')),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    ticket = models.ForeignKey(
        Ticket,
        on_delete=models.CASCADE,
        related_name='messages',
        verbose_name=_('تیکت')
    )
    
    # نویسنده پیام
    sender = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='ticket_messages',
        verbose_name=_('فرستنده')
    )
    
    # محتوا
    content = models.TextField(verbose_name=_('محتوا'))
    
    # نوع پیام
    message_type = models.CharField(
        max_length=20,
        choices=MESSAGE_TYPE_CHOICES,
        default='reply',
        verbose_name=_('نوع پیام')
    )
    
    # آیا پیام از طرف کارشناس است؟
    is_staff_reply = models.BooleanField(default=False, verbose_name=_('پاسخ کارشناس'))
    
    # کارشناس مقصد (برای نوع send_to)
    forwarded_to = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='forwarded_ticket_messages',
        verbose_name=_('ارسال شده به'),
        limit_choices_to={'is_staff': True}
    )
    
    # متادیتا
    metadata = models.JSONField(default=dict, blank=True, verbose_name=_('متادیتا'))
    
    # تاریخ‌ها
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('تاریخ ایجاد'))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_('تاریخ به‌روزرسانی'))
    
    class Meta:
        verbose_name = _('پیام تیکت')
        verbose_name_plural = _('پیام‌های تیکت')
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['ticket', 'created_at']),
        ]
    
    def __str__(self):
        return f"پیام در {self.ticket.ticket_number}"
    
    def save(self, *args, **kwargs):
        # تعیین is_staff_reply
        if self.sender and self.sender.is_staff:
            self.is_staff_reply = True
        
        super().save(*args, **kwargs)
        
        # به‌روزرسانی تیکت
        self.ticket.updated_at = timezone.now()
        
        # اگر اولین پاسخ کارشناس است
        if self.is_staff_reply and not self.ticket.first_response_at:
            self.ticket.first_response_at = self.created_at
        
        # تنظیم وضعیت خوانده شدن
        if self.is_staff_reply:
            self.ticket.user_read = False
        else:
            self.ticket.staff_read = False
        
        self.ticket.save(update_fields=['updated_at', 'first_response_at', 'user_read', 'staff_read'])


class TicketAttachment(models.Model):
    """
    فایل‌های پیوست تیکت
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # می‌تواند به تیکت یا پیام متصل باشد
    ticket = models.ForeignKey(
        Ticket,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='attachments',
        verbose_name=_('تیکت')
    )
    message = models.ForeignKey(
        TicketMessage,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='attachments',
        verbose_name=_('پیام')
    )
    
    # آپلودکننده
    uploaded_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='ticket_attachments',
        verbose_name=_('آپلودکننده')
    )
    
    # اطلاعات فایل
    file = models.FileField(
        upload_to='support/attachments/%Y/%m/',
        verbose_name=_('فایل')
    )
    file_name = models.CharField(max_length=255, verbose_name=_('نام فایل'))
    file_size = models.IntegerField(verbose_name=_('حجم فایل'))
    mime_type = models.CharField(max_length=100, verbose_name=_('نوع فایل'))
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('تاریخ آپلود'))
    
    class Meta:
        verbose_name = _('پیوست تیکت')
        verbose_name_plural = _('پیوست‌های تیکت')
        ordering = ['-created_at']
    
    def __str__(self):
        return self.file_name


class TicketForward(models.Model):
    """
    فوروارد تیکت به کارشناس دیگر
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    ticket = models.ForeignKey(
        Ticket,
        on_delete=models.CASCADE,
        related_name='forwards',
        verbose_name=_('تیکت')
    )
    
    # از کی به کی
    from_agent = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='forwarded_tickets',
        verbose_name=_('از کارشناس')
    )
    to_agent = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='received_forwards',
        verbose_name=_('به کارشناس')
    )
    to_department = models.ForeignKey(
        TicketDepartment,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='received_forwards',
        verbose_name=_('به دپارتمان')
    )
    
    # دلیل فوروارد
    reason = models.TextField(blank=True, verbose_name=_('دلیل'))
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('تاریخ فوروارد'))
    
    class Meta:
        verbose_name = _('فوروارد تیکت')
        verbose_name_plural = _('فوروارد‌های تیکت')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"فوروارد {self.ticket.ticket_number}"


class TicketHistory(models.Model):
    """
    تاریخچه تغییرات تیکت
    """
    ACTION_CHOICES = [
        ('created', _('ایجاد شد')),
        ('status_changed', _('تغییر وضعیت')),
        ('priority_changed', _('تغییر اولویت')),
        ('assigned', _('تخصیص داده شد')),
        ('forwarded', _('فوروارد شد')),
        ('department_changed', _('تغییر دپارتمان')),
        ('category_changed', _('تغییر دسته‌بندی')),
        ('message_added', _('پیام اضافه شد')),
        ('attachment_added', _('پیوست اضافه شد')),
        ('merged', _('ادغام شد')),
        ('split', _('تفکیک شد')),
        ('reopened', _('بازگشایی شد')),
        ('closed', _('بسته شد')),
        ('rated', _('امتیاز داده شد')),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    ticket = models.ForeignKey(
        Ticket,
        on_delete=models.CASCADE,
        related_name='history',
        verbose_name=_('تیکت')
    )
    
    # کاربر انجام‌دهنده
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='ticket_history_actions',
        verbose_name=_('کاربر')
    )
    
    action = models.CharField(
        max_length=30,
        choices=ACTION_CHOICES,
        verbose_name=_('عملیات')
    )
    
    # جزئیات تغییر
    old_value = models.JSONField(null=True, blank=True, verbose_name=_('مقدار قبلی'))
    new_value = models.JSONField(null=True, blank=True, verbose_name=_('مقدار جدید'))
    description = models.TextField(blank=True, verbose_name=_('توضیحات'))
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('تاریخ'))
    
    class Meta:
        verbose_name = _('تاریخچه تیکت')
        verbose_name_plural = _('تاریخچه تیکت‌ها')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['ticket', '-created_at']),
        ]
    
    def __str__(self):
        return f"{self.ticket.ticket_number} - {self.get_action_display()}"


class CannedResponse(models.Model):
    """
    پاسخ‌های آماده برای کارشناسان
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    title = models.CharField(max_length=255, verbose_name=_('عنوان'))
    content = models.TextField(verbose_name=_('محتوا'))
    
    # دسته‌بندی
    category = models.ForeignKey(
        TicketCategory,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='canned_responses',
        verbose_name=_('دسته‌بندی')
    )
    
    # دپارتمان
    department = models.ForeignKey(
        TicketDepartment,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='canned_responses',
        verbose_name=_('دپارتمان')
    )
    
    # ایجادکننده
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='canned_responses',
        verbose_name=_('ایجادکننده')
    )
    
    # دسترسی
    is_public = models.BooleanField(default=True, verbose_name=_('عمومی'))
    is_active = models.BooleanField(default=True, verbose_name=_('فعال'))
    
    # آمار استفاده
    usage_count = models.IntegerField(default=0, verbose_name=_('تعداد استفاده'))
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('تاریخ ایجاد'))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_('تاریخ به‌روزرسانی'))
    
    class Meta:
        verbose_name = _('پاسخ آماده')
        verbose_name_plural = _('پاسخ‌های آماده')
        ordering = ['-usage_count', 'title']
    
    def __str__(self):
        return self.title


class TicketTag(models.Model):
    """
    تگ‌های تیکت
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=50, unique=True, verbose_name=_('نام تگ'))
    color = models.CharField(max_length=7, default='#6B7280', verbose_name=_('رنگ'))
    description = models.TextField(blank=True, verbose_name=_('توضیحات'))
    
    is_active = models.BooleanField(default=True, verbose_name=_('فعال'))
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('تاریخ ایجاد'))
    
    class Meta:
        verbose_name = _('تگ تیکت')
        verbose_name_plural = _('تگ‌های تیکت')
        ordering = ['name']
    
    def __str__(self):
        return self.name


class SLAPolicy(models.Model):
    """
    سیاست‌های SLA
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, verbose_name=_('نام سیاست'))
    description = models.TextField(blank=True, verbose_name=_('توضیحات'))
    
    # شرایط اعمال
    priority = models.CharField(
        max_length=10,
        choices=Ticket.PRIORITY_CHOICES,
        null=True,
        blank=True,
        verbose_name=_('اولویت')
    )
    department = models.ForeignKey(
        TicketDepartment,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='sla_policies',
        verbose_name=_('دپارتمان')
    )
    category = models.ForeignKey(
        TicketCategory,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='sla_policies',
        verbose_name=_('دسته‌بندی')
    )
    
    # زمان‌ها (به دقیقه)
    response_time = models.IntegerField(
        verbose_name=_('زمان پاسخ‌دهی (دقیقه)')
    )
    resolution_time = models.IntegerField(
        verbose_name=_('زمان حل مشکل (دقیقه)')
    )
    
    # فقط ساعات کاری
    business_hours_only = models.BooleanField(
        default=True,
        verbose_name=_('فقط ساعات کاری')
    )
    
    is_active = models.BooleanField(default=True, verbose_name=_('فعال'))
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('تاریخ ایجاد'))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_('تاریخ به‌روزرسانی'))
    
    class Meta:
        verbose_name = _('سیاست SLA')
        verbose_name_plural = _('سیاست‌های SLA')
        ordering = ['name']
    
    def __str__(self):
        return self.name
