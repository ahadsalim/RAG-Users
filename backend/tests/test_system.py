#!/usr/bin/env python3
"""
تست جامع سیستم و ابزارهای کمکی
شامل: MinIO, RAG Core, File Upload, Query, Cleanup
"""
import os
import sys
import asyncio
import httpx
import argparse
from datetime import datetime, timedelta
from io import BytesIO

sys.path.insert(0, '/app')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')

import django
django.setup()

from django.conf import settings
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken
from core.storage import S3Service
from botocore.exceptions import ClientError

User = get_user_model()

GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'


class SystemTester:
    """کلاس تست جامع سیستم"""
    
    def __init__(self):
        self.results = {
            'minio': False,
            'rag_normal': False,
            'rag_streaming': False,
        }
    
    def print_header(self, text):
        print(f"\n{'='*80}")
        print(f"{BLUE}{text}{RESET}")
        print(f"{'='*80}\n")
    
    def print_success(self, text):
        print(f"{GREEN}✅ {text}{RESET}")
    
    def print_error(self, text):
        print(f"{RED}❌ {text}{RESET}")
    
    def print_info(self, text):
        print(f"{YELLOW}ℹ️  {text}{RESET}")
    
    def test_minio(self):
        """تست آپلود فایل به MinIO"""
        self.print_header("تست 1: MinIO File Upload")
        
        try:
            s3 = S3Service()
            self.print_success("اتصال به MinIO برقرار شد")
            
            test_file = BytesIO(b"Test file content for MinIO")
            
            result = s3.upload_file(
                file_content=test_file.read(),
                filename="test_file.txt",
                user_id="test_user",
                content_type="text/plain"
            )
            
            self.print_success(f"فایل آپلود شد: {result['object_key']}")
            self.results['minio'] = True
            return result
            
        except Exception as e:
            self.print_error(f"خطا: {e}")
            return None
    
    async def test_rag_normal_with_token(self, token):
        """تست query عادی به RAG Core"""
        self.print_header("تست 2: RAG Core Normal Query")
        
        try:
            url = "https://core.tejarat.chat/api/v1/query/"
            payload = {"query": "سلام", "language": "fa"}
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            }
            
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(url, json=payload, headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                self.print_success(f"پاسخ دریافت شد: {data.get('answer', '')[:100]}...")
                self.results['rag_normal'] = True
                return data
            else:
                self.print_error(f"Status: {response.status_code}")
                return None
                
        except Exception as e:
            self.print_error(f"خطا: {e}")
            return None
    
    async def test_rag_streaming_with_token(self, token):
        """تست streaming query به RAG Core"""
        self.print_header("تست 3: RAG Core Streaming Query")
        
        try:
            url = "https://core.tejarat.chat/api/v1/query/stream"
            payload = {"query": "سلام", "language": "fa"}
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            }
            
            async with httpx.AsyncClient(timeout=60.0) as client:
                async with client.stream('POST', url, json=payload, headers=headers) as response:
                    if response.status_code == 200:
                        chunks = 0
                        async for chunk in response.aiter_text():
                            if chunk.strip():
                                chunks += 1
                        
                        self.print_success(f"Streaming کار کرد: {chunks} chunks دریافت شد")
                        self.results['rag_streaming'] = True
                        return True
                    else:
                        self.print_error(f"Status: {response.status_code}")
                        if response.status_code == 500:
                            self.print_info("⚠️  Bug در سیستم مرکزی (منتظر fix)")
                        return None
                        
        except Exception as e:
            self.print_error(f"خطا: {e}")
            return None
    
    def print_summary(self):
        """نمایش خلاصه نتایج"""
        self.print_header("📊 خلاصه نتایج")
        
        total = len(self.results)
        passed = sum(1 for v in self.results.values() if v)
        
        for test_name, result in self.results.items():
            status = f"{GREEN}✅ موفق{RESET}" if result else f"{RED}❌ ناموفق{RESET}"
            print(f"  {test_name}: {status}")
        
        print(f"\n{'='*80}")
        print(f"نتیجه کل: {passed}/{total} تست موفق")
        
        if passed == total:
            print(f"{GREEN}🎉 همه تست‌ها موفق بودند!{RESET}")
        else:
            print(f"{YELLOW}⚠️  برخی تست‌ها ناموفق بودند{RESET}")
        
        print(f"{'='*80}\n")


