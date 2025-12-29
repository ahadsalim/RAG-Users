"""
سرویس پرداخت برای درگاه تست تجارت
"""
import requests
import logging
from django.conf import settings
from django.utils import timezone
from typing import Optional, Dict, Any
from .models import Transaction, PaymentStatus, TejaratTestPayment

logger = logging.getLogger(__name__)


class TejaratTestService:
    """سرویس پرداخت درگاه تست تجارت"""
    
    BASE_URL = getattr(settings, 'TEJARAT_TEST_BASE_URL', 'http://payment.tejarat.chat:8000')
    MERCHANT_ID = getattr(settings, 'TEJARAT_TEST_MERCHANT_ID', 'MERCHANT_001')
    
    @classmethod
    def create_payment(cls, transaction: Transaction, callback_url: str) -> Dict[str, Any]:
        """ایجاد پرداخت در درگاه تست تجارت"""
        
        try:
            from finance.models import PaymentGateway as PaymentGatewayModel
            
            # دریافت تنظیمات درگاه تست تجارت
            gateway = PaymentGatewayModel.objects.filter(name='درگاه تست تجارت').first()
            if not gateway:
                raise ValueError("Gateway configuration for Tejarat Test not found")
            
            # تبدیل مبلغ به ارز مبنای درگاه
            amount_in_gateway_currency = transaction.get_amount_in_gateway_currency(gateway)
            amount = int(amount_in_gateway_currency)
            
            payload = {
                'merchant_id': cls.MERCHANT_ID,
                'amount': amount,
                'callback_url': callback_url,
                'description': transaction.description or f'پرداخت {transaction.reference_id}'
            }
            
            # ارسال درخواست
            url = f"{cls.BASE_URL}/api/payment/request"
            response = requests.post(
                url,
                json=payload,
                timeout=30
            )
            
            result = response.json()
            
            if result.get('status') == 0:  # موفق
                token = result.get('token')
                
                # ذخیره اطلاعات
                TejaratTestPayment.objects.create(
                    transaction=transaction,
                    token=token
                )
                
                # به‌روزرسانی تراکنش
                transaction.gateway_response = result
                transaction.status = PaymentStatus.PROCESSING
                transaction.save()
                
                # URL پرداخت
                payment_url = f"{cls.BASE_URL}/payment/gateway/{token}"
                
                return {
                    'success': True,
                    'token': token,
                    'payment_url': payment_url,
                    'message': result.get('message', 'درخواست پرداخت با موفقیت ایجاد شد')
                }
            else:
                return {
                    'success': False,
                    'error': result.get('message', 'خطا در ایجاد درخواست پرداخت')
                }
        
        except requests.exceptions.RequestException as e:
            logger.error(f"Tejarat Test payment request error: {str(e)}")
            return {
                'success': False,
                'error': f'خطا در اتصال به درگاه پرداخت: {str(e)}'
            }
        except Exception as e:
            logger.error(f"Tejarat Test payment error: {str(e)}")
            return {
                'success': False,
                'error': f'خطای غیرمنتظره: {str(e)}'
            }
    
    @classmethod
    def verify_payment(cls, token: str) -> Dict[str, Any]:
        """
        تایید پرداخت
        
        Args:
            token: توکن پرداخت
            
        Returns:
            دیکشنری حاوی نتیجه
        """
        try:
            # یافتن پرداخت
            tejarat_payment = TejaratTestPayment.objects.get(token=token)
            transaction = tejarat_payment.transaction
            
            # ارسال درخواست تایید
            payload = {
                'merchant_id': cls.MERCHANT_ID,
                'token': token
            }
            
            url = f"{cls.BASE_URL}/api/payment/verify"
            response = requests.post(
                url,
                json=payload,
                timeout=30
            )
            
            result = response.json()
            
            if result.get('status') == 0:  # موفق
                # به‌روزرسانی اطلاعات
                tejarat_payment.card_number = result.get('card_number', '')
                tejarat_payment.tracking_code = result.get('tracking_code', '')
                tejarat_payment.save()
                
                # به‌روزرسانی تراکنش
                transaction.status = PaymentStatus.SUCCESS
                transaction.paid_at = timezone.now()
                transaction.gateway_transaction_id = result.get('tracking_code', '')
                transaction.gateway_response = result
                transaction.save()
                
                return {
                    'success': True,
                    'tracking_code': result.get('tracking_code'),
                    'card_number': result.get('card_number'),
                    'amount': result.get('amount'),
                    'message': result.get('message', 'پرداخت با موفقیت انجام شد')
                }
            else:
                # پرداخت ناموفق
                transaction.status = PaymentStatus.FAILED
                transaction.gateway_response = result
                transaction.save()
                
                return {
                    'success': False,
                    'error': result.get('message', 'پرداخت ناموفق بود')
                }
                
        except TejaratTestPayment.DoesNotExist:
            logger.error(f"Tejarat Test payment not found: {token}")
            return {
                'success': False,
                'error': 'پرداخت یافت نشد'
            }
        except requests.exceptions.RequestException as e:
            logger.error(f"Tejarat Test verify error: {str(e)}")
            return {
                'success': False,
                'error': f'خطا در اتصال به درگاه پرداخت: {str(e)}'
            }
        except Exception as e:
            logger.error(f"Tejarat Test verify error: {str(e)}")
            return {
                'success': False,
                'error': f'خطای غیرمنتظره: {str(e)}'
            }
