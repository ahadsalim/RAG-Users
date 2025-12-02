"""
ایجاد قالب‌های اعلان مربوط به اشتراک
"""
from django.core.management.base import BaseCommand
from django.db import transaction
from notifications.models import NotificationTemplate


class Command(BaseCommand):
    help = 'Create notification templates for subscription events'
    
    def handle(self, *args, **options):
        self.stdout.write('Creating subscription notification templates...')
        
        templates = [
            {
                'code': 'subscription_expiring',
                'name': 'اشتراک در حال انقضا',
                'category': 'subscription',
                'title_template': 'اشتراک شما {{ days_remaining }} روز دیگر منقضی می‌شود',
                'body_template': '''{{ user_name }} عزیز،

اشتراک {{ plan_name }} شما {{ days_remaining }} روز دیگر ({{ end_date }}) منقضی می‌شود.

برای ادامه استفاده از خدمات، لطفاً اشتراک خود را تمدید کنید.''',
                'email_subject_template': '⚠️ اشتراک شما {{ days_remaining }} روز دیگر منقضی می‌شود',
                'sms_template': '{{ user_name }} عزیز، اشتراک {{ plan_name }} شما {{ days_remaining }} روز دیگر منقضی می‌شود. برای تمدید به پنل کاربری مراجعه کنید.',
                'channels': ['email', 'sms', 'in_app', 'push'],
                'default_priority': 'high',
                'action_url': '{{ renewal_url }}',
                'action_text': 'تمدید اشتراک',
            },
            {
                'code': 'subscription_expired',
                'name': 'اشتراک منقضی شده',
                'category': 'subscription',
                'title_template': 'اشتراک شما منقضی شد',
                'body_template': '''{{ user_name }} عزیز،

اشتراک {{ plan_name }} شما منقضی شده است.

برای ادامه استفاده از خدمات، لطفاً یک پلن جدید انتخاب کنید.''',
                'email_subject_template': '❌ اشتراک شما منقضی شد',
                'sms_template': '{{ user_name }} عزیز، اشتراک شما منقضی شد. برای ادامه استفاده، اشتراک جدید خریداری کنید.',
                'channels': ['email', 'sms', 'in_app', 'push'],
                'default_priority': 'high',
                'action_url': '{{ renewal_url }}',
                'action_text': 'خرید اشتراک',
            },
            {
                'code': 'quota_warning',
                'name': 'هشدار سهمیه',
                'category': 'subscription',
                'title_template': '{{ usage_percentage }}% سهمیه {{ quota_type }} استفاده شده',
                'body_template': '''{{ user_name }} عزیز،

شما {{ usage_percentage }}% از سهمیه {{ quota_type }} خود ({{ limit_text }}) را استفاده کرده‌اید.

برای افزایش سهمیه، می‌توانید پلن خود را ارتقا دهید.''',
                'email_subject_template': '⚠️ {{ usage_percentage }}% سهمیه {{ quota_type }} استفاده شده',
                'sms_template': '{{ user_name }} عزیز، {{ usage_percentage }}% سهمیه {{ quota_type }} شما استفاده شده. برای ارتقا پلن به پنل مراجعه کنید.',
                'channels': ['email', 'in_app'],
                'default_priority': 'normal',
                'action_url': '{{ upgrade_url }}',
                'action_text': 'ارتقا پلن',
            },
            {
                'code': 'quota_exceeded',
                'name': 'سهمیه تمام شده',
                'category': 'subscription',
                'title_template': 'سهمیه {{ quota_type }} شما تمام شد',
                'body_template': '''{{ user_name }} عزیز،

سهمیه {{ quota_type }} شما تمام شده است.

برای ادامه استفاده، می‌توانید پلن خود را ارتقا دهید یا تا فردا صبر کنید.''',
                'email_subject_template': '❌ سهمیه {{ quota_type }} شما تمام شد',
                'sms_template': '{{ user_name }} عزیز، سهمیه {{ quota_type }} شما تمام شد. برای ادامه، پلن را ارتقا دهید.',
                'channels': ['email', 'sms', 'in_app', 'push'],
                'default_priority': 'high',
                'action_url': '{{ upgrade_url }}',
                'action_text': 'ارتقا پلن',
            },
            {
                'code': 'subscription_renewed',
                'name': 'تمدید اشتراک',
                'category': 'subscription',
                'title_template': 'اشتراک شما تمدید شد',
                'body_template': '''{{ user_name }} عزیز،

اشتراک {{ plan_name }} شما با موفقیت تمدید شد.

تاریخ انقضای جدید: {{ end_date }}

از اعتماد شما سپاسگزاریم.''',
                'email_subject_template': '✅ اشتراک شما تمدید شد',
                'sms_template': '{{ user_name }} عزیز، اشتراک {{ plan_name }} شما تا {{ end_date }} تمدید شد.',
                'channels': ['email', 'sms', 'in_app'],
                'default_priority': 'normal',
                'action_url': '{{ dashboard_url }}',
                'action_text': 'مشاهده پنل',
            },
            {
                'code': 'payment_success',
                'name': 'پرداخت موفق',
                'category': 'payment',
                'title_template': 'پرداخت موفق - {{ amount }} ریال',
                'body_template': '''{{ user_name }} عزیز،

پرداخت شما به مبلغ {{ amount }} ریال برای پلن {{ plan_name }} با موفقیت انجام شد.

از اعتماد شما سپاسگزاریم.''',
                'email_subject_template': '✅ پرداخت موفق - {{ amount }} ریال',
                'sms_template': '{{ user_name }} عزیز، پرداخت {{ amount }} ریال برای {{ plan_name }} موفق بود.',
                'channels': ['email', 'sms', 'in_app'],
                'default_priority': 'normal',
                'action_url': '{{ dashboard_url }}',
                'action_text': 'مشاهده پنل',
            },
            {
                'code': 'payment_failed',
                'name': 'پرداخت ناموفق',
                'category': 'payment',
                'title_template': 'پرداخت ناموفق',
                'body_template': '''{{ user_name }} عزیز،

متأسفانه پرداخت شما به مبلغ {{ amount }} ریال ناموفق بود.

علت: {{ error_message }}

لطفاً دوباره تلاش کنید.''',
                'email_subject_template': '❌ پرداخت ناموفق',
                'sms_template': '{{ user_name }} عزیز، پرداخت {{ amount }} ریال ناموفق بود. لطفا دوباره تلاش کنید.',
                'channels': ['email', 'sms', 'in_app'],
                'default_priority': 'high',
                'action_url': '{{ retry_url }}',
                'action_text': 'تلاش مجدد',
            },
        ]
        
        with transaction.atomic():
            for template_data in templates:
                template, created = NotificationTemplate.objects.update_or_create(
                    code=template_data['code'],
                    defaults=template_data
                )
                
                if created:
                    self.stdout.write(self.style.SUCCESS(f'  ✓ Created: {template.name}'))
                else:
                    self.stdout.write(f'  • Updated: {template.name}')
        
        self.stdout.write(self.style.SUCCESS(f'\n✓ {len(templates)} templates created/updated!'))
