"""
دستور مدیریتی برای راه‌اندازی اولیه درگاه‌های پرداخت
"""
from django.core.management.base import BaseCommand
from finance.models import PaymentGateway, Currency


class Command(BaseCommand):
    help = 'راه‌اندازی اولیه درگاه‌های پرداخت'

    def handle(self, *args, **options):
        # دریافت ارز IRR
        irr_currency, _ = Currency.objects.get_or_create(
            code='IRR',
            defaults={
                'name': 'تومان',
                'symbol': 'تومان',
                'has_decimals': False,
                'decimal_places': 0,
                'exchange_rate': 1
            }
        )
        
        # دریافت ارز USD
        usd_currency, _ = Currency.objects.get_or_create(
            code='USD',
            defaults={
                'name': 'دلار آمریکا',
                'symbol': '$',
                'has_decimals': True,
                'decimal_places': 2,
                'exchange_rate': 60000  # نرخ تقریبی
            }
        )
        
        # 1. زرین‌پال - درگاه پیش‌فرض
        zarinpal, created = PaymentGateway.objects.get_or_create(
            name='زرین‌پال',
            defaults={
                'merchant_id': '',
                'is_active': True,
                'is_sandbox': True,  # حالت تست
                'is_default': True,  # درگاه پیش‌فرض
                'commission_percentage': 0,
                'display_order': 1
            }
        )
        if created:
            zarinpal.supported_currencies.add(irr_currency)
            self.stdout.write(self.style.SUCCESS('✓ زرین‌پال ایجاد شد (پیش‌فرض، حالت تست)'))
        else:
            # به‌روزرسانی
            zarinpal.is_active = True
            zarinpal.is_sandbox = True
            zarinpal.is_default = True
            zarinpal.display_order = 1
            zarinpal.save()
            zarinpal.supported_currencies.add(irr_currency)
            self.stdout.write(self.style.SUCCESS('✓ زرین‌پال به‌روزرسانی شد'))
        
        # 2. درگاه تست تجارت
        tejarat_test, created = PaymentGateway.objects.get_or_create(
            name='درگاه تست تجارت',
            defaults={
                'merchant_id': 'MERCHANT_001',
                'api_key': '',
                'is_active': True,
                'is_sandbox': True,  # حالت تست
                'is_default': False,
                'commission_percentage': 0,
                'display_order': 2
            }
        )
        if created:
            tejarat_test.supported_currencies.add(irr_currency)
            self.stdout.write(self.style.SUCCESS('✓ درگاه تست تجارت ایجاد شد (حالت تست)'))
        else:
            tejarat_test.is_active = True
            tejarat_test.is_sandbox = True
            tejarat_test.is_default = False
            tejarat_test.merchant_id = 'MERCHANT_001'
            tejarat_test.display_order = 2
            tejarat_test.save()
            tejarat_test.supported_currencies.add(irr_currency)
            self.stdout.write(self.style.SUCCESS('✓ درگاه تست تجارت به‌روزرسانی شد'))
        
        # 3. Plisio - ارز دیجیتال
        plisio, created = PaymentGateway.objects.get_or_create(
            name='Plisio',
            defaults={
                'api_key': 'dd_ujqqgwkdaKp7IHHnRxFRDXvPajxKBYcOfZSA9XZBDpVwW_ELAyQRfZi407mLY',
                'is_active': True,
                'is_sandbox': False,  # حالت واقعی
                'is_default': False,
                'commission_percentage': 0.5,
                'display_order': 3
            }
        )
        if created:
            plisio.supported_currencies.add(usd_currency)
            self.stdout.write(self.style.SUCCESS('✓ Plisio ایجاد شد (فعال، حالت واقعی)'))
        else:
            plisio.is_active = True
            plisio.is_sandbox = False
            plisio.is_default = False
            plisio.api_key = 'dd_ujqqgwkdaKp7IHHnRxFRDXvPajxKBYcOfZSA9XZBDpVwW_ELAyQRfZi407mLY'
            plisio.display_order = 3
            plisio.save()
            plisio.supported_currencies.add(usd_currency)
            self.stdout.write(self.style.SUCCESS('✓ Plisio به‌روزرسانی شد'))
        
        self.stdout.write(self.style.SUCCESS('\n=== خلاصه تنظیمات ==='))
        self.stdout.write(f'1. زرین‌پال: فعال={zarinpal.is_active}, تست={zarinpal.is_sandbox}, پیش‌فرض={zarinpal.is_default}')
        self.stdout.write(f'2. درگاه تست تجارت: فعال={tejarat_test.is_active}, تست={tejarat_test.is_sandbox}, پیش‌فرض={tejarat_test.is_default}')
        self.stdout.write(f'3. Plisio: فعال={plisio.is_active}, تست={plisio.is_sandbox}, پیش‌فرض={plisio.is_default}')
        self.stdout.write(self.style.SUCCESS('\n✅ راه‌اندازی درگاه‌های پرداخت با موفقیت انجام شد'))
