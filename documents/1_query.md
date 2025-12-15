# جریان آپلود فایل و ارسال سوال به سیستم مرکزی

این سند نحوه پردازش سوال کاربر همراه با فایل ضمیمه و ارسال به سیستم مرکزی RAG را توضیح می‌دهد.

---

## 📤 مرحله ۱: آپلود فایل (جداگانه)

**Endpoint:** `POST /api/v1/chat/upload/`

کاربر ابتدا فایل را آپلود می‌کند و این اطلاعات برمی‌گردد:

```json
{
  "object_key": "temp_uploads/user123/file.pdf",
  "filename": "document.pdf",
  "size_bytes": 1024,
  "content_type": "application/pdf",
  "expires_at": "2024-11-30T12:00:00",
  "bucket_name": "shared-storage"
}
```

### فرمت‌های پشتیبانی شده:

| نوع | فرمت‌ها |
|-----|---------|
| تصاویر | `jpeg`, `jpg`, `png`, `gif`, `bmp`, `webp` |
| اسناد | `pdf`, `doc`, `docx` |
| متن | `txt`, `md`, `html`, `htm` |

### محدودیت‌ها:
- حداکثر حجم هر فایل: **10MB**
- حداکثر تعداد فایل در هر درخواست: **5 فایل**

---

## 📝 مرحله ۲: ارسال سوال با فایل

**Endpoint:** `POST /api/v1/chat/query/`

Frontend این اطلاعات را می‌فرستد:

```json
{
  "query": "متن سوال کاربر",
  "conversation_id": "uuid (اختیاری)",
  "language": "fa",
  "file_attachments": [
    {
      "filename": "document.pdf",
      "minio_url": "temp_uploads/user123/file.pdf",
      "file_type": "application/pdf",
      "size_bytes": 1024
    }
  ]
}
```

### فیلدها:

| فیلد | نوع | الزامی | توضیح |
|------|-----|--------|-------|
| `query` | string | ✅ | متن سوال (1-2000 کاراکتر) |
| `conversation_id` | UUID | ❌ | شناسه مکالمه برای ادامه گفتگو |
| `language` | string | ❌ | زبان (پیش‌فرض: `fa`) |
| `file_attachments` | array | ❌ | لیست فایل‌های ضمیمه (حداکثر 5) |
| `enable_web_search` | boolean | ❌ | فعال/غیرفعال کردن جستجوی وب |

---

## ⚙️ مرحله ۳: پردازش در Backend

### 3.1 اعتبارسنجی اشتراک
```python
# بررسی اشتراک فعال
active_subscription = user.subscriptions.filter(
    status__in=['active', 'trial'],
    end_date__gt=timezone.now()
).first()

# بررسی محدودیت روزانه/ماهانه
can_query, message = active_subscription.can_query()
```

### 3.2 ایجاد/دریافت Conversation
```python
if conversation_id:
    conversation = Conversation.objects.get(id=conversation_id, user=user)
else:
    conversation = Conversation.objects.create(
        user=user,
        title=query[:50] + '...'
    )
```

### 3.3 ذخیره پیام کاربر
```python
user_message = Message.objects.create(
    conversation=conversation,
    role='user',
    content=query,
    status='completed'
)
```

### 3.4 ذخیره فایل‌های ضمیمه
```python
for file_data in file_attachments:
    MessageAttachment.objects.create(
        message=user_message,
        file=file_data['minio_url'],
        file_name=file_data['filename'],
        file_size=file_data.get('size_bytes', 0),
        file_type='image' if file_data['file_type'].startswith('image/') else 'document',
        mime_type=file_data['file_type']
    )
```

### 3.5 تولید JWT Token
```python
from rest_framework_simplejwt.tokens import RefreshToken
refresh = RefreshToken.for_user(user)
access_token = str(refresh.access_token)
```

---

## 🌐 مرحله ۴: ارسال به سیستم مرکزی (Core RAG)

**Endpoint:** `POST https://core.tejarat.chat/api/v1/query/`

### Payload ارسالی:

```json
{
  "query": "متن سوال کاربر",
  "language": "fa",
  "conversation_id": "uuid (برای حافظه مکالمه)",
  "file_attachments": [
    {
      "filename": "document.pdf",
      "minio_url": "temp_uploads/user123/file.pdf",
      "file_type": "application/pdf",
      "size_bytes": 1024
    }
  ],
  "enable_web_search": true
}
```

### Headers:

```http
Authorization: Bearer <JWT_TOKEN>
Content-Type: application/json
```

