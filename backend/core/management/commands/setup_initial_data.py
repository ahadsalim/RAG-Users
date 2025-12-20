"""
Management command برای ایجاد داده‌های اولیه در دیتابیس خالی
این command باید پس از migrate اجرا شود

Usage:
    python manage.py setup_initial_data
    python manage.py setup_initial_data --admin-password=YOUR_PASSWORD
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from decimal import Decimal
import getpass


class Command(BaseCommand):
    help = 'ایجاد داده‌های اولیه برای راه‌اندازی سیستم'

    def add_arguments(self, parser):
        parser.add_argument(
            '--admin-password',
            type=str,
            help='رمز عبور کاربر ادمین (اگر وارد نشود، از شما پرسیده می‌شود)',
        )
        parser.add_argument(
            '--skip-admin',
            action='store_true',
            help='عدم ایجاد کاربر ادمین',
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE('شروع ایجاد داده‌های اولیه...'))
        
        # 1. ایجاد ارز پایه (ریال)
        self.create_currencies()
        
        # 2. ایجاد پلن‌ها
        self.create_plans()
        
        # 3. ایجاد درگاه پرداخت زرین‌پال
        self.create_payment_gateway()
        
        # 4. ایجاد تنظیمات سایت
        self.create_site_settings()
        
        # 5. ایجاد تنظیمات مالی
        self.create_financial_settings()
        
        # 6. ایجاد قالب‌های اعلان
        self.create_notification_templates()
        
        # 7. ایجاد کاربر سوپر ادمین
        if not options['skip_admin']:
            admin_password = options.get('admin_password')
            if not admin_password:
                admin_password = getpass.getpass('رمز عبور ادمین را وارد کنید: ')
            self.create_superuser(admin_password)
        
        self.stdout.write(self.style.SUCCESS('✓ داده‌های اولیه با موفقیت ایجاد شدند!'))

    def create_currencies(self):
        """ایجاد ارز پایه (ریال)"""
        from finance.models import Currency
        
        currency, created = Currency.objects.get_or_create(
            code='IRR',
            defaults={
                'name': 'ریال',
                'symbol': 'ریال',
                'exchange_rate': Decimal('1'),
                'is_base': True,
                'is_active': True,
                'has_decimals': False,
                'decimal_places': 0,
                'display_order': 1,
            }
        )
        
        if created:
            self.stdout.write(self.style.SUCCESS('  ✓ ارز ریال ایجاد شد'))
        else:
            self.stdout.write(self.style.WARNING('  - ارز ریال از قبل وجود دارد'))

    def create_plans(self):
        """ایجاد پلن‌های پایه"""
        from subscriptions.models import Plan
        
        # پلن رایگان
        plan, created = Plan.objects.get_or_create(
            name='رایگان',
            defaults={
                'description': 'پلن رایگان برای شروع کار با سیستم',
                'price': Decimal('0'),
                'duration_days': 30,
                'max_queries_per_day': 10,
                'max_queries_per_month': 200,
                'is_active': True,
                'features': {
                    'web_search': False,
                    'priority_support': False,
                    'advanced_analytics': False,
                },
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS('  ✓ پلن رایگان ایجاد شد'))
        else:
            self.stdout.write(self.style.WARNING('  - پلن رایگان از قبل وجود دارد'))
        
        # پلن نامحدود (برای سوپر ادمین)
        unlimited_plan, created = Plan.objects.get_or_create(
            name='نامحدود',
            defaults={
                'description': 'پلن نامحدود برای مدیران سیستم',
                'price': Decimal('0'),
                'duration_days': 36500,  # 100 سال
                'max_queries_per_day': 999999,
                'max_queries_per_month': 999999,
                'is_active': True,
                'features': {
                    'web_search': True,
                    'priority_support': True,
                    'advanced_analytics': True,
                    'unlimited': True,
                },
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS('  ✓ پلن نامحدود ایجاد شد'))
        else:
            self.stdout.write(self.style.WARNING('  - پلن نامحدود از قبل وجود دارد'))

    def create_payment_gateway(self):
        """ایجاد درگاه پرداخت زرین‌پال"""
        from finance.models import PaymentGateway
        
        gateway, created = PaymentGateway.objects.get_or_create(
            name='زرین‌پال',
            defaults={
                'merchant_id': '',  # باید توسط ادمین تنظیم شود
                'is_active': False,  # غیرفعال تا تنظیمات کامل شود
                'is_default': True,
                'commission_rate': Decimal('0'),
                'display_order': 1,
            }
        )
        
        if created:
            self.stdout.write(self.style.SUCCESS('  ✓ درگاه زرین‌پال ایجاد شد (نیاز به تنظیم merchant_id)'))
        else:
            self.stdout.write(self.style.WARNING('  - درگاه زرین‌پال از قبل وجود دارد'))

    def create_site_settings(self):
        """ایجاد تنظیمات سایت"""
        from core.models import SiteSettings
        
        settings, created = SiteSettings.objects.get_or_create(
            pk=1,
            defaults={
                'frontend_site_name': 'مشاور هوشمند کسب و کار',
                'support_phone': '021-91097737',
                'support_email': 'support@tejarat.chat',
            }
        )
        
        if created:
            self.stdout.write(self.style.SUCCESS('  ✓ تنظیمات سایت ایجاد شد'))
        else:
            self.stdout.write(self.style.WARNING('  - تنظیمات سایت از قبل وجود دارد'))

    def create_financial_settings(self):
        """ایجاد تنظیمات مالی"""
        from finance.models import FinancialSettings
        
        settings, created = FinancialSettings.objects.get_or_create(
            pk=1,
            defaults={
                'company_name': 'شرکت تجارت چت',
                'tax_rate': Decimal('10'),
                'national_id': '',
                'company_address': '',
                'postal_code': '',
                'phone': '',
            }
        )
        
        if created:
            self.stdout.write(self.style.SUCCESS('  ✓ تنظیمات مالی ایجاد شد'))
        else:
            self.stdout.write(self.style.WARNING('  - تنظیمات مالی از قبل وجود دارد'))

    def create_superuser(self, password):
        """ایجاد کاربر سوپر ادمین"""
        User = get_user_model()
        from subscriptions.models import Subscription, Plan
        from datetime import timedelta
        
        user = User.objects.filter(phone_number='09121082690').first()
        
        if user:
            self.stdout.write(self.style.WARNING('  - کاربر سوپر ادمین از قبل وجود دارد'))
        else:
            user = User.objects.create_superuser(
                phone_number='09121082690',
                email='admin@tejarat.chat',
                password=password,
                first_name='مدیر',
                last_name='سیستم',
            )
            self.stdout.write(self.style.SUCCESS(f'  ✓ کاربر سوپر ادمین ایجاد شد: {user.phone_number}'))
        
        # ایجاد اشتراک نامحدود برای سوپر ادمین
        if not Subscription.objects.filter(user=user).exists():
            unlimited_plan = Plan.objects.filter(name='نامحدود').first()
            if unlimited_plan:
                Subscription.objects.create(
                    user=user,
                    plan=unlimited_plan,
                    status='active',
                    start_date=timezone.now(),
                    end_date=timezone.now() + timedelta(days=36500),  # 100 سال
                    auto_renew=False
                )
                self.stdout.write(self.style.SUCCESS('  ✓ اشتراک نامحدود برای سوپر ادمین ایجاد شد'))

    def create_notification_templates(self):
        """ایجاد قالب‌های اعلان"""
        from notifications.models import NotificationTemplate, NotificationCategory
        
        templates = [
            # اعلان‌های اشتراک
            {
                'code': 'subscription_expiring',
                'name': 'نزدیک به انقضای اشتراک',
                'category': 'subscription',
                'title_template': 'اشتراک شما {{days_remaining}} روز دیگر منقضی می‌شود',
                'body_template': '{{user_name}} عزیز، اشتراک {{plan_name}} شما در تاریخ {{end_date}} منقضی می‌شود. برای تمدید اقدام کنید.',
                'sms_template': 'اشتراک شما {{days_remaining}} روز دیگر منقضی می‌شود. برای تمدید وارد سایت شوید.',
                'channels': ['sms', 'in_app'],
                'default_priority': 'high',
            },
            {
                'code': 'subscription_expired',
                'name': 'انقضای اشتراک',
                'category': 'subscription',
                'title_template': 'اشتراک شما منقضی شد',
                'body_template': '{{user_name}} عزیز، اشتراک {{plan_name}} شما منقضی شده است. برای ادامه استفاده، اقدام به تمدید کنید.',
                'sms_template': 'اشتراک شما منقضی شد. برای تمدید وارد سایت شوید.',
                'channels': ['sms', 'in_app'],
                'default_priority': 'urgent',
            },
            {
                'code': 'subscription_renewed',
                'name': 'تمدید اشتراک',
                'category': 'subscription',
                'title_template': 'اشتراک شما تمدید شد',
                'body_template': '{{user_name}} عزیز، اشتراک {{plan_name}} شما با موفقیت تمدید شد. تاریخ انقضای جدید: {{end_date}}',
                'sms_template': 'اشتراک {{plan_name}} شما تمدید شد. انقضا: {{end_date}}',
                'channels': ['sms', 'in_app'],
                'default_priority': 'normal',
            },
            {
                'code': 'subscription_activated',
                'name': 'فعال‌سازی اشتراک',
                'category': 'subscription',
                'title_template': 'اشتراک شما فعال شد',
                'body_template': '{{user_name}} عزیز، اشتراک {{plan_name}} شما با موفقیت فعال شد. تاریخ انقضا: {{expiry_date}}',
                'sms_template': 'اشتراک {{plan_name}} فعال شد. انقضا: {{expiry_date}}',
                'channels': ['sms', 'in_app'],
                'default_priority': 'high',
            },
            # اعلان‌های سهمیه
            {
                'code': 'quota_warning',
                'name': 'هشدار سهمیه',
                'category': 'subscription',
                'title_template': '{{usage_percentage}}% از سهمیه {{quota_type}} شما استفاده شده',
                'body_template': '{{user_name}} عزیز، {{usage_percentage}}% از سهمیه {{quota_type}} ({{limit_text}}) شما استفاده شده است.',
                'sms_template': '{{usage_percentage}}% سهمیه {{quota_type}} شما استفاده شده.',
                'channels': ['in_app'],
                'default_priority': 'normal',
            },
            {
                'code': 'quota_exceeded',
                'name': 'اتمام سهمیه',
                'category': 'subscription',
                'title_template': 'سهمیه {{quota_type}} شما تمام شد',
                'body_template': '{{user_name}} عزیز، سهمیه {{quota_type}} شما به پایان رسیده است. برای ادامه استفاده، پلن خود را ارتقا دهید.',
                'sms_template': 'سهمیه {{quota_type}} شما تمام شد. برای ارتقا وارد سایت شوید.',
                'channels': ['sms', 'in_app'],
                'default_priority': 'high',
            },
            # اعلان‌های پرداخت
            {
                'code': 'payment_success',
                'name': 'پرداخت موفق',
                'category': 'payment',
                'title_template': 'پرداخت شما موفق بود',
                'body_template': '{{user_name}} عزیز، پرداخت {{amount}} تومان برای {{plan_name}} با موفقیت انجام شد.',
                'sms_template': 'پرداخت {{amount}} تومان برای {{plan_name}} موفق بود.',
                'channels': ['sms', 'in_app'],
                'default_priority': 'normal',
            },
            {
                'code': 'payment_failed',
                'name': 'پرداخت ناموفق',
                'category': 'payment',
                'title_template': 'پرداخت شما ناموفق بود',
                'body_template': '{{user_name}} عزیز، پرداخت {{amount}} تومان ناموفق بود. علت: {{error_message}}',
                'sms_template': 'پرداخت {{amount}} تومان ناموفق بود.',
                'channels': ['sms', 'in_app'],
                'default_priority': 'high',
            },
            # اعلان عضویت کاربر جدید (برای ادمین‌ها)
            {
                'code': 'new_user_registered',
                'name': 'عضویت کاربر جدید',
                'category': 'system',
                'title_template': 'کاربر جدید ثبت‌نام کرد',
                'body_template': 'کاربر جدید با شماره {{user_phone}} در سایت ثبت‌نام کرد.',
                'sms_template': 'کاربر جدید: {{user_phone}}',
                'channels': ['sms'],
                'default_priority': 'low',
            },
            # اعلان‌های حساب کاربری
            {
                'code': 'welcome',
                'name': 'خوش‌آمدگویی',
                'category': 'account',
                'title_template': 'به {{site_name}} خوش آمدید',
                'body_template': '{{user_name}} عزیز، به {{site_name}} خوش آمدید! از اینکه ما را انتخاب کردید متشکریم.',
                'sms_template': '{{user_name}} عزیز، به {{site_name}} خوش آمدید!',
                'channels': ['sms', 'in_app'],
                'default_priority': 'normal',
            },
            {
                'code': 'login_from_new_device',
                'name': 'ورود از دستگاه جدید',
                'category': 'security',
                'title_template': 'ورود از دستگاه جدید',
                'body_template': '{{user_name}} عزیز، ورود جدیدی از دستگاه {{device_name}} در تاریخ {{login_time}} ثبت شد. اگر شما نبودید، رمز عبور خود را تغییر دهید.',
                'sms_template': 'ورود جدید از {{device_name}}. اگر شما نبودید رمز را تغییر دهید.',
                'channels': ['sms', 'in_app'],
                'default_priority': 'high',
            },
            {
                'code': 'password_changed',
                'name': 'تغییر رمز عبور',
                'category': 'security',
                'title_template': 'رمز عبور شما تغییر کرد',
                'body_template': '{{user_name}} عزیز، رمز عبور حساب شما با موفقیت تغییر کرد. اگر شما این کار را انجام نداده‌اید، فوراً با پشتیبانی تماس بگیرید.',
                'sms_template': 'رمز عبور شما تغییر کرد. اگر شما نبودید با پشتیبانی تماس بگیرید.',
                'channels': ['sms', 'in_app'],
                'default_priority': 'high',
            },
        ]
        
        created_count = 0
        for template_data in templates:
            template, created = NotificationTemplate.objects.update_or_create(
                code=template_data['code'],
                defaults=template_data
            )
            if created:
                created_count += 1
        
        if created_count > 0:
            self.stdout.write(self.style.SUCCESS(f'  ✓ {created_count} قالب اعلان ایجاد شد'))
        else:
            self.stdout.write(self.style.WARNING('  - قالب‌های اعلان از قبل وجود دارند'))
