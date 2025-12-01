# 🚀 پیاده‌سازی Streaming در چت

## 📋 خلاصه

سیستم چت حالا از **streaming responses** پشتیبانی می‌کند که به کاربر اجازه می‌دهد پاسخ دستیار هوشمند را **کاراکتر به کاراکتر** و به صورت real-time ببیند.

---

## ✨ ویژگی‌ها

### 1. **نمایش Real-time**
- پاسخ به صورت کاراکتر به کاراکتر نمایش داده می‌شود
- تجربه کاربری مشابه ChatGPT و Claude
- کاهش زمان انتظار ظاهری

### 2. **Fallback خودکار**
- اگر streaming موجود نباشد (404)، به حالت عادی برمی‌گردد
- بدون نیاز به دخالت کاربر
- سازگاری کامل با نسخه‌های قدیمی

### 3. **Server-Sent Events (SSE)**
- استفاده از استاندارد SSE
- پشتیبانی از انواع event: `start`, `chunk`, `sources`, `end`, `error`
- مدیریت خطا و reconnection

---

## 🏗️ معماری

### Backend (Django)

```
┌─────────────────┐
│  StreamingQuery │
│      View       │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  core_service   │
│ send_query_     │
│    stream()     │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   RAG Core API  │
│  /query/stream  │
└─────────────────┘
```

**فایل‌های کلیدی:**
- `/srv/backend/chat/views.py` - `StreamingQueryView`
- `/srv/backend/chat/core_service.py` - `send_query_stream()`
- `/srv/backend/chat/urls.py` - route: `/api/v1/chat/query/stream/`

### Frontend (React + TypeScript)

```
┌─────────────────┐
│   ChatPage      │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  useChatStore   │
│ sendMessage     │
│   Streaming()   │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Fetch API +    │
│  SSE Parser     │
└─────────────────┘
```

**فایل‌های کلیدی:**
- `/srv/frontend/src/store/chat.ts` - `sendMessageStreaming()`
- `/srv/frontend/src/app/chat/page.tsx` - `handleSendMessage()`

---

## 🔧 نحوه کار

### 1. **ارسال درخواست**

```typescript
const response = await fetch('/api/v1/chat/query/stream/', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    query: 'سوال کاربر',
    conversation_id: 'uuid',
  }),
})
```

### 2. **دریافت Stream**

```typescript
const reader = response.body?.getReader()
const decoder = new TextDecoder()

while (true) {
  const { done, value } = await reader.read()
  if (done) break
  
  const chunk = decoder.decode(value)
  // پردازش SSE events
}
```

### 3. **پردازش Events**

#### Event: `start`
```json
{
  "type": "start",
  "conversation_id": "uuid",
  "message_id": "uuid"
}
```

#### Event: `chunk`
```json
{
  "type": "chunk",
  "content": "متن پاسخ..."
}
```

#### Event: `sources`
```json
{
  "type": "sources",
  "sources": [...]
}
```

#### Event: `end`
```json
{
  "type": "end",
  "metadata": {
    "tokens": 150,
    "processing_time_ms": 2500,
    "model_used": "gpt-4",
    "cached": false
  }
}
```

#### Event: `error`
```json
{
  "type": "error",
  "error": "خطا در پردازش"
}
```

---

## 📊 وضعیت فعلی

### ✅ **آماده در Backend**
- `StreamingQueryView` پیاده‌سازی شده
- `send_query_stream()` آماده
- URL routing فعال

### ✅ **آماده در Frontend**
- `sendMessageStreaming()` پیاده‌سازی شده
- SSE parser آماده
- Fallback mechanism فعال

### ⚠️ **RAG Core**
- **وضعیت:** Streaming هنوز فعال نیست (404)
- **Endpoint:** `https://core.tejarat.chat/api/v1/query/stream`
- **Fallback:** به حالت عادی برمی‌گردد

---

## 🧪 تست

### تست Manual

```bash
# تست streaming endpoint
curl -X POST https://core.tejarat.chat/api/v1/query/stream \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"query": "سلام", "language": "fa"}'
```

### تست Automated

```bash
# اجرای تست سیستم
docker exec app_backend python3 /app/tests/integration/test_system.py
```

**نتیجه فعلی:**
- ✅ MinIO: موفق
- ✅ RAG Normal: موفق
- ❌ RAG Streaming: 404 (منتظر فعال‌سازی)

---

## 🚦 فعال‌سازی

### زمانی که RAG Core streaming را فعال کند:

1. **هیچ تغییری در کد لازم نیست** ✨
2. Fallback خودکار غیرفعال می‌شود
3. Streaming به صورت خودکار شروع می‌کند

### بررسی وضعیت:

```bash
# چک کردن که streaming فعال شده یا نه
docker exec app_backend python3 /app/tests/integration/test_system.py | grep "RAG Streaming"
```

اگر خروجی `✅ موفق` بود، streaming فعال است!

---

## 🎯 مزایا

### برای کاربر:
- ⚡ پاسخ سریع‌تر (ظاهری)
- 👁️ مشاهده پیشرفت real-time
- 🎨 تجربه کاربری بهتر

### برای سیستم:
- 📉 کاهش timeout issues
- 🔄 بهبود handling پاسخ‌های طولانی
- 💾 مدیریت بهتر منابع

---

## 📚 منابع

- [Server-Sent Events (MDN)](https://developer.mozilla.org/en-US/docs/Web/API/Server-sent_events)
- [Fetch API Streams](https://developer.mozilla.org/en-US/docs/Web/API/Streams_API)
- [Django StreamingHttpResponse](https://docs.djangoproject.com/en/stable/ref/request-response/#streaminghttpresponse)

---

**آخرین به‌روزرسانی:** 2025-12-01  
**وضعیت:** ✅ آماده (منتظر فعال‌سازی RAG Core)
