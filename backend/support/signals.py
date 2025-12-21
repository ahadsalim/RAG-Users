from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.utils import timezone
from .models import Ticket, TicketMessage, TicketHistory


@receiver(pre_save, sender=Ticket)
def ticket_pre_save(sender, instance, **kwargs):
    """ذخیره وضعیت قبلی برای مقایسه"""
    if instance.pk:
        try:
            instance._previous_status = Ticket.objects.get(pk=instance.pk).status
            instance._previous_assigned_to = Ticket.objects.get(pk=instance.pk).assigned_to
        except Ticket.DoesNotExist:
            instance._previous_status = None
            instance._previous_assigned_to = None
    else:
        instance._previous_status = None
        instance._previous_assigned_to = None


@receiver(post_save, sender=Ticket)
def ticket_post_save(sender, instance, created, **kwargs):
    """ارسال نوتیفیکیشن بعد از ایجاد یا تغییر تیکت"""
    try:
        from notifications.models import Notification
        
        if created:
            # نوتیفیکیشن برای کاربر
            Notification.objects.create(
                user=instance.user,
                title='تیکت جدید ایجاد شد',
                message=f'تیکت #{instance.ticket_number} با موضوع "{instance.subject}" ایجاد شد.',
                notification_type='ticket',
                data={'ticket_id': str(instance.id), 'ticket_number': instance.ticket_number}
            )
            
            # نوتیفیکیشن برای کارشناس تخصیص داده شده
            if instance.assigned_to:
                Notification.objects.create(
                    user=instance.assigned_to,
                    title='تیکت جدید تخصیص داده شد',
                    message=f'تیکت #{instance.ticket_number} به شما تخصیص داده شد.',
                    notification_type='ticket',
                    data={'ticket_id': str(instance.id), 'ticket_number': instance.ticket_number}
                )
        else:
            # بررسی تغییر وضعیت
            previous_status = getattr(instance, '_previous_status', None)
            if previous_status and previous_status != instance.status:
                Notification.objects.create(
                    user=instance.user,
                    title='تغییر وضعیت تیکت',
                    message=f'وضعیت تیکت #{instance.ticket_number} به "{instance.get_status_display()}" تغییر کرد.',
                    notification_type='ticket',
                    data={'ticket_id': str(instance.id), 'ticket_number': instance.ticket_number}
                )
            
            # بررسی تغییر کارشناس
            previous_assigned = getattr(instance, '_previous_assigned_to', None)
            if instance.assigned_to and previous_assigned != instance.assigned_to:
                Notification.objects.create(
                    user=instance.assigned_to,
                    title='تیکت جدید تخصیص داده شد',
                    message=f'تیکت #{instance.ticket_number} به شما تخصیص داده شد.',
                    notification_type='ticket',
                    data={'ticket_id': str(instance.id), 'ticket_number': instance.ticket_number}
                )
    except Exception:
        pass


@receiver(post_save, sender=TicketMessage)
def ticket_message_post_save(sender, instance, created, **kwargs):
    """ارسال نوتیفیکیشن بعد از پیام جدید"""
    if not created:
        return
    
    # یادداشت داخلی نوتیفیکیشن ندارد
    if instance.message_type == 'note':
        return
    
    try:
        from notifications.models import Notification
        
        ticket = instance.ticket
        
        if instance.is_staff_reply:
            # نوتیفیکیشن برای کاربر
            Notification.objects.create(
                user=ticket.user,
                title='پاسخ جدید در تیکت',
                message=f'پاسخ جدیدی در تیکت #{ticket.ticket_number} دریافت شد.',
                notification_type='ticket',
                data={'ticket_id': str(ticket.id), 'ticket_number': ticket.ticket_number}
            )
        else:
            # نوتیفیکیشن برای کارشناس
            if ticket.assigned_to:
                Notification.objects.create(
                    user=ticket.assigned_to,
                    title='پیام جدید در تیکت',
                    message=f'پیام جدیدی در تیکت #{ticket.ticket_number} دریافت شد.',
                    notification_type='ticket',
                    data={'ticket_id': str(ticket.id), 'ticket_number': ticket.ticket_number}
                )
    except Exception:
        pass


