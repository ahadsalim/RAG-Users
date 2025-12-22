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
        from notifications.services import NotificationService
        
        if created:
            # نوتیفیکیشن برای کاربر
            context = {
                'user_name': instance.user.get_full_name() if hasattr(instance.user, 'get_full_name') else str(instance.user),
                'ticket_number': instance.ticket_number,
                'subject': instance.subject,
                'ticket_id': str(instance.id)
            }
            NotificationService.create_notification(
                user=instance.user,
                template_code='ticket_created_user',
                context=context,
                priority='normal'
            )
            
            # نوتیفیکیشن برای کارشناس تخصیص داده شده
            if instance.assigned_to:
                context = {
                    'staff_name': instance.assigned_to.get_full_name() if hasattr(instance.assigned_to, 'get_full_name') else str(instance.assigned_to),
                    'ticket_number': instance.ticket_number,
                    'subject': instance.subject,
                    'ticket_id': str(instance.id)
                }
                NotificationService.create_notification(
                    user=instance.assigned_to,
                    template_code='ticket_assigned_staff',
                    context=context,
                    priority='high'
                )
        else:
            # بررسی تغییر وضعیت
            previous_status = getattr(instance, '_previous_status', None)
            if previous_status and previous_status != instance.status:
                context = {
                    'user_name': instance.user.get_full_name() if hasattr(instance.user, 'get_full_name') else str(instance.user),
                    'ticket_number': instance.ticket_number,
                    'status': instance.get_status_display(),
                    'ticket_id': str(instance.id)
                }
                NotificationService.create_notification(
                    user=instance.user,
                    template_code='ticket_status_changed',
                    context=context,
                    priority='normal'
                )
            
            # بررسی تغییر کارشناس
            previous_assigned = getattr(instance, '_previous_assigned_to', None)
            if instance.assigned_to and previous_assigned != instance.assigned_to:
                context = {
                    'staff_name': instance.assigned_to.get_full_name() if hasattr(instance.assigned_to, 'get_full_name') else str(instance.assigned_to),
                    'ticket_number': instance.ticket_number,
                    'subject': instance.subject,
                    'ticket_id': str(instance.id)
                }
                NotificationService.create_notification(
                    user=instance.assigned_to,
                    template_code='ticket_assigned_staff',
                    context=context,
                    priority='high'
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
        from notifications.services import NotificationService
        
        ticket = instance.ticket
        
        if instance.is_staff_reply:
            # نوتیفیکیشن برای کاربر
            context = {
                'user_name': ticket.user.get_full_name() if hasattr(ticket.user, 'get_full_name') else str(ticket.user),
                'ticket_number': ticket.ticket_number,
                'ticket_id': str(ticket.id)
            }
            NotificationService.create_notification(
                user=ticket.user,
                template_code='ticket_reply_user',
                context=context,
                priority='high'
            )
        else:
            # نوتیفیکیشن برای کارشناس
            if ticket.assigned_to:
                context = {
                    'staff_name': ticket.assigned_to.get_full_name() if hasattr(ticket.assigned_to, 'get_full_name') else str(ticket.assigned_to),
                    'ticket_number': ticket.ticket_number,
                    'ticket_id': str(ticket.id)
                }
                NotificationService.create_notification(
                    user=ticket.assigned_to,
                    template_code='ticket_message_staff',
                    context=context,
                    priority='normal'
                )
    except Exception:
        pass