### کد ارسال:

```python
async def send_query(
    self,
    query: str,
    token: str,
    conversation_id: Optional[str] = None,
    language: str = 'fa',
    file_attachments: Optional[list] = None,
    enable_web_search: Optional[bool] = None,
) -> Dict[str, Any]:
    
    url = f"{self.base_url}/api/v1/query/"
    
    payload = {
        "query": query,
        "language": language,
    }
    
    if conversation_id:
        payload["conversation_id"] = conversation_id
    
    if file_attachments:
        payload["file_attachments"] = file_attachments[:5]
    
    if enable_web_search is not None:
        payload["enable_web_search"] = enable_web_search
    
    async with httpx.AsyncClient(timeout=60) as client:
        response = await client.post(
            url,
            json=payload,
            headers={'Authorization': f'Bearer {token}'}
        )
        return response.json()
```

---

## 📥 مرحله ۵: دریافت پاسخ از Core

Core RAG این اطلاعات را برمی‌گرداند:

```json
{
  "answer": "پاسخ هوش مصنوعی",
  "sources": ["منبع ۱", "منبع ۲"],
  "conversation_id": "uuid",
  "file_analysis": {
    "extracted_text": "متن استخراج شده از فایل",
    "summary": "خلاصه فایل"
  }
}
```

---

## 💾 مرحله ۶: ذخیره و بازگشت پاسخ

### 6.1 به‌روزرسانی Conversation
```python
if not conversation.rag_conversation_id and 'conversation_id' in response:
    conversation.rag_conversation_id = response.get('conversation_id')
    conversation.save()
```

### 6.2 ذخیره پاسخ Assistant
```python
assistant_message.content = response.get('answer', '')
assistant_message.sources = response.get('sources', [])
assistant_message.status = 'completed'
assistant_message.save()
```

### 6.3 ثبت Usage
```python
from subscriptions.usage import UsageService
UsageService.log_usage(
    user=user,
    subscription=active_subscription,
    usage_type='query',
    tokens_used=response.get('tokens_used', 0)
)
```

---

## 🔄 نمودار جریان کامل

```
┌─────────────────┐
│    Frontend     │
└────────┬────────┘
         │ 1. Upload File
         ▼
┌─────────────────┐
│   MinIO/S3      │ ← ذخیره فایل
└────────┬────────┘
         │ object_key
         ▼
┌─────────────────┐
│    Frontend     │
└────────┬────────┘
         │ 2. Send Query + file_attachments
         ▼
┌─────────────────┐
│    Backend      │
│   (Django)      │
└────────┬────────┘
         │ 3. Validate subscription
         │ 4. Save user message
         │ 5. Generate JWT
         │ 6. Send to Core
         ▼
┌─────────────────┐
│   Core RAG      │ ← پردازش سوال + فایل
│  (tejarat.chat) │
└────────┬────────┘
         │ 7. Return answer
         ▼
┌─────────────────┐
│    Backend      │
│   (Django)      │
└────────┬────────┘
         │ 8. Save assistant message
         │ 9. Log usage
         │ 10. Return response
         ▼
┌─────────────────┐
│    Frontend     │ ← نمایش پاسخ
└─────────────────┘
```

---

## ⚠️ نکات مهم

### 1. ذخیره‌سازی فایل
- فایل‌ها در **MinIO** ذخیره می‌شوند
- فقط `object_key` به Core ارسال می‌شود
- Core باید به همان MinIO دسترسی داشته باشد

### 2. احراز هویت
- JWT Token برای هر درخواست تولید می‌شود
- Token از `rest_framework_simplejwt` تولید می‌شود
- Core از همان JWT برای شناسایی کاربر استفاده می‌کند

### 3. محدودیت‌ها
- حداکثر **5 فایل** در هر درخواست
- حداکثر **10MB** برای هر فایل
- حداکثر **2000 کاراکتر** برای متن سوال

### 4. Timeout
- Timeout پیش‌فرض: **60 ثانیه**
- قابل تنظیم در `settings.py`

---

## 📁 فایل‌های مرتبط

| فایل | توضیح |
|------|-------|
| `/srv/backend/chat/upload_views.py` | آپلود فایل |
| `/srv/backend/chat/views.py` | پردازش Query |
| `/srv/backend/chat/core_service.py` | ارتباط با Core RAG |
| `/srv/backend/chat/serializers.py` | Serializers |
| `/srv/backend/core/storage.py` | MinIO Service |

---

**آخرین به‌روزرسانی:** 2025-12-15
