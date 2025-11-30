#!/usr/bin/env python3
"""
تست هر دو حالت RAG Core API:
1. حالت عادی: /api/v1/query/
2. حالت streaming: /api/v1/query/stream/
"""
import os
import sys
import django
import asyncio
import httpx
import json
from datetime import datetime

# Setup Django
sys.path.insert(0, '/app')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.contrib.auth import get_user_model
from chat.utils import generate_jwt_token

User = get_user_model()

# رنگ‌ها برای خروجی
GREEN = '\033[92m'
BLUE = '\033[94m'
YELLOW = '\033[93m'
RED = '\033[91m'
RESET = '\033[0m'


async def test_normal_mode():
    """تست حالت عادی (non-streaming)"""
    print(f"\n{BLUE}{'='*60}{RESET}")
    print(f"{BLUE}تست 1: حالت عادی (Non-Streaming){RESET}")
    print(f"{BLUE}{'='*60}{RESET}\n")
    
    # دریافت کاربر و تولید token
    user = User.objects.first()
    if not user:
        print(f"{RED}❌ کاربری یافت نشد!{RESET}")
        return
    
    token = generate_jwt_token(user)
    
    url = "https://core.tejarat.chat/api/v1/query/"
    
    payload = {
        "query": "سلام، چطوری؟",
        "language": "fa",
    }
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }
    
    print(f"{YELLOW}📤 ارسال درخواست به:{RESET} {url}")
    print(f"{YELLOW}📝 Query:{RESET} {payload['query']}")
    
    start_time = datetime.now()
    
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(url, json=payload, headers=headers)
            
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            print(f"\n{GREEN}✅ Status Code:{RESET} {response.status_code}")
            print(f"{GREEN}⏱️  زمان پاسخ:{RESET} {duration:.2f} ثانیه")
            
            if response.status_code == 200:
                data = response.json()
                print(f"\n{GREEN}📥 پاسخ دریافت شده:{RESET}")
                print(f"{GREEN}{'─'*60}{RESET}")
                
                # نمایش answer
                if 'answer' in data:
                    answer = data['answer']
                    print(f"{BLUE}پاسخ:{RESET} {answer[:200]}...")
                    print(f"{BLUE}طول پاسخ:{RESET} {len(answer)} کاراکتر")
                
                # نمایش سایر فیلدها
                print(f"\n{YELLOW}سایر اطلاعات:{RESET}")
                for key in ['conversation_id', 'tokens_used', 'processing_time_ms', 'context_used']:
                    if key in data:
                        print(f"  • {key}: {data[key]}")
                
                print(f"{GREEN}{'─'*60}{RESET}")
            else:
                print(f"{RED}❌ خطا:{RESET} {response.text}")
                
    except httpx.TimeoutException:
        print(f"{RED}❌ Timeout: پاسخ در 60 ثانیه دریافت نشد{RESET}")
    except Exception as e:
        print(f"{RED}❌ خطا: {e}{RESET}")


async def test_streaming_mode():
    """تست حالت streaming"""
    print(f"\n{BLUE}{'='*60}{RESET}")
    print(f"{BLUE}تست 2: حالت Streaming{RESET}")
    print(f"{BLUE}{'='*60}{RESET}\n")
    
    # دریافت کاربر و تولید token
    user = User.objects.first()
    if not user:
        print(f"{RED}❌ کاربری یافت نشد!{RESET}")
        return
    
    token = generate_jwt_token(user)
    
    url = "https://core.tejarat.chat/api/v1/query/stream/"
    
    payload = {
        "query": "سلام، چطوری؟",
        "language": "fa",
    }
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }
    
    print(f"{YELLOW}📤 ارسال درخواست به:{RESET} {url}")
    print(f"{YELLOW}📝 Query:{RESET} {payload['query']}")
    print(f"\n{GREEN}📥 دریافت پاسخ (streaming):{RESET}")
    print(f"{GREEN}{'─'*60}{RESET}")
    
    start_time = datetime.now()
    chunk_count = 0
    total_content = ""
    
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            async with client.stream('POST', url, json=payload, headers=headers) as response:
                
                if response.status_code != 200:
                    print(f"{RED}❌ Status Code: {response.status_code}{RESET}")
                    text = await response.aread()
                    print(f"{RED}خطا: {text.decode()}{RESET}")
                    return
                
                print(f"{BLUE}🔄 شروع دریافت chunks...{RESET}\n")
                
                # خواندن chunks
                async for chunk in response.aiter_text():
                    if chunk.strip():
                        chunk_count += 1
                        
                        # نمایش chunk
                        print(f"{GREEN}[Chunk {chunk_count}]{RESET} ", end='', flush=True)
                        
                        # تلاش برای parse کردن به عنوان JSON
                        try:
                            # اگر SSE باشد
                            if chunk.startswith('data: '):
                                json_str = chunk[6:].strip()
                                if json_str:
                                    data = json.loads(json_str)
                                    if 'content' in data:
                                        content = data['content']
                                        print(content, end='', flush=True)
                                        total_content += content
                                    elif 'answer' in data:
                                        content = data['answer']
                                        print(content, end='', flush=True)
                                        total_content += content
                            else:
                                # اگر plain text باشد
                                print(chunk, end='', flush=True)
                                total_content += chunk
                        except json.JSONDecodeError:
                            # اگر JSON نبود، به عنوان text نمایش بده
                            print(chunk, end='', flush=True)
                            total_content += chunk
                
                end_time = datetime.now()
                duration = (end_time - start_time).total_seconds()
                
                print(f"\n\n{GREEN}{'─'*60}{RESET}")
                print(f"{GREEN}✅ دریافت کامل شد{RESET}")
                print(f"{GREEN}📊 تعداد chunks:{RESET} {chunk_count}")
                print(f"{GREEN}📏 طول کل:{RESET} {len(total_content)} کاراکتر")
                print(f"{GREEN}⏱️  زمان کل:{RESET} {duration:.2f} ثانیه")
                print(f"{GREEN}{'─'*60}{RESET}")
                
    except httpx.TimeoutException:
        print(f"\n{RED}❌ Timeout: پاسخ در 60 ثانیه دریافت نشد{RESET}")
    except Exception as e:
        print(f"\n{RED}❌ خطا: {e}{RESET}")
        import traceback
        traceback.print_exc()


async def main():
    """اجرای هر دو تست"""
    print(f"\n{YELLOW}{'='*60}{RESET}")
    print(f"{YELLOW}🧪 تست RAG Core API - هر دو حالت{RESET}")
    print(f"{YELLOW}{'='*60}{RESET}")
    
    # تست 1: حالت عادی
    await test_normal_mode()
    
    # فاصله بین تست‌ها
    print("\n" + "="*60 + "\n")
    await asyncio.sleep(2)
    
    # تست 2: حالت streaming
    await test_streaming_mode()
    
    print(f"\n{YELLOW}{'='*60}{RESET}")
    print(f"{YELLOW}✅ تست‌ها تمام شد{RESET}")
    print(f"{YELLOW}{'='*60}{RESET}\n")


if __name__ == '__main__':
    asyncio.run(main())
