from django import forms
from django.contrib import admin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.contrib.auth import get_user_model
from .models import Ticket, TicketMessage

User = get_user_model()


class TicketReplyForm(forms.ModelForm):
    """فرم سفارشی برای پاسخ به تیکت"""
    content = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 6, 'style': 'width: 100%;'}),
        label='محتوای پیام',
        required=True
    )
    message_type = forms.ChoiceField(
        choices=TicketMessage.MESSAGE_TYPE_CHOICES,
        label='نوع پیام',
        initial='reply',
        widget=forms.RadioSelect
    )
    forwarded_to = forms.ModelChoiceField(
        queryset=User.objects.filter(is_staff=True, is_active=True),
        label='ارسال به کارشناس',
        required=False,
        help_text='فقط برای نوع پیام "ارسال به" انتخاب کنید'
    )
    
    class Meta:
        model = TicketMessage
        fields = ['content', 'message_type', 'forwarded_to']
    
    def clean(self):
        cleaned_data = super().clean()
        message_type = cleaned_data.get('message_type')
        forwarded_to = cleaned_data.get('forwarded_to')
        
        if message_type == 'send_to' and not forwarded_to:
            raise forms.ValidationError('برای نوع پیام "ارسال به" باید کارشناس مقصد را انتخاب کنید.')
        
        return cleaned_data


