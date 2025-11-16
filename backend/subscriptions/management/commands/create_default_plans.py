from django.core.management.base import BaseCommand
from django.db import transaction
from subscriptions.models import Plan, PlanFeature
from decimal import Decimal


class Command(BaseCommand):
    help = 'Create default subscription plans'
    
    def handle(self, *args, **options):
        self.stdout.write('Creating default plans...')
        
        with transaction.atomic():
            # Create Features first
            features = self.create_features()
            
            # Create Plans
            self.create_free_plan(features)
            self.create_basic_plan(features)
            self.create_professional_plan(features)
            self.create_enterprise_plan(features)
        
        self.stdout.write(self.style.SUCCESS('✓ Default plans created successfully!'))
    
    def create_features(self):
        """Create default features"""
        features_data = [
            ('ai_gpt35', 'دسترسی به GPT-3.5', 'استفاده از مدل GPT-3.5 برای پاسخ‌دهی', 'ai'),
            ('ai_gpt4', 'دسترسی به GPT-4', 'استفاده از مدل پیشرفته GPT-4', 'ai'),
            ('ai_claude', 'دسترسی به Claude', 'استفاده از مدل Claude Anthropic', 'ai'),
            ('priority_queue', 'صف اولویت', 'پردازش سریع‌تر درخواست‌ها', 'support'),
            ('phone_support', 'پشتیبانی تلفنی', 'پشتیبانی مستقیم تلفنی', 'support'),
            ('custom_training', 'آموزش اختصاصی', 'آموزش مدل روی داده‌های شما', 'ai'),
            ('api_access', 'دسترسی API', 'استفاده از API برای یکپارچه‌سازی', 'api'),
            ('webhook', 'Webhook', 'دریافت اطلاع‌رسانی از طریق Webhook', 'api'),
            ('export_data', 'خروجی داده', 'دانلود داده‌ها در فرمت‌های مختلف', 'storage'),
            ('team_collaboration', 'همکاری تیمی', 'افزودن اعضای تیم', 'support'),
            ('custom_branding', 'برندسازی', 'سفارشی‌سازی رابط کاربری', 'integration'),
            ('analytics', 'گزارش‌گیری پیشرفته', 'دسترسی به گزارش‌های تحلیلی', 'analytics'),
        ]
        
        features = {}
        for code, name, desc, category in features_data:
            feature, created = PlanFeature.objects.get_or_create(
                code=code,
                defaults={
                    'name': name,
                    'description': desc,
                    'category': category,
                    'is_active': True
                }
            )
            features[code] = feature
            if created:
                self.stdout.write(f'  ✓ Feature created: {name}')
        
        return features
    
    def create_free_plan(self, features):
        """Create Free plan"""
        plan, created = Plan.objects.get_or_create(
            slug='free',
            defaults={
                'name': 'رایگان',
                'plan_type': 'free',
                'description': 'پلن رایگان برای آشنایی با سیستم',
                'price': Decimal('0'),
                'billing_period': 'monthly',
                'trial_days': 0,
                
                # Limitations
                'max_queries_per_day': 3,
                'max_queries_per_month': 30,
                'max_tokens_per_query': 2000,
                'max_conversations': 3,
                'max_file_upload_size_mb': 2,
                'max_total_storage_gb': 0.1,  # 100MB
                
                # AI Models
                'gpt_3_5_access': True,
                'gpt_4_access': False,
                'claude_access': False,
                'custom_model_access': False,
                
                # Support
                'support_response_hours': 168,  # 7 days
                'priority_support': False,
                
                # API
                'api_access': False,
                'api_rate_limit': 0,
                'webhook_access': False,
                
                # Additional
                'allow_export': False,
                'allow_api_key_generation': False,
                'allow_team_members': False,
                'max_team_members': 1,
                
                'sort_order': 1,
                'is_active': True,
                'is_visible': True,
            }
        )
        
        if created:
            # Add features
            plan.features.add(features['ai_gpt35'])
            self.stdout.write(self.style.SUCCESS('  ✓ Free plan created'))
        else:
            self.stdout.write('  • Free plan already exists')
        
        return plan
    
    def create_basic_plan(self, features):
        """Create Basic plan"""
        plan, created = Plan.objects.get_or_create(
            slug='basic',
            defaults={
                'name': 'پایه',
                'plan_type': 'basic',
                'description': 'مناسب برای کاربران شخصی و استارتاپ‌ها',
                'price': Decimal('299000'),  # 299,000 تومان
                'billing_period': 'monthly',
                'discount_percentage': 0,
                'trial_days': 7,
                
                # Limitations
                'max_queries_per_day': 20,
                'max_queries_per_month': 500,
                'max_tokens_per_query': 4000,
                'max_conversations': 20,
                'max_file_upload_size_mb': 10,
                'max_total_storage_gb': 1,
                
                # AI Models
                'gpt_3_5_access': True,
                'gpt_4_access': False,
                'claude_access': False,
                'custom_model_access': False,
                
                # Support
                'support_response_hours': 48,
                'priority_support': False,
                
                # API
                'api_access': True,
                'api_rate_limit': 60,
                'webhook_access': False,
                
                # Additional
                'allow_export': True,
                'allow_api_key_generation': True,
                'allow_team_members': False,
                'max_team_members': 1,
                
                'sort_order': 2,
                'badge_text': 'محبوب',
                'badge_color': '#4CAF50',
                'is_active': True,
                'is_visible': True,
            }
        )
        
        if created:
            # Add features
            plan.features.add(features['ai_gpt35'], features['api_access'], features['export_data'])
            self.stdout.write(self.style.SUCCESS('  ✓ Basic plan created'))
        else:
            self.stdout.write('  • Basic plan already exists')
        
        return plan
    
    def create_professional_plan(self, features):
        """Create Professional plan"""
        plan, created = Plan.objects.get_or_create(
            slug='professional',
            defaults={
                'name': 'حرفه‌ای',
                'plan_type': 'professional',
                'description': 'برای تیم‌ها و کسب‌وکارهای در حال رشد',
                'price': Decimal('799000'),  # 799,000 تومان
                'billing_period': 'monthly',
                'discount_percentage': 10,  # 10% تخفیف
                'trial_days': 14,
                
                # Limitations
                'max_queries_per_day': 100,
                'max_queries_per_month': 2000,
                'max_tokens_per_query': 8000,
                'max_conversations': 100,
                'max_file_upload_size_mb': 50,
                'max_total_storage_gb': 10,
                
                # AI Models
                'gpt_3_5_access': True,
                'gpt_4_access': True,
                'claude_access': False,
                'custom_model_access': False,
                
                # Support
                'support_response_hours': 24,
                'priority_support': True,
                
                # API
                'api_access': True,
                'api_rate_limit': 300,
                'webhook_access': True,
                
                # Additional
                'allow_export': True,
                'allow_api_key_generation': True,
                'allow_team_members': True,
                'max_team_members': 5,
                
                'sort_order': 3,
                'badge_text': 'پیشنهادی',
                'badge_color': '#FF9800',
                'is_active': True,
                'is_visible': True,
            }
        )
        
        if created:
            # Add features
            plan.features.add(
                features['ai_gpt35'], 
                features['ai_gpt4'],
                features['api_access'],
                features['webhook'],
                features['export_data'],
                features['priority_queue'],
                features['team_collaboration'],
                features['analytics']
            )
            self.stdout.write(self.style.SUCCESS('  ✓ Professional plan created'))
        else:
            self.stdout.write('  • Professional plan already exists')
        
        return plan
    
    def create_enterprise_plan(self, features):
        """Create Enterprise plan"""
        plan, created = Plan.objects.get_or_create(
            slug='enterprise',
            defaults={
                'name': 'سازمانی',
                'plan_type': 'enterprise',
                'description': 'راه‌حل کامل برای سازمان‌های بزرگ',
                'price': Decimal('2999000'),  # 2,999,000 تومان
                'billing_period': 'monthly',
                'discount_percentage': 20,  # 20% تخفیف
                'trial_days': 30,
                
                # Limitations (virtually unlimited)
                'max_queries_per_day': 1000,
                'max_queries_per_month': 30000,
                'max_tokens_per_query': 16000,
                'max_conversations': 1000,
                'max_file_upload_size_mb': 100,
                'max_total_storage_gb': 100,
                
                # AI Models
                'gpt_3_5_access': True,
                'gpt_4_access': True,
                'claude_access': True,
                'custom_model_access': True,
                
                # Support
                'support_response_hours': 4,
                'priority_support': True,
                'dedicated_account_manager': True,
                
                # API
                'api_access': True,
                'api_rate_limit': 1000,
                'webhook_access': True,
                
                # Additional
                'allow_export': True,
                'allow_api_key_generation': True,
                'allow_team_members': True,
                'max_team_members': 50,
                
                'sort_order': 4,
                'is_active': True,
                'is_visible': True,
            }
        )
        
        if created:
            # Add all features
            for feature in features.values():
                plan.features.add(feature)
            self.stdout.write(self.style.SUCCESS('  ✓ Enterprise plan created'))
        else:
            self.stdout.write('  • Enterprise plan already exists')
        
        return plan
