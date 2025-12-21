from django import forms
from django.contrib import admin
from django.utils.html import format_html
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
            'fields': ('ticket_info_display', 'time_info_display', 'messages_display', 'reply_form_display')
        }),
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
            from notifications.models import Notification
            
            # فقط برای reply و question به کاربر نوتیف می‌فرستیم
            if message_type in ['reply', 'question']:
                title = 'پاسخ جدید در تیکت' if message_type == 'reply' else 'سوال جدید در تیکت'
                body = f'پیام جدیدی در تیکت #{ticket.ticket_number} دریافت شد.'
                
                # ایجاد نوتیفیکیشن با کانال‌های مختلف
                notification = Notification.objects.create(
                    user=ticket.user,
                    title=title,
                    body=body,
                    category='support',
                    priority='high' if message_type == 'question' else 'normal',
                    channels=['in_app', 'sms', 'email'],  # ارسال به همه کانال‌ها
                    metadata={'ticket_id': str(ticket.id), 'ticket_number': ticket.ticket_number}
                )
                
                # ارسال به کانال‌های مختلف
                self._send_to_all_channels(notification, ticket.user)
            
            # برای send_to به کارشناس مقصد نوتیف می‌فرستیم
            if message_type == 'send_to' and message.forwarded_to:
                notification = Notification.objects.create(
                    user=message.forwarded_to,
                    title='تیکت جدید ارسال شده',
                    body=f'تیکت #{ticket.ticket_number} به شما ارسال شد.',
                    category='support',
                    priority='normal',
                    channels=['in_app', 'email'],
                    metadata={'ticket_id': str(ticket.id), 'ticket_number': ticket.ticket_number}
                )
                
                self._send_to_all_channels(notification, message.forwarded_to)
        except Exception as e:
            import logging
            logging.error(f'Error sending notification: {e}')
    
    def _send_to_all_channels(self, notification, user):
        """ارسال نوتیفیکیشن به تمام کانال‌ها"""
        try:
            from notifications.services import SMSService, EmailService
            from notifications.models import NotificationPreference
            
            # دریافت تنظیمات کاربر
            try:
                prefs = user.notification_preferences
            except NotificationPreference.DoesNotExist:
                prefs = NotificationPreference.objects.create(user=user)
            
            # ارسال SMS
            if 'sms' in notification.channels and prefs.sms_enabled and user.phone_number:
                rendered_content = {'sms_text': notification.body}
                SMSService.send(notification, rendered_content)
            
            # ارسال Email
            if 'email' in notification.channels and prefs.email_enabled and user.email:
                rendered_content = {
                    'email_subject': notification.title,
                    'email_html': f'<p>{notification.body}</p>'
                }
                EmailService.send(notification, rendered_content)
        except Exception as e:
            import logging
            logging.error(f'Error in _send_to_all_channels: {e}')
    
    def ticket_info_display(self, obj):
        """نمایش اطلاعات تیکت - افقی"""
        if not obj:
            return ''
        
        html = f'''
        <div style="width: 100%; background: #f8f9fa; padding: 20px; border-radius: 8px; margin-bottom: 0;">
            <h2 style="margin-top: 0; color: #2c3e50; border-bottom: 2px solid #3b82f6; padding-bottom: 10px;">📋 اطلاعات تیکت</h2>
            <div style="background: white; padding: 15px; border-radius: 6px;">
                <div style="display: flex; justify-content: space-between; margin-bottom: 10px; padding-bottom: 10px; border-bottom: 1px solid #e5e7eb;">
                    <span><strong>شماره تیکت:</strong> <span style="font-family: monospace; font-size: 14px; color: #3b82f6;">{obj.ticket_number}</span></span>
                    <span><strong>کاربر:</strong> {obj.user.get_full_name() if hasattr(obj.user, 'get_full_name') else obj.user}</span>
                </div>
                <div style="display: flex; justify-content: space-between; margin-bottom: 10px; padding-bottom: 10px; border-bottom: 1px solid #e5e7eb;">
                    <span><strong>سازمان:</strong> {obj.organization.name if obj.organization else '-'}</span>
                    <span><strong>دپارتمان:</strong> {obj.department.name if obj.department else '-'}</span>
                </div>
                <div style="display: flex; justify-content: space-between; margin-bottom: 10px; padding-bottom: 10px; border-bottom: 1px solid #e5e7eb;">
                    <span><strong>دسته‌بندی:</strong> {obj.category.name if obj.category else '-'}</span>
                    <span><strong>اولویت:</strong> {self._get_priority_badge(obj.priority)}</span>
                </div>
                <div style="display: flex; justify-content: space-between;">
                    <span><strong>وضعیت:</strong> {self._get_status_badge(obj.status)}</span>
                    <span><strong>کارشناس مسئول:</strong> {obj.assigned_to.get_full_name() if obj.assigned_to and hasattr(obj.assigned_to, 'get_full_name') else (obj.assigned_to if obj.assigned_to else '-')}</span>
                </div>
            </div>
        </div>
        '''
        return format_html(html)
    ticket_info_display.short_description = ''
    
    def time_info_display(self, obj):
        """نمایش اطلاعات زمانی و SLA با تاریخ شمسی"""
        if not obj:
            return ''
        
        # تبدیل به تاریخ شمسی
        jalali_created = jdatetime.datetime.fromgregorian(datetime=obj.created_at)
        jalali_created_str = jalali_created.strftime('%Y/%m/%d %H:%M')
        
        jalali_first_response = ''
        if obj.first_response_at:
            jalali_first_response_dt = jdatetime.datetime.fromgregorian(datetime=obj.first_response_at)
            jalali_first_response = jalali_first_response_dt.strftime('%Y/%m/%d %H:%M')
        
        # پیدا کردن SLA Policy مناسب
        from support.models import SLAPolicy
        sla_policy = None
        if obj.department:
            sla_policies = SLAPolicy.objects.filter(
                department=obj.department,
                is_active=True
            ).filter(priority__contains=obj.priority)
            sla_policy = sla_policies.first()
        
        # استفاده مستقیم از فیلدهای response_due و resolution_due
        sla_html = ''
        
        if obj.response_due or obj.resolution_due:
            is_response_breached = obj.response_due and timezone.now() > obj.response_due and not obj.first_response_at
            is_resolution_breached = obj.resolution_due and timezone.now() > obj.resolution_due and obj.status not in ['closed', 'resolved']
            
            sla_parts = []
            
            if obj.response_due:
                jalali_response_deadline = jdatetime.datetime.fromgregorian(datetime=obj.response_due)
                sla_parts.append(f'''
                <div style="background: white; padding: 10px; border-radius: 4px; margin-bottom: 8px;">
                    <strong>مهلت پاسخ‌دهی:</strong> <span style="color: {'#ef4444' if is_response_breached else '#22c55e'}; font-weight: bold;">{jalali_response_deadline.strftime('%Y/%m/%d %H:%M')}</span>
                    {'<span style="color: #ef4444; margin-right: 10px;">⚠️ نقض شده - جریمه خواهد شد!</span>' if is_response_breached else '<span style="color: #22c55e; margin-right: 10px;">✓</span>'}
                </div>
                ''')
            
            if obj.resolution_due:
                jalali_resolution_deadline = jdatetime.datetime.fromgregorian(datetime=obj.resolution_due)
                sla_parts.append(f'''
                <div style="background: white; padding: 10px; border-radius: 4px;">
                    <strong>مهلت حل مشکل:</strong> <span style="color: {'#ef4444' if is_resolution_breached else '#22c55e'}; font-weight: bold;">{jalali_resolution_deadline.strftime('%Y/%m/%d %H:%M')}</span>
                    {'<span style="color: #ef4444; margin-right: 10px;">⚠️ نقض شده - جریمه خواهد شد!</span>' if is_resolution_breached else '<span style="color: #22c55e; margin-right: 10px;">✓</span>'}
                </div>
                ''')
            
            bg_color = '#fee2e2' if (is_response_breached or is_resolution_breached) else '#dcfce7'
            border_color = '#ef4444' if (is_response_breached or is_resolution_breached) else '#22c55e'
            
            sla_title = f'⏱️ محدودیت‌های زمانی SLA'
            if sla_policy:
                sla_title += f' - {sla_policy.name}'
            
            sla_html = f'''
            <div style="background: {bg_color}; padding: 15px; border-radius: 6px; border-right: 4px solid {border_color}; margin-top: 15px;">
                <h3 style="margin: 0 0 10px 0; color: {border_color};">{sla_title}</h3>
                {''.join(sla_parts)}
            </div>
            '''
        
        html = f'''
        <div style="width: 100%; background: #f8f9fa; padding: 20px; border-radius: 8px; margin-bottom: 0;">
            <h2 style="margin-top: 0; color: #2c3e50; border-bottom: 2px solid #3b82f6; padding-bottom: 10px;">⏰ اطلاعات زمانی</h2>
            <div style="background: white; padding: 15px; border-radius: 6px;">
                <div style="display: flex; justify-content: space-between; margin-bottom: 10px;">
                    <span><strong>زمان ایجاد تیکت:</strong> {jalali_created_str}</span>
                    <span><strong>زمان آخرین پاسخ:</strong> {jalali_first_response if jalali_first_response else '<span style="color: #ef4444;">هنوز پاسخ داده نشده</span>'}</span>
                </div>
            </div>
            {sla_html}
        </div>
        '''
        return format_html(html)
    time_info_display.short_description = ''
    
    def messages_display(self, obj):
        """نمایش موضوع و تاریخچه مکالمات"""
        if not obj:
            return ''
        
        # موضوع تیکت
        subject_html = f'''
        <div style="background: white; padding: 15px; border-radius: 6px; margin-bottom: 15px; border-right: 4px solid #3b82f6;">
            <h3 style="margin: 0 0 10px 0; color: #3b82f6;">موضوع:</h3>
            <div style="font-size: 16px; line-height: 1.6;">{obj.subject}</div>
        </div>
        '''
        
        # محتوای اولیه تیکت
        jalali_created = jdatetime.datetime.fromgregorian(datetime=obj.created_at)
        initial_message = f'''
        <div style="background: #f0fdf4; padding: 15px; border-radius: 8px; margin-bottom: 15px; border-right: 4px solid #16a34a;">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
                <div>
                    <strong style="color: #16a34a;">👤 {obj.user.get_full_name() if hasattr(obj.user, 'get_full_name') else obj.user}</strong>
                    <span style="background: #dcfce7; color: #166534; padding: 2px 8px; border-radius: 4px; font-size: 12px; margin-right: 10px;">ایجاد تیکت</span>
                </div>
                <span style="color: #6b7280; font-size: 13px;">{jalali_created.strftime('%Y/%m/%d %H:%M')}</span>
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
            jalali_msg_time = jdatetime.datetime.fromgregorian(datetime=msg.created_at)
            
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
                    <span style="color: #6b7280; font-size: 13px;">{jalali_msg_time.strftime('%Y/%m/%d %H:%M')}</span>
                </div>
                <div style="white-space: pre-wrap; line-height: 1.6; font-size: 14px;">
                    {msg.content}
                </div>
                {forwarded_info}
            </div>
            '''
        
        html = f'''
        <div style="width: 100%; background: #f8f9fa; padding: 20px; border-radius: 8px; margin-bottom: 0;">
            <h2 style="margin-top: 0; color: #2c3e50; border-bottom: 2px solid #3b82f6; padding-bottom: 10px;">💬 تاریخچه مکالمات</h2>
            {subject_html}
            {initial_message}
            {messages_html if messages_html else '<p style="color: #6b7280; text-align: center; padding: 20px;">هنوز پیامی ثبت نشده است.</p>'}
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
                var messageType = document.querySelector('input[name="message_type"]:checked').value;
                var field = document.getElementById('forwarded_to_field');
                if (messageType === 'send_to') {
                    field.style.display = 'block';
                } else {
                    field.style.display = 'none';
                }
            }
        '''
        
        # ساخت HTML با استفاده از + به جای f-string برای JavaScript
        html = '''
        <div style="width: 100%; background: #ffffff; padding: 25px; border-radius: 8px; border: 2px solid #e5e7eb; margin-top: 0;">
            <h2 style="margin-top: 0; color: #2c3e50; border-bottom: 2px solid #3b82f6; padding-bottom: 10px;">✍️ ارسال پاسخ / پیام جدید</h2>
            
            <form method="post" action="" id="ticket-reply-form">
                <input type="hidden" name="action" value="send_reply">
                <input type="hidden" name="ticket_id" value="''' + str(obj.id) + '''">
                
                <div style="margin-bottom: 20px;">
                    <label style="display: block; font-weight: bold; margin-bottom: 8px; color: #374151; font-size: 14px;">
                        نوع پیام: <span style="color: #ef4444;">*</span>
                    </label>
                    <div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 10px;">
                        <label style="display: flex; align-items: center; padding: 12px; border: 2px solid #e5e7eb; border-radius: 6px; cursor: pointer; transition: all 0.2s;">
                            <input type="radio" name="message_type" value="reply" checked style="margin-left: 8px;" onchange="toggleForwardedTo()">
                            <span style="font-weight: 500; font-size: 14px;">پاسخ</span>
                        </label>
                        <label style="display: flex; align-items: center; padding: 12px; border: 2px solid #e5e7eb; border-radius: 6px; cursor: pointer; transition: all 0.2s;">
                            <input type="radio" name="message_type" value="note" style="margin-left: 8px;" onchange="toggleForwardedTo()">
                            <span style="font-weight: 500; font-size: 14px;">یادداشت داخلی</span>
                        </label>
                        <label style="display: flex; align-items: center; padding: 12px; border: 2px solid #e5e7eb; border-radius: 6px; cursor: pointer; transition: all 0.2s;">
                            <input type="radio" name="message_type" value="question" style="margin-left: 8px;" onchange="toggleForwardedTo()">
                            <span style="font-weight: 500; font-size: 14px;">منتظر پاسخ کاربر</span>
                        </label>
                        <label style="display: flex; align-items: center; padding: 12px; border: 2px solid #e5e7eb; border-radius: 6px; cursor: pointer; transition: all 0.2s;">
                            <input type="radio" name="message_type" value="send_to" style="margin-left: 8px;" onchange="toggleForwardedTo()">
                            <span style="font-weight: 500; font-size: 14px;">ارسال به کارشناس</span>
                        </label>
                    </div>
                    <div style="margin-top: 10px; padding: 12px; background: #f0f9ff; border-radius: 6px; border-right: 4px solid #3b82f6;">
                        <div style="font-size: 13px; color: #1e40af; line-height: 1.8;">
                            <strong>📌 راهنما:</strong><br>
                            • <strong>پاسخ:</strong> پاسخ به کاربر (قابل رویت برای کاربر) - وضعیت: "پاسخ داده شده"<br>
                            • <strong>یادداشت داخلی:</strong> محرمانه - فقط برای کارشناسان - وضعیت: "در حال بررسی"<br>
                            • <strong>منتظر پاسخ کاربر:</strong> سوال از کاربر (قابل رویت) - وضعیت: "منتظر پاسخ کاربر" (بدون محدودیت SLA)<br>
                            • <strong>ارسال به کارشناس:</strong> محرمانه - تخصیص به کارشناس دیگر - وضعیت: "در حال بررسی"
                        </div>
                    </div>
                </div>
                
                <div style="margin-bottom: 20px; display: none;" id="forwarded_to_field">
                    <label style="display: block; font-weight: bold; margin-bottom: 8px; color: #374151; font-size: 14px;">
                        ارسال به کارشناس: <span style="color: #ef4444;">*</span>
                    </label>
                    <select name="forwarded_to" style="width: 100%; padding: 12px; border: 2px solid #d1d5db; border-radius: 6px; font-size: 14px; font-family: Tahoma, Arial, sans-serif;">
                        <option value="">انتخاب کارشناس...</option>
                        ''' + staff_options + '''
                    </select>
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
