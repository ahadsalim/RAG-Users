# Generated migration for updating status and message types

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('support', '0001_initial'),
    ]

    operations = [
        # تغییر STATUS_CHOICES - حذف on_hold و resolved، اضافه answered
        migrations.AlterField(
            model_name='ticket',
            name='status',
            field=models.CharField(
                choices=[
                    ('open', 'باز'),
                    ('in_progress', 'در حال بررسی'),
                    ('waiting', 'در انتظار پاسخ کاربر'),
                    ('answered', 'پاسخ داده شده'),
                    ('closed', 'بسته شده')
                ],
                default='open',
                max_length=20,
                verbose_name='وضعیت'
            ),
        ),
        # تغییر MESSAGE_TYPE_CHOICES - حذف system و forward، اضافه question و send_to
        migrations.AlterField(
            model_name='ticketmessage',
            name='message_type',
            field=models.CharField(
                choices=[
                    ('reply', 'پاسخ'),
                    ('note', 'یادداشت داخلی'),
                    ('question', 'سوال از کاربر'),
                    ('send_to', 'ارسال به')
                ],
                default='reply',
                max_length=20,
                verbose_name='نوع پیام'
            ),
        ),
        # اضافه کردن فیلد forwarded_to
        migrations.AddField(
            model_name='ticketmessage',
            name='forwarded_to',
            field=models.ForeignKey(
                blank=True,
                limit_choices_to={'is_staff': True},
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='forwarded_ticket_messages',
                to=settings.AUTH_USER_MODEL,
                verbose_name='ارسال شده به'
            ),
        ),
        # به‌روزرسانی وضعیت‌های قدیمی
        migrations.RunSQL(
            sql="UPDATE support_ticket SET status = 'answered' WHERE status IN ('on_hold', 'resolved');",
            reverse_sql="UPDATE support_ticket SET status = 'open' WHERE status = 'answered';"
        ),
        # به‌روزرسانی نوع پیام‌های قدیمی
        migrations.RunSQL(
            sql="UPDATE support_ticketmessage SET message_type = 'note' WHERE message_type IN ('system', 'forward');",
            reverse_sql="UPDATE support_ticketmessage SET message_type = 'reply' WHERE message_type = 'note';"
        ),
    ]
