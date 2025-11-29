"""
اسکریپت دیباگ برای بررسی اتصال به RAG Core
"""
import os
import sys
import django
import asyncio
import httpx

# Setup Django
sys.path.insert(0, '/srv/backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.conf import settings
from chat.core_service import core_service

async def test_rag_core_connection():
    """تست اتصال به RAG Core"""
    
    print("=" * 80)
    print("🔍 تست اتصال به RAG Core")
    print("=" * 80)
    
    # بررسی تنظیمات
    rag_core_url = getattr(settings, 'CORE_API_URL', 'https://core.tejarat.chat')
    print(f"\n📡 URL سرور RAG Core: {rag_core_url}")
    print(f"⏱️  Timeout: {core_service.timeout} seconds")
    
    # تست اتصال ساده
    print("\n1️⃣ تست اتصال ساده...")
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"{rag_core_url}/health", timeout=10.0)
            print(f"   ✅ سرور در دسترس است (Status: {response.status_code})")
    except httpx.ConnectError as e:
        print(f"   ❌ خطا در اتصال: {e}")
        print(f"   💡 بررسی کنید که RAG Core روی {rag_core_url} در حال اجرا است")
        return
    except httpx.TimeoutException:
        print(f"   ⏱️  Timeout: سرور پاسخ نداد")
        return
    except Exception as e:
        print(f"   ❌ خطای غیرمنتظره: {e}")
        return
    
    # تست query ساده
    print("\n2️⃣ تست ارسال query ساده...")
    try:
        # نیاز به JWT token واقعی دارید
        # این فقط برای تست اتصال است
        print("   ℹ️  برای تست کامل، نیاز به JWT token معتبر دارید")
        print("   ℹ️  می‌توانید از Postman یا curl استفاده کنید:")
        print(f"""
   curl -X POST "{rag_core_url}/api/v1/query/" \\
     -H "Authorization: Bearer YOUR_TOKEN" \\
     -H "Content-Type: application/json" \\
     -d '{{
       "query": "تست",
       "language": "fa",
       "max_results": 5
     }}'
        """)
    except Exception as e:
        print(f"   ❌ خطا: {e}")
    
    print("\n" + "=" * 80)
    print("✅ تست اتصال به پایان رسید")
    print("=" * 80)

if __name__ == '__main__':
    asyncio.run(test_rag_core_connection())