class CustomTicketAdmin(admin.ModelAdmin):
    """Admin سفارشی برای نمایش بهتر تیکت"""
    
    change_form_template = 'admin/support/ticket_change_form.html'
    
    list_display = [
        'ticket_number', 'subject', 'user', 'status_badge', 'priority_badge',
        'department', 'assigned_to', 'sla_indicator', 'created_at'
    ]
    list_filter = ['status', 'priority', 'department', 'category', 'created_at']
    search_fields = ['ticket_number', 'subject', 'description', 'user__phone_number', 'user__email']
    readonly_fields = [
        'ticket_info_display', 'time_info_display', 'messages_display',
        'ticket_number', 'user', 'organization', 'subject', 'description',
        'category', 'department', 'priority', 'source',
        'first_response_at', 'resolved_at', 'closed_at',
        'created_at', 'updated_at', 'user_read', 'staff_read'
    ]
    
    fieldsets = (
        (None, {
            'fields': ('ticket_info_display', 'time_info_display', 'messages_display')
        }),
    )
    
    def get_form(self, request, obj=None, **kwargs):
        if obj:
            kwargs['form'] = TicketReplyForm
        return super().get_form(request, obj, **kwargs)
    
    def save_model(self, request, obj, form, change):
        # این متد برای ذخیره پاسخ جدید است
        if change and isinstance(form, TicketReplyForm):
            ticket = obj
            content = form.cleaned_data.get('content')
            message_type = form.cleaned_data.get('message_type')
            forwarded_to = form.cleaned_data.get('forwarded_to')
            
            if content:
                # ایجاد پیام جدید
                message = TicketMessage.objects.create(
                    ticket=ticket,
                    sender=request.user,
                    content=content,
                    message_type=message_type,
                    is_staff_reply=True,
                    forwarded_to=forwarded_to
                )
                
                # تغییر وضعیت بر اساس نوع پیام
                if message_type == 'reply':
                    ticket.status = 'answered'
                    if not ticket.first_response_at:
                        ticket.first_response_at = timezone.now()
                elif message_type == 'note':
                    ticket.status = 'in_progress'
                elif message_type == 'question':
                    ticket.status = 'waiting'
                elif message_type == 'send_to' and forwarded_to:
                    ticket.assigned_to = forwarded_to
                    ticket.status = 'in_progress'
                
                ticket.staff_read = True
                ticket.save()
                
                # ارسال نوتیفیکیشن
                self._send_notification(ticket, message, message_type)
        
        return super().save_model(request, obj, form, change)
    
    def _send_notification(self, ticket, message, message_type):
        """ارسال نوتیفیکیشن بر اساس نوع پیام"""
        try:
            from notifications.models import Notification
            
            # فقط برای reply و question به کاربر نوتیف می‌فرستیم
            if message_type in ['reply', 'question']:
                Notification.objects.create(
                    user=ticket.user,
                    title='پاسخ جدید در تیکت' if message_type == 'reply' else 'سوال جدید در تیکت',
                    message=f'پیام جدیدی در تیکت #{ticket.ticket_number} دریافت شد.',
                    notification_type='ticket',
                    data={'ticket_id': str(ticket.id), 'ticket_number': ticket.ticket_number}
                )
            
            # برای send_to به کارشناس مقصد نوتیف می‌فرستیم
            if message_type == 'send_to' and message.forwarded_to:
                Notification.objects.create(
                    user=message.forwarded_to,
                    title='تیکت جدید ارسال شده',
                    message=f'تیکت #{ticket.ticket_number} به شما ارسال شد.',
                    notification_type='ticket',
                    data={'ticket_id': str(ticket.id), 'ticket_number': ticket.ticket_number}
                )
        except Exception:
            pass
    
    def ticket_info_display(self, obj):
        """نمایش اطلاعات تیکت"""
        if not obj:
            return ''
        
        html = f'''
        <div style="background: #f8f9fa; padding: 20px; border-radius: 8px; margin-bottom: 20px;">
            <h2 style="margin-top: 0; color: #2c3e50;">📋 اطلاعات تیکت</h2>
            <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 15px;">
                <div>
                    <strong>شماره تیکت:</strong><br>
                    <span style="font-family: monospace; font-size: 16px;">{obj.ticket_number}</span>
                </div>
                <div>
                    <strong>کاربر:</strong><br>
                    {obj.user.get_full_name() if hasattr(obj.user, 'get_full_name') else obj.user}
                </div>
                <div>
                    <strong>سازمان:</strong><br>
                    {obj.organization.name if obj.organization else '-'}
                </div>
                <div>
                    <strong>اولویت:</strong><br>
                    {self._get_priority_badge(obj.priority)}
                </div>
                <div>
                    <strong>دسته‌بندی:</strong><br>
                    {obj.category.name if obj.category else '-'}
                </div>
                <div>
                    <strong>وضعیت:</strong><br>
                    {self._get_status_badge(obj.status)}
                </div>
            </div>
            <div style="margin-top: 15px;">
                <strong>موضوع:</strong><br>
                <div style="background: white; padding: 10px; border-radius: 4px; margin-top: 5px;">
                    {obj.subject}
                </div>
            </div>
            <div style="margin-top: 15px;">
                <strong>توضیحات:</strong><br>
                <div style="background: white; padding: 10px; border-radius: 4px; margin-top: 5px; white-space: pre-wrap;">
                    {obj.description}
                </div>
            </div>
        </div>
        '''
        return format_html(html)
    ticket_info_display.short_description = ''
    
    def time_info_display(self, obj):
        """نمایش اطلاعات زمانی و SLA"""
        if not obj:
            return ''
        
        sla_policy = obj.get_applicable_sla()
        sla_status = ''
        
        if sla_policy:
            response_deadline = obj.created_at + timezone.timedelta(minutes=sla_policy.response_time)
            is_breached = timezone.now() > response_deadline and not obj.first_response_at
            
            sla_status = f'''
            <div style="background: {'#fee2e2' if is_breached else '#dcfce7'}; padding: 10px; border-radius: 4px; border-left: 4px solid {'#ef4444' if is_breached else '#22c55e'};">
                <strong>⏱️ SLA:</strong> {sla_policy.name}<br>
                <strong>مهلت پاسخ:</strong> {response_deadline.strftime('%Y-%m-%d %H:%M')}<br>
                <strong>وضعیت:</strong> <span style="color: {'#ef4444' if is_breached else '#22c55e'}; font-weight: bold;">
                    {'⚠️ نقض شده' if is_breached else '✓ در زمان مقرر'}
                </span>
            </div>
            '''
        
        html = f'''
        <div style="background: #f8f9fa; padding: 20px; border-radius: 8px; margin-bottom: 20px;">
            <h2 style="margin-top: 0; color: #2c3e50;">⏰ اطلاعات زمانی</h2>
            <div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 15px;">
                <div>
                    <strong>زمان ایجاد:</strong><br>
                    {obj.created_at.strftime('%Y-%m-%d %H:%M')}
                </div>
                <div>
                    <strong>زمان اولین پاسخ:</strong><br>
                    {obj.first_response_at.strftime('%Y-%m-%d %H:%M') if obj.first_response_at else '<span style="color: #ef4444;">هنوز پاسخ داده نشده</span>'}
                </div>
            </div>
            {sla_status}
        </div>
        '''
        return format_html(html)
    time_info_display.short_description = ''
    
    def messages_display(self, obj):
        """نمایش تاریخچه مکالمات"""
        if not obj:
            return ''
        
        messages = obj.messages.all().order_by('created_at')
        messages_html = ''
        
        for msg in messages:
            # تعیین رنگ بر اساس نوع پیام
            if msg.is_staff_reply:
                bg_color = '#e0f2fe'  # آبی روشن برای کارشناس
                border_color = '#0284c7'
            else:
                bg_color = '#f0fdf4'  # سبز روشن برای کاربر
                border_color = '#16a34a'
            
            # نمایش نوع پیام برای غیر کاربر
            message_type_badge = ''
            if msg.is_staff_reply and msg.message_type != 'reply':
                type_labels = {
                    'note': '📝 یادداشت داخلی',
                    'question': '❓ سوال از کاربر',
                    'send_to': '➡️ ارسال به'
                }
                message_type_badge = f'<span style="background: #fbbf24; color: #78350f; padding: 2px 8px; border-radius: 4px; font-size: 12px; margin-left: 10px;">{type_labels.get(msg.message_type, msg.message_type)}</span>'
            
            # نمایش کارشناس مقصد برای send_to
            forwarded_info = ''
            if msg.message_type == 'send_to' and msg.forwarded_to:
                forwarded_info = f'<div style="margin-top: 5px; font-size: 12px; color: #6b7280;">➡️ ارسال شده به: {msg.forwarded_to.get_full_name() if hasattr(msg.forwarded_to, "get_full_name") else msg.forwarded_to}</div>'
            
            messages_html += f'''
            <div style="background: {bg_color}; padding: 15px; border-radius: 8px; margin-bottom: 15px; border-right: 4px solid {border_color};">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
                    <div>
                        <strong>{msg.sender.get_full_name() if msg.sender and hasattr(msg.sender, 'get_full_name') else (msg.sender if msg.sender else 'سیستم')}</strong>
                        {message_type_badge}
                    </div>
                    <span style="color: #6b7280; font-size: 14px;">{msg.created_at.strftime('%Y-%m-%d %H:%M')}</span>
                </div>
                <div style="white-space: pre-wrap; line-height: 1.6;">
                    {msg.content}
                </div>
                {forwarded_info}
            </div>
            '''
        
        html = f'''
        <div style="background: #f8f9fa; padding: 20px; border-radius: 8px; margin-bottom: 20px;">
            <h2 style="margin-top: 0; color: #2c3e50;">💬 تاریخچه مکالمات</h2>
            {messages_html if messages_html else '<p style="color: #6b7280;">هنوز پیامی ثبت نشده است.</p>'}
        </div>
        '''
        return format_html(html)
    messages_display.short_description = ''
    
    def _get_status_badge(self, status):
        colors = {
            'open': '#22c55e',
            'in_progress': '#3b82f6',
            'waiting': '#f59e0b',
            'answered': '#8b5cf6',
            'closed': '#ef4444',
        }
        labels = dict(Ticket.STATUS_CHOICES)
        color = colors.get(status, '#6b7280')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 4px 12px; border-radius: 4px; font-weight: 500;">{}</span>',
            color, labels.get(status, status)
        )
    
    def _get_priority_badge(self, priority):
        colors = {
            'low': '#6b7280',
            'medium': '#3b82f6',
            'high': '#f59e0b',
            'urgent': '#ef4444',
        }
        labels = dict(Ticket.PRIORITY_CHOICES)
        color = colors.get(priority, '#6b7280')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 4px 12px; border-radius: 4px; font-weight: 500;">{}</span>',
            color, labels.get(priority, priority)
        )
    
    def status_badge(self, obj):
        return self._get_status_badge(obj.status)
    status_badge.short_description = 'وضعیت'
    
    def priority_badge(self, obj):
        return self._get_priority_badge(obj.priority)
    priority_badge.short_description = 'اولویت'
    
    def sla_indicator(self, obj):
        if obj.is_sla_breached():
            return format_html('<span style="color: #ef4444; font-weight: bold;">⚠ نقض SLA</span>')
        return format_html('<span style="color: #22c55e;">✓ عادی</span>')
    sla_indicator.short_description = 'SLA'
