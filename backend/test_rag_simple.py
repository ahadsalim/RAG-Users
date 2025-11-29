#!/usr/bin/env python3
"""تست ساده RAG Core"""
import os
import sys
import asyncio
import httpx
import time

# خواندن API Key
def get_config():
    env_file = '/srv/deployment/.env'
    config = {}
    if os.path.exists(env_file):
        with open(env_file, 'r') as f:
            for line in f:
                if '=' in line and not line.startswith('#'):
                    key, value = line.strip().split('=', 1)
                    config[key] = value
    return config

async def test_rag():
    print("="*60)
    print("🧪 تست اتصال به RAG Core")
    print("="*60)
    
    config = get_config()
    API_KEY = config.get('RAG_CORE_API_KEY', '').strip()
    URL = config.get('RAG_CORE_BASE_URL', config.get('RAG_CORE_URL', 'https://core.tejarat.chat')).strip()
    
    if not API_KEY:
        print("❌ RAG_CORE_API_KEY یافت نشد در .env")
        return False
    
    print(f"\n📍 URL: {URL}")
    print(f"🔑 API Key: {API_KEY[:20]}...")
    
    payload = {
        'query': 'قانون مدنی ایران در مورد مالکیت چه می‌گوید؟',
        'language': 'fa',
        'max_results': 5,
        'use_cache': True,
        'use_reranking': True
    }
    
    print(f"\n📤 ارسال query: {payload['query']}")
    print("⏳ لطفاً صبر کنید...")
    
    start = time.time()
    
    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                f'{URL}/api/v1/query/',
                json=payload,
                headers={
                    'Authorization': f'Bearer {API_KEY}',
                    'Content-Type': 'application/json'
                }
            )
        
        elapsed = time.time() - start
        
        print(f"\n⏱️  زمان پاسخ: {elapsed:.2f} ثانیه")
        print(f"📊 Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("\n" + "="*60)
            print("✅ پاسخ دریافت شد!")
            print("="*60)
            
            answer = data.get('answer', '')
            if len(answer) > 300:
                print(f"\n📝 پاسخ:\n{answer[:300]}...")
            else:
                print(f"\n📝 پاسخ:\n{answer}")
            
            print(f"\n📊 آمار:")
            print(f"   🔢 Tokens: {data.get('tokens_used', 0)}")
            print(f"   ⏱️  Processing: {data.get('processing_time_ms', 0)}ms")
            print(f"   💾 Cached: {data.get('cached', False)}")
            print(f"   📚 Sources: {len(data.get('sources', []))}")
            print(f"   🆔 Conversation: {data.get('conversation_id', 'N/A')}")
            
            return True
        else:
            print(f"\n❌ خطا: {response.status_code}")
            print(f"📄 Response: {response.text[:500]}")
            return False
    
    except httpx.TimeoutException:
        elapsed = time.time() - start
        print(f"\n❌ Timeout بعد از {elapsed:.2f} ثانیه")
        return False
    except Exception as e:
        print(f"\n❌ خطا: {type(e).__name__}: {e}")
        return False

if __name__ == "__main__":
    result = asyncio.run(test_rag())
    sys.exit(0 if result else 1)
