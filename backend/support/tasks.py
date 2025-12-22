"""
Celery tasks for support ticket management
تسک‌های زمان‌بندی شده برای مدیریت تیکت‌ها
"""
import logging
from celery import shared_task
from django.utils import timezone
from datetime import timedelta

logger = logging.getLogger(__name__)


@shared_task(name='support.tasks.auto_close_answered_tickets')
def auto_close_answered_tickets():
    """
    بررسی تیکت‌های با وضعیت 'answered' که مهلت حل مشکل آنها گذشته
    و تغییر خودکار وضعیت به 'closed'
    """
    from support.models import Ticket, TicketHistory
    
    logger.info("Starting auto_close_answered_tickets task")
    
    try:
        now = timezone.now()
        
        # پیدا کردن تیکت‌های answered که resolution_due گذشته
        tickets_to_close = Ticket.objects.filter(
            status='answered',
            resolution_due__isnull=False,
            resolution_due__lt=now
        )
        
        closed_count = 0
        for ticket in tickets_to_close:
            ticket.status = 'closed'
            ticket.closed_at = now
            ticket.save(update_fields=['status', 'closed_at'])
            
            # ثبت در تاریخچه
            TicketHistory.objects.create(
                ticket=ticket,
                user=None,
                action='auto_closed',
                description='تیکت به دلیل گذشت مهلت حل مشکل به صورت خودکار بسته شد'
            )
            
            closed_count += 1
            logger.info(f"Auto-closed ticket {ticket.ticket_number}")
        
        logger.info(f"auto_close_answered_tickets completed: {closed_count} tickets closed")
        return {'closed_count': closed_count}
        
    except Exception as e:
        logger.error(f"auto_close_answered_tickets failed: {e}")
        raise
