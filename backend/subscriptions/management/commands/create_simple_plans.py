"""
Simple management command to create basic subscription plans without features
"""
from django.core.management.base import BaseCommand
from django.db import transaction
from subscriptions.models import Plan
from decimal import Decimal


class Command(BaseCommand):
    help = 'Create simple subscription plans'
    
    def handle(self, *args, **options):
        self.stdout.write('Creating simple plans...')
        
        with transaction.atomic():
            # Create Free Plan
            free_plan, created = Plan.objects.get_or_create(
                name='رایگان',
                defaults={
                    'description': 'پلن رایگان برای آشنایی با سیستم - 10 سوال در روز',
                    'price': Decimal('0'),
                    'duration_days': 30,
                    'features': {
                        'max_queries_per_day': 10,
                        'max_queries_per_month': 300,
                        'gpt_3_5_access': True,
                        'gpt_4_access': False,
                    },
                    'is_active': True,
                }
            )
            if created:
                self.stdout.write(self.style.SUCCESS('  ✓ Free plan created'))
            else:
                self.stdout.write('  • Free plan already exists')
            
            # Create Basic Plan
            basic_plan, created = Plan.objects.get_or_create(
                name='پایه',
                defaults={
                    'description': 'مناسب برای کاربران شخصی - 50 سوال در روز',
                    'price': Decimal('299000'),
                    'duration_days': 30,
                    'features': {
                        'max_queries_per_day': 50,
                        'max_queries_per_month': 1500,
                        'gpt_3_5_access': True,
                        'gpt_4_access': False,
                    },
                    'is_active': True,
                }
            )
            if created:
                self.stdout.write(self.style.SUCCESS('  ✓ Basic plan created'))
            else:
                self.stdout.write('  • Basic plan already exists')
            
            # Create Professional Plan
            pro_plan, created = Plan.objects.get_or_create(
                name='حرفه‌ای',
                defaults={
                    'description': 'برای کسب‌وکارها - 200 سوال در روز + GPT-4',
                    'price': Decimal('799000'),
                    'duration_days': 30,
                    'features': {
                        'max_queries_per_day': 200,
                        'max_queries_per_month': 6000,
                        'gpt_3_5_access': True,
                        'gpt_4_access': True,
                    },
                    'is_active': True,
                }
            )
            if created:
                self.stdout.write(self.style.SUCCESS('  ✓ Professional plan created'))
            else:
                self.stdout.write('  • Professional plan already exists')
        
        self.stdout.write(self.style.SUCCESS('\n✓ Plans created successfully!'))
