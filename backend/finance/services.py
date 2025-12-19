"""
سرویس‌های امور مالی
"""
import logging
from decimal import Decimal
from django.utils import timezone
from django.db import transaction

from .models import FinancialSettings, Invoice, InvoiceItem

logger = logging.getLogger(__name__)


class InvoiceService:
    """سرویس مدیریت فاکتورها"""
    
    @staticmethod
    @transaction.atomic
    def create_invoice_from_payment(payment):
        """ایجاد فاکتور از پرداخت"""
        from subscriptions.models import Subscription
        
        settings = FinancialSettings.get_settings()
        user = payment.user
        
        # بررسی نیاز به صدور فاکتور
        is_legal = user.user_type == 'business'
        
        if not settings.auto_invoice_all and not (settings.auto_invoice_legal and is_legal):
            logger.info(f"Invoice not required for payment {payment.id}")
            return None
        
        # اطلاعات خریدار
        buyer_name = user.get_full_name() or user.phone_number
        buyer_national_id = getattr(user, 'national_id', '') or ''
        buyer_economic_code = getattr(user, 'economic_code', '') or ''
        buyer_address = getattr(user, 'address', '') or ''
        buyer_postal_code = getattr(user, 'postal_code', '') or ''
        buyer_phone = user.phone_number or ''
        
        # محاسبه مبالغ
        subtotal = Decimal(str(payment.amount))
        tax_rate = settings.tax_rate
        tax_amount = (subtotal * tax_rate / 100).quantize(Decimal('1'))
        total = subtotal + tax_amount
        
        # ایجاد فاکتور
        invoice = Invoice.objects.create(
            invoice_number=Invoice.generate_invoice_number(),
            user=user,
            buyer_name=buyer_name,
            buyer_national_id=buyer_national_id,
            buyer_economic_code=buyer_economic_code,
            buyer_address=buyer_address,
            buyer_postal_code=buyer_postal_code,
            buyer_phone=buyer_phone,
            is_legal_buyer=is_legal,
            subtotal=subtotal,
            tax_rate=tax_rate,
            tax_amount=tax_amount,
            discount=0,
            total=total,
            status='paid',
            payment=payment,
            paid_at=timezone.now()
        )
        
        # ایجاد آیتم فاکتور
        description = f'اشتراک {payment.subscription.plan.name if hasattr(payment, "subscription") else "پلن"}'
        
        InvoiceItem.objects.create(
            invoice=invoice,
            description=description,
            quantity=1,
            unit_price=subtotal,
            discount=0,
            tax_rate=tax_rate,
            tax_amount=tax_amount,
            total=total,
            service_code='1001'  # کد خدمات نرم‌افزاری
        )
        
        logger.info(f"Invoice {invoice.invoice_number} created for payment {payment.id}")
        
        # ارسال به سامانه مالیات اگر فعال باشد
        if settings.moadian_enabled and is_legal:
            MoadianService.send_invoice(invoice)
        
        return invoice


class MoadianService:
    """سرویس اتصال به سامانه مودیان"""
    
    @staticmethod
    def send_invoice(invoice):
        """ارسال فاکتور به سامانه مودیان"""
        settings = FinancialSettings.get_settings()
        
        if not settings.moadian_enabled:
            logger.warning("Moadian service is not enabled")
            return False
        
        if not settings.moadian_api_key or not settings.moadian_memory_id:
            logger.error("Moadian credentials not configured")
            return False
        
        try:
            # TODO: پیاده‌سازی واقعی API سامانه مودیان
            # این بخش نیاز به مستندات و API واقعی سامانه مودیان دارد
            # 
            # مراحل کلی:
            # 1. تبدیل فاکتور به فرمت XML/JSON سامانه مودیان
            # 2. امضای دیجیتال با کلید خصوصی
            # 3. ارسال به endpoint سامانه
            # 4. دریافت و ذخیره شناسه یکتای مالیاتی
            
            logger.info(f"Would send invoice {invoice.invoice_number} to Moadian")
            
            # شبیه‌سازی موفقیت
            # invoice.tax_id = f"TAX-{invoice.invoice_number}"
            # invoice.sent_to_tax_at = timezone.now()
            # invoice.status = 'sent_to_tax'
            # invoice.save()
            
            return True
            
        except Exception as e:
            logger.error(f"Error sending invoice to Moadian: {e}")
            invoice.tax_response = {'error': str(e)}
            invoice.save()
            return False
    
    @staticmethod
    def check_invoice_status(invoice):
        """بررسی وضعیت فاکتور در سامانه مودیان"""
        if not invoice.tax_id:
            return None
        
        try:
            # TODO: پیاده‌سازی واقعی
            pass
        except Exception as e:
            logger.error(f"Error checking invoice status: {e}")
            return None
    
    @staticmethod
    def cancel_invoice(invoice):
        """ابطال فاکتور در سامانه مودیان"""
        if not invoice.tax_id:
            return False
        
        try:
            # TODO: پیاده‌سازی واقعی
            pass
        except Exception as e:
            logger.error(f"Error canceling invoice in Moadian: {e}")
            return False


class FinancialReportService:
    """سرویس گزارشات مالی"""
    
    @staticmethod
    def get_revenue_by_period(start_date, end_date):
        """گزارش درآمد بر اساس دوره"""
        invoices = Invoice.objects.filter(
            status='paid',
            paid_at__gte=start_date,
            paid_at__lte=end_date
        )
        
        return invoices.aggregate(
            total_revenue=Sum('subtotal'),
            total_tax=Sum('tax_amount'),
            total_amount=Sum('total'),
            invoice_count=Count('id')
        )
    
    @staticmethod
    def get_revenue_by_plan(start_date=None, end_date=None):
        """گزارش درآمد به تفکیک پلن"""
        from django.db.models import Sum, Count
        
        queryset = Invoice.objects.filter(status='paid')
        
        if start_date:
            queryset = queryset.filter(paid_at__gte=start_date)
        if end_date:
            queryset = queryset.filter(paid_at__lte=end_date)
        
        return queryset.values(
            'items__description'
        ).annotate(
            total_revenue=Sum('subtotal'),
            invoice_count=Count('id')
        ).order_by('-total_revenue')
    
    @staticmethod
    def get_customer_report():
        """گزارش مشتریان"""
        from django.db.models import Sum, Count
        
        return Invoice.objects.filter(status='paid').values(
            'is_legal_buyer'
        ).annotate(
            customer_count=Count('user', distinct=True),
            total_revenue=Sum('subtotal'),
            invoice_count=Count('id')
        )
