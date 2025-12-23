"""
درگاه پرداخت Mock برای تست
این ماژول کاملاً مستقل است و می‌توان آن را حذف کرد بدون آسیب به پروژه

استفاده:
1. در settings.py تنظیم کنید: ENABLE_MOCK_GATEWAY = True
2. در PaymentGateway.choices اضافه کنید: MOCK = 'mock', 'Mock Gateway (Test)'
3. برای غیرفعال کردن: ENABLE_MOCK_GATEWAY = False
"""

from typing import Dict, Any, Optional
from decimal import Decimal
from django.conf import settings
from django.utils import timezone
import uuid
import random
import logging

logger = logging.getLogger(__name__)


class MockGatewayService:
    """
    سرویس درگاه پرداخت Mock برای تست
    
    این سرویس رفتار یک درگاه پرداخت واقعی را شبیه‌سازی می‌کند:
    - ایجاد پرداخت
    - تأیید پرداخت
    - شبیه‌سازی موفقیت/شکست
    - شبیه‌سازی تأخیر
    """
    
    # تنظیمات Mock Gateway
    ENABLED = getattr(settings, 'ENABLE_MOCK_GATEWAY', False)
    
    # درصد موفقیت پیش‌فرض (می‌توان از query parameter تغییر داد)
    DEFAULT_SUCCESS_RATE = 100  # 100% موفق
    
    # شبیه‌سازی تأخیر (ثانیه)
    SIMULATE_DELAY = False
    MIN_DELAY = 1
    MAX_DELAY = 3
    
    # URL‌های Mock
    MOCK_GATEWAY_URL = '/mock-payment-gateway/'
    
    @classmethod
    def is_enabled(cls) -> bool:
        """بررسی فعال بودن Mock Gateway"""
        return cls.ENABLED
    
    @classmethod
    def create_payment(cls, transaction, callback_url: str, 
                       description: str = None, 
                       success_rate: int = None,
                       force_status: str = None) -> Dict[str, Any]:
        """
        ایجاد پرداخت Mock
        
        Args:
            transaction: شیء Transaction
            callback_url: URL بازگشت
            description: توضیحات پرداخت
            success_rate: درصد موفقیت (0-100)
            force_status: اجبار وضعیت ('success', 'failed', 'cancelled')
        
        Returns:
            Dict شامل authority و payment_url
        """
        
        if not cls.is_enabled():
            raise ValueError("Mock Gateway is not enabled")
        
        # تولید Authority فیک
        authority = f"MOCK{uuid.uuid4().hex[:32].upper()}"
        
        # ذخیره اطلاعات در metadata
        metadata = {
            'mock_authority': authority,
            'success_rate': success_rate or cls.DEFAULT_SUCCESS_RATE,
            'force_status': force_status,
            'created_at': timezone.now().isoformat(),
        }
        
        # URL پرداخت Mock
        from django.urls import reverse
        payment_url = f"{settings.FRONTEND_URL}{cls.MOCK_GATEWAY_URL}?authority={authority}"
        
        logger.info(f"Mock Payment Created: {authority} for transaction {transaction.reference_id}")
        
        return {
            'status': 'success',
            'authority': authority,
            'payment_url': payment_url,
            'metadata': metadata,
            'message': 'Mock payment created successfully'
        }
    
    @classmethod
    def verify_payment(cls, authority: str, amount: Decimal, 
                      success_rate: int = None,
                      force_status: str = None) -> Dict[str, Any]:
        """
        تأیید پرداخت Mock
        
        Args:
            authority: کد Authority
            amount: مبلغ پرداخت
            success_rate: درصد موفقیت
            force_status: اجبار وضعیت
        
        Returns:
            Dict شامل نتیجه تأیید
        """
        
        if not cls.is_enabled():
            raise ValueError("Mock Gateway is not enabled")
        
        # بررسی Authority
        if not authority.startswith('MOCK'):
            return {
                'status': 'failed',
                'code': -1,
                'message': 'Invalid mock authority'
            }
        
        # تعیین وضعیت پرداخت
        if force_status:
            is_success = force_status == 'success'
        else:
            rate = success_rate or cls.DEFAULT_SUCCESS_RATE
            is_success = random.randint(1, 100) <= rate
        
        if is_success:
            # پرداخت موفق
            ref_id = random.randint(100000000, 999999999)
            card_pan = f"****{random.randint(1000, 9999)}"
            
            logger.info(f"Mock Payment Verified Successfully: {authority}, RefID: {ref_id}")
            
            return {
                'status': 'success',
                'code': 100,
                'message': 'تراکنش با موفقیت انجام شد (Mock)',
                'ref_id': ref_id,
                'card_pan': card_pan,
                'card_hash': f"MOCK{uuid.uuid4().hex[:16].upper()}",
                'fee_type': 'Merchant',
                'fee': 0,
            }
        else:
            # پرداخت ناموفق
            error_codes = [
                (-1, 'اطلاعات ارسال شده ناقص است'),
                (-2, 'IP یا مرچنت کد پذیرنده صحیح نیست'),
                (-3, 'مبلغ بایستی بزرگتر از 1,000 ریال باشد'),
                (-11, 'درخواست مورد نظر یافت نشد'),
                (-21, 'هیچ نوع عملیات مالی برای این تراکنش یافت نشد'),
                (-50, 'مبلغ پرداخت شده با مبلغ درخواستی مطابقت ندارد'),
            ]
            
            code, message = random.choice(error_codes)
            
            logger.warning(f"Mock Payment Failed: {authority}, Code: {code}")
            
            return {
                'status': 'failed',
                'code': code,
                'message': f'{message} (Mock)',
            }
    
    @classmethod
    def get_payment_status(cls, authority: str) -> Dict[str, Any]:
        """
        دریافت وضعیت پرداخت
        
        Args:
            authority: کد Authority
        
        Returns:
            Dict شامل وضعیت پرداخت
        """
        
        if not cls.is_enabled():
            raise ValueError("Mock Gateway is not enabled")
        
        # در Mock همیشه pending برمی‌گردانیم تا verify فراخوانی شود
        return {
            'status': 'pending',
            'authority': authority,
            'message': 'Payment is pending (Mock)'
        }
    
    @classmethod
    def cancel_payment(cls, authority: str) -> Dict[str, Any]:
        """
        لغو پرداخت
        
        Args:
            authority: کد Authority
        
        Returns:
            Dict شامل نتیجه لغو
        """
        
        if not cls.is_enabled():
            raise ValueError("Mock Gateway is not enabled")
        
        logger.info(f"Mock Payment Cancelled: {authority}")
        
        return {
            'status': 'success',
            'message': 'Payment cancelled successfully (Mock)'
        }


# Helper Functions برای استفاده آسان

def create_mock_payment(transaction, callback_url: str, **kwargs) -> Dict[str, Any]:
    """Helper function برای ایجاد پرداخت Mock"""
    return MockGatewayService.create_payment(transaction, callback_url, **kwargs)


def verify_mock_payment(authority: str, amount: Decimal, **kwargs) -> Dict[str, Any]:
    """Helper function برای تأیید پرداخت Mock"""
    return MockGatewayService.verify_payment(authority, amount, **kwargs)


def is_mock_enabled() -> bool:
    """بررسی فعال بودن Mock Gateway"""
    return MockGatewayService.is_enabled()
