#!/usr/bin/env python3
"""
نمایش دقیق درخواستی که به سیستم مرکزی RAG Core ارسال می‌شود
"""
import os
import sys
import django
import json

sys.path.insert(0, '/app')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.conf import settings
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken

User = get_user_model()

print('='*80)
print('📋 نمایش کامل درخواست به سیستم مرکزی RAG Core')
print('='*80)

# 1. تولید JWT Token
print('\n' + '='*80)
print('🔑 مرحله 1: تولید JWT Token')
print('='*80)

user = User.objects.first()
if not user:
    print('❌ هیچ کاربری در دیتابیس وجود ندارد')
    sys.exit(1)

refresh = RefreshToken.for_user(user)
access_token = str(refresh.access_token)

print(f'✅ کاربر: {user.username}')
print(f'✅ User ID: {user.id}')
print(f'\n📝 JWT Token (کامل):')
print(f'{access_token}')

# 2. آماده‌سازی فایل‌های تستی
print('\n' + '='*80)
print('📁 مرحله 2: آماده‌سازی File Attachments')
print('='*80)

file_attachments = [
    {
        "filename": "contract.pdf",
        "minio_url": "temp_uploads/57e5cf9a-8c43-4be1-89cc-29c81c61396d/20251130_044636_f8d95d76-90d3-453d-8ef1-149210e6f754_contract.pdf",
        "file_type": "application/pdf",
        "size_bytes": 524288
    },
    {
        "filename": "invoice.png",
        "minio_url": "temp_uploads/57e5cf9a-8c43-4be1-89cc-29c81c61396d/20251130_044636_176cd22a-a521-4b28-9cf7-07582960cfec_invoice.png",
        "file_type": "image/png",
        "size_bytes": 111055
    }
]

print(f'✅ تعداد فایل‌ها: {len(file_attachments)}')
for i, f in enumerate(file_attachments, 1):
    print(f'   {i}. {f["filename"]} ({f["size_bytes"]} bytes)')

# 3. ساخت Payload
print('\n' + '='*80)
print('📦 مرحله 3: ساخت Request Payload')
print('='*80)

payload = {
    "query": "این اسناد را بررسی کن و خلاصه‌ای از محتوای آنها بده",
    "language": "fa",
    "conversation_id": "123e4567-e89b-12d3-a456-426614174000",
    "file_attachments": file_attachments
}

print('✅ Payload (JSON):')
print(json.dumps(payload, indent=2, ensure_ascii=False))

# 4. ساخت Headers
print('\n' + '='*80)
print('📋 مرحله 4: ساخت Request Headers')
print('='*80)

headers = {
    'Authorization': f'Bearer {access_token}',
    'Content-Type': 'application/json',
}

print('✅ Headers:')
for key, value in headers.items():
    if key == 'Authorization':
        # نمایش 50 کاراکتر اول token
        print(f'   {key}: {value[:70]}...')
    else:
        print(f'   {key}: {value}')

# 5. URL و Method
print('\n' + '='*80)
print('🌐 مرحله 5: URL و HTTP Method')
print('='*80)

url = f"{settings.RAG_CORE_BASE_URL}/api/v1/query/"
print(f'✅ Method: POST')
print(f'✅ URL: {url}')
print(f'✅ Timeout: 300 seconds (5 minutes)')

# 6. نمایش کامل درخواست به صورت cURL
print('\n' + '='*80)
print('🔧 مرحله 6: دستور cURL معادل')
print('='*80)

curl_command = f'''curl -X POST '{url}' \\
  -H 'Content-Type: application/json' \\
  -H 'Authorization: Bearer {access_token}' \\
  -d '{json.dumps(payload, ensure_ascii=False)}'
'''

print(curl_command)

# 7. نمایش به صورت Python requests
print('\n' + '='*80)
print('🐍 مرحله 7: کد Python معادل')
print('='*80)

python_code = f'''import requests
import json

url = "{url}"

headers = {{
    "Content-Type": "application/json",
    "Authorization": "Bearer {access_token}"
}}

payload = {json.dumps(payload, indent=4, ensure_ascii=False)}

response = requests.post(
    url,
    headers=headers,
    json=payload,
    timeout=300
)

print(f"Status Code: {{response.status_code}}")
print(f"Response: {{response.json()}}")
'''

print(python_code)

# 8. اطلاعات MinIO
print('\n' + '='*80)
print('🗄️  مرحله 8: اطلاعات MinIO/S3')
print('='*80)

print(f'✅ S3 Endpoint: {settings.S3_ENDPOINT_URL}')
print(f'✅ S3 Bucket: {settings.S3_TEMP_BUCKET}')
print(f'✅ Access Key: {settings.S3_ACCESS_KEY_ID[:10]}...')
print(f'\n💡 سیستم مرکزی باید با همین اطلاعات به MinIO متصل شود')

# 9. خلاصه
print('\n' + '='*80)
print('📊 خلاصه درخواست')
print('='*80)

print(f'''
🎯 درخواست به سیستم مرکزی:

1. URL: {url}
2. Method: POST
3. Content-Type: application/json
4. Authorization: Bearer {access_token[:50]}...

5. Body:
   - query: "{payload["query"]}"
   - language: {payload["language"]}
   - conversation_id: {payload.get("conversation_id", "None")}
   - file_attachments: {len(payload.get("file_attachments", []))} فایل

6. فایل‌ها در MinIO:
   - Bucket: {settings.S3_TEMP_BUCKET}
   - Endpoint: {settings.S3_ENDPOINT_URL}
   
7. Timeout: 300 seconds

⚠️  نکات مهم:
   - سیستم مرکزی باید JWT token را validate کند
   - سیستم مرکزی باید به MinIO دسترسی داشته باشد
   - فایل‌ها باید از bucket '{settings.S3_TEMP_BUCKET}' خوانده شوند
   - پاسخ باید شامل: answer, file_analysis, conversation_id باشد
''')

print('='*80)
print('✅ اطلاعات کامل آماده است')
print('='*80)
