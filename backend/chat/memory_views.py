"""
API Views برای مدیریت حافظه بلندمدت کاربر
Proxy به سیستم مرکزی (RAG Core)
"""
import logging
import httpx
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from django.conf import settings

logger = logging.getLogger(__name__)

# Base URL for RAG Core Memory API
MEMORY_API_BASE = f"{settings.RAG_CORE_BASE_URL}/api/v1/memory"


class MemoryListView(APIView):
    """لیست و ایجاد حافظه‌ها"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """دریافت لیست حافظه‌های کاربر"""
        try:
            response = httpx.get(
                f"{MEMORY_API_BASE}/",
                headers={
                    'Authorization': request.headers.get('Authorization'),
                    'X-User-ID': str(request.user.id),
                },
                timeout=30.0
            )
            
            if response.status_code == 200:
                return Response(response.json())
            else:
                logger.error(f"Memory API error: {response.status_code} - {response.text}")
                return Response(
                    {'error': 'خطا در دریافت حافظه‌ها'},
                    status=response.status_code
                )
        except httpx.TimeoutException:
            return Response(
                {'error': 'زمان درخواست به پایان رسید'},
                status=status.HTTP_504_GATEWAY_TIMEOUT
            )
        except Exception as e:
            logger.error(f"Memory list error: {e}")
            return Response(
                {'error': 'خطای داخلی سرور'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def post(self, request):
        """افزودن حافظه جدید"""
        try:
            response = httpx.post(
                f"{MEMORY_API_BASE}/",
                headers={
                    'Authorization': request.headers.get('Authorization'),
                    'X-User-ID': str(request.user.id),
                    'Content-Type': 'application/json',
                },
                json=request.data,
                timeout=30.0
            )
            
            if response.status_code in [200, 201]:
                return Response(response.json(), status=status.HTTP_201_CREATED)
            else:
                logger.error(f"Memory create error: {response.status_code} - {response.text}")
                return Response(
                    {'error': 'خطا در ایجاد حافظه'},
                    status=response.status_code
                )
        except Exception as e:
            logger.error(f"Memory create error: {e}")
            return Response(
                {'error': 'خطای داخلی سرور'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def delete(self, request):
        """پاک کردن همه حافظه‌ها"""
        try:
            response = httpx.delete(
                f"{MEMORY_API_BASE}/",
                headers={
                    'Authorization': request.headers.get('Authorization'),
                    'X-User-ID': str(request.user.id),
                },
                timeout=30.0
            )
            
            if response.status_code == 200:
                return Response(response.json())
            else:
                return Response(
                    {'error': 'خطا در پاک کردن حافظه‌ها'},
                    status=response.status_code
                )
        except Exception as e:
            logger.error(f"Memory clear error: {e}")
            return Response(
                {'error': 'خطای داخلی سرور'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class MemoryDetailView(APIView):
    """ویرایش و حذف یک حافظه"""
    permission_classes = [IsAuthenticated]
    
    def put(self, request, memory_id):
        """ویرایش حافظه"""
        try:
            response = httpx.put(
                f"{MEMORY_API_BASE}/{memory_id}",
                headers={
                    'Authorization': request.headers.get('Authorization'),
                    'X-User-ID': str(request.user.id),
                    'Content-Type': 'application/json',
                },
                json=request.data,
                timeout=30.0
            )
            
            if response.status_code == 200:
                return Response(response.json())
            else:
                return Response(
                    {'error': 'خطا در ویرایش حافظه'},
                    status=response.status_code
                )
        except Exception as e:
            logger.error(f"Memory update error: {e}")
            return Response(
                {'error': 'خطای داخلی سرور'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def delete(self, request, memory_id):
        """حذف یک حافظه"""
        try:
            response = httpx.delete(
                f"{MEMORY_API_BASE}/{memory_id}",
                headers={
                    'Authorization': request.headers.get('Authorization'),
                    'X-User-ID': str(request.user.id),
                },
                timeout=30.0
            )
            
            if response.status_code == 200:
                return Response(response.json())
            else:
                return Response(
                    {'error': 'خطا در حذف حافظه'},
                    status=response.status_code
                )
        except Exception as e:
            logger.error(f"Memory delete error: {e}")
            return Response(
                {'error': 'خطای داخلی سرور'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class MemorySummarizeView(APIView):
    """خلاصه‌سازی حافظه‌ها"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        """خلاصه‌سازی حافظه‌ها"""
        try:
            response = httpx.post(
                f"{MEMORY_API_BASE}/summarize",
                headers={
                    'Authorization': request.headers.get('Authorization'),
                    'X-User-ID': str(request.user.id),
                },
                timeout=60.0  # خلاصه‌سازی ممکن است زمان‌بر باشد
            )
            
            if response.status_code == 200:
                return Response(response.json())
            else:
                return Response(
                    {'error': 'خطا در خلاصه‌سازی'},
                    status=response.status_code
                )
        except Exception as e:
            logger.error(f"Memory summarize error: {e}")
            return Response(
                {'error': 'خطای داخلی سرور'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class MemoryContextView(APIView):
    """دریافت context حافظه (برای دیباگ)"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """دریافت context متنی حافظه"""
        try:
            response = httpx.get(
                f"{MEMORY_API_BASE}/context/text",
                headers={
                    'Authorization': request.headers.get('Authorization'),
                    'X-User-ID': str(request.user.id),
                },
                timeout=30.0
            )
            
            if response.status_code == 200:
                return Response(response.json())
            else:
                return Response(
                    {'error': 'خطا در دریافت context'},
                    status=response.status_code
                )
        except Exception as e:
            logger.error(f"Memory context error: {e}")
            return Response(
                {'error': 'خطای داخلی سرور'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
