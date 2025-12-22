from django import forms
from django.contrib import admin
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.contrib.auth import get_user_model
from .models import Ticket, TicketMessage
import jdatetime

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
        'department', 'assigned_to', 'sla_indicator', 'created_at_jalali'
    ]
    list_filter = ['status', 'priority', 'department', 'category', 'created_at']
    search_fields = ['ticket_number', 'subject', 'description', 'user__phone_number', 'user__email']
    readonly_fields = [
        'ticket_info_display', 'time_info_display', 'messages_display', 'reply_form_display',
        'ticket_number', 'user', 'organization', 'subject', 'description',
        'category', 'department', 'priority', 'source',
        'first_response_at', 'resolved_at', 'closed_at',
        'created_at', 'updated_at', 'user_read', 'staff_read'
    ]
    
    fieldsets = (
        (None, {
            'fields': ('ticket_info_display', 'messages_display', 'reply_form_display'),
        }),
    )
    
    def has_add_permission(self, request):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return False
    
    class Media:
        css = {
            'all': (
                'https://cdn.jsdelivr.net/npm/select2@4.1.0-rc.0/dist/css/select2.min.css',
            )
        }
        js = (
            'https://cdn.jsdelivr.net/npm/select2@4.1.0-rc.0/dist/js/select2.min.js',
        )
    
    def get_form(self, request, obj=None, **kwargs):
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
            from notifications.services import NotificationService
            
            # فقط برای reply و question به کاربر نوتیف می‌فرستیم
            if message_type in ['reply', 'question']:
                template_code = 'ticket_reply_user' if message_type == 'reply' else 'ticket_question_user'
                context = {
                    'user_name': ticket.user.get_full_name() if hasattr(ticket.user, 'get_full_name') else str(ticket.user),
                    'ticket_number': ticket.ticket_number,
                    'subject': ticket.subject,
                    'ticket_id': str(ticket.id)
                }
                
                NotificationService.create_notification(
                    user=ticket.user,
                    template_code=template_code,
                    context=context,
                    priority='high' if message_type == 'question' else 'normal'
                )
            
            # برای send_to به کارشناس مقصد نوتیف می‌فرستیم
            if message_type == 'send_to' and message.forwarded_to:
                context = {
                    'staff_name': message.forwarded_to.get_full_name() if hasattr(message.forwarded_to, 'get_full_name') else str(message.forwarded_to),
                    'sender_name': message.sender.get_full_name() if message.sender and hasattr(message.sender, 'get_full_name') else 'کارشناس',
                    'ticket_number': ticket.ticket_number,
                    'subject': ticket.subject,
                    'ticket_id': str(ticket.id)
                }
                
                NotificationService.create_notification(
                    user=message.forwarded_to,
                    template_code='ticket_forwarded_staff',
                    context=context,
                    priority='high'
                )
        except Exception as e:
            import logging
            logging.error(f'Error sending notification: {e}')
    
    def ticket_info_display(self, obj, request=None):
        """نمایش اطلاعات تیکت و زمانی - یکپارچه"""
        if not obj:
            return ''
        
        from core.utils.timezone_utils import format_datetime_jalali
        
        # تبدیل به تاریخ شمسی بر اساس timezone کاربر
        user = request.user if request else None
        jalali_created_str = format_datetime_jalali(obj.created_at, user)
        
        # وضعیت پاسخ
        if obj.first_response_at:
            jalali_first_response = format_datetime_jalali(obj.first_response_at, user)
            response_status = f'<span style="color: #22c55e; font-weight: bold;">{jalali_first_response}</span>'
        else:
            response_status = '<span style="color: #ef4444; font-weight: bold;">پاسخ داده نشده</span>'
        
        # محاسبه SLA
        sla_row_response = ''
        sla_row_resolution = ''
        
        if obj.response_due or obj.resolution_due:
            is_response_breached = obj.response_due and timezone.now() > obj.response_due and not obj.first_response_at
            is_resolution_breached = obj.resolution_due and timezone.now() > obj.resolution_due and obj.status not in ['closed', 'resolved']
            
            if obj.response_due:
                jalali_response_deadline = format_datetime_jalali(obj.response_due, user)
                response_color = '#ef4444' if is_response_breached else '#22c55e'
                response_icon = '⚠️' if is_response_breached else '✓'
                response_bg = '#fef2f2' if is_response_breached else '#f0fdf4'
                sla_row_response = f'''
                <tr style="border-bottom: 1px solid #e5e7eb; background: {response_bg};">
                    <td style="padding: 10px;"><strong>⏰ مهلت پاسخ‌دهی:</strong></td>
                    <td style="padding: 10px;" colspan="3">
                        <span style="color: {response_color}; font-weight: bold; font-size: 14px;">{jalali_response_deadline} {response_icon}</span>
                        {' <span style="background: #fee2e2; color: #991b1b; padding: 3px 10px; border-radius: 4px; font-size: 12px; margin-right: 10px;">تأخیر در پاسخ</span>' if is_response_breached else ''}
                    </td>
                </tr>
                '''
            
            if obj.resolution_due:
                jalali_resolution_deadline = format_datetime_jalali(obj.resolution_due, user)
                resolution_color = '#ef4444' if is_resolution_breached else '#22c55e'
                resolution_icon = '⚠️' if is_resolution_breached else '✓'
                resolution_bg = '#fef2f2' if is_resolution_breached else '#f0fdf4'
                sla_row_resolution = f'''
                <tr style="border-bottom: 1px solid #e5e7eb; background: {resolution_bg};">
                    <td style="padding: 10px;"><strong>🎯 مهلت حل مشکل:</strong></td>
                    <td style="padding: 10px;" colspan="3">
                        <span style="color: {resolution_color}; font-weight: bold; font-size: 14px;">{jalali_resolution_deadline} {resolution_icon}</span>
                        {' <span style="background: #fee2e2; color: #991b1b; padding: 3px 10px; border-radius: 4px; font-size: 12px; margin-right: 10px;">تأخیر در حل</span>' if is_resolution_breached else ''}
                    </td>
                </tr>
                '''
        
        html = f'''
        <div style="width: 100% !important; max-width: none !important; background: white; padding: 20px; border-radius: 8px; margin-bottom: 0; border: 1px solid #e5e7eb;">
            <table style="width: 100%; border-collapse: collapse;">
                <tr style="border-bottom: 1px solid #e5e7eb;">
                    <td style="padding: 10px; width: 25%;"><strong>شماره تیکت:</strong></td>
                    <td style="padding: 10px; width: 25%;"><span style="font-family: monospace; font-size: 14px; color: #3b82f6;">{obj.ticket_number}</span></td>
                    <td style="padding: 10px; width: 25%;"><strong>موبایل:</strong></td>
                    <td style="padding: 10px; width: 25%;">{obj.user.phone_number if hasattr(obj.user, 'phone_number') else obj.user}</td>
                </tr>
                <tr style="border-bottom: 1px solid #e5e7eb;">
                    <td style="padding: 10px;"><strong>سازمان:</strong></td>
                    <td style="padding: 10px;">{obj.organization.name if obj.organization else '-'}</td>
                    <td style="padding: 10px;"><strong>دپارتمان:</strong></td>
                    <td style="padding: 10px;">{obj.department.name if obj.department else '-'}</td>
                </tr>
                <tr style="border-bottom: 1px solid #e5e7eb;">
                    <td style="padding: 10px;"><strong>دسته‌بندی:</strong></td>
                    <td style="padding: 10px;">{obj.category.name if obj.category else '-'}</td>
                    <td style="padding: 10px;"><strong>کارشناس مسئول:</strong></td>
                    <td style="padding: 10px;">{obj.assigned_to.get_full_name() if obj.assigned_to and hasattr(obj.assigned_to, 'get_full_name') else (obj.assigned_to if obj.assigned_to else '-')}</td>
                </tr>
                <tr style="border-bottom: 1px solid #e5e7eb;">
                    <td style="padding: 10px;"><strong>وضعیت:</strong></td>
                    <td style="padding: 10px;">{self._get_status_badge(obj.status)}</td>
                    <td style="padding: 10px;"><strong>اولویت:</strong></td>
                    <td style="padding: 10px;">{self._get_priority_badge(obj.priority)}</td>
                </tr>
                <tr style="border-bottom: 1px solid #e5e7eb;">
                    <td style="padding: 10px;"><strong>زمان ایجاد تیکت:</strong></td>
                    <td style="padding: 10px;">{jalali_created_str}</td>
                    <td style="padding: 10px;"><strong>زمان آخرین پاسخ:</strong></td>
                    <td style="padding: 10px;">{response_status}</td>
                </tr>
                {sla_row_response}
                {sla_row_resolution}
            </table>
        </div>
        '''
        return mark_safe(html)
    ticket_info_display.short_description = ''
    
    def time_info_display(self, obj):
        """این متد دیگر استفاده نمی‌شود - همه چیز در ticket_info_display است"""
        return ''
    time_info_display.short_description = ''
    
    def messages_display(self, obj, request=None):
        """نمایش موضوع و تاریخچه مکالمات"""
        if not obj:
            return ''
        
        from core.utils.timezone_utils import format_datetime_jalali
        user = request.user if request else None
        
        # موضوع تیکت - در همان خط
        subject_html = f'''
        <div style="background: white; padding: 15px; border-radius: 6px; margin-bottom: 15px; border-right: 4px solid #3b82f6;">
            <div style="display: flex; align-items: center; gap: 10px;">
                <strong style="color: #3b82f6; white-space: nowrap;">موضوع:</strong>
                <div style="font-size: 16px; line-height: 1.6; flex: 1;">{obj.subject}</div>
            </div>
        </div>
        '''
        
        # محتوای اولیه تیکت
        jalali_created = format_datetime_jalali(obj.created_at, user)
        initial_message = f'''
        <div style="background: #f0fdf4; padding: 15px; border-radius: 8px; margin-bottom: 15px; border-right: 4px solid #16a34a;">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
                <div>
                    <strong style="color: #16a34a;">👤 {obj.user.get_full_name() if hasattr(obj.user, 'get_full_name') else obj.user}</strong>
                    <span style="background: #dcfce7; color: #166534; padding: 2px 8px; border-radius: 4px; font-size: 12px; margin-right: 10px;">ایجاد تیکت</span>
                </div>
                <span style="color: #6b7280; font-size: 13px;">{jalali_created}</span>
            </div>
            <div style="white-space: pre-wrap; line-height: 1.6; font-size: 14px;">
                {obj.description}
            </div>
        </div>
        '''
        
        # پیام‌های بعدی
        messages = obj.messages.all().order_by('created_at')
        messages_html = ''
        
        for msg in messages:
            jalali_msg_time = format_datetime_jalali(msg.created_at, user)
            
            # تعیین رنگ و آیکون بر اساس نوع پیام
            if msg.is_staff_reply:
                bg_color = '#e0f2fe'
                border_color = '#0284c7'
                icon = '👨‍💼'
            else:
                bg_color = '#f0fdf4'
                border_color = '#16a34a'
                icon = '👤'
            
            # نمایش نوع پیام
            message_type_badge = ''
            if msg.is_staff_reply and msg.message_type != 'reply':
                type_labels = {
                    'note': '📝 یادداشت داخلی (محرمانه)',
                    'question': '❓ سوال از کاربر',
                    'send_to': '➡️ ارسال به کارشناس (محرمانه)',
                    'forward': '↪️ فوروارد شد'
                }
                badge_color = '#fbbf24' if msg.message_type in ['note', 'send_to'] else '#8b5cf6'
                message_type_badge = f'<span style="background: {badge_color}; color: white; padding: 2px 8px; border-radius: 4px; font-size: 12px; margin-right: 10px;">{type_labels.get(msg.message_type, msg.message_type)}</span>'
            
            # نمایش کارشناس مقصد برای send_to
            forwarded_info = ''
            if msg.message_type == 'send_to' and msg.forwarded_to:
                forwarded_info = f'<div style="margin-top: 8px; padding: 8px; background: rgba(251, 191, 36, 0.1); border-radius: 4px; font-size: 12px; color: #78350f;">➡️ ارسال شده به: <strong>{msg.forwarded_to.get_full_name() if hasattr(msg.forwarded_to, "get_full_name") else msg.forwarded_to}</strong></div>'
            
            messages_html += f'''
            <div style="background: {bg_color}; padding: 15px; border-radius: 8px; margin-bottom: 15px; border-right: 4px solid {border_color};">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
                    <div>
                        <strong style="color: {border_color};">{icon} {msg.sender.get_full_name() if msg.sender and hasattr(msg.sender, 'get_full_name') else (msg.sender if msg.sender else 'سیستم')}</strong>
                        {message_type_badge}
                    </div>
                    <span style="color: #6b7280; font-size: 13px;">{jalali_msg_time}</span>
                </div>
                <div style="white-space: pre-wrap; line-height: 1.6; font-size: 14px;">
                    {msg.content}
                </div>
                {forwarded_info}
            </div>
            '''
        
        html = f'''
        <div style="width: 100% !important; max-width: none !important; background: white; padding: 20px; border-radius: 8px; margin-bottom: 0; margin-top: 0; border: 1px solid #e5e7eb;">
            {subject_html}
            {initial_message}
            {messages_html if messages_html else '<p style="color: #6b7280; text-align: center; padding: 20px;">هنوز پیامی ثبت نشده است.</p>'}
        </div>
        '''
        return mark_safe(html)
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
        """نمایش وضعیت SLA در لیست تیکت‌ها"""
        # بررسی نقض پاسخ‌دهی
        response_breached = obj.response_due and timezone.now() > obj.response_due and not obj.first_response_at
        # بررسی نقض حل مشکل
        resolution_breached = obj.resolution_due and timezone.now() > obj.resolution_due and obj.status not in ['closed', 'resolved']
        
        if response_breached or resolution_breached:
            return format_html('<span style="color: #ef4444; font-weight: bold;">⚠️ با تاخیر</span>')
        elif obj.first_response_at and obj.response_due and obj.first_response_at <= obj.response_due:
            return format_html('<span style="color: #22c55e; font-weight: bold;">✓ در موعد مقرر</span>')
        elif obj.response_due:
            return format_html('<span style="color: #3b82f6;">⏳ در حال بررسی</span>')
        return format_html('<span style="color: #6b7280;">-</span>')
    sla_indicator.short_description = 'وضعیت SLA'
    
    def created_at_jalali(self, obj):
        """نمایش تاریخ ایجاد به شمسی"""
        if obj.created_at:
            jalali_date = jdatetime.datetime.fromgregorian(datetime=obj.created_at)
            return jalali_date.strftime('%Y/%m/%d %H:%M')
        return '-'
    created_at_jalali.short_description = 'تاریخ ایجاد'
    created_at_jalali.admin_order_field = 'created_at'
    
    def reply_form_display(self, obj):
        """نمایش فرم پاسخ"""
        if not obj:
            return ''
        
        # لیست کارشناسان برای dropdown
        staff_users = User.objects.filter(is_staff=True, is_active=True).order_by('first_name', 'last_name')
        staff_options = ''.join([
            f'<option value="{user.id}">{user.get_full_name() if hasattr(user, "get_full_name") else user}</option>'
            for user in staff_users
        ])
        
        # JavaScript code - جدا از f-string
        js_code = '''
            function toggleForwardedTo() {
                var messageType = document.querySelector('select[name="message_type"]').value;
                var field = document.getElementById('forwarded_to_field');
                if (messageType === 'send_to') {
                    field.style.display = 'block';
                } else {
                    field.style.display = 'none';
                }
            }
            
            function toggleHelp() {
                var popup = document.getElementById('help_popup');
                if (popup.style.display === 'none') {
                    popup.style.display = 'block';
                } else {
                    popup.style.display = 'none';
                }
            }
        '''
        
        # ساخت HTML با استفاده از + به جای f-string برای JavaScript
        html = '''
        <div style="width: 100% !important; max-width: none !important; background: #ffffff; padding: 25px; border-radius: 8px; border: 2px solid #e5e7eb; margin-top: 0;">
            <h2 style="margin-top: 0; color: #2c3e50; border-bottom: 2px solid #3b82f6; padding-bottom: 10px;">✍️ ارسال پاسخ / پیام جدید</h2>
            
            <form method="post" action="" id="ticket-reply-form">
                <input type="hidden" name="action" value="send_reply">
                <input type="hidden" name="ticket_id" value="''' + str(obj.id) + '''">
                
                <div style="margin-bottom: 20px;">
                    <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 8px;">
                        <label style="font-weight: bold; color: #374151; font-size: 14px;">
                            نوع پیام: <span style="color: #ef4444;">*</span>
                        </label>
                        <button type="button" onclick="toggleHelp()" style="background: #3b82f6; color: white; border: none; border-radius: 50%; width: 20px; height: 20px; font-size: 12px; cursor: pointer; display: flex; align-items: center; justify-content: center; font-weight: bold;">i</button>
                    </div>
                    <div style="display: flex; gap: 10px; align-items: center;">
                        <select name="message_type" onchange="toggleForwardedTo()" style="width: 250px; padding: 12px; border: 2px solid #d1d5db; border-radius: 6px; font-size: 14px; font-family: Tahoma, Arial, sans-serif; direction: rtl; text-align: right;">
                            <option value="reply" selected>پاسخ</option>
                            <option value="note">یادداشت داخلی</option>
                            <option value="question">منتظر پاسخ کاربر</option>
                            <option value="send_to">ارسال به کارشناس</option>
                        </select>
                        <select name="forwarded_to" id="forwarded_to_field" style="width: 250px; padding: 12px; border: 2px solid #d1d5db; border-radius: 6px; font-size: 14px; font-family: Tahoma, Arial, sans-serif; direction: rtl; text-align: right; display: none;">
                            <option value="">انتخاب کارشناس...</option>
                            ''' + staff_options + '''
                        </select>
                    </div>
                    <div id="help_popup" style="display: none; margin-top: 10px; padding: 12px; background: #f0f9ff; border-radius: 6px; border-right: 4px solid #3b82f6;">
                        <div style="font-size: 13px; color: #1e40af; line-height: 1.8;">
                            <strong>📌 راهنما:</strong><br>
                            • <strong>پاسخ:</strong> پاسخ به کاربر (قابل رویت برای کاربر) - وضعیت: "پاسخ داده شده"<br>
                            • <strong>یادداشت داخلی:</strong> محرمانه - فقط برای کارشناسان - وضعیت: "در حال بررسی"<br>
                            • <strong>منتظر پاسخ کاربر:</strong> سوال از کاربر (قابل رویت) - وضعیت: "منتظر پاسخ کاربر" (بدون محدودیت SLA)<br>
                            • <strong>ارسال به کارشناس:</strong> محرمانه - تخصیص به کارشناس دیگر - وضعیت: "در حال بررسی"
                        </div>
                    </div>
                </div>
                
                <div style="margin-bottom: 20px;">
                    <label style="display: block; font-weight: bold; margin-bottom: 8px; color: #374151; font-size: 14px;">
                        محتوای پیام: <span style="color: #ef4444;">*</span>
                    </label>
                    <textarea name="content" rows="6" required style="width: 100%; padding: 12px; border: 2px solid #d1d5db; border-radius: 6px; font-family: Tahoma, Arial, sans-serif; font-size: 14px; line-height: 1.6;"></textarea>
                </div>
                
                <div style="display: flex; gap: 10px;">
                    <button type="submit" style="background: #3b82f6; color: white; padding: 14px 28px; border: none; border-radius: 6px; font-weight: 600; cursor: pointer; font-size: 15px; transition: all 0.2s;">
                        ✉️ ارسال پیام
                    </button>
                </div>
            </form>
            
            <script>''' + js_code + '''</script>
        </div>
        '''
        from django.utils.safestring import mark_safe
        return mark_safe(html)
    reply_form_display.short_description = ''
    
    def change_view(self, request, object_id, form_url='', extra_context=None):
        """Override change_view برای handle کردن فرم پاسخ"""
        if request.method == 'POST' and request.POST.get('action') == 'send_reply':
            try:
                ticket = Ticket.objects.get(pk=object_id)
                content = request.POST.get('content', '').strip()
                message_type = request.POST.get('message_type', 'reply')
                forwarded_to_id = request.POST.get('forwarded_to')
                
                if not content:
                    self.message_user(request, 'محتوای پیام نمی‌تواند خالی باشد.', level='error')
                    return super().change_view(request, object_id, form_url, extra_context)
                
                if message_type == 'send_to' and not forwarded_to_id:
                    self.message_user(request, 'برای نوع پیام "ارسال به" باید کارشناس مقصد را انتخاب کنید.', level='error')
                    return super().change_view(request, object_id, form_url, extra_context)
                
                # ایجاد پیام جدید
                forwarded_to = User.objects.get(pk=forwarded_to_id) if forwarded_to_id else None
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
                
                self.message_user(request, 'پیام با موفقیت ارسال شد.', level='success')
                
            except Exception as e:
                self.message_user(request, f'خطا در ارسال پیام: {str(e)}', level='error')
        
        return super().change_view(request, object_id, form_url, extra_context)
