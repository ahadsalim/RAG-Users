from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.conf import settings
from django.utils import timezone
from decimal import Decimal
import logging

from .models import (
    Transaction, PaymentGateway as PaymentGatewayChoices, PaymentStatus,
    ZarinpalPayment, PlisioPayment, Wallet
)
from finance.models import PaymentGateway as PaymentGatewayModel
from .serializers import (
    TransactionSerializer, TransactionDetailSerializer,
    CreatePaymentSerializer, VerifyPaymentSerializer,
    WalletSerializer, WalletChargeSerializer,
    PlisioPaymentSerializer
)
from .services import (
    ZarinpalService, WalletService
)
from .plisio_service import PlisioService
from subscriptions.models import Subscription, Plan
from accounts.models import AuditLog

logger = logging.getLogger(__name__)


class TransactionViewSet(viewsets.ModelViewSet):
    """ViewSet برای مدیریت تراکنش‌ها"""
    
    serializer_class = TransactionSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """فیلتر تراکنش‌ها بر اساس کاربر"""
        user = self.request.user
        if user.is_staff:
            return Transaction.objects.all()
        return Transaction.objects.filter(user=user)
    
    def get_serializer_class(self):
        if self.action == 'retrieve':
            return TransactionDetailSerializer
        elif self.action == 'create_payment':
            return CreatePaymentSerializer
        elif self.action == 'verify_payment':
            return VerifyPaymentSerializer
        return TransactionSerializer
    
    @action(detail=False, methods=['post'])
    def create_payment(self, request):
        """ایجاد پرداخت جدید"""
        
        serializer = CreatePaymentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        data = serializer.validated_data
        gateway = data['gateway']
        plan_id = data.get('plan_id')
        subscription_id = data.get('subscription_id')
        amount = data.get('amount')
        
        # تعیین مبلغ و توضیحات
        description = ''
        if plan_id:
            plan = get_object_or_404(Plan, id=plan_id)
            amount = plan.get_final_price()
            description = f'خرید پلن {plan.name}'
        elif subscription_id:
            subscription = get_object_or_404(Subscription, id=subscription_id, user=request.user)
            amount = subscription.plan.get_final_price()
            description = f'تمدید اشتراک {subscription.plan.name}'
        elif not amount:
            return Response(
                {'error': 'مبلغ پرداخت مشخص نشده است'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # دریافت ارز کاربر و نرخ تبدیل
        from finance.models import Currency
        currency_code = data.get('currency', 'IRR')
        try:
            currency_obj = Currency.objects.get(code=currency_code)
            exchange_rate = currency_obj.exchange_rate
        except Currency.DoesNotExist:
            return Response(
                {'error': f'ارز {currency_code} یافت نشد'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # ایجاد تراکنش
        transaction = Transaction.objects.create(
            user=request.user,
            plan_id=plan_id,
            subscription_id=subscription_id,
            amount=amount,
            currency=currency_code,
            exchange_rate=exchange_rate,  # ذخیره نرخ تبدیل لحظه تراکنش
            gateway=gateway,
            description=description,
            discount_code=data.get('discount_code', ''),
            discount_amount=data.get('discount_amount', 0),
            ip_address=request.META.get('REMOTE_ADDR'),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )
        
        # پردازش بر اساس درگاه
        if gateway == PaymentGatewayChoices.ZARINPAL:
            result = self._process_zarinpal_payment(transaction, request)
        elif gateway == PaymentGatewayChoices.PLISIO:
            result = self._process_plisio_payment(transaction, request, data)
        elif gateway == PaymentGatewayChoices.CREDIT:
            result = self._process_wallet_payment(transaction)
        else:
            result = {
                'success': False,
                'error': 'درگاه پرداخت پشتیبانی نمی‌شود'
            }
        
        if result['success']:
            # ثبت در audit log
            AuditLog.objects.create(
                user=request.user,
                action='payment_initiated',
                details={
                    'transaction_id': str(transaction.id),
                    'amount': str(amount),
                    'gateway': gateway
                },
                ip_address=request.META.get('REMOTE_ADDR'),
                user_agent=request.META.get('HTTP_USER_AGENT', '')
            )
            
            return Response({
                'transaction_id': transaction.id,
                'reference_id': transaction.reference_id,
                **result
            })
        else:
            transaction.status = PaymentStatus.FAILED
            transaction.save()
            
            return Response(
                {'error': result.get('error', 'خطا در پردازش پرداخت')},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    def _process_zarinpal_payment(self, transaction, request):
        """پردازش پرداخت زرین‌پال"""
        
        callback_url = request.build_absolute_uri(
            reverse('payments:zarinpal-callback')
        )
        
        return ZarinpalService.create_payment(
            transaction=transaction,
            callback_url=callback_url,
            mobile=request.user.phone_number,
            email=request.user.email
        )
    
    def _process_plisio_payment(self, transaction, request, data):
        """پردازش پرداخت Plisio"""
        
        callback_url = request.build_absolute_uri(
            reverse('payments:plisio-callback')
        )
        
        crypto_currency = data.get('crypto_currency', 'USDT_TRX')
        
        return PlisioService.create_invoice(
            transaction=transaction,
            callback_url=callback_url,
            currency=crypto_currency
        )
    
    def _process_wallet_payment(self, transaction):
        """پردازش پرداخت از کیف پول"""
        
        return WalletService.pay_with_wallet(transaction)
    
    @action(detail=True, methods=['post'])
    def verify_payment(self, request, pk=None):
        """تایید پرداخت"""
        
        transaction = self.get_object()
        
        if transaction.status == PaymentStatus.SUCCESS:
            return Response({
                'message': 'این پرداخت قبلاً تایید شده است',
                'transaction': TransactionDetailSerializer(transaction).data
            })
        
        gateway = transaction.gateway
        
        # فقط Plisio نیاز به تایید دستی دارد
        if gateway == PaymentGatewayChoices.PLISIO:
            txn_id = request.data.get('txn_id')
            if not txn_id:
                return Response(
                    {'error': 'txn_id الزامی است'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            result = PlisioService.process_callback({'txn_id': txn_id})
        else:
            return Response(
                {'error': 'تایید برای این درگاه پشتیبانی نمی‌شود'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if result['success']:
            # فعال‌سازی اشتراک در صورت موفقیت
            self._activate_subscription(transaction)
            
            return Response({
                'message': 'پرداخت با موفقیت تایید شد',
                'transaction': TransactionDetailSerializer(transaction).data
            })
        else:
            return Response(
                {'error': result.get('error', 'خطا در تایید پرداخت')},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    def _activate_subscription(self, transaction):
        """فعال‌سازی اشتراک پس از پرداخت موفق"""
        
        if transaction.plan:
            # ایجاد یا تمدید اشتراک
            subscription, created = Subscription.objects.get_or_create(
                user=transaction.user,
                defaults={
                    'plan': transaction.plan,
                    'status': 'active',
                    'start_date': timezone.now().date(),
                    'end_date': timezone.now().date() + timezone.timedelta(days=30),
                    'payment_method': transaction.gateway
                }
            )
            
            if not created:
                # تمدید اشتراک موجود
                subscription.renew()
            
            transaction.subscription = subscription
            transaction.save()
    
    @action(detail=True, methods=['get'])
    def invoice(self, request, pk=None):
        """دریافت فاکتور"""
        
        transaction = self.get_object()
        
        if transaction.status != PaymentStatus.SUCCESS:
            return Response(
                {'error': 'فاکتور فقط برای پرداخت‌های موفق صادر می‌شود'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # تولید فاکتور HTML (قابل تبدیل به PDF با wkhtmltopdf یا weasyprint)
        from django.template.loader import render_to_string
        from django.http import HttpResponse
        
        invoice_data = {
            'invoice_number': transaction.invoice_number,
            'date': transaction.paid_at or transaction.created_at,
            'user': transaction.user,
            'amount': transaction.amount,
            'currency': transaction.currency,
            'description': transaction.description,
            'gateway': transaction.get_gateway_display(),
            'status': 'پرداخت شده',
        }
        
        # تولید HTML فاکتور
        html_content = f"""
        <!DOCTYPE html>
        <html dir="rtl" lang="fa">
        <head>
            <meta charset="UTF-8">
            <title>فاکتور {transaction.invoice_number}</title>
            <style>
                body {{ font-family: Tahoma, sans-serif; padding: 40px; }}
                .header {{ text-align: center; border-bottom: 2px solid #333; padding-bottom: 20px; }}
                .invoice-info {{ margin: 20px 0; }}
                .invoice-info p {{ margin: 5px 0; }}
                .amount {{ font-size: 24px; font-weight: bold; color: #2563eb; }}
                .footer {{ margin-top: 40px; text-align: center; color: #666; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>فاکتور رسمی</h1>
                <p>شماره فاکتور: {transaction.invoice_number}</p>
            </div>
            <div class="invoice-info">
                <p><strong>تاریخ:</strong> {invoice_data['date'].strftime('%Y/%m/%d') if invoice_data['date'] else '-'}</p>
                <p><strong>نام مشتری:</strong> {transaction.user.get_full_name() or transaction.user.email}</p>
                <p><strong>شرح:</strong> {transaction.description or 'خرید اشتراک'}</p>
                <p><strong>درگاه پرداخت:</strong> {invoice_data['gateway']}</p>
                <p class="amount"><strong>مبلغ:</strong> {transaction.amount:,.0f} {transaction.currency}</p>
            </div>
            <div class="footer">
                <p>با تشکر از خرید شما</p>
            </div>
        </body>
        </html>
        """
        
        response = HttpResponse(html_content, content_type='text/html; charset=utf-8')
        response['Content-Disposition'] = f'attachment; filename="invoice_{transaction.invoice_number}.html"'
        return response
    
    @action(detail=True, methods=['post'])
    def refund(self, request, pk=None):
        """درخواست بازگشت وجه"""
        
        transaction = self.get_object()
        
        if transaction.status != PaymentStatus.SUCCESS:
            return Response(
                {'error': 'فقط پرداخت‌های موفق قابل بازگشت هستند'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if transaction.gateway == PaymentGateway.STRIPE:
            service = StripeService()
            amount = request.data.get('amount')
            
            if amount:
                amount = Decimal(str(amount))
            
            result = service.create_refund(transaction, amount)
            
            if result['success']:
                return Response({
                    'message': 'بازگشت وجه با موفقیت انجام شد',
                    'refund_id': result['refund_id'],
                    'amount': result['amount']
                })
            else:
                return Response(
                    {'error': result.get('error', 'خطا در بازگشت وجه')},
                    status=status.HTTP_400_BAD_REQUEST
                )
        else:
            return Response(
                {'error': 'بازگشت وجه برای این درگاه پشتیبانی نمی‌شود'},
                status=status.HTTP_400_BAD_REQUEST
            )


class ZarinpalCallbackView(APIView):
    """Callback برای زرین‌پال"""
    
    permission_classes = []
    
    def get(self, request):
        """دریافت نتیجه از زرین‌پال"""
        
        authority = request.GET.get('Authority')
        status_param = request.GET.get('Status')
        
        if not authority:
            return redirect(f"{settings.FRONTEND_URL}/payment/error?message=Authority not provided")
        
        if status_param != 'OK':
            return redirect(f"{settings.FRONTEND_URL}/payment/cancelled")
        
        try:
            # یافتن پرداخت
            zarinpal_payment = ZarinpalPayment.objects.get(authority=authority)
            transaction = zarinpal_payment.transaction
            
            # تایید پرداخت
            result = ZarinpalService.verify_payment(
                authority=authority,
                amount=int(transaction.amount)
            )
            
            if result['success']:
                # فعال‌سازی اشتراک
                if transaction.plan:
                    # محاسبه تاریخ پایان بر اساس مدت زمان پلن
                    duration_days = transaction.plan.duration_days
                    end_date = timezone.now() + timezone.timedelta(days=duration_days)
                    
                    subscription, created = Subscription.objects.get_or_create(
                        user=transaction.user,
                        plan=transaction.plan,
                        defaults={
                            'status': 'active',
                            'start_date': timezone.now(),
                            'end_date': end_date,
                        }
                    )
                    
                    if not created:
                        subscription.renew()
                    
                    transaction.subscription = subscription
                    transaction.save()
                
                return redirect(
                    f"{settings.FRONTEND_URL}/payment/success?"
                    f"ref_id={result['ref_id']}&"
                    f"transaction_id={transaction.id}"
                )
            else:
                return redirect(
                    f"{settings.FRONTEND_URL}/payment/error?"
                    f"message={result.get('error', 'Verification failed')}"
                )
                
        except ZarinpalPayment.DoesNotExist:
            return redirect(f"{settings.FRONTEND_URL}/payment/error?message=Payment not found")
        except Exception as e:
            logger.error(f"Zarinpal callback error: {e}")
            return redirect(f"{settings.FRONTEND_URL}/payment/error?message=Internal error")


class WalletViewSet(viewsets.ModelViewSet):
    """ViewSet برای مدیریت کیف پول"""
    
    serializer_class = WalletSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """فقط کیف پول کاربر فعلی"""
        return Wallet.objects.filter(user=self.request.user)
    
    def get_object(self):
        """دریافت کیف پول کاربر"""
        return WalletService.get_or_create_wallet(self.request.user)
    
    @action(detail=False, methods=['get'])
    def balance(self, request):
        """دریافت موجودی کیف پول"""
        
        wallet = WalletService.get_or_create_wallet(request.user)
        
        return Response({
            'balance': wallet.balance,
            'currency': wallet.currency,
            'is_active': wallet.is_active
        })
    
    @action(detail=False, methods=['post'])
    def charge(self, request):
        """شارژ کیف پول"""
        
        serializer = WalletChargeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        amount = serializer.validated_data['amount']
        gateway = serializer.validated_data['gateway']
        
        # ایجاد تراکنش برای شارژ
        transaction = Transaction.objects.create(
            user=request.user,
            amount=amount,
            currency='IRR',
            gateway=gateway,
            description=f'شارژ کیف پول - {amount:,} تومان',
            ip_address=request.META.get('REMOTE_ADDR'),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )
        
        # پردازش پرداخت
        if gateway == PaymentGateway.ZARINPAL:
            callback_url = request.build_absolute_uri(
                reverse('payments:zarinpal-wallet-callback')
            )
            
            result = ZarinpalService.create_payment(
                transaction=transaction,
                callback_url=callback_url,
                mobile=request.user.phone_number,
                email=request.user.email
            )
        else:
            result = {
                'success': False,
                'error': 'درگاه پرداخت پشتیبانی نمی‌شود'
            }
        
        if result['success']:
            return Response({
                'transaction_id': transaction.id,
                'reference_id': transaction.reference_id,
                **result
            })
        else:
            transaction.status = PaymentStatus.FAILED
            transaction.save()
            
            return Response(
                {'error': result.get('error', 'خطا در پردازش پرداخت')},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=False, methods=['get'])
    def transactions(self, request):
        """لیست تراکنش‌های کیف پول"""
        
        wallet = WalletService.get_or_create_wallet(request.user)
        transactions = wallet.transactions.all()[:50]  # آخرین 50 تراکنش
        
        return Response([{
            'id': t.id,
            'type': t.transaction_type,
            'amount': t.amount,
            'balance_after': t.balance_after,
            'description': t.description,
            'created_at': t.created_at
        } for t in transactions])


class PaymentGatewayListView(APIView):
    """لیست درگاه‌های پرداخت فعال"""
    
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        """دریافت لیست درگاه‌های پرداخت فعال بر اساس ارز کاربر"""
        from finance.models import Currency
        
        # دریافت ارز پیش‌فرض کاربر (از query param یا تنظیمات کاربر)
        user_currency_code = request.query_params.get('currency', 'IRR')
        
        try:
            user_currency = Currency.objects.get(code=user_currency_code)
        except Currency.DoesNotExist:
            user_currency = Currency.objects.get(code='IRR')  # پیش‌فرض
        
        # فیلتر درگاه‌ها بر اساس ارزهای پشتیبانی شده
        gateways = PaymentGatewayModel.objects.filter(
            is_active=True,
            supported_currencies=user_currency
        ).order_by('display_order')
        
        data = [{
            'id': g.id,
            'name': g.name,
            'gateway_type': g.gateway_type,
            'is_active': g.is_active,
        } for g in gateways]
        
        return Response(data)


class StripeWebhookView(APIView):
    """Webhook برای Stripe"""
    
    permission_classes = []
    
    def post(self, request):
        """دریافت webhook از Stripe"""
        
        import stripe
        
        payload = request.body
        sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
        endpoint_secret = settings.STRIPE_WEBHOOK_SECRET
        
        try:
            event = stripe.Webhook.construct_event(
                payload, sig_header, endpoint_secret
            )
        except ValueError:
            return Response(status=400)
        except stripe.error.SignatureVerificationError:
            return Response(status=400)
        
        # پردازش event
        if event['type'] == 'payment_intent.succeeded':
            payment_intent = event['data']['object']
            
            # یافتن و به‌روزرسانی تراکنش
            try:
                stripe_payment = StripePayment.objects.get(
                    payment_intent_id=payment_intent['id']
                )
                
                service = StripeService()
                service.confirm_payment(payment_intent['id'])
                
            except StripePayment.DoesNotExist:
                logger.error(f"Stripe payment not found: {payment_intent['id']}")
        
        elif event['type'] == 'payment_intent.payment_failed':
            payment_intent = event['data']['object']
            
            try:
                stripe_payment = StripePayment.objects.get(
                    payment_intent_id=payment_intent['id']
                )
                transaction = stripe_payment.transaction
                transaction.status = PaymentStatus.FAILED
                transaction.save()
                
            except StripePayment.DoesNotExist:
                logger.error(f"Stripe payment not found: {payment_intent['id']}")
        
        return Response(status=200)
