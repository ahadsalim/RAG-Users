from rest_framework import serializers
from decimal import Decimal
from .models import (
    Transaction, PaymentGateway, PaymentStatus,
    ZarinpalPayment, StripePayment, CryptoPayment,
    Wallet, WalletTransaction
)
from subscriptions.models import Plan, Subscription


class TransactionSerializer(serializers.ModelSerializer):
    """Serializer پایه برای تراکنش"""
    
    user_email = serializers.EmailField(source='user.email', read_only=True)
    plan_name = serializers.CharField(source='plan.name', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    gateway_display = serializers.CharField(source='get_gateway_display', read_only=True)
    final_amount = serializers.DecimalField(
        source='get_final_amount',
        max_digits=12,
        decimal_places=2,
        read_only=True
    )
    
    class Meta:
        model = Transaction
        fields = [
            'id', 'reference_id', 'user', 'user_email',
            'plan', 'plan_name', 'subscription',
            'amount', 'currency', 'final_amount',
            'gateway', 'gateway_display', 'status', 'status_display',
            'discount_code', 'discount_amount', 'tax_amount',
            'invoice_number', 'description',
            'created_at', 'paid_at'
        ]
        read_only_fields = [
            'id', 'reference_id', 'invoice_number',
            'created_at', 'paid_at'
        ]


class ZarinpalPaymentSerializer(serializers.ModelSerializer):
    """Serializer برای پرداخت زرین‌پال"""
    
    class Meta:
        model = ZarinpalPayment
        fields = ['authority', 'card_hash', 'card_pan', 'ref_id', 'fee_type', 'fee']


class StripePaymentSerializer(serializers.ModelSerializer):
    """Serializer برای پرداخت Stripe"""
    
    class Meta:
        model = StripePayment
        fields = [
            'payment_intent_id', 'charge_id', 'customer_id',
            'payment_method_id', 'card_brand', 'card_last4'
        ]


class CryptoPaymentSerializer(serializers.ModelSerializer):
    """Serializer برای پرداخت رمزارز"""
    
    cryptocurrency_display = serializers.CharField(
        source='get_cryptocurrency_display',
        read_only=True
    )
    network_display = serializers.CharField(
        source='get_network_display',
        read_only=True
    )
    confirmation_progress = serializers.SerializerMethodField()
    
    class Meta:
        model = CryptoPayment
        fields = [
            'cryptocurrency', 'cryptocurrency_display',
            'network', 'network_display',
            'wallet_address', 'from_address', 'tx_hash',
            'amount_crypto', 'confirmations',
            'required_confirmations', 'confirmation_progress'
        ]
    
    def get_confirmation_progress(self, obj):
        """محاسبه درصد پیشرفت تاییدیه"""
        if obj.required_confirmations > 0:
            return min(100, (obj.confirmations / obj.required_confirmations) * 100)
        return 0


class TransactionDetailSerializer(TransactionSerializer):
    """Serializer کامل برای جزئیات تراکنش"""
    
    zarinpal_payment = ZarinpalPaymentSerializer(read_only=True)
    stripe_payment = StripePaymentSerializer(read_only=True)
    crypto_payment = CryptoPaymentSerializer(read_only=True)
    
    class Meta(TransactionSerializer.Meta):
        fields = TransactionSerializer.Meta.fields + [
            'gateway_transaction_id', 'gateway_response',
            'zarinpal_payment', 'stripe_payment', 'crypto_payment',
            'notes', 'metadata', 'ip_address',
            'updated_at', 'refunded_at'
        ]


class CreatePaymentSerializer(serializers.Serializer):
    """Serializer برای ایجاد پرداخت"""
    
    # می‌تواند gateway (string) یا gateway_id (int) باشد
    gateway = serializers.ChoiceField(choices=PaymentGateway.choices, required=False)
    gateway_id = serializers.IntegerField(required=False)
    plan_id = serializers.UUIDField(required=False, allow_null=True)
    subscription_id = serializers.UUIDField(required=False, allow_null=True)
    amount = serializers.DecimalField(
        max_digits=12,
        decimal_places=2,
        required=False,
        allow_null=True
    )
    currency = serializers.CharField(max_length=3, default='IRR')
    discount_code = serializers.CharField(
        max_length=50,
        required=False,
        allow_blank=True
    )
    discount_amount = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0
    )
    
    # فیلدهای مخصوص رمزارز
    cryptocurrency = serializers.CharField(required=False)
    network = serializers.CharField(required=False)
    
    def validate(self, attrs):
        """اعتبارسنجی داده‌ها"""
        from finance.models import PaymentGateway as PaymentGatewayModel
        
        # اگر gateway_id داده شده، gateway_type را از آن بگیر
        if attrs.get('gateway_id'):
            try:
                gateway_obj = PaymentGatewayModel.objects.get(id=attrs['gateway_id'], is_active=True)
                attrs['gateway'] = gateway_obj.gateway_type
                attrs['gateway_model'] = gateway_obj
            except PaymentGatewayModel.DoesNotExist:
                raise serializers.ValidationError({'gateway_id': 'درگاه پرداخت یافت نشد یا غیرفعال است'})
        elif not attrs.get('gateway'):
            raise serializers.ValidationError('درگاه پرداخت مشخص نشده است')
        
        # باید حداقل یکی از plan_id، subscription_id یا amount وجود داشته باشد
        if not any([attrs.get('plan_id'), attrs.get('subscription_id'), attrs.get('amount')]):
            raise serializers.ValidationError(
                'حداقل یکی از موارد plan_id، subscription_id یا amount باید مشخص شود'
            )
        
        # برای پرداخت رمزارز، cryptocurrency و network الزامی است
        if attrs.get('gateway') == PaymentGateway.CRYPTO:
            if not attrs.get('cryptocurrency'):
                raise serializers.ValidationError(
                    {'cryptocurrency': 'برای پرداخت رمزارز، نوع رمزارز الزامی است'}
                )
            if not attrs.get('network'):
                raise serializers.ValidationError(
                    {'network': 'برای پرداخت رمزارز، شبکه الزامی است'}
                )
        
        return attrs


