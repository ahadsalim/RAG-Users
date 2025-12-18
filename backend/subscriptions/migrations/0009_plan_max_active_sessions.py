from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('subscriptions', '0008_rename_usagelog_to_modelusagelog'),
    ]

    operations = [
        migrations.AddField(
            model_name='plan',
            name='max_active_sessions',
            field=models.IntegerField(default=3, help_text='حداکثر تعداد دستگاه‌های همزمان', verbose_name='حداکثر جلسات فعال'),
        ),
    ]
