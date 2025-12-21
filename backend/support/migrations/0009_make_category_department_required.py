# Generated manually

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('support', '0008_remove_ticketattachment'),
    ]

    operations = [
        migrations.AlterField(
            model_name='ticket',
            name='category',
            field=models.ForeignKey(
                help_text='انتخاب دسته‌بندی الزامی است',
                on_delete=django.db.models.deletion.PROTECT,
                related_name='tickets',
                to='support.ticketcategory',
                verbose_name='دسته‌بندی'
            ),
        ),
        migrations.AlterField(
            model_name='ticket',
            name='department',
            field=models.ForeignKey(
                help_text='انتخاب دپارتمان الزامی است',
                on_delete=django.db.models.deletion.PROTECT,
                related_name='tickets',
                to='support.ticketdepartment',
                verbose_name='دپارتمان'
            ),
        ),
    ]
