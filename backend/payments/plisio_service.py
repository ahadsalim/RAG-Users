"""
سرویس پرداخت Plisio برای ارز دیجیتال
"""
import requests
import hashlib
import hmac
import logging
from django.conf import settings
from django.utils import timezone
from typing import Optional, Dict, Any
from .models import Transaction, PaymentStatus, PlisioPayment

logger = logging.getLogger(__name__)


class PlisioService:
    """سرویس پرداخت Plisio"""
    
    BASE_URL = 'https://api.plisio.net/api/v1'
    API_KEY = getattr(settings, 'PLISIO_API_KEY', '')
    
    @classmethod
    def create_invoice(cls, transaction: Transaction, callback_url: str, 
                      currency: str = 'USDT_TRX') -> Dict[str, Any]:
        """
        ایجاد invoice در Plisio
        
        Args:
            transaction: تراکنش
            callback_url: آدرس بازگشت
            currency: ارز دیجیتال (پیش‌فرض: USDT_TRX)
            
        Returns:
            دیکشنری حاوی نتیجه
        """
        try:
            from finance.models import PaymentGateway as PaymentGatewayModel
            
            # دریافت تنظیمات درگاه Plisio
            gateway = PaymentGatewayModel.objects.filter(name='Plisio').first()
            if not gateway:
                raise ValueError("Gateway configuration for Plisio not found")
            
            # تبدیل مبلغ به ارز مبنای درگاه (USD)
            amount_in_gateway_currency = transaction.get_amount_in_gateway_currency(gateway)
            amount_usd = float(amount_in_gateway_currency)
            
            # پارامترهای درخواست
            params = {
                'api_key': cls.API_KEY,
                'order_number': transaction.reference_id,
                'order_name': f'Payment {transaction.reference_id}',
                'source_currency': 'USD',
                'source_amount': round(amount_usd, 2),
                'currency': currency,
                'callback_url': f"{callback_url}?json=true",
                'email': transaction.user.email if transaction.user.email else '',
                'description': transaction.description or f'Payment for order {transaction.reference_id}',
            }
            
            # ارسال درخواست
            url = f"{cls.BASE_URL}/invoices/new"
            response = requests.get(url, params=params, timeout=30)
            result = response.json()
            
            if result.get('status') == 'success':
                data = result.get('data', {})
                
                # ذخیره اطلاعات Plisio
                PlisioPayment.objects.create(
                    transaction=transaction,
                    txn_id=data.get('txn_id'),
                    invoice_url=data.get('invoice_url', ''),
                    wallet_hash=data.get('wallet_hash', ''),
                    psys_cid=data.get('psys_cid', currency),
                    amount_crypto=data.get('amount', 0),
                    expected_confirmations=data.get('expected_confirmations', 1),
                    verify_hash=data.get('verify_hash', '')
                )
                
                # به‌روزرسانی تراکنش
                transaction.gateway_response = result
                transaction.status = PaymentStatus.PROCESSING
                transaction.save()
                
                return {
                    'success': True,
                    'txn_id': data.get('txn_id'),
                    'invoice_url': data.get('invoice_url'),
                    'wallet_hash': data.get('wallet_hash'),
                    'amount_crypto': data.get('amount'),
                    'currency': data.get('psys_cid', currency),
                    'message': 'Invoice created successfully'
                }
            else:
                error_data = result.get('data', {})
                return {
                    'success': False,
                    'error': error_data.get('message', 'Failed to create invoice')
                }
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Plisio API request error: {str(e)}")
            return {
                'success': False,
                'error': f'Connection error: {str(e)}'
            }
        except Exception as e:
            logger.error(f"Plisio service error: {str(e)}")
            return {
                'success': False,
                'error': f'Unexpected error: {str(e)}'
            }
    
    @classmethod
    def verify_callback(cls, callback_data: Dict[str, Any]) -> bool:
        """
        تایید صحت callback از Plisio
        
        Args:
            callback_data: داده‌های دریافتی از callback
            
        Returns:
            True اگر معتبر باشد
        """
        try:
            if 'verify_hash' not in callback_data:
                return False
            
            verify_hash = callback_data.get('verify_hash')
            data = callback_data.copy()
            del data['verify_hash']
            
            # مرتب‌سازی کلیدها
            sorted_data = dict(sorted(data.items()))
            
            # تبدیل expire_utc به string
            if 'expire_utc' in sorted_data:
                sorted_data['expire_utc'] = str(sorted_data['expire_utc'])
            
            # سریالایز کردن داده‌ها (مشابه PHP serialize)
            # برای سادگی از JSON استفاده می‌کنیم
            import json
            data_string = json.dumps(sorted_data, separators=(',', ':'), ensure_ascii=False)
            
            # محاسبه hash
            calculated_hash = hmac.new(
                cls.API_KEY.encode('utf-8'),
                data_string.encode('utf-8'),
                hashlib.sha1
            ).hexdigest()
            
            return calculated_hash == verify_hash
            
        except Exception as e:
            logger.error(f"Plisio callback verification error: {str(e)}")
            return False
    
    @classmethod
    def process_callback(cls, callback_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        پردازش callback از Plisio
        
        Args:
            callback_data: داده‌های callback
            
        Returns:
            نتیجه پردازش
        """
        try:
            txn_id = callback_data.get('txn_id')
            status = callback_data.get('status')
            
            if not txn_id:
                return {
                    'success': False,
                    'error': 'Missing txn_id'
                }
            
            # یافتن پرداخت
            plisio_payment = PlisioPayment.objects.get(txn_id=txn_id)
            transaction = plisio_payment.transaction
            
            # به‌روزرسانی اطلاعات
            plisio_payment.confirmations = callback_data.get('confirmations', 0)
            plisio_payment.tx_urls = callback_data.get('tx_urls', [])
            plisio_payment.save()
            
            # به‌روزرسانی تراکنش بر اساس وضعیت
            if status == 'completed':
                transaction.status = PaymentStatus.SUCCESS
                transaction.paid_at = timezone.now()
                transaction.gateway_transaction_id = txn_id
            elif status in ['expired', 'error', 'cancelled']:
                transaction.status = PaymentStatus.FAILED
            elif status in ['pending', 'pending internal']:
                transaction.status = PaymentStatus.PROCESSING
            
            transaction.gateway_response = callback_data
            transaction.save()
            
            return {
                'success': True,
                'status': status,
                'transaction_id': str(transaction.id)
            }
            
        except PlisioPayment.DoesNotExist:
            logger.error(f"Plisio payment not found: {txn_id}")
            return {
                'success': False,
                'error': 'Payment not found'
            }
        except Exception as e:
            logger.error(f"Plisio callback processing error: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    @classmethod
    def get_supported_currencies(cls) -> list:
        """لیست ارزهای دیجیتال پشتیبانی شده"""
        return [
            'BTC',           # Bitcoin
            'ETH',           # Ethereum
            'USDT_TRX',      # Tether (Tron)
            'USDT',          # Tether (Ethereum)
            'USDC',          # USD Coin
            'BNB',           # Binance Coin
            'TRX',           # Tron
            'LTC',           # Litecoin
            'DOGE',          # Dogecoin
            'DASH',          # Dash
            'SHIB',          # Shiba Inu
        ]
