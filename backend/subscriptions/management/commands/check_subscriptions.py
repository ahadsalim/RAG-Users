"""
Management command برای بررسی اشتراک‌ها
باید روزانه با cron اجرا شود
"""
from django.core.management.base import BaseCommand
from subscriptions.notification_service import SubscriptionScheduledTasks


class Command(BaseCommand):
    help = 'Check subscriptions for expiring, expired, and quota warnings'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--expiring',
            action='store_true',
            help='Check expiring subscriptions (7, 3, 1 days)',
        )
        parser.add_argument(
            '--expired',
            action='store_true',
            help='Check and update expired subscriptions',
        )
        parser.add_argument(
            '--quota',
            action='store_true',
            help='Check quota warnings',
        )
        parser.add_argument(
            '--all',
            action='store_true',
            help='Run all checks',
        )
    
    def handle(self, *args, **options):
        run_all = options['all'] or not any([options['expiring'], options['expired'], options['quota']])
        
        if run_all or options['expiring']:
            self.stdout.write('Checking expiring subscriptions...')
            SubscriptionScheduledTasks.check_expiring_subscriptions()
            self.stdout.write(self.style.SUCCESS('  ✓ Done'))
        
        if run_all or options['expired']:
            self.stdout.write('Checking expired subscriptions...')
            SubscriptionScheduledTasks.check_expired_subscriptions()
            self.stdout.write(self.style.SUCCESS('  ✓ Done'))
        
        if run_all or options['quota']:
            self.stdout.write('Checking quota warnings...')
            SubscriptionScheduledTasks.check_quota_warnings()
            self.stdout.write(self.style.SUCCESS('  ✓ Done'))
        
        self.stdout.write(self.style.SUCCESS('\n✓ All checks completed!'))
