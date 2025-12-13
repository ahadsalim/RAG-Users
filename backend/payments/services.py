"""
سرویس‌های پرداخت برای Zarinpal، Stripe و Crypto
"""
import requests
import hashlib
import hmac
import json
from decimal import Decimal
from django.conf import settings
from django.utils import timezone
from typing import Optional, Dict, Any
import stripe
from .models import (
    Transaction, PaymentStatus, PaymentGateway,
    ZarinpalPayment, StripePayment, CryptoPayment, Wallet
)


class ZarinpalService:
    """سرویس پرداخت زرین‌پال"""
    
    SANDBOX = getattr(settings, 'ZARINPAL_SANDBOX', True)
    MERCHANT_ID = getattr(settings, 'ZARINPAL_MERCHANT_ID', '')
    
    if SANDBOX:
        BASE_URL = 'https://sandbox.zarinpal.com/pg/v4/payment/'
        GATEWAY_URL = 'https://sandbox.zarinpal.com/pg/StartPay/'
    else:
        BASE_URL = 'https://api.zarinpal.com/pg/v4/payment/'
        GATEWAY_URL = 'https://www.zarinpal.com/pg/StartPay/'
    
    @classmethod
    def create_payment(cls, transaction: Transaction, callback_url: str, 
                       description: str = None, mobile: str = None, email: str = None) -> Dict[str, Any]:
        """ایجاد پرداخت در زرین‌پال"""
        
        amount = int(transaction.amount)  # زرین‌پال مبلغ را به ریال می‌خواهد
        
        data = {
            'merchant_id': cls.MERCHANT_ID,
            'amount': amount,
            'callback_url': callback_url,
            'description': description or f'پرداخت فاکتور {transaction.reference_id}',
        }
        
        if mobile:
            data['mobile'] = mobile
        if email:
            data['email'] = email
        
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
        
        try:
            response = requests.post(
                f'{cls.BASE_URL}request.json',
                data=json.dumps(data),
                headers=headers,
                timeout=10
            )
            result = response.json()
            
            if result['data'].get('code') == 100:
                # ذخیره اطلاعات زرین‌پال
                ZarinpalPayment.objects.create(
                    transaction=transaction,
                    authority=result['data']['authority']
                )
                
                # به‌روزرسانی تراکنش
                transaction.gateway_response = result
                transaction.status = PaymentStatus.PROCESSING
                transaction.save()
                
                return {
                    'success': True,
                    'authority': result['data']['authority'],
                    'payment_url': f"{cls.GATEWAY_URL}{result['data']['authority']}"
                }
            else:
                return {
                    'success': False,
                    'error': result['errors'] if 'errors' in result else 'خطا در ایجاد پرداخت'
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    @classmethod
    def verify_payment(cls, authority: str, amount: int) -> Dict[str, Any]:
        """تایید پرداخت زرین‌پال"""
        
        data = {
            'merchant_id': cls.MERCHANT_ID,
            'authority': authority,
            'amount': amount
        }
        
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
        
        try:
            response = requests.post(
                f'{cls.BASE_URL}verify.json',
                data=json.dumps(data),
                headers=headers,
                timeout=10
            )
            result = response.json()
            
            if result['data'].get('code') == 100:
                # یافتن پرداخت
                zarinpal_payment = ZarinpalPayment.objects.get(authority=authority)
                transaction = zarinpal_payment.transaction
                
                # به‌روزرسانی اطلاعات
                zarinpal_payment.ref_id = result['data']['ref_id']
                zarinpal_payment.card_hash = result['data'].get('card_hash', '')
                zarinpal_payment.card_pan = result['data'].get('card_pan', '')
                zarinpal_payment.fee_type = result['data'].get('fee_type', '')
                zarinpal_payment.fee = result['data'].get('fee', 0)
                zarinpal_payment.save()
                
                # به‌روزرسانی تراکنش
                transaction.status = PaymentStatus.SUCCESS
                transaction.paid_at = timezone.now()
                transaction.gateway_transaction_id = result['data']['ref_id']
                transaction.gateway_response = result
                transaction.save()
                
                return {
                    'success': True,
                    'ref_id': result['data']['ref_id'],
                    'transaction': transaction
                }
            else:
                return {
                    'success': False,
                    'error': result.get('errors', 'خطا در تایید پرداخت')
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }


class StripeService:
    """سرویس پرداخت Stripe"""
    
    def __init__(self):
        stripe.api_key = settings.STRIPE_SECRET_KEY
    
    def create_payment_intent(self, transaction: Transaction, 
                             return_url: str = None) -> Dict[str, Any]:
        """ایجاد Payment Intent در Stripe"""
        
        try:
            # تبدیل مبلغ به سنت (Stripe با سنت کار می‌کند)
            amount_cents = int(transaction.amount * 100)
            
            # ایجاد یا دریافت مشتری
            customer = self.get_or_create_customer(transaction.user)
            
            # ایجاد Payment Intent
            intent = stripe.PaymentIntent.create(
                amount=amount_cents,
                currency=transaction.currency.lower(),
                customer=customer.id,
                metadata={
                    'transaction_id': str(transaction.id),
                    'reference_id': transaction.reference_id
                },
                description=f'Payment for {transaction.reference_id}'
            )
            
            # ذخیره اطلاعات Stripe
            StripePayment.objects.create(
                transaction=transaction,
                payment_intent_id=intent.id,
                customer_id=customer.id
            )
            
            # به‌روزرسانی تراکنش
            transaction.status = PaymentStatus.PROCESSING
            transaction.gateway_response = {'intent': intent.to_dict()}
            transaction.save()
            
            return {
                'success': True,
                'client_secret': intent.client_secret,
                'payment_intent_id': intent.id
            }
            
        except stripe.error.StripeError as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_or_create_customer(self, user):
        """ایجاد یا دریافت مشتری در Stripe"""
        
        # چک کردن آیا قبلاً مشتری ایجاد شده
        stripe_payments = StripePayment.objects.filter(
            transaction__user=user,
            customer_id__isnull=False
        ).first()
        
        if stripe_payments and stripe_payments.customer_id:
            try:
                return stripe.Customer.retrieve(stripe_payments.customer_id)
            except:
                pass
        
        # ایجاد مشتری جدید
        return stripe.Customer.create(
            email=user.email,
            name=user.get_full_name(),
            metadata={'user_id': str(user.id)}
        )
    
    def confirm_payment(self, payment_intent_id: str) -> Dict[str, Any]:
        """تایید پرداخت Stripe"""
        
        try:
            # دریافت Payment Intent
            intent = stripe.PaymentIntent.retrieve(payment_intent_id)
            
            # یافتن پرداخت
            stripe_payment = StripePayment.objects.get(payment_intent_id=payment_intent_id)
            transaction = stripe_payment.transaction
            
            if intent.status == 'succeeded':
                # به‌روزرسانی اطلاعات Stripe
                stripe_payment.charge_id = intent.charges.data[0].id if intent.charges.data else ''
                stripe_payment.payment_method_id = intent.payment_method
                
                # دریافت اطلاعات کارت
                if intent.charges.data:
                    charge = intent.charges.data[0]
                    if charge.payment_method_details and charge.payment_method_details.card:
                        card = charge.payment_method_details.card
                        stripe_payment.card_brand = card.brand
                        stripe_payment.card_last4 = card.last4
                
                stripe_payment.save()
                
                # به‌روزرسانی تراکنش
                transaction.status = PaymentStatus.SUCCESS
                transaction.paid_at = timezone.now()
                transaction.gateway_transaction_id = intent.id
                transaction.gateway_response = {'intent': intent.to_dict()}
                transaction.save()
                
                return {
                    'success': True,
                    'transaction': transaction
                }
            else:
                transaction.status = PaymentStatus.FAILED
                transaction.save()
                
                return {
                    'success': False,
                    'error': f'Payment status: {intent.status}'
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def create_refund(self, transaction: Transaction, amount: Optional[Decimal] = None) -> Dict[str, Any]:
        """بازگشت وجه از طریق Stripe"""
        
        try:
            stripe_payment = transaction.stripe_payment
            
            # مبلغ بازگشت (اگر مشخص نشده، کل مبلغ)
            refund_amount = amount or transaction.amount
            refund_amount_cents = int(refund_amount * 100)
            
            # ایجاد بازگشت
            refund = stripe.Refund.create(
                payment_intent=stripe_payment.payment_intent_id,
                amount=refund_amount_cents,
                metadata={
                    'transaction_id': str(transaction.id),
                    'reference_id': transaction.reference_id
                }
            )
            
            # به‌روزرسانی تراکنش
            if refund_amount == transaction.amount:
                transaction.status = PaymentStatus.REFUNDED
            else:
                transaction.status = PaymentStatus.PARTIALLY_REFUNDED
            
            transaction.refunded_at = timezone.now()
            transaction.gateway_response['refund'] = refund.to_dict()
            transaction.save()
            
            return {
                'success': True,
                'refund_id': refund.id,
                'amount': refund_amount
            }
            
        except stripe.error.StripeError as e:
            return {
                'success': False,
                'error': str(e)
            }


class CryptoService:
    """سرویس پرداخت رمزارز"""
    
    @staticmethod
    def generate_wallet_address(cryptocurrency: str, network: str) -> str:
        """تولید آدرس کیف پول (در محیط واقعی باید با API Exchange کار کند)"""
        
        # این یک نمونه ساده است
        # در محیط واقعی باید با API های مثل Binance, Coinbase, BlockCypher کار کنید
        
        import hashlib
        import time
        
        # تولید یک آدرس نمونه
        seed = f"{cryptocurrency}_{network}_{time.time()}"
        hash_object = hashlib.sha256(seed.encode())
        hex_dig = hash_object.hexdigest()
        
        if cryptocurrency == 'BTC':
            return f"1{hex_dig[:33]}"  # Bitcoin address starts with 1
        elif cryptocurrency == 'ETH':
            return f"0x{hex_dig[:40]}"  # Ethereum address
        elif cryptocurrency in ['USDT', 'USDC']:
            if network == 'ethereum':
                return f"0x{hex_dig[:40]}"
            elif network == 'tron':
                return f"T{hex_dig[:33]}"
        else:
            return hex_dig[:40]
    
    @classmethod
    def create_crypto_payment(cls, transaction: Transaction, 
                            cryptocurrency: str, network: str) -> Dict[str, Any]:
        """ایجاد پرداخت رمزارز"""
        
        try:
            # تولید آدرس کیف پول
            wallet_address = cls.generate_wallet_address(cryptocurrency, network)
            
            # محاسبه مبلغ رمزارز (نیاز به API نرخ ارز)
            crypto_amount = cls.calculate_crypto_amount(
                transaction.amount,
                transaction.currency,
                cryptocurrency
            )
            
            # ایجاد پرداخت رمزارز
            crypto_payment = CryptoPayment.objects.create(
                transaction=transaction,
                cryptocurrency=cryptocurrency,
                network=network,
                wallet_address=wallet_address,
                amount_crypto=crypto_amount,
                required_confirmations=cls.get_required_confirmations(cryptocurrency)
            )
            
            # به‌روزرسانی تراکنش
            transaction.status = PaymentStatus.PROCESSING
            transaction.metadata['crypto'] = {
                'wallet_address': wallet_address,
                'amount': str(crypto_amount),
                'cryptocurrency': cryptocurrency,
                'network': network
            }
            transaction.save()
            
            return {
                'success': True,
                'wallet_address': wallet_address,
                'amount': crypto_amount,
                'cryptocurrency': cryptocurrency,
                'network': network,
                'qr_code': cls.generate_qr_code(wallet_address, crypto_amount, cryptocurrency)
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    @staticmethod
    def get_crypto_rates() -> dict:
        """دریافت نرخ رمزارزها از API خارجی"""
        import requests
        
        crypto_rates_api = getattr(settings, 'CRYPTO_RATES_API_URL', None)
        
        if crypto_rates_api:
            try:
                response = requests.get(crypto_rates_api, timeout=10)
                if response.status_code == 200:
                    return response.json()
            except Exception as e:
                logger.warning(f"Failed to fetch crypto rates from API: {e}")
        
        # نرخ‌های پیش‌فرض در صورت عدم دسترسی به API
        return {
            'BTC': 45000,
            'ETH': 3000,
            'USDT': 1,
            'USDC': 1,
            'BNB': 300,
        }
    
    @classmethod
    def calculate_crypto_amount(cls, amount: Decimal, currency: str, cryptocurrency: str) -> Decimal:
        """محاسبه مبلغ رمزارز بر اساس نرخ روز"""
        
        rates = cls.get_crypto_rates()
        
        # تبدیل به USD (فرض می‌کنیم currency=IRR)
        if currency == 'IRR':
            amount_usd = amount / 500000  # نرخ تقریبی
        else:
            amount_usd = amount
        
        # تبدیل به رمزارز
        rate = rates.get(cryptocurrency, 1)
        crypto_amount = Decimal(str(amount_usd / rate))
        
        return crypto_amount.quantize(Decimal('0.00000001'))
    
    @staticmethod
    def get_required_confirmations(cryptocurrency: str) -> int:
        """تعداد تاییدیه‌های مورد نیاز برای هر رمزارز"""
        
        confirmations = {
            'BTC': 3,
            'ETH': 12,
            'USDT': 12,
            'USDC': 12,
            'BNB': 15,
        }
        
        return confirmations.get(cryptocurrency, 6)
    
    @staticmethod
    def generate_qr_code(address: str, amount: Decimal, cryptocurrency: str) -> str:
        """تولید QR Code برای پرداخت"""
        
        import qrcode
        import io
        import base64
        
        # ساخت URI پرداخت
        if cryptocurrency == 'BTC':
            uri = f"bitcoin:{address}?amount={amount}"
        elif cryptocurrency == 'ETH':
            uri = f"ethereum:{address}?value={amount}"
        else:
            uri = address
        
        # تولید QR Code
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(uri)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        
        # تبدیل به Base64
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        img_str = base64.b64encode(buffer.getvalue()).decode()
        
        return f"data:image/png;base64,{img_str}"
    
    @classmethod
    def verify_crypto_payment(cls, tx_hash: str) -> Dict[str, Any]:
        """تایید پرداخت رمزارز از طریق بررسی بلاکچین"""
        
        try:
            # یافتن پرداخت
            crypto_payment = CryptoPayment.objects.get(tx_hash=tx_hash)
            transaction = crypto_payment.transaction
            
            # در محیط واقعی باید از API های بلاکچین استفاده کنید
            # مثل BlockCypher, Etherscan, etc.
            
            # فرض می‌کنیم پرداخت تایید شده
            confirmations = 6  # در واقعیت از API دریافت می‌شود
            
            crypto_payment.confirmations = confirmations
            crypto_payment.save()
            
            if confirmations >= crypto_payment.required_confirmations:
                # به‌روزرسانی تراکنش
                transaction.status = PaymentStatus.SUCCESS
                transaction.paid_at = timezone.now()
                transaction.gateway_transaction_id = tx_hash
                transaction.save()
                
                return {
                    'success': True,
                    'confirmations': confirmations,
                    'transaction': transaction
                }
            else:
                return {
                    'success': False,
                    'error': f'تاییدیه‌های کافی نیست ({confirmations}/{crypto_payment.required_confirmations})'
                }
                
        except CryptoPayment.DoesNotExist:
            return {
                'success': False,
                'error': 'پرداخت یافت نشد'
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }


class WalletService:
    """سرویس کیف پول اعتباری"""
    
    @staticmethod
    def get_or_create_wallet(user) -> Wallet:
        """دریافت یا ایجاد کیف پول برای کاربر"""
        
        wallet, created = Wallet.objects.get_or_create(
            user=user,
            defaults={
                'balance': 0,
                'currency': 'IRR'
            }
        )
        
        return wallet
    
    @staticmethod
    def pay_with_wallet(transaction: Transaction) -> Dict[str, Any]:
        """پرداخت از طریق کیف پول"""
        
        try:
            wallet = WalletService.get_or_create_wallet(transaction.user)
            
            # بررسی موجودی
            if wallet.balance < transaction.amount:
                return {
                    'success': False,
                    'error': 'موجودی کیف پول کافی نیست',
                    'balance': wallet.balance,
                    'required': transaction.amount
                }
            
            # کسر از کیف پول
            wallet.deduct_credit(
                transaction.amount,
                f'پرداخت فاکتور {transaction.reference_id}'
            )
            
            # به‌روزرسانی تراکنش
            transaction.status = PaymentStatus.SUCCESS
            transaction.paid_at = timezone.now()
            transaction.gateway = PaymentGateway.CREDIT
            transaction.save()
            
            return {
                'success': True,
                'new_balance': wallet.balance,
                'transaction': transaction
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    @staticmethod
    def charge_wallet(user, amount: Decimal, transaction: Transaction = None) -> bool:
        """شارژ کیف پول"""
        
        try:
            wallet = WalletService.get_or_create_wallet(user)
            wallet.add_credit(
                amount,
                f'شارژ کیف پول - {transaction.reference_id if transaction else "مستقیم"}'
            )
            
            return True
            
        except Exception as e:
            return False
