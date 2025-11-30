# Generated manually on 2025-11-30 15:10

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('chat', '0003_alter_messageattachment_fields'),
    ]

    operations = [
        migrations.AlterField(
            model_name='messageattachment',
            name='file',
            field=models.CharField(max_length=500),
        ),
    ]
