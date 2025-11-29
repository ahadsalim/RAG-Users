#!/usr/bin/env python3
"""تست اتصال به S3/MinIO"""
import boto3
from botocore.config import Config
from botocore.exceptions import ClientError
import os
import sys

# خواندن از فایل .env
config = {}
try:
    with open('/srv/deployment/.env', 'r') as f:
        for line in f:
            if '=' in line and not line.strip().startswith('#'):
                key, value = line.strip().split('=', 1)
                config[key] = value
except Exception as e:
    print(f"❌ خطا در خواندن .env: {e}")
    sys.exit(1)

endpoint = config.get('S3_ENDPOINT_URL', '')
access_key = config.get('S3_ACCESS_KEY_ID', '')
secret_key = config.get('S3_SECRET_ACCESS_KEY', '')
bucket_name = config.get('S3_TEMP_BUCKET', 'temp-userfile')
use_ssl = config.get('S3_USE_SSL', 'true').lower() == 'true'

print('='*70)
print('🧪 تست اتصال به S3/MinIO')
print('='*70)
print(f'\n📍 تنظیمات:')
print(f'   Endpoint: {endpoint}')
print(f'   Bucket: {bucket_name}')
print(f'   SSL: {use_ssl}')
print(f'   Access Key: {access_key[:20] if access_key else "NOT SET"}...')

if not access_key or not secret_key:
    print('\n❌ S3_ACCESS_KEY_ID یا S3_SECRET_ACCESS_KEY تنظیم نشده')
    sys.exit(1)

try:
    import time
    
    # ساخت client با تنظیمات مختلف
    print('\n' + '='*70)
    print('🔧 تست 1: ساخت S3 Client')
    print('='*70)
    
    boto_config = Config(
        signature_version='s3v4',
        s3={'addressing_style': 'path'}
    )
    
    s3 = boto3.client(
        's3',
        endpoint_url=endpoint,
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key,
        region_name='us-east-1',
        use_ssl=use_ssl,
        config=boto_config
    )
    
    print('✅ Client ساخته شد')
    
    # تست 2: لیست buckets
    print('\n' + '='*70)
    print('🔧 تست 2: لیست Buckets')
    print('='*70)
    
    start = time.time()
    try:
        response = s3.list_buckets()
        elapsed = time.time() - start
        print(f'✅ لیست buckets دریافت شد ({elapsed:.2f}s)')
        print(f'\n📦 Buckets موجود:')
        for bucket in response['Buckets']:
            print(f'   - {bucket["Name"]} (Created: {bucket["CreationDate"]})')
    except Exception as e:
        print(f'❌ خطا: {type(e).__name__}: {e}')
    
    # تست 3: بررسی bucket
    print('\n' + '='*70)
    print(f'🔧 تست 3: بررسی bucket "{bucket_name}"')
    print('='*70)
    
    start = time.time()
    try:
        s3.head_bucket(Bucket=bucket_name)
        elapsed = time.time() - start
        print(f'✅ Bucket "{bucket_name}" موجود است ({elapsed:.2f}s)')
    except ClientError as e:
        error_code = e.response['Error']['Code']
        print(f'❌ خطا {error_code}: {e}')
        if error_code == '404':
            print(f'   Bucket "{bucket_name}" یافت نشد')
        elif error_code == '403':
            print(f'   ⚠️  Access Denied - ولی bucket احتمالاً موجود است')
    
    # تست 4: لیست فایل‌های bucket
    print('\n' + '='*70)
    print(f'🔧 تست 4: لیست فایل‌های bucket "{bucket_name}"')
    print('='*70)
    
    start = time.time()
    try:
        response = s3.list_objects_v2(Bucket=bucket_name, MaxKeys=10)
        elapsed = time.time() - start
        
        if 'Contents' in response:
            print(f'✅ لیست فایل‌ها دریافت شد ({elapsed:.2f}s)')
            print(f'\n📄 فایل‌های موجود (تا 10 فایل اول):')
            for obj in response['Contents']:
                size_kb = obj['Size'] / 1024
                print(f'   - {obj["Key"]} ({size_kb:.2f} KB)')
        else:
            print(f'✅ Bucket خالی است ({elapsed:.2f}s)')
    except ClientError as e:
        error_code = e.response['Error']['Code']
        print(f'❌ خطا {error_code}: {e}')
    
    # تست 5: آپلود فایل تستی
    print('\n' + '='*70)
    print('🔧 تست 5: آپلود فایل تستی')
    print('='*70)
    
    test_key = 'test_uploads/test_file_' + str(int(time.time())) + '.txt'
    test_content = b'Test content from RAG Users system - ' + os.urandom(50)
    
    start = time.time()
    try:
        s3.put_object(
            Bucket=bucket_name,
            Key=test_key,
            Body=test_content,
            ContentType='text/plain'
        )
        elapsed = time.time() - start
        
        print(f'✅ فایل آپلود شد ({elapsed:.2f}s)')
        print(f'   Bucket: {bucket_name}')
        print(f'   Key: {test_key}')
        print(f'   Size: {len(test_content)} bytes')
        
        # تست 6: خواندن فایل
        print('\n' + '='*70)
        print('🔧 تست 6: خواندن فایل آپلود شده')
        print('='*70)
        
        start = time.time()
        response = s3.get_object(Bucket=bucket_name, Key=test_key)
        content = response['Body'].read()
        elapsed = time.time() - start
        
        if content == test_content:
            print(f'✅ فایل خوانده شد و محتوا صحیح است ({elapsed:.2f}s)')
        else:
            print(f'❌ محتوای خوانده شده با محتوای اصلی مطابقت ندارد')
        
        # تست 7: حذف فایل تستی
        print('\n' + '='*70)
        print('🔧 تست 7: حذف فایل تستی')
        print('='*70)
        
        start = time.time()
        s3.delete_object(Bucket=bucket_name, Key=test_key)
        elapsed = time.time() - start
        print(f'✅ فایل حذف شد ({elapsed:.2f}s)')
        
    except ClientError as e:
        error_code = e.response['Error']['Code']
        print(f'❌ خطا {error_code}: {e}')
        print(f'\n🔍 جزئیات خطا:')
        print(f'   Message: {e.response["Error"].get("Message", "N/A")}')
        if 'ResponseMetadata' in e.response:
            print(f'   HTTPStatusCode: {e.response["ResponseMetadata"].get("HTTPStatusCode", "N/A")}')
    
    print('\n' + '='*70)
    print('✅ تست‌های S3/MinIO تمام شد')
    print('='*70)
    
except Exception as e:
    print(f'\n❌ خطای کلی: {type(e).__name__}: {e}')
    import traceback
    traceback.print_exc()
    sys.exit(1)
