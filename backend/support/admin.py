from django.contrib import admin
from django import forms
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from django.db.models import Count
from django.utils import timezone
from .models import (
    TicketDepartment, TicketCategory, Ticket, TicketMessage,
    TicketAttachment, TicketForward, TicketHistory, CannedResponse,
    TicketTag, SLAPolicy
)
from .admin_custom import CustomTicketAdmin


# Inline classes حذف شدند - از template سفارشی استفاده می‌شود


@admin.register(TicketDepartment)
class TicketDepartmentAdmin(admin.ModelAdmin):
    list_display = ['name', 'manager', 'agents_count', 'open_tickets_count', 'is_active', 'is_public', 'priority']
    list_filter = ['is_active', 'is_public', 'auto_assign']
    search_fields = ['name', 'description']
    filter_horizontal = ['agents']
    ordering = ['-priority', 'name']
    
    # حذف تب‌ها - همه فیلدها در یک صفحه
    fields = ('name', 'description', 'email', 'manager', 'agents', 'is_active', 'is_public', 'auto_assign', 'priority')
    
    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        # تغییر ویجت description به 2 سطری با عرض مناسب
        if 'description' in form.base_fields:
            form.base_fields['description'].widget = forms.Textarea(attrs={'rows': 2, 'style': 'width: 100%; max-width: 600px;'})
        return form
    
    def agents_count(self, obj):
        return obj.agents.count()
    agents_count.short_description = _('تعداد کارشناسان')
    
    def open_tickets_count(self, obj):
        return obj.tickets.filter(status__in=['open', 'in_progress', 'waiting']).count()
    open_tickets_count.short_description = _('تیکت‌های باز')


@admin.register(TicketCategory)
class TicketCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'parent', 'default_department', 'default_priority', 'color_display', 'is_active', 'order']
    list_filter = ['is_active', 'default_priority', 'default_department']
    search_fields = ['name', 'description']
    ordering = ['order', 'name']
    
    fieldsets = (
        (None, {
            'fields': ('name', 'description', 'parent')
        }),
        (_('نمایش'), {
            'fields': ('icon', 'color', 'order')
        }),
        (_('پیش‌فرض‌ها'), {
            'fields': ('default_department', 'default_priority')
        }),
        (_('وضعیت'), {
            'fields': ('is_active',)
        }),
    )
    
    def color_display(self, obj):
        return format_html(
            '<span style="background-color: {}; padding: 2px 10px; border-radius: 3px;">{}</span>',
            obj.color, obj.color
        )
    color_display.short_description = _('رنگ')


@admin.register(Ticket)
class TicketAdmin(CustomTicketAdmin):
    """Admin برای مدل Ticket - از CustomTicketAdmin ارث‌بری می‌کند"""
    pass


@admin.register(TicketMessage)
class TicketMessageAdmin(admin.ModelAdmin):
    list_display = ['ticket', 'sender', 'message_type', 'is_staff_reply', 'created_at']
    list_filter = ['message_type', 'is_staff_reply', 'created_at']
    search_fields = ['ticket__ticket_number', 'content']
    readonly_fields = ['ticket', 'sender', 'is_staff_reply', 'created_at', 'updated_at']
    raw_id_fields = ['ticket', 'sender']
    ordering = ['-created_at']


@admin.register(TicketAttachment)
class TicketAttachmentAdmin(admin.ModelAdmin):
    list_display = ['file_name', 'ticket', 'message', 'uploaded_by', 'file_size_display', 'mime_type', 'created_at']
    list_filter = ['mime_type', 'created_at']
    search_fields = ['file_name', 'ticket__ticket_number']
    readonly_fields = ['uploaded_by', 'file_size', 'mime_type', 'created_at']
    raw_id_fields = ['ticket', 'message', 'uploaded_by']
    ordering = ['-created_at']
    
    def file_size_display(self, obj):
        if obj.file_size < 1024:
            return f'{obj.file_size} B'
        elif obj.file_size < 1024 * 1024:
            return f'{obj.file_size / 1024:.1f} KB'
        else:
            return f'{obj.file_size / (1024 * 1024):.1f} MB'
    file_size_display.short_description = _('حجم')


@admin.register(TicketForward)
class TicketForwardAdmin(admin.ModelAdmin):
    list_display = ['ticket', 'from_agent', 'to_agent', 'to_department', 'created_at']
    list_filter = ['to_department', 'created_at']
    search_fields = ['ticket__ticket_number', 'reason']
    readonly_fields = ['ticket', 'from_agent', 'created_at']
    raw_id_fields = ['ticket', 'from_agent', 'to_agent']
    ordering = ['-created_at']


