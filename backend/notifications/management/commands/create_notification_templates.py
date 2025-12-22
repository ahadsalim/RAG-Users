from django.core.management.base import BaseCommand
from notifications.models import NotificationTemplate, NotificationCategory


class Command(BaseCommand):
    help = 'ایجاد قالب‌های پیش‌فرض اعلان‌رسانی'
    
    def handle(self, *args, **options):
        self.stdout.write('شروع ایجاد قالب‌های اعلان...')
        
        templates = [
            # System Notifications
            {
                'code': 'welcome',
                'name': 'خوش‌آمدگویی',
                'category': NotificationCategory.SYSTEM,
                'title_template': 'به {{site_name}} خوش آمدید!',
                'body_template': 'سلام {{user_name}} عزیز، از اینکه به ما پیوستید خوشحالیم.',
                'email_subject_template': 'به {{site_name}} خوش آمدید',
                'email_html_template': '<h1>سلام {{user_name}}!</h1><p>از اینکه به ما پیوستید خوشحالیم.</p>',
                'sms_template': 'سلام {{user_name}}، به {{site_name}} خوش آمدید.',
                'channels': ['email', 'sms', 'in_app'],
                'default_priority': 'normal',
                'action_url': '/dashboard',
                'action_text': 'شروع کنید'
            },
            
            # Payment Notifications
            {
                'code': 'payment_success',
                'name': 'پرداخت موفق',
                'category': NotificationCategory.PAYMENT,
                'title_template': 'پرداخت شما موفق بود',
                'body_template': 'پرداخت به مبلغ {{amount}} تومان با موفقیت انجام شد. شماره پیگیری: {{reference_id}}',
                'email_subject_template': 'تایید پرداخت - {{reference_id}}',
                'email_html_template': '<p>پرداخت شما به مبلغ <strong>{{amount}} تومان</strong> با موفقیت انجام شد.</p>',
                'sms_template': 'پرداخت {{amount}} تومان انجام شد. کد پیگیری: {{reference_id}}',
                'channels': ['email', 'sms', 'in_app'],
                'default_priority': 'high',
                'action_url': '/transactions/{{transaction_id}}',
                'action_text': 'مشاهده فاکتور'
            },
            {
                'code': 'payment_failed',
                'name': 'پرداخت ناموفق',
                'category': NotificationCategory.PAYMENT,
                'title_template': 'پرداخت شما ناموفق بود',
                'body_template': 'پرداخت به مبلغ {{amount}} تومان ناموفق بود. لطفا دوباره تلاش کنید.',
                'email_subject_template': 'خطا در پرداخت',
                'sms_template': 'پرداخت {{amount}} تومان ناموفق بود.',
                'channels': ['email', 'in_app'],
                'default_priority': 'high',
                'action_url': '/payment/retry/{{transaction_id}}',
                'action_text': 'تلاش مجدد'
            },
            
            # Subscription Notifications
            {
                'code': 'subscription_activated',
                'name': 'فعال‌سازی اشتراک',
                'category': NotificationCategory.SUBSCRIPTION,
                'title_template': 'اشتراک شما فعال شد',
                'body_template': 'اشتراک {{plan_name}} شما با موفقیت فعال شد. تاریخ انقضا: {{expiry_date}}',
                'email_subject_template': 'اشتراک شما فعال شد',
                'sms_template': 'اشتراک {{plan_name}} فعال شد.',
                'channels': ['email', 'sms', 'in_app'],
                'default_priority': 'high',
                'action_url': '/subscription',
                'action_text': 'مشاهده اشتراک'
            },
            {
                'code': 'subscription_expiring',
                'name': 'نزدیک به انقضای اشتراک',
                'category': NotificationCategory.SUBSCRIPTION,
                'title_template': 'اشتراک شما {{days_left}} روز دیگر منقضی می‌شود',
                'body_template': 'اشتراک {{plan_name}} شما در تاریخ {{expiry_date}} منقضی می‌شود. برای تمدید اقدام کنید.',
                'email_subject_template': 'یادآوری: اشتراک شما در حال انقضا است',
                'sms_template': 'اشتراک شما {{days_left}} روز دیگر منقضی می‌شود.',
                'channels': ['email', 'sms', 'in_app'],
                'default_priority': 'high',
                'action_url': '/subscription/renew',
                'action_text': 'تمدید اشتراک'
            },
            {
                'code': 'subscription_expired',
                'name': 'انقضای اشتراک',
                'category': NotificationCategory.SUBSCRIPTION,
                'title_template': 'اشتراک شما منقضی شد',
                'body_template': 'اشتراک {{plan_name}} شما منقضی شده است. برای ادامه استفاده، اقدام به تمدید کنید.',
                'email_subject_template': 'اشتراک شما منقضی شد',
                'sms_template': 'اشتراک شما منقضی شد.',
                'channels': ['email', 'sms', 'in_app'],
                'default_priority': 'urgent',
                'action_url': '/subscription/renew',
                'action_text': 'تمدید اشتراک'
            },
            
            # Chat Notifications
            {
                'code': 'chat_response_ready',
                'name': 'پاسخ آماده است',
                'category': NotificationCategory.CHAT,
                'title_template': 'پاسخ سوال شما آماده است',
                'body_template': 'پاسخ سوال "{{question}}" آماده شد.',
                'channels': ['push', 'websocket', 'in_app'],
                'default_priority': 'normal',
                'action_url': '/chat/{{conversation_id}}',
                'action_text': 'مشاهده پاسخ'
            },
            
            # Account Notifications
            {
                'code': 'password_changed',
                'name': 'تغییر رمز عبور',
                'category': NotificationCategory.SECURITY,
                'title_template': 'رمز عبور شما تغییر کرد',
                'body_template': 'رمز عبور حساب کاربری شما با موفقیت تغییر یافت. اگر این کار را انجام نداده‌اید، فورا با پشتیبانی تماس بگیرید.',
                'email_subject_template': 'هشدار امنیتی: تغییر رمز عبور',
                'sms_template': 'رمز عبور شما تغییر کرد.',
                'channels': ['email', 'sms', 'in_app'],
                'default_priority': 'urgent',
                'action_url': '/security',
                'action_text': 'بررسی امنیت'
            },
            {
                'code': 'login_from_new_device',
                'name': 'ورود از دستگاه جدید',
                'category': NotificationCategory.SECURITY,
                'title_template': 'ورود از دستگاه جدید',
                'body_template': 'ورود به حساب شما از دستگاه {{device_name}} در {{location}} تشخیص داده شد.',
                'email_subject_template': 'هشدار: ورود از دستگاه جدید',
                'channels': ['email', 'in_app'],
                'default_priority': 'high',
                'action_url': '/security/devices',
                'action_text': 'مدیریت دستگاه‌ها'
            },
            
            # Marketing Notifications
            {
                'code': 'special_offer',
                'name': 'پیشنهاد ویژه',
                'category': NotificationCategory.MARKETING,
                'title_template': 'پیشنهاد ویژه برای شما!',
                'body_template': '{{offer_title}}: {{offer_description}}',
                'email_subject_template': '🎉 پیشنهاد ویژه: {{offer_title}}',
                'channels': ['email', 'in_app'],
                'default_priority': 'low',
                'action_url': '/offers/{{offer_id}}',
                'action_text': 'مشاهده پیشنهاد'
            },
            
            # Support Notifications
            {
                'code': 'ticket_created_user',
                'name': 'تیکت جدید - کاربر',
                'category': NotificationCategory.SUPPORT,
                'title_template': 'تیکت جدید ایجاد شد',
                'body_template': 'تیکت #{{ticket_number}} با موضوع "{{subject}}" ایجاد شد.',
                'email_subject_template': 'تیکت #{{ticket_number}} ایجاد شد',
                'email_html_template': '<p>سلام {{user_name}} عزیز،</p><p>تیکت شما با شماره <strong>#{{ticket_number}}</strong> و موضوع "{{subject}}" با موفقیت ایجاد شد.</p><p>کارشناسان ما در اسرع وقت به تیکت شما رسیدگی خواهند کرد.</p>',
                'sms_template': 'تیکت #{{ticket_number}} با موضوع "{{subject}}" ایجاد شد.',
                'channels': ['in_app', 'sms', 'email'],
                'default_priority': 'normal',
                'action_url': '/support/tickets/{{ticket_id}}',
                'action_text': 'مشاهده تیکت'
            },
            {
                'code': 'ticket_assigned_staff',
                'name': 'تیکت تخصیص داده شده - کارشناس',
                'category': NotificationCategory.SUPPORT,
                'title_template': 'تیکت جدید تخصیص داده شد',
                'body_template': 'تیکت #{{ticket_number}} به شما تخصیص داده شد.',
                'email_subject_template': 'تیکت #{{ticket_number}} به شما تخصیص داده شد',
                'email_html_template': '<p>سلام {{staff_name}} عزیز،</p><p>تیکت شماره <strong>#{{ticket_number}}</strong> با موضوع "{{subject}}" به شما تخصیص داده شد.</p><p>لطفاً در اسرع وقت به این تیکت رسیدگی کنید.</p>',
                'sms_template': 'تیکت #{{ticket_number}} به شما تخصیص داده شد.',
                'channels': ['in_app', 'email'],
                'default_priority': 'high',
                'action_url': '/admin/support/ticket/{{ticket_id}}/change/',
                'action_text': 'مشاهده تیکت'
            },
            {
                'code': 'ticket_status_changed',
                'name': 'تغییر وضعیت تیکت',
                'category': NotificationCategory.SUPPORT,
                'title_template': 'تغییر وضعیت تیکت',
                'body_template': 'وضعیت تیکت #{{ticket_number}} به "{{status}}" تغییر کرد.',
                'email_subject_template': 'تغییر وضعیت تیکت #{{ticket_number}}',
                'email_html_template': '<p>سلام {{user_name}} عزیز،</p><p>وضعیت تیکت شماره <strong>#{{ticket_number}}</strong> به "{{status}}" تغییر کرد.</p>',
                'sms_template': 'وضعیت تیکت #{{ticket_number}} به "{{status}}" تغییر کرد.',
                'channels': ['in_app', 'sms'],
                'default_priority': 'normal',
                'action_url': '/support/tickets/{{ticket_id}}',
                'action_text': 'مشاهده تیکت'
            },
            {
                'code': 'ticket_reply_user',
                'name': 'پاسخ جدید تیکت - کاربر',
                'category': NotificationCategory.SUPPORT,
                'title_template': 'پاسخ جدید در تیکت',
                'body_template': 'پاسخ جدیدی در تیکت #{{ticket_number}} دریافت شد.',
                'email_subject_template': 'پاسخ جدید در تیکت #{{ticket_number}}',
                'email_html_template': '<p>سلام {{user_name}} عزیز،</p><p>کارشناس ما پاسخ جدیدی در تیکت شماره <strong>#{{ticket_number}}</strong> ارسال کرده است.</p><p>برای مشاهده پاسخ به پنل کاربری خود مراجعه کنید.</p>',
                'sms_template': 'پاسخ جدیدی در تیکت #{{ticket_number}} دریافت شد.',
                'channels': ['in_app', 'sms', 'email'],
                'default_priority': 'high',
                'action_url': '/support/tickets/{{ticket_id}}',
                'action_text': 'مشاهده پاسخ'
            },
            {
                'code': 'ticket_question_user',
                'name': 'سوال جدید در تیکت - کاربر',
                'category': NotificationCategory.SUPPORT,
                'title_template': 'سوال جدید در تیکت',
                'body_template': 'کارشناس سوالی در تیکت #{{ticket_number}} مطرح کرده است.',
                'email_subject_template': 'سوال جدید در تیکت #{{ticket_number}}',
                'email_html_template': '<p>سلام {{user_name}} عزیز،</p><p>کارشناس ما سوالی در تیکت شماره <strong>#{{ticket_number}}</strong> مطرح کرده است.</p><p>لطفاً در اسرع وقت به این سوال پاسخ دهید.</p>',
                'sms_template': 'کارشناس سوالی در تیکت #{{ticket_number}} مطرح کرده است. لطفاً پاسخ دهید.',
                'channels': ['in_app', 'sms', 'email'],
                'default_priority': 'high',
                'action_url': '/support/tickets/{{ticket_id}}',
                'action_text': 'پاسخ به سوال'
            },
            {
                'code': 'ticket_forwarded_staff',
                'name': 'تیکت ارسال شده - کارشناس',
                'category': NotificationCategory.SUPPORT,
                'title_template': 'تیکت جدید ارسال شده',
                'body_template': 'تیکت #{{ticket_number}} توسط {{sender_name}} به شما ارسال شد.',
                'email_subject_template': 'تیکت #{{ticket_number}} به شما ارسال شد',
                'email_html_template': '<p>سلام {{staff_name}} عزیز،</p><p>تیکت شماره <strong>#{{ticket_number}}</strong> با موضوع "{{subject}}" توسط {{sender_name}} به شما ارسال شد.</p><p>لطفاً در اسرع وقت به این تیکت رسیدگی کنید.</p>',
                'sms_template': 'تیکت #{{ticket_number}} توسط {{sender_name}} به شما ارسال شد.',
                'channels': ['in_app', 'email'],
                'default_priority': 'high',
                'action_url': '/admin/support/ticket/{{ticket_id}}/change/',
                'action_text': 'مشاهده تیکت'
            },
            {
                'code': 'ticket_message_staff',
                'name': 'پیام جدید تیکت - کارشناس',
                'category': NotificationCategory.SUPPORT,
                'title_template': 'پیام جدید در تیکت',
                'body_template': 'پیام جدیدی در تیکت #{{ticket_number}} دریافت شد.',
                'email_subject_template': 'پیام جدید در تیکت #{{ticket_number}}',
                'email_html_template': '<p>سلام {{staff_name}} عزیز،</p><p>کاربر پیام جدیدی در تیکت شماره <strong>#{{ticket_number}}</strong> ارسال کرده است.</p><p>لطفاً به این پیام پاسخ دهید.</p>',
                'sms_template': 'پیام جدیدی در تیکت #{{ticket_number}} دریافت شد.',
                'channels': ['in_app', 'email'],
                'default_priority': 'normal',
                'action_url': '/admin/support/ticket/{{ticket_id}}/change/',
                'action_text': 'پاسخ به پیام'
            },
        ]
        
        created_count = 0
        updated_count = 0
        
        for template_data in templates:
            template, created = NotificationTemplate.objects.update_or_create(
                code=template_data['code'],
                defaults=template_data
            )
            
            if created:
                created_count += 1
                self.stdout.write(self.style.SUCCESS(f'✓ قالب "{template.name}" ایجاد شد'))
            else:
                updated_count += 1
                self.stdout.write(self.style.WARNING(f'○ قالب "{template.name}" به‌روزرسانی شد'))
        
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS(f'✓ {created_count} قالب جدید ایجاد شد'))
        self.stdout.write(self.style.WARNING(f'○ {updated_count} قالب به‌روزرسانی شد'))
        self.stdout.write(self.style.SUCCESS('✓ تمام قالب‌ها با موفقیت آماده شدند'))
