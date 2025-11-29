#!/usr/bin/env python3
"""
تست اتصال به RAG Core و ارسال query واقعی
"""
import asyncio
import httpx
import json
from datetime import datetime

# تنظیمات
RAG_CORE_URL = "http://rag-core:7001"  # یا https://core.tejarat.chat
TEST_TOKEN = "test_token_here"  # باید یک JWT token واقعی باشد

async def test_connection():
    """تست اتصال به RAG Core"""
    
    print("=" * 80)
    print(f"🔍 تست اتصال به RAG Core")
    print(f"📡 URL: {RAG_CORE_URL}")
    print(f"⏰ زمان: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    
    # 1. تست Health Check
    print("\n1️⃣ تست Health Check...")
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"{RAG_CORE_URL}/health")
            print(f"   ✅ Status Code: {response.status_code}")
            print(f"   📄 Response: {response.text[:200]}")
    except httpx.ConnectError as e:
        print(f"   ❌ خطای اتصال: {e}")
        print(f"   💡 آیا RAG Core روی {RAG_CORE_URL} در حال اجرا است؟")
        return False
    except Exception as e:
        print(f"   ❌ خطا: {type(e).__name__}: {e}")
        return False
    
    # 2. تست API Endpoint بدون Token
    print("\n2️⃣ تست API Endpoint (بدون token)...")
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                f"{RAG_CORE_URL}/api/v1/query/",
                json={
                    "query": "تست",
                    "language": "fa",
                    "max_results": 5
                },
                headers={"Content-Type": "application/json"}
            )
            print(f"   📊 Status Code: {response.status_code}")
            print(f"   📄 Response: {response.text[:500]}")
            
            if response.status_code == 401:
                print(f"   ℹ️  انتظار می‌رفت: نیاز به JWT token دارد")
            elif response.status_code == 403:
                print(f"   ℹ️  انتظار می‌رفت: دسترسی غیرمجاز")
                
    except Exception as e:
        print(f"   ❌ خطا: {type(e).__name__}: {e}")
    
    # 3. تست با Token (اگر موجود باشد)
    print("\n3️⃣ تست با JWT Token...")
    if TEST_TOKEN == "test_token_here":
        print("   ⚠️  Token تنظیم نشده است")
        print("   💡 برای تست کامل، یک JWT token واقعی در فایل وارد کنید")
    else:
        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                payload = {
                    "query": "قانون مدنی چیست؟",
                    "language": "fa",
                    "max_results": 5,
                    "use_cache": True,
                    "use_reranking": True
                }
                
                print(f"   📤 ارسال query: {payload['query']}")
                
                response = await client.post(
                    f"{RAG_CORE_URL}/api/v1/query/",
                    json=payload,
                    headers={
                        "Authorization": f"Bearer {TEST_TOKEN}",
                        "Content-Type": "application/json"
                    }
                )
                
                print(f"   📊 Status Code: {response.status_code}")
                
                if response.status_code == 200:
                    data = response.json()
                    print(f"   ✅ پاسخ دریافت شد!")
                    print(f"   📝 Answer: {data.get('answer', '')[:200]}...")
                    print(f"   🔢 Tokens: {data.get('tokens_used', 0)}")
                    print(f"   ⏱️  Time: {data.get('processing_time_ms', 0)}ms")
                else:
                    print(f"   ❌ خطا: {response.text[:500]}")
                    
        except httpx.TimeoutException:
            print(f"   ⏱️  Timeout: سرور بیش از 120 ثانیه پاسخ نداد")
        except Exception as e:
            print(f"   ❌ خطا: {type(e).__name__}: {e}")
    
    # 4. تست با فایل
    print("\n4️⃣ تست با فایل ضمیمه...")
    if TEST_TOKEN == "test_token_here":
        print("   ⚠️  نیاز به Token برای تست فایل")
    else:
        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                payload = {
                    "query": "این فایل چه می‌گوید؟",
                    "language": "fa",
                    "max_results": 5,
                    "file_attachments": [
                        {
                            "filename": "test.pdf",
                            "minio_url": "temp_uploads/test/test.pdf",
                            "file_type": "application/pdf"
                        }
                    ]
                }
                
                print(f"   📤 ارسال query با فایل")
                
                response = await client.post(
                    f"{RAG_CORE_URL}/api/v1/query/",
                    json=payload,
                    headers={
                        "Authorization": f"Bearer {TEST_TOKEN}",
                        "Content-Type": "application/json"
                    }
                )
                
                print(f"   📊 Status Code: {response.status_code}")
                print(f"   📄 Response: {response.text[:500]}")
                
        except Exception as e:
            print(f"   ❌ خطا: {type(e).__name__}: {e}")
    
    print("\n" + "=" * 80)
    print("✅ تست به پایان رسید")
    print("=" * 80)
    
    return True

if __name__ == "__main__":
    print("\n💡 نکته: برای تست کامل، یک JWT token واقعی در متغیر TEST_TOKEN وارد کنید\n")
    asyncio.run(test_connection())
