#!/usr/bin/env python3
"""
اسکریپت پاک‌سازی فایل‌های قدیمی از MinIO.
فایل‌های بیش از 24 ساعت را حذف می‌کند.
"""
import os
import sys
import django
from datetime import datetime, timedelta

# Setup Django
sys.path.insert(0, '/app')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from core.storage import S3Service
from botocore.exceptions import ClientError

def cleanup_old_files(hours=24):
    """
    حذف فایل‌های قدیمی‌تر از X ساعت از MinIO.
    
    Args:
        hours: فایل‌های قدیمی‌تر از این تعداد ساعت حذف می‌شوند
    """
    s3 = S3Service()
    bucket = 'temp-userfile'
    
    print(f"🔍 جستجوی فایل‌های قدیمی‌تر از {hours} ساعت...")
    
    try:
        # لیست تمام فایل‌ها
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
                # فایل قدیمی است - حذف کن
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
    """حذف تمام فایل‌ها از MinIO (برای تست)."""
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


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='پاک‌سازی فایل‌های قدیمی از MinIO')
    parser.add_argument('--hours', type=int, default=24, help='حذف فایل‌های قدیمی‌تر از X ساعت (پیش‌فرض: 24)')
    parser.add_argument('--all', action='store_true', help='حذف تمام فایل‌ها (خطرناک!)')
    
    args = parser.parse_args()
    
    if args.all:
        confirm = input("⚠️  آیا مطمئن هستید که می‌خواهید تمام فایل‌ها را حذف کنید؟ (yes/no): ")
        if confirm.lower() == 'yes':
            cleanup_all_files()
        else:
            print("❌ لغو شد.")
    else:
        cleanup_old_files(args.hours)
