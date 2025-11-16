"""
RAG Core API Client
مسئول ارتباط با سیستم مرکزی RAG
"""
import httpx
import asyncio
import json
import logging
from typing import Dict, Optional, List, AsyncGenerator
from django.conf import settings
from django.core.cache import cache
from rest_framework.exceptions import APIException
import aiohttp
import time

logger = logging.getLogger('app')


class RAGCoreException(APIException):
    """خطاهای مربوط به RAG Core"""
    status_code = 500
    default_detail = 'خطا در ارتباط با سیستم مرکزی'
    default_code = 'rag_core_error'


class RateLimitException(RAGCoreException):
    """خطای محدودیت درخواست"""
    status_code = 429
    default_detail = 'محدودیت روزانه شما تمام شده است'
    default_code = 'rate_limit_exceeded'


class InsufficientTierException(RAGCoreException):
    """خطای عدم دسترسی به ویژگی"""
    status_code = 403
    default_detail = 'پلن شما این ویژگی را پشتیبانی نمی‌کند'
    default_code = 'insufficient_tier'


class RAGCoreClient:
    """کلاینت اتصال به RAG Core API"""
    
    def __init__(self):
        self.base_url = settings.RAG_CORE_BASE_URL.rstrip('/')
        self.api_key = settings.RAG_CORE_API_KEY
        self.timeout = httpx.Timeout(60.0, connect=10.0)
        self.headers = {
            'Content-Type': 'application/json',
        }
        if self.api_key:
            self.headers['X-API-Key'] = self.api_key
    
    def _get_jwt_token(self, user):
        """دریافت JWT token برای کاربر"""
        # اگر توکن در کش موجود است، آن را برگردان
        cache_key = f"rag_jwt_{user.id}"
        token = cache.get(cache_key)
        
        if not token:
            # اگر توکن موجود نیست، از سیستم مرکزی دریافت کن
            token = self._authenticate_user(user)
            # توکن را برای 25 دقیقه کش کن (کمتر از 30 دقیقه expiry)
            cache.set(cache_key, token, 1500)
        
        return token
    
    def _authenticate_user(self, user):
        """احراز هویت کاربر در سیستم مرکزی"""
        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.post(
                    f"{self.base_url}/api/v1/auth/login",
                    json={
                        'username': user.email,
                        'password': 'temp_password'  # این باید از طریق secure channel انجام شود
                    },
                    headers=self.headers
                )
                response.raise_for_status()
                data = response.json()
                return data.get('access_token')
        except Exception as e:
            logger.error(f"خطا در احراز هویت RAG Core: {str(e)}")
            raise RAGCoreException("خطا در احراز هویت با سیستم مرکزی")
    
    async def send_query(
        self,
        query: str,
        user,
        conversation_id: Optional[str] = None,
        response_mode: str = 'simple_explanation',
        max_results: int = 5,
        use_cache: bool = True,
        use_reranking: bool = True,
        stream: bool = False,
        filters: Optional[Dict] = None,
        llm_config: Optional[Dict] = None,
        context: Optional[Dict] = None
    ) -> Dict:
        """ارسال سوال به سیستم RAG Core"""
        
        # آماده‌سازی payload
        payload = {
            'query': query,
            'user_id': str(user.id),  # استفاده از user.id به عنوان external_user_id
            'language': user.language or 'fa',
            'conversation_id': conversation_id,
            'max_results': max_results,
            'use_cache': use_cache,
            'use_reranking': use_reranking,
            'stream': stream,
        }
        
        # افزودن فیلترها در صورت وجود
        if filters:
            payload['filters'] = filters
        
        # تنظیمات LLM
        if llm_config:
            payload['llm_config'] = llm_config
        
        # Context اضافی
        if not context:
            context = {}
        
        # افزودن اطلاعات کاربر به context
        context.update({
            'user_tier': self._get_user_tier(user),
            'user_preferences': {
                'detailed_response': True,
                'include_sources': True,
                'response_mode': response_mode,
            },
            'organization': str(user.organization.id) if user.organization else None,
        })
        payload['context'] = context
        
        # دریافت JWT token
        jwt_token = self._get_jwt_token(user)
        headers = {
            **self.headers,
            'Authorization': f'Bearer {jwt_token}'
        }
        
        try:
            # ارسال درخواست async
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                start_time = time.time()
                
                response = await client.post(
                    f"{self.base_url}/api/v1/query",
                    json=payload,
                    headers=headers
                )
                
                processing_time = int((time.time() - start_time) * 1000)
                
                # بررسی خطاها
                if response.status_code == 429:
                    error_data = response.json()
                    retry_after = error_data.get('retry_after', 3600)
                    raise RateLimitException(
                        detail=error_data.get('detail', 'محدودیت روزانه شما تمام شده است'),
                        code='rate_limit_exceeded'
                    )
                
                if response.status_code == 403:
                    error_data = response.json()
                    raise InsufficientTierException(
                        detail=error_data.get('detail', 'پلن شما این ویژگی را پشتیبانی نمی‌کند')
                    )
                
                response.raise_for_status()
                
                # پردازش پاسخ موفق
                data = response.json()
                
                # افزودن زمان پردازش محلی
                if 'metadata' in data:
                    data['metadata']['local_processing_time_ms'] = processing_time
                
                return data
                
        except httpx.TimeoutException:
            logger.error(f"Timeout در ارسال query به RAG Core")
            raise RAGCoreException("زمان پاسخ سیستم مرکزی بیش از حد طولانی شد")
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP Error from RAG Core: {e.response.status_code} - {e.response.text}")
            raise RAGCoreException(f"خطای HTTP {e.response.status_code} از سیستم مرکزی")
        except Exception as e:
            logger.error(f"خطا در ارسال query به RAG Core: {str(e)}")
            raise RAGCoreException(f"خطا در ارتباط با سیستم مرکزی: {str(e)}")
    
    async def send_query_stream(
        self,
        query: str,
        user,
        conversation_id: Optional[str] = None,
        response_mode: str = 'simple_explanation',
        **kwargs
    ) -> AsyncGenerator[Dict, None]:
        """ارسال سوال با پاسخ streaming"""
        
        payload = {
            'query': query,
            'user_id': str(user.id),
            'language': user.language or 'fa',
            'conversation_id': conversation_id,
            'stream': True,
            **kwargs
        }
        
        # دریافت JWT token
        jwt_token = self._get_jwt_token(user)
        headers = {
            **self.headers,
            'Authorization': f'Bearer {jwt_token}',
            'Accept': 'text/event-stream'
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/api/v1/query/stream",
                    json=payload,
                    headers=headers
                ) as response:
                    
                    if response.status == 429:
                        raise RateLimitException()
                    
                    response.raise_for_status()
                    
                    # خواندن stream
                    async for line in response.content:
                        if line:
                            decoded = line.decode('utf-8')
                            if decoded.startswith('data: '):
                                try:
                                    data = json.loads(decoded[6:])
                                    yield data
                                except json.JSONDecodeError:
                                    continue
                                    
        except Exception as e:
            logger.error(f"خطا در streaming از RAG Core: {str(e)}")
            raise RAGCoreException(f"خطا در دریافت پاسخ streaming: {str(e)}")
    
    async def get_conversations(self, user, page: int = 1, page_size: int = 10) -> Dict:
        """دریافت لیست گفتگوهای کاربر از RAG Core"""
        jwt_token = self._get_jwt_token(user)
        headers = {
            **self.headers,
            'Authorization': f'Bearer {jwt_token}'
        }
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    f"{self.base_url}/api/v1/users/{user.id}/conversations",
                    params={'page': page, 'page_size': page_size},
                    headers=headers
                )
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.error(f"خطا در دریافت conversations: {str(e)}")
            return {'conversations': [], 'total': 0}
    
    async def get_conversation_messages(
        self,
        user,
        conversation_id: str,
        page: int = 1,
        page_size: int = 50
    ) -> Dict:
        """دریافت پیام‌های یک گفتگو"""
        jwt_token = self._get_jwt_token(user)
        headers = {
            **self.headers,
            'Authorization': f'Bearer {jwt_token}'
        }
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    f"{self.base_url}/api/v1/conversations/{conversation_id}/messages",
                    params={'page': page, 'page_size': page_size},
                    headers=headers
                )
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.error(f"خطا در دریافت messages: {str(e)}")
            return {'messages': [], 'total': 0}
    
    async def send_feedback(
        self,
        user,
        message_id: str,
        rating: Optional[int] = None,
        feedback_type: Optional[str] = None,
        feedback_text: Optional[str] = None,
        suggested_response: Optional[str] = None
    ) -> bool:
        """ارسال بازخورد کاربر به RAG Core"""
        jwt_token = self._get_jwt_token(user)
        headers = {
            **self.headers,
            'Authorization': f'Bearer {jwt_token}'
        }
        
        payload = {
            'message_id': message_id,
        }
        
        if rating is not None:
            payload['rating'] = rating
        if feedback_type:
            payload['feedback_type'] = feedback_type
        if feedback_text:
            payload['feedback_text'] = feedback_text
        if suggested_response:
            payload['suggested_response'] = suggested_response
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/api/v1/feedback",
                    json=payload,
                    headers=headers
                )
                response.raise_for_status()
                return True
        except Exception as e:
            logger.error(f"خطا در ارسال feedback: {str(e)}")
            return False
    
    async def sync_user(self, user) -> bool:
        """همگام‌سازی اطلاعات کاربر با RAG Core"""
        
        # آماده‌سازی داده‌های کاربر
        user_data = {
            'external_user_id': str(user.id),
            'username': user.username,
            'email': user.email,
            'full_name': f"{user.first_name} {user.last_name}".strip() or user.username,
            'tier': self._get_user_tier(user),
            'daily_query_limit': self._get_user_query_limit(user),
            'preferences': {
                'language': user.language,
                'timezone': user.timezone,
                'detailed_responses': True,
            },
            'feature_flags': {
                'voice_search_enabled': False,  # می‌تواند بر اساس پلن تنظیم شود
                'image_search_enabled': False,
                'streaming_enabled': True,
            }
        }
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/api/v1/users/sync",
                    json=user_data,
                    headers={
                        **self.headers,
                        'X-API-Key': self.api_key
                    }
                )
                response.raise_for_status()
                return True
        except Exception as e:
            logger.error(f"خطا در sync کاربر با RAG Core: {str(e)}")
            return False
    
    async def get_user_statistics(self, user) -> Dict:
        """دریافت آمار کاربر از RAG Core"""
        jwt_token = self._get_jwt_token(user)
        headers = {
            **self.headers,
            'Authorization': f'Bearer {jwt_token}'
        }
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    f"{self.base_url}/api/v1/users/{user.id}/profile",
                    headers=headers
                )
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.error(f"خطا در دریافت آمار کاربر: {str(e)}")
            return {
                'daily_query_count': 0,
                'daily_query_limit': self._get_user_query_limit(user),
                'total_query_count': 0,
                'total_tokens_used': 0,
            }
    
    def _get_user_tier(self, user) -> str:
        """تعیین سطح کاربر بر اساس اشتراک"""
        # این باید از مدل Subscription خوانده شود
        # فعلاً به صورت موقت
        if hasattr(user, 'subscription'):
            subscription = user.subscription
            if subscription.plan.name == 'رایگان':
                return 'free'
            elif subscription.plan.name == 'پایه':
                return 'basic'
            elif subscription.plan.name == 'حرفه‌ای':
                return 'premium'
            elif subscription.plan.name == 'سازمانی':
                return 'enterprise'
        return 'free'
    
    def _get_user_query_limit(self, user) -> int:
        """دریافت محدودیت روزانه کاربر"""
        tier = self._get_user_tier(user)
        limits = {
            'free': 50,
            'basic': 200,
            'premium': 1000,
            'enterprise': -1  # نامحدود
        }
        return limits.get(tier, 50)


# ایجاد instance global از client
rag_client = RAGCoreClient()
