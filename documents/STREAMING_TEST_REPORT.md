# گزارش تست Streaming RAG Core API

تاریخ: 2025-11-30
تست شده توسط: Cascade AI

## 📊 نتایج تست

### ✅ تست 1: حالت عادی (Non-Streaming)

**URL:** `https://core.tejarat.chat/api/v1/query/`

**نتیجه:** ✅ موفق

**جزئیات:**
- Status Code: 200 OK
- زمان پاسخ: 3.47 ثانیه
- پاسخ دریافت شد: "سلام! من خوبم، مرسی که پرسیدی. شما چطورید؟"
- طول پاسخ: 42 کاراکتر

**نتیجه‌گیری:** حالت عادی کاملاً کار می‌کند ✅

---

### ❌ تست 2: حالت Streaming

**URL تست شده:**
1. `https://core.tejarat.chat/api/v1/query/stream/` → 307 Redirect
2. `https://core.tejarat.chat/api/v1/query/stream` → 500 Internal Server Error

**خطای دریافتی:**
```json
{
  "detail": "name 'select' is not defined",
  "type": "NameError",
  "path": "/api/v1/query/stream"
}
```

**تحلیل:**
- Endpoint streaming پیدا شد ✅
- سیستم مرکزی یک bug دارد: `NameError: name 'select' is not defined` ❌
- احتمالاً یک import گم شده یا تابع تعریف نشده

**نتیجه‌گیری:** Streaming endpoint موجود است ولی bug دارد ❌

---

## 🔧 وضعیت Backend ما

### ✅ آماده برای Streaming

کد backend ما برای streaming کاملاً آماده است:

1. **`/srv/backend/chat/core_service.py`:**
   - متد `send_query_stream()` موجود است (خطوط 84-142)
   - از `httpx.AsyncClient.stream()` استفاده می‌کند
   - Error handling کامل دارد

2. **`/srv/backend/chat/views.py`:**
   - `StreamQueryView` موجود است (خطوط 320-500)
   - `generate_stream()` async generator آماده است
   - Server-Sent Events (SSE) پیاده‌سازی شده

3. **URL Pattern:**
   - `/api/v1/chat/query/stream/` آماده است
   - فقط باید uncomment شود

---

## 📋 اقدامات لازم

### برای تیم سیستم مرکزی (RAG Core):

**Bug Report:**
```
Title: NameError در streaming endpoint

URL: https://core.tejarat.chat/api/v1/query/stream

Error:
{
  "detail": "name 'select' is not defined",
  "type": "NameError",
  "path": "/api/v1/query/stream"
}

Steps to reproduce:
1. POST request به /api/v1/query/stream
2. با Authorization header و valid JWT token
3. Payload: {"query": "سلام", "language": "fa"}

Expected: Streaming response
Actual: 500 Internal Server Error

احتمالاً یک import گم شده:
- از asyncio import select
- یا از selectors import select
```

### برای ما (بعد از fix سیستم مرکزی):

1. **Uncomment streaming URL در `urls.py`:**
   ```python
   path('query/stream/', views.StreamQueryView.as_view(), name='stream-query'),
   ```

2. **تست streaming endpoint:**
   ```bash
   curl -X POST https://your-domain.com/api/v1/chat/query/stream/ \
     -H "Authorization: Bearer YOUR_TOKEN" \
     -H "Content-Type: application/json" \
     -d '{"query": "سلام"}'
   ```

3. **پیاده‌سازی frontend:**
   - استفاده از `EventSource` یا `fetch` با `ReadableStream`
   - نمایش کاراکتر به کاراکتر
   - کد نمونه در `/srv/backend/chat/streaming_views.py` موجود است

---

## 🎯 خلاصه

| مورد | وضعیت | توضیحات |
|------|-------|---------|
| **حالت عادی** | ✅ کار می‌کند | پاسخ یکجا برگردانده می‌شود |
| **Streaming Endpoint** | ✅ موجود است | `/api/v1/query/stream` |
| **Streaming عملکرد** | ❌ Bug دارد | `NameError: name 'select' is not defined` |
| **Backend ما** | ✅ آماده است | کد streaming کامل پیاده‌سازی شده |
| **Frontend ما** | ⏳ منتظر | بعد از fix سیستم مرکزی |

---

## 📞 اقدام بعدی

1. **فوری:** گزارش bug به تیم سیستم مرکزی
2. **بعد از fix:** تست مجدد streaming
3. **سپس:** فعال‌سازی streaming در backend و frontend ما

---

**تاریخ تست:** 2025-11-30 17:28 UTC
**تست شده توسط:** Cascade AI Assistant
**محیط:** Production (core.tejarat.chat)
