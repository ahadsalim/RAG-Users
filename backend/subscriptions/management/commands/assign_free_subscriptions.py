"""
Management command to assign free subscriptions to existing users without one
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta

from subscriptions.models import Subscription, Plan

User = get_user_model()


class Command(BaseCommand):
    help = 'Assign free trial subscriptions to existing users without subscription'
    
    def handle(self, *args, **options):
        self.stdout.write('Checking users without subscriptions...')
        
        # پیدا کردن پلن رایگان
        free_plan = Plan.objects.filter(
            name__icontains='free',
            is_active=True
        ).first()
        
        if not free_plan:
            # اگر پلن رایگان نبود، اولین پلن فعال را بگیر
            free_plan = Plan.objects.filter(is_active=True).first()
        
        if not free_plan:
            self.stdout.write(self.style.ERROR('No active subscription plan found!'))
            return
        
        self.stdout.write(f'Using plan: {free_plan.name}')
        
        # پیدا کردن کاربرانی که subscription ندارند
        users_without_subscription = User.objects.filter(
            subscriptions__isnull=True,
            is_active=True
        ).exclude(is_superuser=True)
        
        count = 0
        for user in users_without_subscription:
            try:
                subscription = Subscription.objects.create(
                    user=user,
                    plan=free_plan,
                    status='trial',
                    start_date=timezone.now(),
                    end_date=timezone.now() + timedelta(days=30),
                    auto_renew=False
                )
                self.stdout.write(
                    self.style.SUCCESS(
                        f'✓ Created subscription for {user.phone_number or user.email}'
                    )
                )
                count += 1
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(
                        f'✗ Failed for {user.phone_number or user.email}: {e}'
                    )
                )
        
        self.stdout.write(
            self.style.SUCCESS(
                f'\nDone! Created {count} subscriptions.'
            )
        )