def cleanup_old_files(hours=24):
    """حذف فایل‌های قدیمی‌تر از X ساعت از MinIO"""
    s3 = S3Service()
    bucket = 'temp-userfile'
    
    print(f"🔍 جستجوی فایل‌های قدیمی‌تر از {hours} ساعت...")
    
    try:
        response = s3.s3_client.list_objects_v2(Bucket=bucket)
        
        if 'Contents' not in response:
            print("✅ هیچ فایلی در MinIO وجود ندارد.")
            return
        
        files = response['Contents']
        now = datetime.utcnow()
        cutoff_time = now - timedelta(hours=hours)
        
        deleted_count = 0
        deleted_size = 0
        kept_count = 0
        
        for file in files:
            file_time = file['LastModified'].replace(tzinfo=None)
            
            if file_time < cutoff_time:
                try:
                    s3.s3_client.delete_object(Bucket=bucket, Key=file['Key'])
                    deleted_count += 1
                    deleted_size += file['Size']
                    print(f"  ❌ حذف شد: {file['Key']} ({file['Size']/1024:.1f} KB)")
                except Exception as e:
                    print(f"  ⚠️  خطا در حذف {file['Key']}: {e}")
            else:
                kept_count += 1
        
        print(f"\n📊 نتیجه:")
        print(f"  ✅ فایل‌های حذف شده: {deleted_count}")
        print(f"  💾 حجم آزاد شده: {deleted_size / (1024*1024):.2f} MB")
        print(f"  📁 فایل‌های باقی‌مانده: {kept_count}")
        
    except ClientError as e:
        print(f"❌ خطا در دسترسی به MinIO: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ خطای غیرمنتظره: {e}")
        sys.exit(1)


def cleanup_all_files():
    """حذف تمام فایل‌ها از MinIO"""
    s3 = S3Service()
    bucket = 'temp-userfile'
    
    print("⚠️  حذف تمام فایل‌ها از MinIO...")
    
    try:
        response = s3.s3_client.list_objects_v2(Bucket=bucket)
        
        if 'Contents' not in response:
            print("✅ هیچ فایلی در MinIO وجود ندارد.")
            return
        
        files = response['Contents']
        total_size = sum(f['Size'] for f in files)
        
        for file in files:
            s3.s3_client.delete_object(Bucket=bucket, Key=file['Key'])
        
        print(f"✅ {len(files)} فایل حذف شد ({total_size / (1024*1024):.2f} MB)")
        
    except Exception as e:
        print(f"❌ خطا: {e}")
        sys.exit(1)


async def run_tests():
    """اجرای تست‌های سیستم"""
    user = User.objects.first()
    if not user:
        print(f"{RED}❌ کاربری یافت نشد{RESET}")
        return
    
    refresh = RefreshToken.for_user(user)
    token = str(refresh.access_token)
    
    tester = SystemTester()
    tester.test_minio()
    await tester.test_rag_normal_with_token(token)
    await tester.test_rag_streaming_with_token(token)
    tester.print_summary()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='تست سیستم و ابزارهای کمکی')
    parser.add_argument('--test', action='store_true', help='اجرای تست‌های سیستم')
    parser.add_argument('--cleanup', type=int, metavar='HOURS', help='حذف فایل‌های قدیمی‌تر از X ساعت')
    parser.add_argument('--cleanup-all', action='store_true', help='حذف تمام فایل‌ها (خطرناک!)')
    
    args = parser.parse_args()
    
    if args.test:
        print(f"\n{BLUE}{'='*80}{RESET}")
        print(f"{BLUE}🚀 شروع تست جامع سیستم{RESET}")
        print(f"{BLUE}⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}{RESET}")
        print(f"{BLUE}{'='*80}{RESET}\n")
        asyncio.run(run_tests())
    elif args.cleanup:
        cleanup_old_files(args.cleanup)
    elif args.cleanup_all:
        confirm = input("⚠️  آیا مطمئن هستید که می‌خواهید تمام فایل‌ها را حذف کنید؟ (yes/no): ")
        if confirm.lower() == 'yes':
            cleanup_all_files()
        else:
            print("❌ لغو شد.")
    else:
        parser.print_help()
