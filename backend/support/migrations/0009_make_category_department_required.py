# Generated manually on 2025-12-21

from django.db import migrations, models
import django.db.models.deletion


def create_default_category_department(apps, schema_editor):
    """ایجاد دسته‌بندی و دپارتمان پیش‌فرض"""
    TicketCategory = apps.get_model('support', 'TicketCategory')
    TicketDepartment = apps.get_model('support', 'TicketDepartment')
    
    # ایجاد دپارتمان پیش‌فرض
    default_department, created = TicketDepartment.objects.get_or_create(
        name='عمومی',
        defaults={
            'description': 'دپارتمان پیش‌فرض برای تیکت‌ها',
            'is_active': True,
            'is_public': True,
            'priority': 1,
            'auto_assign': False
        }
    )
    
    # ایجاد دسته‌بندی پیش‌فرض
    default_category, created = TicketCategory.objects.get_or_create(
        name='عمومی',
        defaults={
            'description': 'دسته‌بندی پیش‌فرض برای تیکت‌ها',
            'default_department': default_department,
            'default_priority': 'medium',
            'is_active': True,
            'order': 1
        }
    )
    
    # به‌روزرسانی تیکت‌های بدون دسته‌بندی یا دپارتمان
    Ticket = apps.get_model('support', 'Ticket')
    Ticket.objects.filter(category__isnull=True).update(category=default_category)
    Ticket.objects.filter(department__isnull=True).update(department=default_department)


class Migration(migrations.Migration):

    dependencies = [
        ('support', '0008_remove_ticketattachment'),
    ]

    operations = [
        # ایجاد دسته‌بندی و دپارتمان پیش‌فرض
        migrations.RunPython(create_default_category_department, migrations.RunPython.noop),
        
        # تغییر فیلدها به NOT NULL
        migrations.AlterField(
            model_name='ticket',
            name='category',
            field=models.ForeignKey(
                help_text='انتخاب دسته‌بندی الزامی است',
                on_delete=django.db.models.deletion.SET_NULL,
                null=True,
                blank=True,
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
                on_delete=django.db.models.deletion.SET_NULL,
                null=True,
                blank=True,
                related_name='tickets',
                to='support.ticketdepartment',
                verbose_name='دپارتمان'
            ),
        ),
    ]
