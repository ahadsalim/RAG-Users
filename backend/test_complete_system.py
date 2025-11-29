#!/usr/bin/env python3
"""
تست کامل سیستم: MinIO + RAG Core
"""
import os
import sys
import time
import json
from datetime import datetime
from io import BytesIO

# Add Django to path
sys.path.insert(0, '/srv/backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')

import django
django.setup()

from django.conf import settings
from core.storage import MinIOService
import asyncio
import httpx

# رنگ‌ها برای خروجی
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'

def print_header(text):
    print(f"\n{'='*80}")
    print(f"{BLUE}{text}{RESET}")
    print(f"{'='*80}\n")

def print_success(text):
    print(f"{GREEN}✅ {text}{RESET}")

def print_error(text):
    print(f"{RED}❌ {text}{RESET}")

def print_info(text):
    print(f"{YELLOW}ℹ️  {text}{RESET}")

def print_time(start_time):
    elapsed = time.time() - start_time
    print(f"{BLUE}⏱️  زمان: {elapsed:.2f} ثانیه{RESET}")


# ============================================================================
# تست 1: ذخیره فایل در MinIO
# ============================================================================
def test_minio_upload():
    print_header("تست 1: ذخیره فایل در MinIO")
    
    try:
        # ایجاد سرویس MinIO
        print_info("ایجاد اتصال به MinIO...")
        minio_service = MinIOService()
        print_success(f"اتصال به MinIO برقرار شد: {settings.MINIO_ENDPOINT}")
        
        # ایجاد فایل تستی 1 (PDF)
        print_info("\nایجاد فایل تستی 1 (PDF)...")
        test_file_1 = BytesIO(b"%PDF-1.4\n%Test PDF file for RAG system\nThis is a test document.")
        test_file_1.name = "test_document.pdf"
        
        start_time = time.time()
        result_1 = minio_service.upload_file(
            file=test_file_1,
            filename="test_document.pdf",
            content_type="application/pdf",
            user_id="test_user_123"
        )
        print_time(start_time)
        
        print_success(f"فایل 1 آپلود شد:")
        print(f"   📦 Bucket: {result_1['bucket_name']}")
        print(f"   🔑 Object Key: {result_1['object_key']}")
        print(f"   📏 Size: {result_1['size_bytes']} bytes")
        print(f"   🔗 URL: {result_1['minio_url']}")
        
        # ایجاد فایل تستی 2 (Text)
        print_info("\nایجاد فایل تستی 2 (Text)...")
        test_file_2 = BytesIO("این یک فایل متنی تستی است.\nبرای آزمایش سیستم RAG.".encode('utf-8'))
        test_file_2.name = "test_text.txt"
        
        start_time = time.time()
        result_2 = minio_service.upload_file(
            file=test_file_2,
            filename="test_text.txt",
            content_type="text/plain",
            user_id="test_user_123"
        )
        print_time(start_time)
        
        print_success(f"فایل 2 آپلود شد:")
        print(f"   📦 Bucket: {result_2['bucket_name']}")
        print(f"   🔑 Object Key: {result_2['object_key']}")
        print(f"   📏 Size: {result_2['size_bytes']} bytes")
        print(f"   🔗 URL: {result_2['minio_url']}")
        
        return result_1, result_2
        
    except Exception as e:
        print_error(f"خطا در آپلود به MinIO: {e}")
        import traceback
        traceback.print_exc()
        return None, None


