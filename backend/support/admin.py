from django.contrib import admin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from django.db.models import Count
from .models import (
    TicketDepartment, TicketCategory, Ticket, TicketMessage,
    TicketAttachment, TicketForward, TicketHistory, CannedResponse,
    TicketTag, SLAPolicy
)


class TicketMessageInline(admin.TabularInline):
    model = TicketMessage
    extra = 0
    readonly_fields = ['sender', 'message_type', 'is_staff_reply', 'created_at']
    fields = ['sender', 'content', 'message_type', 'is_staff_reply', 'created_at']
    ordering = ['created_at']
    
    def has_delete_permission(self, request, obj=None):
        return False


class TicketAttachmentInline(admin.TabularInline):
    model = TicketAttachment
    extra = 0
    readonly_fields = ['uploaded_by', 'file_name', 'file_size', 'mime_type', 'created_at']
    fields = ['file', 'file_name', 'file_size', 'mime_type', 'uploaded_by', 'created_at']


class TicketHistoryInline(admin.TabularInline):
    model = TicketHistory
    extra = 0
    readonly_fields = ['user', 'action', 'old_value', 'new_value', 'description', 'created_at']
    fields = ['action', 'user', 'description', 'old_value', 'new_value', 'created_at']
    ordering = ['-created_at']
    
    def has_add_permission(self, request, obj=None):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(TicketDepartment)
class TicketDepartmentAdmin(admin.ModelAdmin):
    list_display = ['name', 'manager', 'agents_count', 'open_tickets_count', 'is_active', 'is_public', 'priority']
    list_filter = ['is_active', 'is_public', 'auto_assign']
    search_fields = ['name', 'description']
    filter_horizontal = ['agents']
    ordering = ['-priority', 'name']
    
    fieldsets = (
        (None, {
            'fields': ('name', 'description', 'email')
        }),
        (_('مدیریت'), {
            'fields': ('manager', 'agents')
        }),
        (_('تنظیمات'), {
            'fields': ('is_active', 'is_public', 'auto_assign', 'priority')
        }),
        (_('SLA پیش‌فرض'), {
            'fields': ('default_response_time', 'default_resolution_time')
        }),
    )
    
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
class TicketAdmin(admin.ModelAdmin):
    list_display = [
        'ticket_number', 'subject', 'user', 'status_display', 'priority_display',
        'department', 'assigned_to', 'sla_status', 'created_at'
    ]
    list_filter = ['status', 'priority', 'department', 'category', 'source', 'created_at']
    search_fields = ['ticket_number', 'subject', 'description', 'user__phone_number', 'user__email']
    readonly_fields = [
        'ticket_number', 'user', 'organization', 'source',
        'first_response_at', 'resolved_at', 'closed_at',
        'created_at', 'updated_at'
    ]
    raw_id_fields = ['user', 'assigned_to']
    date_hierarchy = 'created_at'
    ordering = ['-created_at']
    
    inlines = [TicketMessageInline, TicketAttachmentInline, TicketHistoryInline]
    
    fieldsets = (
        (_('اطلاعات اصلی'), {
            'fields': ('ticket_number', 'user', 'organization', 'subject', 'description')
        }),
        (_('دسته‌بندی'), {
            'fields': ('category', 'department', 'tags')
        }),
        (_('وضعیت'), {
            'fields': ('status', 'priority', 'source', 'assigned_to')
        }),
        (_('SLA'), {
            'fields': ('response_due', 'resolution_due', 'first_response_at', 'resolved_at'),
            'classes': ('collapse',)
        }),
        (_('رضایت کاربر'), {
            'fields': ('satisfaction_rating', 'satisfaction_feedback'),
            'classes': ('collapse',)
        }),
        (_('تاریخ‌ها'), {
            'fields': ('created_at', 'updated_at', 'closed_at'),
            'classes': ('collapse',)
        }),
    )
    
    def status_display(self, obj):
        colors = {
            'open': '#22C55E',
            'in_progress': '#3B82F6',
            'waiting': '#F59E0B',
            'on_hold': '#6B7280',
            'resolved': '#8B5CF6',
            'closed': '#EF4444',
        }
        color = colors.get(obj.status, '#6B7280')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 2px 8px; border-radius: 3px;">{}</span>',
            color, obj.get_status_display()
        )
    status_display.short_description = _('وضعیت')
    
    def priority_display(self, obj):
        colors = {
            'low': '#6B7280',
            'medium': '#3B82F6',
            'high': '#F59E0B',
            'urgent': '#EF4444',
        }
        color = colors.get(obj.priority, '#6B7280')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 2px 8px; border-radius: 3px;">{}</span>',
            color, obj.get_priority_display()
        )
    priority_display.short_description = _('اولویت')
    
    def sla_status(self, obj):
        if obj.is_sla_breached():
            return format_html(
                '<span style="color: #EF4444; font-weight: bold;">⚠ نقض SLA</span>'
            )
        return format_html('<span style="color: #22C55E;">✓ عادی</span>')
    sla_status.short_description = _('وضعیت SLA')
    
    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        
        # ثبت تغییرات در تاریخچه
        if change:
            TicketHistory.objects.create(
                ticket=obj,
                user=request.user,
                action='status_changed' if 'status' in form.changed_data else 'admin_action',
                description=f'تغییر از پنل مدیریت: {", ".join(form.changed_data)}'
            )
    
    actions = ['mark_as_resolved', 'mark_as_closed', 'assign_to_me']
    
    @admin.action(description=_('علامت‌گذاری به عنوان حل شده'))
    def mark_as_resolved(self, request, queryset):
        from django.utils import timezone
        count = queryset.update(status='resolved', resolved_at=timezone.now())
        self.message_user(request, f'{count} تیکت به عنوان حل شده علامت‌گذاری شد.')
    
    @admin.action(description=_('بستن تیکت‌ها'))
    def mark_as_closed(self, request, queryset):
        from django.utils import timezone
        count = queryset.update(status='closed', closed_at=timezone.now())
        self.message_user(request, f'{count} تیکت بسته شد.')
    
    @admin.action(description=_('تخصیص به من'))
    def assign_to_me(self, request, queryset):
        count = queryset.update(assigned_to=request.user)
        self.message_user(request, f'{count} تیکت به شما تخصیص داده شد.')


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


@admin.register(SLAPolicy)
class SLAPolicyAdmin(admin.ModelAdmin):
    list_display = ['name', 'priority', 'department', 'category', 'response_time_display', 'resolution_time_display', 'is_active']
    list_filter = ['is_active', 'priority', 'department', 'business_hours_only']
    search_fields = ['name', 'description']
    ordering = ['name']
    
    fieldsets = (
        (None, {
            'fields': ('name', 'description')
        }),
        (_('شرایط اعمال'), {
            'fields': ('priority', 'department', 'category')
        }),
        (_('زمان‌ها'), {
            'fields': ('response_time', 'resolution_time', 'business_hours_only')
        }),
        (_('وضعیت'), {
            'fields': ('is_active',)
        }),
    )
    
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
