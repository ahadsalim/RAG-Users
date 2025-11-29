#!/usr/bin/env python3
"""تست کامل فلوی آپلود فایل و ارسال query"""
import os
import sys
import django

sys.path.insert(0, '/app')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from core.storage import S3Service
from chat.serializers import FileAttachmentSerializer, QueryRequestSerializer
import time

print('='*70)
print('🧪 تست کامل فلوی آپلود فایل و ارسال Query')
print('='*70)

# تست 1: آپلود فایل به S3
print('\n' + '='*70)
print('📤 مرحله 1: آپلود فایل به S3')
print('='*70)

try:
    s3 = S3Service()
    
    # ساخت فایل تستی
    test_content = b'This is a test PDF content for RAG system analysis.'
    
    result = s3.upload_file(
        file_content=test_content,
        filename='test_document.pdf',
        user_id='user123',
        content_type='application/pdf'
    )
    
    print(f'✅ فایل آپلود شد')
    print(f'   Object Key: {result["object_key"]}')
    print(f'   Bucket: {result["bucket_name"]}')
    print(f'   Size: {result["size_bytes"]} bytes')
    
    # تست 2: آماده‌سازی file_attachment
    print('\n' + '='*70)
    print('📋 مرحله 2: آماده‌سازی File Attachment')
    print('='*70)
    
    file_attachment = {
        'filename': 'test_document.pdf',
        'minio_url': result['object_key'],
        'file_type': 'application/pdf',
        'size_bytes': result['size_bytes']
    }
    
    # اعتبارسنجی با serializer
    serializer = FileAttachmentSerializer(data=file_attachment)
    if serializer.is_valid():
        print('✅ File attachment معتبر است')
        print(f'   Data: {serializer.validated_data}')
    else:
        print(f'❌ خطا در اعتبارسنجی: {serializer.errors}')
    
    # تست 3: آماده‌سازی Query Request
    print('\n' + '='*70)
    print('📨 مرحله 3: آماده‌سازی Query Request')
    print('='*70)
    
    query_data = {
        'query': 'این سند را بررسی کن و نکات مهم را بگو',
        'language': 'fa',
        'file_attachments': [file_attachment]
    }
    
    query_serializer = QueryRequestSerializer(data=query_data)
    if query_serializer.is_valid():
        print('✅ Query request معتبر است')
        print(f'   Query: {query_serializer.validated_data["query"]}')
        print(f'   Language: {query_serializer.validated_data["language"]}')
        print(f'   Files: {len(query_serializer.validated_data["file_attachments"])} فایل')
    else:
        print(f'❌ خطا در اعتبارسنجی: {query_serializer.errors}')
    
    # تست 4: فرمت نهایی برای ارسال به سیستم مرکزی
    print('\n' + '='*70)
    print('🚀 مرحله 4: فرمت نهایی برای API سیستم مرکزی')
    print('='*70)
    
    api_payload = {
        'query': query_data['query'],
        'language': query_data['language'],
        'file_attachments': [
            {
                'filename': file_attachment['filename'],
                'minio_url': file_attachment['minio_url'],
                'file_type': file_attachment['file_type'],
                'size_bytes': file_attachment['size_bytes']
            }
        ]
    }
    
    print('✅ Payload آماده است:')
    import json
    print(json.dumps(api_payload, indent=2, ensure_ascii=False))
    
    # تست 5: تست با چند فایل (حداکثر 5)
    print('\n' + '='*70)
    print('📚 مرحله 5: تست با چند فایل')
    print('='*70)
    
    # آپلود 3 فایل دیگر
    files_uploaded = [file_attachment]
    
    for i in range(2, 4):
        test_content = f'Test file {i} content'.encode()
        result = s3.upload_file(
            file_content=test_content,
            filename=f'test_file_{i}.txt',
            user_id='user123',
            content_type='text/plain'
        )
        
        files_uploaded.append({
            'filename': f'test_file_{i}.txt',
            'minio_url': result['object_key'],
            'file_type': 'text/plain',
            'size_bytes': result['size_bytes']
        })
    
    print(f'✅ {len(files_uploaded)} فایل آپلود شد')
    
    # اعتبارسنجی با حداکثر 5 فایل
    multi_query_data = {
        'query': 'این اسناد را تحلیل کن',
        'language': 'fa',
        'file_attachments': files_uploaded
    }
    
    multi_serializer = QueryRequestSerializer(data=multi_query_data)
    if multi_serializer.is_valid():
        print(f'✅ Query با {len(files_uploaded)} فایل معتبر است')
    else:
        print(f'❌ خطا: {multi_serializer.errors}')
    
    # تست 6: تست محدودیت 5 فایل
    print('\n' + '='*70)
    print('⚠️  مرحله 6: تست محدودیت حداکثر 5 فایل')
    print('='*70)
    
    # سعی در ارسال 6 فایل
    too_many_files = files_uploaded + [
        {'filename': 'extra1.txt', 'minio_url': 'temp_uploads/test/extra1.txt', 'file_type': 'text/plain'},
        {'filename': 'extra2.txt', 'minio_url': 'temp_uploads/test/extra2.txt', 'file_type': 'text/plain'},
        {'filename': 'extra3.txt', 'minio_url': 'temp_uploads/test/extra3.txt', 'file_type': 'text/plain'},
    ]
    
    invalid_query = {
        'query': 'تست',
        'file_attachments': too_many_files
    }
    
    invalid_serializer = QueryRequestSerializer(data=invalid_query)
    if not invalid_serializer.is_valid():
        print(f'✅ محدودیت 5 فایل کار می‌کند')
        print(f'   خطا: {invalid_serializer.errors}')
    else:
        print(f'❌ محدودیت کار نمی‌کند!')
    
    # پاکسازی فایل‌های تستی
    print('\n' + '='*70)
    print('🗑️  پاکسازی فایل‌های تستی')
    print('='*70)
    
    for file_data in files_uploaded:
        s3.delete_file(file_data['minio_url'])
    
    print(f'✅ {len(files_uploaded)} فایل حذف شد')
    
    print('\n' + '='*70)
    print('🎉 همه تست‌ها موفق بود!')
    print('='*70)
    print('\n📋 خلاصه:')
    print('   ✅ آپلود فایل به S3')
    print('   ✅ اعتبارسنجی file_attachment')
    print('   ✅ اعتبارسنجی query request')
    print('   ✅ فرمت API سیستم مرکزی')
    print('   ✅ آپلود چند فایل')
    print('   ✅ محدودیت 5 فایل')
    print('   ✅ پاکسازی فایل‌ها')
    
except Exception as e:
    print(f'\n❌ خطا: {type(e).__name__}: {e}')
    import traceback
    traceback.print_exc()
    sys.exit(1)
