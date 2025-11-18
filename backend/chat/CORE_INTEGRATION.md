# یکپارچه‌سازی با Core RAG System

این سند نحوه یکپارچه‌سازی سیستم کاربران با Core RAG System را توضیح می‌دهد.

---

## 🔗 حذف خودکار Conversation از Core

### نحوه کار

وقتی یک `Conversation` در سیستم کاربران حذف می‌شود، به صورت خودکار از Core RAG System نیز حذف می‌شود.

### پیاده‌سازی

#### 1. Signal Handler (`chat/signals.py`)

```python
@receiver(pre_delete, sender=Conversation)
def delete_conversation_from_rag_core(sender, instance, **kwargs):
    """حذف conversation از RAG Core قبل از حذف از دیتابیس"""
    if instance.rag_conversation_id:
        # تولید JWT token برای کاربر
        refresh = RefreshToken.for_user(instance.user)
        access_token = str(refresh.access_token)
        
        # حذف از Core RAG
        success = loop.run_until_complete(
            core_service.delete_conversation(
                conversation_id=instance.rag_conversation_id,
                token=access_token
            )
        )
```

#### 2. Core API Service (`chat/core_service.py`)

```python
async def delete_conversation(
    self,
    conversation_id: str,
    token: str,
) -> bool:
    """Delete a conversation from Core RAG system."""
    url = f"{self.base_url}/api/v1/users/conversations/{conversation_id}"
    
    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.delete(
            url,
            headers=self._get_headers(token),
        )
        
        if response.status_code == 200:
            logger.info(f"✅ Conversation {conversation_id} deleted from Core RAG")
            return True
        elif response.status_code == 404:
            logger.warning(f"⚠️ Conversation {conversation_id} not found in Core RAG")
            return True  # Consider it deleted if not found
        else:
            logger.error(f"❌ Failed to delete conversation {conversation_id}: {response.status_code}")
            return False
```

---

## 📡 Core API Endpoint

### DELETE /api/v1/users/conversations/{conversation_id}

**Headers:**
```http
Authorization: Bearer <JWT_TOKEN>
Content-Type: application/json
```

**Path Parameters:**
- `conversation_id` (string, UUID): شناسه گفتگو

**Response (Success - 200):**
```json
{
  "status": "success",
  "message": "Conversation deleted"
}
```

**Response (Error - 404):**
```json
{
  "detail": "Conversation not found"
}
```

---

## 🔐 امنیت

Core API به صورت خودکار بررسی می‌کند که:
- ✅ کاربر احراز هویت شده باشد (JWT Token)
- ✅ گفتگو متعلق به همان کاربر باشد
- ✅ گفتگو واقعاً وجود داشته باشد

اگر کاربر سعی کند گفتگوی کاربر دیگری را حذف کند، خطای **404 Not Found** دریافت می‌کند.

---

## 🗑️ رفتار Cascade Delete

وقتی گفتگو حذف می‌شود، به صورت خودکار:
- ✅ تمام messages مرتبط با آن گفتگو حذف می‌شوند (CASCADE)
- ✅ کش‌های مرتبط پاک می‌شوند
- ✅ آمار کاربر به‌روزرسانی می‌شود

---

## 🔄 جریان کامل حذف

```
1. کاربر در Frontend روی "حذف گفتگو" کلیک می‌کند
   ↓
2. Frontend درخواست DELETE به Backend می‌فرستد
   ↓
3. Backend conversation را از دیتابیس حذف می‌کند
   ↓
4. Signal `pre_delete` فعال می‌شود
   ↓
5. Signal درخواست DELETE به Core RAG می‌فرستد
   ↓
6. Core RAG گفتگو و تمام پیام‌های آن را حذف می‌کند
   ↓
7. Signal `post_delete` لاگ حذف را ثبت می‌کند
   ↓
8. Frontend لیست گفتگوها را به‌روزرسانی می‌کند
```

---

## 🧪 تست

برای تست کردن یکپارچه‌سازی:

```bash
# 1. ایجاد یک conversation
# 2. حذف آن از Frontend یا Django Admin
# 3. بررسی لاگ‌ها

docker-compose logs backend | grep "Conversation.*deleted"
```

خروجی مورد انتظار:
```
INFO: ✅ Conversation <uuid> deleted from Core RAG
INFO: Conversation <uuid> (Title) deleted by user email@example.com
```

---

## ⚠️ نکات مهم

### 1. خطا در Core API
اگر Core API در دسترس نباشد یا خطا دهد:
- ✅ حذف در Django ادامه پیدا می‌کند
- ⚠️ یک warning در لاگ ثبت می‌شود
- ❌ گفتگو در Core باقی می‌ماند (باید manual پاکسازی شود)

### 2. JWT Token
- Signal به صورت خودکار یک JWT token برای کاربر تولید می‌کند
- این token فقط برای این درخواست استفاده می‌شود
- Token از `rest_framework_simplejwt` تولید می‌شود

### 3. Async در Sync Context
- Signal ها در Django synchronous هستند
- ما از `asyncio.run_until_complete()` برای اجرای async call استفاده می‌کنیم
- این روش برای production مناسب است

---

## 📊 لاگ‌ها

### موفقیت‌آمیز
```
INFO: ✅ Conversation abc-123 deleted from Core RAG
INFO: Conversation abc-123 (My Chat) deleted by user test@example.com
```

### خطا در Core
```
ERROR: ❌ Failed to delete conversation abc-123: 500
WARNING: ⚠️ Failed to delete conversation abc-123 from RAG Core
INFO: Conversation abc-123 (My Chat) deleted by user test@example.com
```

### Not Found در Core
```
WARNING: ⚠️ Conversation abc-123 not found in Core RAG
INFO: Conversation abc-123 (My Chat) deleted by user test@example.com
```

---

## 🔧 تنظیمات

در `settings.py`:

```python
# Core RAG API Configuration
CORE_API_URL = env('CORE_API_URL', default='https://core.tejarat.chat')
CORE_API_KEY = env('CORE_API_KEY', default='')
```

---

## ✅ چک‌لیست

- [x] Signal برای `pre_delete` پیاده‌سازی شد
- [x] متد `delete_conversation` در `CoreAPIService` اضافه شد
- [x] JWT token برای احراز هویت تولید می‌شود
- [x] خطاها به درستی handle می‌شوند
- [x] لاگ‌های مناسب ثبت می‌شوند
- [x] حذف در Django حتی در صورت خطای Core ادامه پیدا می‌کند
- [x] Cascade delete برای messages کار می‌کند

---

**تاریخ آخرین به‌روزرسانی:** 2025-11-18
**نسخه:** 1.0
