#!/usr/bin/env python3
"""
تست RAG Core بدون MinIO
"""
import asyncio
import httpx
import time
from datetime import datetime

# رنگ‌ها
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


# خواندن API Key
def get_api_key():
    import os
    env_file = '/srv/deployment/.env'
    if os.path.exists(env_file):
        with open(env_file, 'r') as f:
            for line in f:
                if line.startswith('CORE_API_KEY='):
                    return line.split('=', 1)[1].strip()
    return None


async def test_rag_core_text_query():
    """تست ارسال سوال متنی به RAG Core"""
    print_header("تست: ارسال سوال متنی به RAG Core")
    
    # تنظیمات
    RAG_CORE_URL = "https://core.tejarat.chat"
    API_KEY = get_api_key()
    
    if not API_KEY:
        print_error("CORE_API_KEY یافت نشد در /srv/deployment/.env")
        return None
    
    print_success(f"API Key یافت شد: {API_KEY[:20]}...")
    print_info(f"URL: {RAG_CORE_URL}")
    
    # Payload
    payload = {
        "query": "قانون مدنی ایران در مورد مالکیت چه می‌گوید؟",
        "language": "fa",
        "max_results": 5,
        "use_cache": True,
        "use_reranking": True
    }
    
    print_info(f"\n📤 ارسال query: {payload['query']}")
    
    try:
        start_time = time.time()
        
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                f"{RAG_CORE_URL}/api/v1/query/",
                json=payload,
                headers={
                    "Authorization": f"Bearer {API_KEY}",
                    "Content-Type": "application/json"
                }
            )
        
        elapsed = time.time() - start_time
        
        print_time(start_time)
        print_info(f"📊 Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print_success("✅ پاسخ دریافت شد!")
            
            print(f"\n{'='*80}")
            print(f"{GREEN}📝 پاسخ:{RESET}")
            print(f"{'='*80}")
            answer = data.get('answer', '')
            if len(answer) > 800:
                print(f"{answer[:800]}...")
            else:
                print(answer)
            
            print(f"\n{'='*80}")
            print(f"{BLUE}📊 آمار:{RESET}")
            print(f"{'='*80}")
            print(f"   🔢 Tokens Used: {data.get('tokens_used', 0)}")
            print(f"   ⏱️  Processing Time: {data.get('processing_time_ms', 0)}ms")
            print(f"   💾 Cached: {data.get('cached', False)}")
            print(f"   📚 Sources Count: {len(data.get('sources', []))}")
            print(f"   🆔 Conversation ID: {data.get('conversation_id', 'N/A')}")
            print(f"   🆔 Message ID: {data.get('message_id', 'N/A')}")
            print(f"   📁 Files Processed: {data.get('files_processed', 0)}")
            
            if data.get('sources'):
                print(f"\n   📚 Sources:")
                for i, source in enumerate(data.get('sources', [])[:3], 1):
                    print(f"      {i}. {source}")
            
            return data
            
        else:
            print_error(f"❌ خطا: {response.status_code}")
            print(f"\n📄 Response:")
            print(response.text[:1000])
            return None
            
    except httpx.TimeoutException:
        print_error("⏱️  Timeout: سرور بیش از 120 ثانیه پاسخ نداد")
        return None
    except httpx.ConnectError as e:
        print_error(f"🔌 خطای اتصال: {e}")
        return None
    except Exception as e:
        print_error(f"❌ خطا: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return None


async def test_rag_core_with_fake_files():
    """تست ارسال سوال با فایل‌های فرضی"""
    print_header("تست: ارسال سوال با فایل‌های فرضی")
    
    RAG_CORE_URL = "https://core.tejarat.chat"
    API_KEY = get_api_key()
    
    if not API_KEY:
        print_error("CORE_API_KEY یافت نشد")
        return None
    
    # فایل‌های فرضی (فقط برای تست ساختار API)
    file_attachments = [
        {
            "filename": "test_document.pdf",
            "minio_url": "temp_uploads/test_user/test_doc.pdf",
            "file_type": "application/pdf",
            "size_bytes": 1024
        },
        {
            "filename": "test_text.txt",
            "minio_url": "temp_uploads/test_user/test_text.txt",
            "file_type": "text/plain",
            "size_bytes": 512
        }
    ]
    
    payload = {
        "query": "این فایل‌ها چه محتوایی دارند؟",
        "language": "fa",
        "max_results": 5,
        "use_cache": False,
        "use_reranking": True,
        "file_attachments": file_attachments
    }
    
    print_info(f"📤 ارسال query: {payload['query']}")
    print_info(f"📁 تعداد فایل‌ها: {len(file_attachments)}")
    print_info("⚠️  توجه: فایل‌ها فرضی هستند و در MinIO وجود ندارند")
    
    try:
        start_time = time.time()
        
        async with httpx.AsyncClient(timeout=180.0) as client:
            response = await client.post(
                f"{RAG_CORE_URL}/api/v1/query/",
                json=payload,
                headers={
                    "Authorization": f"Bearer {API_KEY}",
                    "Content-Type": "application/json"
                }
            )
        
        elapsed = time.time() - start_time
        
        print_time(start_time)
        print_info(f"📊 Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print_success("✅ پاسخ دریافت شد!")
            print(f"\n📝 پاسخ: {data.get('answer', '')[:500]}...")
            print(f"\n📊 آمار:")
            print(f"   📁 Files Processed: {data.get('files_processed', 0)}")
            print(f"   🔢 Tokens: {data.get('tokens_used', 0)}")
            print(f"   ⏱️  Time: {data.get('processing_time_ms', 0)}ms")
            return data
        else:
            print_error(f"❌ خطا: {response.status_code}")
            print(f"📄 Response: {response.text[:500]}")
            return None
            
    except Exception as e:
        print_error(f"❌ خطا: {type(e).__name__}: {e}")
        return None


async def main():
    print_header("🚀 تست سیستم RAG Core")
    print(f"⏰ زمان: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    total_start = time.time()
    
    # تست 1: Query متنی
    result1 = await test_rag_core_text_query()
    
    # تست 2: Query با فایل (فرضی)
    print("\n" + "="*80)
    result2 = await test_rag_core_with_fake_files()
    
    # خلاصه
    total_time = time.time() - total_start
    
    print_header("📊 خلاصه نتایج")
    print(f"⏱️  زمان کل: {total_time:.2f} ثانیه\n")
    print(f"{GREEN}✅ تست 1 (Text Query):{RESET} {'موفق' if result1 else 'ناموفق'}")
    print(f"{GREEN}✅ تست 2 (Query + Files):{RESET} {'موفق' if result2 else 'ناموفق'}")
    print(f"\n{'='*80}\n")
    
    if result1 and result2:
        print(f"{GREEN}🎉 همه تست‌ها موفق بودند!{RESET}")
    elif result1:
        print(f"{YELLOW}⚠️  فقط تست متنی موفق بود{RESET}")
    else:
        print(f"{RED}❌ تست‌ها ناموفق بودند{RESET}")


if __name__ == "__main__":
    asyncio.run(main())
