"""
سریالایزرهای امور مالی
"""
from rest_framework import serializers
from .models import FinancialSettings, Invoice, InvoiceItem, TaxReport


class FinancialSettingsSerializer(serializers.ModelSerializer):
    """سریالایزر تنظیمات مالی"""
    
    class Meta:
        model = FinancialSettings
        fields = '__all__'


class FinancialSettingsPublicSerializer(serializers.ModelSerializer):
    """سریالایزر عمومی تنظیمات مالی (برای نمایش در فاکتور)"""
    
    class Meta:
        model = FinancialSettings
        fields = [
            'company_name', 'company_name_en', 'company_address',
            'postal_code', 'phone', 'email', 'website',
            'economic_code', 'national_id', 'tax_rate'
        ]


class InvoiceItemSerializer(serializers.ModelSerializer):
    """سریالایزر آیتم فاکتور"""
    
    class Meta:
        model = InvoiceItem
        fields = [
            'id', 'description', 'quantity', 'unit_price',
            'discount', 'tax_rate', 'tax_amount', 'total', 'service_code'
        ]


class InvoiceSerializer(serializers.ModelSerializer):
    """سریالایزر فاکتور"""
    
    items = InvoiceItemSerializer(many=True, read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    type_display = serializers.CharField(source='get_invoice_type_display', read_only=True)
    
    class Meta:
        model = Invoice
        fields = [
            'id', 'invoice_number', 'buyer_name', 'buyer_national_id',
            'buyer_economic_code', 'buyer_address', 'buyer_postal_code',
            'buyer_phone', 'is_legal_buyer', 'subtotal', 'tax_rate',
            'tax_amount', 'discount', 'total', 'status', 'status_display',
            'invoice_type', 'type_display', 'issue_date', 'due_date',
            'paid_at', 'tax_id', 'tax_serial', 'notes', 'items',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['invoice_number', 'tax_id', 'tax_serial']


class InvoiceListSerializer(serializers.ModelSerializer):
    """سریالایزر لیست فاکتورها"""
    
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = Invoice
        fields = [
            'id', 'invoice_number', 'buyer_name', 'is_legal_buyer',
            'total', 'status', 'status_display', 'issue_date', 'paid_at'
        ]


class TaxReportSerializer(serializers.ModelSerializer):
    """سریالایزر گزارش مالیاتی"""
    
    period_type_display = serializers.CharField(source='get_period_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = TaxReport
        fields = [
            'id', 'period_type', 'period_type_display', 'period_start',
            'period_end', 'total_sales', 'total_tax', 'invoice_count',
            'status', 'status_display', 'submitted_at', 'notes',
            'created_at', 'updated_at'
        ]


class FinancialDashboardSerializer(serializers.Serializer):
    """سریالایزر داشبورد مالی"""
    
    total_revenue = serializers.DecimalField(max_digits=20, decimal_places=0)
    total_tax_collected = serializers.DecimalField(max_digits=20, decimal_places=0)
    total_invoices = serializers.IntegerField()
    paid_invoices = serializers.IntegerField()
    pending_invoices = serializers.IntegerField()
    legal_customers = serializers.IntegerField()
    individual_customers = serializers.IntegerField()
    revenue_this_month = serializers.DecimalField(max_digits=20, decimal_places=0)
    revenue_last_month = serializers.DecimalField(max_digits=20, decimal_places=0)
