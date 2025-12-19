"""
ویوهای امور مالی
"""
from rest_framework import viewsets, permissions, status, generics
from rest_framework.decorators import action, api_view, permission_classes as perm_classes
from rest_framework.response import Response
from rest_framework.views import APIView
from django.db.models import Sum, Count, Q
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal

from .models import Currency, FinancialSettings, Invoice, InvoiceItem, TaxReport
from .serializers import (
    CurrencySerializer,
    FinancialSettingsSerializer, FinancialSettingsPublicSerializer,
    InvoiceSerializer, InvoiceListSerializer, InvoiceItemSerializer,
    TaxReportSerializer, FinancialDashboardSerializer
)


class CurrencyListView(generics.ListAPIView):
    """لیست ارزهای فعال"""
    permission_classes = [permissions.AllowAny]
    serializer_class = CurrencySerializer
    queryset = Currency.objects.filter(is_active=True)


class CurrencyDetailView(generics.RetrieveAPIView):
    """جزئیات ارز"""
    permission_classes = [permissions.AllowAny]
    serializer_class = CurrencySerializer
    queryset = Currency.objects.filter(is_active=True)


@api_view(['POST'])
@perm_classes([permissions.AllowAny])
def convert_currency(request):
    """تبدیل مبلغ بین ارزها"""
    from_currency_code = request.data.get('from_currency')
    to_currency_code = request.data.get('to_currency')
    amount = request.data.get('amount', 0)
    
    try:
        amount = Decimal(str(amount))
    except (ValueError, TypeError):
        return Response({'error': 'مبلغ نامعتبر است'}, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        from_currency = Currency.objects.get(code=from_currency_code, is_active=True)
        to_currency = Currency.objects.get(code=to_currency_code, is_active=True)
    except Currency.DoesNotExist:
        return Response({'error': 'ارز یافت نشد'}, status=status.HTTP_404_NOT_FOUND)
    
    # تبدیل به ارز پایه و سپس به ارز مقصد
    base_amount = from_currency.convert_to_base(amount)
    converted_amount = to_currency.convert_from_base(base_amount)
    
    return Response({
        'from_currency': from_currency_code,
        'to_currency': to_currency_code,
        'amount': float(amount),
        'converted_amount': round(float(converted_amount), to_currency.decimal_places),
        'formatted': to_currency.format_price(converted_amount)
    })


class IsAdminUser(permissions.BasePermission):
    """فقط ادمین‌ها دسترسی دارند"""
    def has_permission(self, request, view):
        return request.user and request.user.is_staff


class FinancialSettingsView(APIView):
    """مدیریت تنظیمات مالی"""
    
    permission_classes = [IsAdminUser]
    
    def get(self, request):
        settings = FinancialSettings.get_settings()
        serializer = FinancialSettingsSerializer(settings)
        return Response(serializer.data)
    
    def put(self, request):
        settings = FinancialSettings.get_settings()
        serializer = FinancialSettingsSerializer(settings, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class FinancialSettingsPublicView(APIView):
    """تنظیمات مالی عمومی (برای نمایش در فاکتور)"""
    
    permission_classes = [permissions.AllowAny]
    
    def get(self, request):
        settings = FinancialSettings.get_settings()
        serializer = FinancialSettingsPublicSerializer(settings)
        return Response(serializer.data)


class InvoiceViewSet(viewsets.ModelViewSet):
    """مدیریت فاکتورها"""
    
    permission_classes = [IsAdminUser]
    
    def get_queryset(self):
        queryset = Invoice.objects.all()
        
        # فیلترها
        status_filter = self.request.query_params.get('status')
        is_legal = self.request.query_params.get('is_legal')
        date_from = self.request.query_params.get('date_from')
        date_to = self.request.query_params.get('date_to')
        search = self.request.query_params.get('search')
        
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        if is_legal is not None:
            queryset = queryset.filter(is_legal_buyer=is_legal.lower() == 'true')
        if date_from:
            queryset = queryset.filter(issue_date__gte=date_from)
        if date_to:
            queryset = queryset.filter(issue_date__lte=date_to)
        if search:
            queryset = queryset.filter(
                Q(invoice_number__icontains=search) |
                Q(buyer_name__icontains=search) |
                Q(buyer_national_id__icontains=search)
            )
        
        return queryset.order_by('-created_at')
    
    def get_serializer_class(self):
        if self.action == 'list':
            return InvoiceListSerializer
        return InvoiceSerializer
    
    @action(detail=True, methods=['post'])
    def send_to_tax(self, request, pk=None):
        """ارسال فاکتور به سامانه مالیات"""
        invoice = self.get_object()
        
        settings = FinancialSettings.get_settings()
        if not settings.moadian_enabled:
            return Response(
                {'error': 'سامانه مودیان فعال نیست'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # TODO: پیاده‌سازی ارسال به سامانه مودیان
        # این بخش نیاز به API واقعی سامانه مودیان دارد
        
        return Response({'message': 'این قابلیت در حال توسعه است'})
    
    @action(detail=True, methods=['post'])
    def mark_paid(self, request, pk=None):
        """علامت‌گذاری به عنوان پرداخت شده"""
        invoice = self.get_object()
        invoice.status = 'paid'
        invoice.paid_at = timezone.now()
        invoice.save()
        return Response({'message': 'فاکتور پرداخت شده علامت‌گذاری شد'})
    
    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """لغو فاکتور"""
        invoice = self.get_object()
        if invoice.status == 'paid':
            return Response(
                {'error': 'فاکتور پرداخت شده قابل لغو نیست'},
                status=status.HTTP_400_BAD_REQUEST
            )
        invoice.status = 'cancelled'
        invoice.save()
        return Response({'message': 'فاکتور لغو شد'})


class UserInvoiceViewSet(viewsets.ReadOnlyModelViewSet):
    """فاکتورهای کاربر (برای کاربران عادی)"""
    
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = InvoiceSerializer
    
    def get_queryset(self):
        return Invoice.objects.filter(user=self.request.user).order_by('-created_at')


class TaxReportViewSet(viewsets.ModelViewSet):
    """مدیریت گزارشات مالیاتی"""
    
    permission_classes = [IsAdminUser]
    serializer_class = TaxReportSerializer
    queryset = TaxReport.objects.all()
    
    @action(detail=False, methods=['post'])
    def generate(self, request):
        """تولید گزارش مالیاتی"""
        period_type = request.data.get('period_type', 'monthly')
        period_start = request.data.get('period_start')
        period_end = request.data.get('period_end')
        
        if not period_start or not period_end:
            return Response(
                {'error': 'تاریخ شروع و پایان الزامی است'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # محاسبه آمار
        invoices = Invoice.objects.filter(
            status='paid',
            issue_date__gte=period_start,
            issue_date__lte=period_end
        )
        
        stats = invoices.aggregate(
            total_sales=Sum('subtotal'),
            total_tax=Sum('tax_amount'),
            invoice_count=Count('id')
        )
        
        report = TaxReport.objects.create(
            period_type=period_type,
            period_start=period_start,
            period_end=period_end,
            total_sales=stats['total_sales'] or 0,
            total_tax=stats['total_tax'] or 0,
            invoice_count=stats['invoice_count'] or 0
        )
        
        serializer = TaxReportSerializer(report)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class FinancialDashboardView(APIView):
    """داشبورد مالی"""
    
    permission_classes = [IsAdminUser]
    
    def get(self, request):
        now = timezone.now()
        this_month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        last_month_start = (this_month_start - timedelta(days=1)).replace(day=1)
        
        # آمار کلی
        all_invoices = Invoice.objects.filter(status='paid')
        total_stats = all_invoices.aggregate(
            total_revenue=Sum('subtotal'),
            total_tax=Sum('tax_amount')
        )
        
        # آمار این ماه
        this_month_invoices = all_invoices.filter(paid_at__gte=this_month_start)
        this_month_stats = this_month_invoices.aggregate(
            revenue=Sum('subtotal')
        )
        
        # آمار ماه گذشته
        last_month_invoices = all_invoices.filter(
            paid_at__gte=last_month_start,
            paid_at__lt=this_month_start
        )
        last_month_stats = last_month_invoices.aggregate(
            revenue=Sum('subtotal')
        )
        
        # تعداد فاکتورها
        total_invoices = Invoice.objects.count()
        paid_invoices = Invoice.objects.filter(status='paid').count()
        pending_invoices = Invoice.objects.filter(status__in=['draft', 'issued']).count()
        
        # تعداد مشتریان
        legal_customers = Invoice.objects.filter(is_legal_buyer=True).values('user').distinct().count()
        individual_customers = Invoice.objects.filter(is_legal_buyer=False).values('user').distinct().count()
        
        data = {
            'total_revenue': total_stats['total_revenue'] or Decimal('0'),
            'total_tax_collected': total_stats['total_tax'] or Decimal('0'),
            'total_invoices': total_invoices,
            'paid_invoices': paid_invoices,
            'pending_invoices': pending_invoices,
            'legal_customers': legal_customers,
            'individual_customers': individual_customers,
            'revenue_this_month': this_month_stats['revenue'] or Decimal('0'),
            'revenue_last_month': last_month_stats['revenue'] or Decimal('0'),
        }
        
        serializer = FinancialDashboardSerializer(data)
        return Response(serializer.data)