@admin.register(TicketHistory)
class TicketHistoryAdmin(admin.ModelAdmin):
    list_display = ['ticket', 'user', 'action', 'description', 'created_at']
    list_filter = ['action', 'created_at']
    search_fields = ['ticket__ticket_number', 'description']
    readonly_fields = ['ticket', 'user', 'action', 'old_value', 'new_value', 'description', 'created_at']
    raw_id_fields = ['ticket', 'user']
    ordering = ['-created_at']
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False


@admin.register(CannedResponse)
class CannedResponseAdmin(admin.ModelAdmin):
    list_display = ['title', 'category', 'department', 'created_by', 'usage_count', 'is_public', 'is_active']
    list_filter = ['is_public', 'is_active', 'category', 'department']
    search_fields = ['title', 'content']
    readonly_fields = ['created_by', 'usage_count', 'created_at', 'updated_at']
    ordering = ['-usage_count', 'title']
    
    fieldsets = (
        (None, {
            'fields': ('title', 'content')
        }),
        (_('دسته‌بندی'), {
            'fields': ('category', 'department')
        }),
        (_('تنظیمات'), {
            'fields': ('is_public', 'is_active')
        }),
        (_('آمار'), {
            'fields': ('created_by', 'usage_count', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(TicketTag)
class TicketTagAdmin(admin.ModelAdmin):
    list_display = ['name', 'color_display', 'is_active', 'created_at']
    list_filter = ['is_active']
    search_fields = ['name', 'description']
    ordering = ['name']
    
    def color_display(self, obj):
        return format_html(
            '<span style="background-color: {}; color: white; padding: 2px 10px; border-radius: 3px;">{}</span>',
            obj.color, obj.name
        )
    color_display.short_description = _('تگ')


class SLAPolicyAdminForm(forms.ModelForm):
    """فرم سفارشی برای SLA Policy با اولویت چندانتخابی"""
    priority = forms.MultipleChoiceField(
        choices=Ticket.PRIORITY_CHOICES,
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label=_('اولویت'),
        help_text=_('می‌توانید چند اولویت انتخاب کنید')
    )
    
    class Meta:
        model = SLAPolicy
        fields = '__all__'
        widgets = {
            'description': forms.Textarea(attrs={'rows': 2, 'cols': 80}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            # بارگذاری مقادیر اولویت از JSONField
            if isinstance(self.instance.priority, list):
                self.initial['priority'] = self.instance.priority
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        # ذخیره اولویت‌های انتخاب شده به صورت لیست
        instance.priority = list(self.cleaned_data.get('priority', []))
        if commit:
            instance.save()
        return instance


@admin.register(SLAPolicy)
class SLAPolicyAdmin(admin.ModelAdmin):
    form = SLAPolicyAdminForm
    list_display = ['name', 'priority_display', 'department', 'response_time_display', 'resolution_time_display', 'is_active']
    list_filter = ['is_active', 'department']
    search_fields = ['name', 'description']
    ordering = ['name']
    
    # همه فیلدها در یک صفحه - بدون تب
    fields = ('name', 'description', 'priority', 'department', 'response_time', 'resolution_time', 'is_active')
    
    def priority_display(self, obj):
        if obj.priority and isinstance(obj.priority, list) and len(obj.priority) > 0:
            priority_dict = dict(Ticket.PRIORITY_CHOICES)
            priorities = [str(priority_dict.get(p, p)) for p in obj.priority]
            return ', '.join(priorities)
        return '-'
    priority_display.short_description = _('اولویت')
    
    def response_time_display(self, obj):
        hours = obj.response_time // 60
        minutes = obj.response_time % 60
        if hours > 0:
            return f'{hours} ساعت و {minutes} دقیقه' if minutes else f'{hours} ساعت'
        return f'{minutes} دقیقه'
    response_time_display.short_description = _('زمان پاسخ')
    
    def resolution_time_display(self, obj):
        hours = obj.resolution_time // 60
        minutes = obj.resolution_time % 60
        if hours > 0:
            return f'{hours} ساعت و {minutes} دقیقه' if minutes else f'{hours} ساعت'
        return f'{minutes} دقیقه'
    resolution_time_display.short_description = _('زمان حل')
