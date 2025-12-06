"""
ایجاد قالب‌های اعلان برای اشتراک‌ها
"""
from django.core.management.base import BaseCommand
from notifications.models import NotificationTemplate


class Command(BaseCommand):
    help = 'Create notification templates for subscriptions'
    
    def handle(self, *args, **options):
        templates = [
            {
                'code': 'subscription_expiring',
                'name': 'هشدار انقضای اشتراک',
                'category': 'subscription',
                'title_template': 'اشتراک شما در حال انقضاست',
                'body_template': '''{{ user_name }} عزیز،
اشتراک {{ plan_name }} شما تا {{ days_remaining }} روز دیگر ({{ end_date }}) منقضی می‌شود.
برای ادامه استفاده از خدمات، لطفاً اشتراک خود را تمدید کنید.''',
                'sms_template': 'اشتراک {{ plan_name }} شما تا {{ days_remaining }} روز دیگر منقضی می‌شود. برای تمدید به tejarat.chat مراجعه کنید.',
                'email_subject_template': 'هشدار: اشتراک شما در حال انقضاست',
                'email_html_template': '''<div dir="rtl" style="font-family: Tahoma, Arial; padding: 20px;">
<h2>{{ user_name }} عزیز،</h2>
<p>اشتراک <strong>{{ plan_name }}</strong> شما تا <strong>{{ days_remaining }} روز دیگر</strong> ({{ end_date }}) منقضی می‌شود.</p>
<p>برای ادامه استفاده از خدمات، لطفاً اشتراک خود را تمدید کنید.</p>
<a href="https://tejarat.chat{{ renewal_url }}" style="background: #4CAF50; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">تمدید اشتراک</a>
</div>''',
                'channels': ['in_app', 'email', 'sms'],
            },
            {
                'code': 'subscription_expired',
                'name': 'اعلان انقضای اشتراک',
                'category': 'subscription',
                'title_template': 'اشتراک شما منقضی شد',
                'body_template': '''{{ user_name }} عزیز،
اشتراک {{ plan_name }} شما منقضی شده است.
برای ادامه استفاده از خدمات، لطفاً یک پلن جدید انتخاب کنید.''',
                'sms_template': 'اشتراک {{ plan_name }} شما منقضی شد. برای خرید پلن جدید به tejarat.chat مراجعه کنید.',
                'email_subject_template': 'اشتراک شما منقضی شد',
                'email_html_template': '''<div dir="rtl" style="font-family: Tahoma, Arial; padding: 20px;">
<h2>{{ user_name }} عزیز،</h2>
<p>اشتراک <strong>{{ plan_name }}</strong> شما منقضی شده است.</p>
<p>برای ادامه استفاده از خدمات، لطفاً یک پلن جدید انتخاب کنید.</p>
<a href="https://tejarat.chat{{ renewal_url }}" style="background: #2196F3; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">مشاهده پلن‌ها</a>
</div>''',
                'channels': ['in_app', 'email', 'sms'],
            },
            {
                'code': 'subscription_renewed',
                'name': 'اعلان تمدید اشتراک',
                'category': 'subscription',
                'title_template': 'اشتراک شما تمدید شد',
                'body_template': '''{{ user_name }} عزیز،
اشتراک {{ plan_name }} شما با موفقیت تمدید شد.
تاریخ انقضای جدید: {{ end_date }}''',
                'sms_template': 'اشتراک {{ plan_name }} شما تمدید شد. تاریخ انقضا: {{ end_date }}',
                'email_subject_template': 'اشتراک شما با موفقیت تمدید شد',
                'email_html_template': '''<div dir="rtl" style="font-family: Tahoma, Arial; padding: 20px;">
<h2>{{ user_name }} عزیز،</h2>
<p>اشتراک <strong>{{ plan_name }}</strong> شما با موفقیت تمدید شد.</p>
<p>تاریخ انقضای جدید: <strong>{{ end_date }}</strong></p>
<a href="https://tejarat.chat{{ dashboard_url }}" style="background: #4CAF50; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">رفتن به داشبورد</a>
</div>''',
                'channels': ['in_app', 'email', 'sms'],
            },
            {
                'code': 'payment_success',
                'name': 'اعلان پرداخت موفق',
                'category': 'payment',
                'title_template': 'پرداخت موفق',
                'body_template': '''{{ user_name }} عزیز،
پرداخت شما به مبلغ {{ amount }} ریال برای پلن {{ plan_name }} با موفقیت انجام شد.''',
                'sms_template': 'پرداخت {{ amount }} ریال برای {{ plan_name }} موفق بود. tejarat.chat',
                'email_subject_template': 'پرداخت شما با موفقیت انجام شد',
                'email_html_template': '''<div dir="rtl" style="font-family: Tahoma, Arial; padding: 20px;">
<h2>{{ user_name }} عزیز،</h2>
<p>پرداخت شما به مبلغ <strong>{{ amount }} ریال</strong> برای پلن <strong>{{ plan_name }}</strong> با موفقیت انجام شد.</p>
<p>از اعتماد شما متشکریم.</p>
<a href="https://tejarat.chat{{ dashboard_url }}" style="background: #4CAF50; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">رفتن به داشبورد</a>
</div>''',
                'channels': ['in_app', 'email', 'sms'],
            },
            {
                'code': 'payment_failed',
                'name': 'اعلان پرداخت ناموفق',
                'category': 'payment',
                'title_template': 'پرداخت ناموفق',
                'body_template': '''{{ user_name }} عزیز،
متأسفانه پرداخت شما به مبلغ {{ amount }} ریال ناموفق بود.
علت: {{ error_message }}''',
                'sms_template': 'پرداخت {{ amount }} ریال ناموفق بود. لطفا مجددا تلاش کنید. tejarat.chat',
                'email_subject_template': 'پرداخت شما ناموفق بود',
                'email_html_template': '''<div dir="rtl" style="font-family: Tahoma, Arial; padding: 20px;">
<h2>{{ user_name }} عزیز،</h2>
<p>متأسفانه پرداخت شما به مبلغ <strong>{{ amount }} ریال</strong> ناموفق بود.</p>
<p>علت: {{ error_message }}</p>
<a href="https://tejarat.chat{{ retry_url }}" style="background: #f44336; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">تلاش مجدد</a>
</div>''',
                'channels': ['in_app', 'email'],
            },
            {
                'code': 'quota_warning',
                'name': 'هشدار سهمیه',
                'category': 'subscription',
                'title_template': 'هشدار: سهمیه {{ quota_type }} شما رو به اتمام است',
                'body_template': '''{{ user_name }} عزیز،
{{ usage_percentage }}% از سهمیه {{ quota_type }} شما ({{ limit_text }}) استفاده شده است.
برای افزایش سهمیه، پلن خود را ارتقا دهید.''',
                'sms_template': '{{ usage_percentage }}% سهمیه {{ quota_type }} استفاده شده. برای ارتقا به tejarat.chat مراجعه کنید.',
                'email_subject_template': 'هشدار: سهمیه شما رو به اتمام است',
                'email_html_template': '''<div dir="rtl" style="font-family: Tahoma, Arial; padding: 20px;">
<h2>{{ user_name }} عزیز،</h2>
<p><strong>{{ usage_percentage }}%</strong> از سهمیه {{ quota_type }} شما ({{ limit_text }}) استفاده شده است.</p>
<p>برای افزایش سهمیه، پلن خود را ارتقا دهید.</p>
<a href="https://tejarat.chat{{ upgrade_url }}" style="background: #FF9800; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">ارتقای پلن</a>
</div>''',
                'channels': ['in_app', 'email'],
            },
            {
                'code': 'quota_exceeded',
                'name': 'اتمام سهمیه',
                'category': 'subscription',
                'title_template': 'سهمیه {{ quota_type }} شما تمام شد',
                'body_template': '''{{ user_name }} عزیز،
سهمیه {{ quota_type }} شما به پایان رسیده است.
برای ادامه استفاده، پلن خود را ارتقا دهید یا تا فردا صبر کنید.''',
                'sms_template': 'سهمیه {{ quota_type }} شما تمام شد. برای ارتقا به tejarat.chat مراجعه کنید.',
                'email_subject_template': 'سهمیه شما به پایان رسید',
                'email_html_template': '''<div dir="rtl" style="font-family: Tahoma, Arial; padding: 20px;">
<h2>{{ user_name }} عزیز،</h2>
<p>سهمیه {{ quota_type }} شما به پایان رسیده است.</p>
<p>برای ادامه استفاده، پلن خود را ارتقا دهید یا تا فردا صبر کنید.</p>
<a href="https://tejarat.chat{{ upgrade_url }}" style="background: #f44336; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">ارتقای پلن</a>
</div>''',
                'channels': ['in_app', 'email', 'sms'],
            },
        ]
        
        created_count = 0
        updated_count = 0
        
        for template_data in templates:
            code = template_data.pop('code')
            obj, created = NotificationTemplate.objects.update_or_create(
                code=code,
                defaults=template_data
            )
            if created:
                created_count += 1
                self.stdout.write(self.style.SUCCESS(f'  ✓ Created: {code}'))
            else:
                updated_count += 1
                self.stdout.write(self.style.WARNING(f'  ↻ Updated: {code}'))
        
        self.stdout.write(self.style.SUCCESS(
            f'\n✓ Done! Created: {created_count}, Updated: {updated_count}'
        ))
