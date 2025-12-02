"""
Management command برای پردازش تمدید خودکار اشتراک‌ها
باید روزانه با cron اجرا شود
"""
from django.core.management.base import BaseCommand
from subscriptions.auto_renewal import AutoRenewalService


class Command(BaseCommand):
    help = 'Process auto-renewals for subscriptions expiring soon'
    
    def handle(self, *args, **options):
        self.stdout.write('Processing auto-renewals...')
        
        renewed, failed = AutoRenewalService.process_auto_renewals()
        
        self.stdout.write(self.style.SUCCESS(
            f'\n✓ Auto-renewal completed: {renewed} renewed, {failed} failed'
        ))
