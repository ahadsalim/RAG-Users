from django.core.management.base import BaseCommand
from core.models import Currency, SiteSettings, PaymentGateway


class Command(BaseCommand):
    help = 'Initialize site settings with default currencies and settings'
    
    def handle(self, *args, **options):
        self.stdout.write('Initializing site settings...')
        
        # Create Currencies
        currencies_data = [
            {
                'code': 'IRR',
                'name': 'ریال ایران',
                'symbol': '﷼',
                'has_decimals': False,
                'decimal_places': 0,
                'exchange_rate': 1,  # Base currency
                'is_active': True,
                'display_order': 1
            },
            {
                'code': 'IRT',
                'name': 'تومان',
                'symbol': 'تومان',
                'has_decimals': False,
                'decimal_places': 0,
                'exchange_rate': 10,  # 1 Toman = 10 Rial
                'is_active': True,
                'display_order': 2
            },
            {
                'code': 'USD',
                'name': 'دلار آمریکا',
                'symbol': '$',
                'has_decimals': True,
                'decimal_places': 2,
                'exchange_rate': 500000,  # Example rate: 1 USD = 500,000 IRR
                'is_active': True,
                'display_order': 3
            },
            {
                'code': 'EUR',
                'name': 'یورو',
                'symbol': '€',
                'has_decimals': True,
                'decimal_places': 2,
                'exchange_rate': 550000,  # Example rate: 1 EUR = 550,000 IRR
                'is_active': True,
                'display_order': 4
            },
        ]
        
        for currency_data in currencies_data:
            currency, created = Currency.objects.get_or_create(
                code=currency_data['code'],
                defaults=currency_data
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'✓ Created currency: {currency.name}'))
            else:
                self.stdout.write(f'  Currency already exists: {currency.name}')
        
        # Create Payment Gateways
        gateways_data = [
            {
                'name': 'زرین‌پال',
                'gateway_type': 'zarinpal',
                'is_active': True,
                'is_sandbox': True,
                'commission_percentage': 2.5,
                'display_order': 1
            },
            {
                'name': 'آیدی‌پی',
                'gateway_type': 'idpay',
                'is_active': True,
                'is_sandbox': True,
                'commission_percentage': 2.0,
                'display_order': 2
            },
        ]
        
        created_gateways = []
        for gateway_data in gateways_data:
            gateway, created = PaymentGateway.objects.get_or_create(
                gateway_type=gateway_data['gateway_type'],
                defaults=gateway_data
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'✓ Created payment gateway: {gateway.name}'))
                created_gateways.append(gateway)
            else:
                self.stdout.write(f'  Payment gateway already exists: {gateway.name}')
                created_gateways.append(gateway)
        
        # Add supported currencies to gateways
        irr = Currency.objects.get(code='IRR')
        irt = Currency.objects.get(code='IRT')
        for gateway in created_gateways:
            gateway.supported_currencies.add(irr, irt)
        
        # Create Site Settings
        settings, created = SiteSettings.objects.get_or_create(pk=1)
        if created:
            # Set defaults
            settings.frontend_site_name = 'تجارت چت'
            settings.admin_site_name = 'پنل مدیریت تجارت چت'
            settings.base_currency = irt  # Default to Toman
            if created_gateways:
                settings.default_payment_gateway = created_gateways[0]
            settings.save()
            self.stdout.write(self.style.SUCCESS('✓ Created site settings'))
        else:
            # Update currency if not set
            if not settings.base_currency:
                settings.base_currency = irt
                settings.save()
            self.stdout.write('  Site settings already exist')
        
        self.stdout.write(self.style.SUCCESS('\n✅ Site settings initialized successfully!'))
        self.stdout.write(f'\nBase currency: {settings.base_currency}')
        self.stdout.write(f'Default payment gateway: {settings.default_payment_gateway}')