# ============================================================================
# تست 2: ارسال سوال متنی به RAG Core
# ============================================================================
async def test_text_query():
    print_header("تست 2: ارسال سوال متنی به RAG Core")
    
    try:
        rag_core_url = settings.RAG_CORE_URL
        print_info(f"URL سیستم مرکزی: {rag_core_url}")
        
        # خواندن API Key از .env
        api_key = None
        env_file = '/srv/deployment/.env'
        if os.path.exists(env_file):
            with open(env_file, 'r') as f:
                for line in f:
                    if line.startswith('CORE_API_KEY='):
                        api_key = line.split('=', 1)[1].strip()
                        break
        
        if not api_key:
            print_error("CORE_API_KEY یافت نشد در /srv/deployment/.env")
            return None
        
        print_success(f"API Key یافت شد: {api_key[:20]}...")
        
        # آماده‌سازی payload
        payload = {
            "query": "قانون مدنی ایران در مورد مالکیت چه می‌گوید؟",
            "language": "fa",
            "max_results": 5,
            "use_cache": True,
            "use_reranking": True
        }
        
        print_info(f"\nارسال query: {payload['query']}")
        
        start_time = time.time()
        
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                f"{rag_core_url}/api/v1/query/",
                json=payload,
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                }
            )
        
        elapsed = time.time() - start_time
        
        print_time(start_time)
        print_info(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print_success("پاسخ دریافت شد!")
            print(f"\n📝 پاسخ:")
            print(f"{data.get('answer', '')[:500]}...")
            print(f"\n📊 آمار:")
            print(f"   🔢 Tokens: {data.get('tokens_used', 0)}")
            print(f"   ⏱️  Processing Time: {data.get('processing_time_ms', 0)}ms")
            print(f"   💾 Cached: {data.get('cached', False)}")
            print(f"   📚 Sources: {len(data.get('sources', []))}")
            print(f"   🆔 Conversation ID: {data.get('conversation_id', 'N/A')}")
            print(f"   🆔 Message ID: {data.get('message_id', 'N/A')}")
            
            return data
        else:
            print_error(f"خطا: {response.status_code}")
            print(f"Response: {response.text[:500]}")
            return None
            
    except httpx.TimeoutException:
        print_error("Timeout: سرور بیش از 120 ثانیه پاسخ نداد")
        return None
    except Exception as e:
        print_error(f"خطا: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return None


# ============================================================================
# تست 3: ارسال سوال با 2 فایل به RAG Core
# ============================================================================
async def test_query_with_files(file1_info, file2_info):
    print_header("تست 3: ارسال سوال با 2 فایل به RAG Core")
    
    if not file1_info or not file2_info:
        print_error("فایل‌ها در MinIO آپلود نشده‌اند")
        return None
    
    try:
        rag_core_url = settings.RAG_CORE_URL
        
        # خواندن API Key
        api_key = None
        env_file = '/srv/deployment/.env'
        if os.path.exists(env_file):
            with open(env_file, 'r') as f:
                for line in f:
                    if line.startswith('CORE_API_KEY='):
                        api_key = line.split('=', 1)[1].strip()
                        break
        
        if not api_key:
            print_error("CORE_API_KEY یافت نشد")
            return None
        
        # آماده‌سازی file_attachments
        file_attachments = [
            {
                "filename": "test_document.pdf",
                "minio_url": file1_info['object_key'],
                "file_type": "application/pdf",
                "size_bytes": file1_info['size_bytes']
            },
            {
                "filename": "test_text.txt",
                "minio_url": file2_info['object_key'],
                "file_type": "text/plain",
                "size_bytes": file2_info['size_bytes']
            }
        ]
        
        payload = {
            "query": "این فایل‌ها چه محتوایی دارند؟ لطفاً خلاصه کن.",
            "language": "fa",
            "max_results": 5,
            "use_cache": False,  # برای اطمینان از پردازش فایل‌ها
            "use_reranking": True,
            "file_attachments": file_attachments
        }
        
        print_info(f"ارسال query: {payload['query']}")
        print_info(f"تعداد فایل‌ها: {len(file_attachments)}")
        print(f"   📄 فایل 1: {file_attachments[0]['filename']} ({file_attachments[0]['size_bytes']} bytes)")
        print(f"   📄 فایل 2: {file_attachments[1]['filename']} ({file_attachments[1]['size_bytes']} bytes)")
        
        start_time = time.time()
        
        async with httpx.AsyncClient(timeout=180.0) as client:  # 3 minutes برای پردازش فایل
            response = await client.post(
                f"{rag_core_url}/api/v1/query/",
                json=payload,
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                }
            )
        
        elapsed = time.time() - start_time
        
        print_time(start_time)
        print_info(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print_success("پاسخ دریافت شد!")
            print(f"\n📝 پاسخ:")
            print(f"{data.get('answer', '')[:500]}...")
            print(f"\n📊 آمار:")
            print(f"   🔢 Tokens: {data.get('tokens_used', 0)}")
            print(f"   ⏱️  Processing Time: {data.get('processing_time_ms', 0)}ms")
            print(f"   💾 Cached: {data.get('cached', False)}")
            print(f"   📚 Sources: {len(data.get('sources', []))}")
            print(f"   📁 Files Processed: {data.get('files_processed', 0)}")
            print(f"   🆔 Conversation ID: {data.get('conversation_id', 'N/A')}")
            print(f"   🆔 Message ID: {data.get('message_id', 'N/A')}")
            
            return data
        else:
            print_error(f"خطا: {response.status_code}")
            print(f"Response: {response.text[:500]}")
            return None
            
    except httpx.TimeoutException:
        print_error("Timeout: سرور بیش از 180 ثانیه پاسخ نداد")
        return None
    except Exception as e:
        print_error(f"خطا: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return None


# ============================================================================
# اجرای تست‌ها
# ============================================================================
async def main():
    print_header("🚀 شروع تست کامل سیستم")
    print(f"⏰ زمان شروع: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    total_start = time.time()
    
    # تست 1: MinIO
    file1, file2 = test_minio_upload()
    
    if file1 and file2:
        print_success("\n✅ تست 1 موفق: فایل‌ها در MinIO ذخیره شدند")
    else:
        print_error("\n❌ تست 1 ناموفق: مشکل در آپلود به MinIO")
        return
    
    # تست 2: Query متنی
    text_result = await test_text_query()
    
    if text_result:
        print_success("\n✅ تست 2 موفق: سوال متنی پاسخ داده شد")
    else:
        print_error("\n❌ تست 2 ناموفق: مشکل در ارسال سوال متنی")
    
    # تست 3: Query با فایل
    file_result = await test_query_with_files(file1, file2)
    
    if file_result:
        print_success("\n✅ تست 3 موفق: سوال با فایل پاسخ داده شد")
    else:
        print_error("\n❌ تست 3 ناموفق: مشکل در ارسال سوال با فایل")
    
    # خلاصه نهایی
    total_time = time.time() - total_start
    
    print_header("📊 خلاصه نتایج")
    print(f"⏱️  زمان کل: {total_time:.2f} ثانیه")
    print(f"\n{'='*80}")
    print(f"{GREEN}✅ تست 1 (MinIO Upload):{RESET} {'موفق' if file1 and file2 else 'ناموفق'}")
    print(f"{GREEN}✅ تست 2 (Text Query):{RESET} {'موفق' if text_result else 'ناموفق'}")
    print(f"{GREEN}✅ تست 3 (Query + Files):{RESET} {'موفق' if file_result else 'ناموفق'}")
    print(f"{'='*80}\n")
    
    if file1 and file2 and text_result and file_result:
        print(f"{GREEN}🎉 همه تست‌ها موفق بودند!{RESET}")
    else:
        print(f"{RED}⚠️  برخی تست‌ها ناموفق بودند{RESET}")


if __name__ == "__main__":
    asyncio.run(main())
