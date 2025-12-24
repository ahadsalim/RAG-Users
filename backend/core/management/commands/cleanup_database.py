from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db import transaction
from chat.models import Conversation, Message, MessageAttachment, ConversationFolder, SharedConversation
from notifications.models import Notification, DeviceToken, NotificationLog
from subscriptions.models import Subscription
from payments.models import Transaction
from support.models import Ticket
from accounts.models import UserSession, AuditLog, Organization, OrganizationInvitation
from analytics.models import UserAnalytics, DailyMetric, RevenueAnalytics, SystemMetrics

User = get_user_model()


class Command(BaseCommand):
    help = 'حذف تمام کاربران غیر سوپرادمین و داده‌های مرتبط با آنها'

    def add_arguments(self, parser):
        parser.add_argument(
            '--confirm',
            action='store_true',
            help='تایید حذف داده‌ها',
        )

    def handle(self, *args, **options):
        if not options['confirm']:
            self.stdout.write(
                self.style.WARNING(
                    'این دستور تمام کاربران غیر سوپرادمین و داده‌های مرتبط را حذف می‌کند!\n'
                    'برای اجرا از --confirm استفاده کنید.'
                )
            )
            return

        self.stdout.write(self.style.WARNING('شروع پاکسازی دیتابیس...'))

        # شمارش کاربران
        superadmins = User.objects.filter(is_superuser=True)
        non_superadmins = User.objects.filter(is_superuser=False)
        
        superadmin_count = superadmins.count()
        non_superadmin_count = non_superadmins.count()

        self.stdout.write(f'تعداد سوپرادمین‌ها: {superadmin_count}')
        self.stdout.write(f'تعداد کاربران غیر سوپرادمین: {non_superadmin_count}')

        if non_superadmin_count == 0:
            self.stdout.write(self.style.SUCCESS('هیچ کاربر غیر سوپرادمینی برای حذف وجود ندارد.'))
            return

        try:
            with transaction.atomic():
                # 1. حذف تمام مکالمات و پیام‌ها
                self.stdout.write('حذف مکالمات و پیام‌ها...')
                conversations_count = Conversation.objects.count()
                messages_count = Message.objects.count()
                MessageAttachment.objects.all().delete()
                Message.objects.all().delete()
                SharedConversation.objects.all().delete()
                Conversation.objects.all().delete()
                ConversationFolder.objects.filter(user__is_superuser=False).delete()
                self.stdout.write(self.style.SUCCESS(f'✓ {conversations_count} مکالمه و {messages_count} پیام حذف شد'))

                # 2. حذف اعلان‌های کاربران غیر سوپرادمین
                self.stdout.write('حذف اعلان‌ها...')
                notifications_count = Notification.objects.filter(user__is_superuser=False).count()
                NotificationLog.objects.filter(notification__user__is_superuser=False).delete()
                Notification.objects.filter(user__is_superuser=False).delete()
                DeviceToken.objects.filter(user__is_superuser=False).delete()
                self.stdout.write(self.style.SUCCESS(f'✓ {notifications_count} اعلان حذف شد'))

                # 3. حذف اشتراک‌ها
                self.stdout.write('حذف اشتراک‌ها...')
                subscriptions_count = Subscription.objects.filter(user__is_superuser=False).count()
                Subscription.objects.filter(user__is_superuser=False).delete()
                self.stdout.write(self.style.SUCCESS(f'✓ {subscriptions_count} اشتراک حذف شد'))

                # 4. حذف تراکنش‌ها
                self.stdout.write('حذف تراکنش‌ها...')
                transactions_count = Transaction.objects.filter(user__is_superuser=False).count()
                Transaction.objects.filter(user__is_superuser=False).delete()
                self.stdout.write(self.style.SUCCESS(f'✓ {transactions_count} تراکنش حذف شد'))

                # 5. حذف تیکت‌های پشتیبانی
                self.stdout.write('حذف تیکت‌های پشتیبانی...')
                tickets_count = Ticket.objects.filter(user__is_superuser=False).count()
                Ticket.objects.filter(user__is_superuser=False).delete()
                self.stdout.write(self.style.SUCCESS(f'✓ {tickets_count} تیکت حذف شد'))

                # 6. حذف نشست‌ها و لاگ‌های حسابرسی
                self.stdout.write('حذف نشست‌ها و لاگ‌ها...')
                sessions_count = UserSession.objects.filter(user__is_superuser=False).count()
                audit_logs_count = AuditLog.objects.filter(user__is_superuser=False).count()
                UserSession.objects.filter(user__is_superuser=False).delete()
                AuditLog.objects.filter(user__is_superuser=False).delete()
                self.stdout.write(self.style.SUCCESS(f'✓ {sessions_count} نشست و {audit_logs_count} لاگ حذف شد'))

                # 7. حذف سازمان‌ها و دعوت‌نامه‌ها
                self.stdout.write('حذف سازمان‌ها...')
                organizations_count = Organization.objects.filter(owner__is_superuser=False).count()
                OrganizationInvitation.objects.all().delete()
                Organization.objects.filter(owner__is_superuser=False).delete()
                self.stdout.write(self.style.SUCCESS(f'✓ {organizations_count} سازمان حذف شد'))

                # 8. حذف آنالیتیکس
                self.stdout.write('حذف آنالیتیکس...')
                analytics_count = UserAnalytics.objects.filter(user__is_superuser=False).count()
                UserAnalytics.objects.filter(user__is_superuser=False).delete()
                self.stdout.write(self.style.SUCCESS(f'✓ {analytics_count} رکورد آنالیتیکس حذف شد'))

                # 9. حذف کاربران غیر سوپرادمین
                self.stdout.write('حذف کاربران غیر سوپرادمین...')
                deleted_users = non_superadmins.delete()
                self.stdout.write(self.style.SUCCESS(f'✓ {non_superadmin_count} کاربر حذف شد'))

                self.stdout.write(self.style.SUCCESS('\n✅ پاکسازی دیتابیس با موفقیت انجام شد!'))
                self.stdout.write(f'کاربران باقی‌مانده (سوپرادمین): {superadmin_count}')

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'خطا در پاکسازی: {str(e)}'))
            raise
