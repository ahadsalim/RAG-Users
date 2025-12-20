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
        
        # 6. ایجاد کاربر سوپر ادمین
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
