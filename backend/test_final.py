#!/usr/bin/env python3
"""تست نهایی کامل سیستم"""
import os
import sys
import asyncio
import httpx
import time

sys.path.insert(0, '/app')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')

import django
django.setup()

from django.conf import settings
from io import BytesIO
from core.storage import MinIOService

print("="*80)
print("🚀 تست کامل سیستم RAG Users")
print("="*80)

# تست 1: S3/MinIO
print("\n" + "="*80)
print("تست 1: آپلود فایل به S3/MinIO")
print("="*80)

try:
    start = time.time()
    
    minio = MinIOService()
    print(f"✅ اتصال به S3: {settings.S3_ENDPOINT_URL}")
    print(f"   Bucket: {settings.S3_TEMP_BUCKET}")
    
    # آپلود فایل تستی
    test_content = b"Test file for RAG system - " + os.urandom(100)
    
    result = minio.upload_file(
        file_content=test_content,
        filename="test_upload.txt",
        user_id="test_user_123",
        content_type="text/plain"
    )
    
    elapsed1 = time.time() - start
    
    print(f"✅ فایل آپلود شد")
    print(f"   Object Key: {result['object_key']}")
    print(f"   Size: {result['size_bytes']} bytes")
    print(f"   ⏱️  زمان: {elapsed1:.2f} ثانیه")
    
    test1_success = True
except Exception as e:
    print(f"❌ خطا: {type(e).__name__}: {e}")
    test1_success = False
    elapsed1 = 0

# تست 2: RAG Core
print("\n" + "="*80)
print("تست 2: ارسال سوال به RAG Core")
print("="*80)

async def test_rag():
    try:
        start = time.time()
        
        url = settings.RAG_CORE_URL
        api_key = settings.RAG_CORE_API_KEY
        
        if not api_key:
            print("❌ RAG_CORE_API_KEY تنظیم نشده")
            return False, 0
        
        print(f"✅ URL: {url}")
        print(f"   API Key: {api_key[:20]}...")
        
        payload = {
            'query': 'قانون مدنی ایران در مورد مالکیت چه می‌گوید؟',
            'language': 'fa',
            'max_results': 5,
            'use_cache': True,
            'use_reranking': True
        }
        
        print(f"\n📤 ارسال query: {payload['query']}")
        print("⏳ لطفاً صبر کنید...")
        
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                f'{url}/api/v1/query/',
                json=payload,
                headers={
                    'Authorization': f'Bearer {api_key}',
                    'Content-Type': 'application/json'
                }
            )
        
        elapsed = time.time() - start
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ پاسخ دریافت شد")
            print(f"   📝 پاسخ: {data.get('answer', '')[:150]}...")
            print(f"   🔢 Tokens: {data.get('tokens_used', 0)}")
            print(f"   💾 Cached: {data.get('cached', False)}")
            print(f"   📚 Sources: {len(data.get('sources', []))}")
            print(f"   ⏱️  زمان: {elapsed:.2f} ثانیه")
            return True, elapsed
        else:
            print(f"❌ خطا: {response.status_code}")
            print(f"   Response: {response.text[:200]}")
            return False, elapsed
    
    except httpx.TimeoutException:
        elapsed = time.time() - start
        print(f"❌ Timeout بعد از {elapsed:.2f} ثانیه")
        return False, elapsed
    except Exception as e:
        print(f"❌ خطا: {type(e).__name__}: {e}")
        return False, 0

test2_success, elapsed2 = asyncio.run(test_rag())

# خلاصه نهایی
print("\n" + "="*80)
print("📊 خلاصه نتایج")
print("="*80)

total_time = elapsed1 + elapsed2

print(f"\n{'تست':<30} {'وضعیت':<15} {'زمان':<15}")
print("-" * 60)
print(f"{'1. آپلود فایل به S3/MinIO':<30} {'✅ موفق' if test1_success else '❌ ناموفق':<15} {f'{elapsed1:.2f}s':<15}")
print(f"{'2. ارسال سوال به RAG Core':<30} {'✅ موفق' if test2_success else '❌ ناموفق':<15} {f'{elapsed2:.2f}s':<15}")
print("-" * 60)
print(f"{'مجموع':<30} {'':<15} {f'{total_time:.2f}s':<15}")

print("\n" + "="*80)
if test1_success and test2_success:
    print("🎉 همه تست‌ها موفق بودند!")
elif test1_success or test2_success:
    print("⚠️  برخی تست‌ها موفق بودند")
else:
    print("❌ همه تست‌ها ناموفق بودند")
print("="*80)

sys.exit(0 if (test1_success and test2_success) else 1)
