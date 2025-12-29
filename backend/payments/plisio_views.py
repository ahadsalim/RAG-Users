"""
Views برای Plisio callback
"""
from rest_framework.views import APIView
from django.shortcuts import redirect
from django.conf import settings
from django.utils import timezone
import logging

from .models import PlisioPayment, PaymentStatus
from .plisio_service import PlisioService
from subscriptions.models import Subscription

logger = logging.getLogger(__name__)


class PlisioCallbackView(APIView):
    """Callback برای Plisio"""
    
    permission_classes = []  # No authentication required for callback
    
    def post(self, request):
        """پردازش callback از Plisio"""
        
        callback_data = request.data
        
        # تایید صحت callback
        if not PlisioService.verify_callback(callback_data):
            logger.error(f"Invalid Plisio callback signature: {callback_data}")
            return redirect(f"{settings.FRONTEND_URL}/payment/error?message=Invalid signature")
        
        try:
            # پردازش callback
            result = PlisioService.process_callback(callback_data)
            
            if result['success']:
                # یافتن تراکنش
                txn_id = callback_data.get('txn_id')
                plisio_payment = PlisioPayment.objects.get(txn_id=txn_id)
                transaction = plisio_payment.transaction
                
                # فعال‌سازی اشتراک در صورت موفقیت
                if callback_data.get('status') == 'completed' and transaction.plan:
                    subscription, created = Subscription.objects.get_or_create(
                        user=transaction.user,
                        defaults={
                            'plan': transaction.plan,
                            'status': 'active',
                            'start_date': timezone.now().date(),
                            'end_date': timezone.now().date() + timezone.timedelta(days=transaction.plan.duration_days),
                            'payment_method': transaction.gateway
                        }
                    )
                    
                    if not created:
                        subscription.renew()
                    
                    transaction.subscription = subscription
                    transaction.save()
                
                return redirect(
                    f"{settings.FRONTEND_URL}/payment/success?"
                    f"txn_id={txn_id}&"
                    f"transaction_id={transaction.id}"
                )
            else:
                return redirect(
                    f"{settings.FRONTEND_URL}/payment/error?"
                    f"message={result.get('error', 'Payment failed')}"
                )
                
        except PlisioPayment.DoesNotExist:
            logger.error(f"Plisio payment not found: {callback_data.get('txn_id')}")
            return redirect(f"{settings.FRONTEND_URL}/payment/error?message=Payment not found")
        except Exception as e:
            logger.error(f"Plisio callback error: {e}")
            return redirect(f"{settings.FRONTEND_URL}/payment/error?message=Internal error")