class VerifyPaymentSerializer(serializers.Serializer):
    """Serializer برای تایید پرداخت"""
    
    payment_intent_id = serializers.CharField(required=False)  # Stripe
    tx_hash = serializers.CharField(required=False)  # Crypto
    
    def validate(self, attrs):
        """اعتبارسنجی بر اساس نوع درگاه"""
        
        # حداقل یکی باید وجود داشته باشد
        if not any([attrs.get('payment_intent_id'), attrs.get('tx_hash')]):
            raise serializers.ValidationError(
                'اطلاعات تایید پرداخت ارسال نشده است'
            )
        
        return attrs


class WalletSerializer(serializers.ModelSerializer):
    """Serializer برای کیف پول"""
    
    user_email = serializers.EmailField(source='user.email', read_only=True)
    formatted_balance = serializers.SerializerMethodField()
    
    class Meta:
        model = Wallet
        fields = [
            'id', 'user', 'user_email',
            'balance', 'formatted_balance',
            'currency', 'is_active',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'user', 'created_at', 'updated_at']
    
    def get_formatted_balance(self, obj):
        """نمایش فرمت شده موجودی"""
        if obj.currency == 'IRR':
            return f"{obj.balance:,.0f} تومان"
        return f"{obj.balance:,.2f} {obj.currency}"


class WalletTransactionSerializer(serializers.ModelSerializer):
    """Serializer برای تراکنش‌های کیف پول"""
    
    transaction_type_display = serializers.CharField(
        source='get_transaction_type_display',
        read_only=True
    )
    
    class Meta:
        model = WalletTransaction
        fields = [
            'id', 'wallet', 'transaction_type', 'transaction_type_display',
            'amount', 'balance_after', 'description',
            'related_transaction', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class WalletChargeSerializer(serializers.Serializer):
    """Serializer برای شارژ کیف پول"""
    
    amount = serializers.DecimalField(
        max_digits=12,
        decimal_places=2,
        min_value=Decimal('10000')  # حداقل 10,000 تومان
    )
    gateway = serializers.ChoiceField(
        choices=[
            PaymentGateway.ZARINPAL,
            PaymentGateway.STRIPE,
            PaymentGateway.CRYPTO
        ]
    )


class PaymentStatisticsSerializer(serializers.Serializer):
    """Serializer برای آمار پرداخت‌ها"""
    
    total_transactions = serializers.IntegerField()
    successful_transactions = serializers.IntegerField()
    failed_transactions = serializers.IntegerField()
    total_revenue = serializers.DecimalField(max_digits=15, decimal_places=2)
    average_transaction = serializers.DecimalField(max_digits=12, decimal_places=2)
    most_used_gateway = serializers.CharField()
    conversion_rate = serializers.FloatField()
    
    # آمار زمانی
    daily_revenue = serializers.DecimalField(max_digits=12, decimal_places=2)
    weekly_revenue = serializers.DecimalField(max_digits=12, decimal_places=2)
    monthly_revenue = serializers.DecimalField(max_digits=12, decimal_places=2)
    
    # آمار بر اساس درگاه
    gateway_breakdown = serializers.DictField()
    
    # آمار بر اساس پلن
    plan_breakdown = serializers.DictField()
