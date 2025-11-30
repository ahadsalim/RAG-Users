# Generated manually on 2025-11-30 13:30

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('chat', '0002_message_metadata'),
    ]

    operations = [
        migrations.AlterField(
            model_name='messageattachment',
            name='file_name',
            field=models.CharField(max_length=500),
        ),
        migrations.AlterField(
            model_name='messageattachment',
            name='mime_type',
            field=models.CharField(max_length=200),
        ),
    ]
