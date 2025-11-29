#!/usr/bin/env python3
"""تست ساده MinIO"""
import os
import sys
sys.path.insert(0, '/app')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')

import django
django.setup()

from io import BytesIO
from core.storage import MinIOService

print("="*60)
print("🧪 تست اتصال به MinIO")
print("="*60)

try:
    # ایجاد سرویس
    print("\n1️⃣ ایجاد MinIO Service...")
    minio = MinIOService()
    print(f"✅ اتصال برقرار شد")
    print(f"   Endpoint: {minio.s3_client._endpoint}")
    print(f"   Bucket: {minio.bucket_name}")
    
    # تست آپلود
    print("\n2️⃣ تست آپلود فایل...")
    test_content = b"Test file for RAG system - " + os.urandom(100)
    test_file = BytesIO(test_content)
    test_file.name = "test_upload.txt"
    
    result = minio.upload_file(
        file=test_file,
        filename="test_upload.txt",
        content_type="text/plain",
        user_id="test_user_123"
    )
    
    print(f"✅ فایل آپلود شد")
    print(f"   Object Key: {result['object_key']}")
    print(f"   Size: {result['size_bytes']} bytes")
    print(f"   URL: {result['minio_url']}")
    
    # تست URL امن
    print("\n3️⃣ تولید URL امن...")
    secure_url = minio.generate_presigned_url(result['object_key'])
    print(f"✅ URL امن تولید شد")
    print(f"   URL: {secure_url[:80]}...")
    
    print("\n" + "="*60)
    print("✅ همه تست‌های MinIO موفق بودند!")
    print("="*60)
    
except Exception as e:
    print(f"\n❌ خطا: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
