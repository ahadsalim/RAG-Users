# 🔗 Core RAG API Integration

**تاریخ:** 17 نوامبر 2025  
**نسخه:** 1.0.0

---

## 📋 خلاصه

سیستم کاربران حالا برای پردازش سوالات و مدیریت مکالمات به **Core RAG API** متصل شده است.

---

## 🏗️ معماری

```
┌─────────────┐      WebSocket      ┌──────────────┐       HTTPS        ┌─────────────┐
│   Frontend  │ ←─────────────────→ │   Backend    │ ←────────────────→ │  Core RAG   │
│  (Next.js)  │                     │   (Django)   │                    │   (FastAPI) │
└─────────────┘                     └──────────────┘                    └─────────────┘
     ↓                                      ↓                                   ↓
  Browser                              Proxy Layer                         RAG Engine
```

### مسیر ارسال سوال:

1. **کاربر** سوال را در Frontend می‌نویسد
2. **Frontend** سوال را از طریق WebSocket به **Backend** می‌فرستد
3. **Backend** سوال را با JWT Token به **Core API** می‌فرستد
4. **Core RAG** پاسخ را به صورت streaming می‌فرستد
5. **Backend** chunks را به **Frontend** forward می‌کند
6. **Frontend** پاسخ را به صورت real-time نمایش می‌دهد

---

## 🔧 تغییرات انجام شده

### 1️⃣ Core API Service (`/srv/backend/chat/core_service.py`)

**ایجاد شده:** سرویس جدید برای ارتباط با Core API

**قابلیت‌ها:**
- ✅ ارسال سوال (با و بدون streaming)
- ✅ دریافت لیست مکالمات
- ✅ دریافت پیام‌های یک مکالمه
- ✅ حذف مکالمه
- ✅ ارسال بازخورد (feedback)
- ✅ دریافت پروفایل کاربر

**کلاس اصلی:**
```python
class CoreAPIService:
    def __init__(self):
        self.base_url = 'https://core.tejarat.chat'
        self.api_key = settings.CORE_API_KEY
        self.timeout = 120.0
```

**متدهای کلیدی:**
- `send_query()` - ارسال سوال ساده
- `send_query_stream()` - ارسال سوال با streaming
- `get_conversations()` - دریافت مکالمات
- `submit_feedback()` - ارسال بازخورد

---

### 2️⃣ WebSocket Consumer (`/srv/backend/chat/consumers.py`)

**تغییرات:**
- ✅ استفاده از `core_service` به جای `rag_client`
- ✅ تولید JWT Token برای احراز هویت با Core API
- ✅ پردازش streaming response از Core API
- ✅ ارسال feedback به Core API

**تغییر کلیدی:**
```python
# قبل:
async for chunk in rag_client.send_query_stream(...):
    ...

# بعد:
async for chunk in core_service.send_query_stream(
    query=query,
    token=self.jwt_token,
    conversation_id=conversation.rag_conversation_id,
    language='fa'
):
    ...
```

---

### 3️⃣ Settings (`/srv/backend/core/settings.py`)

**اضافه شده:**
```python
# Core RAG API Configuration
CORE_API_URL = config('CORE_API_URL', default='https://core.tejarat.chat')
CORE_API_KEY = config('CORE_API_KEY', default='')
```

---

### 4️⃣ Environment Variables (`/srv/deployment/.env`)

**اضافه شده:**
```env
CORE_API_URL=https://core.tejarat.chat
CORE_API_KEY=Cw02XlM2EZ1jsHNr/Suc20EdeP/iJXMVDXnMYucF0WbZ5dDaVheXJsWISNgPFUOP
```

---

## 🔐 احراز هویت

### JWT Token Flow:

1. **کاربر** login می‌کند و JWT token دریافت می‌کند
2. **Backend** همین token را برای Core API استفاده می‌کند
3. **Core API** کاربر را از روی token تشخیص می‌دهد

**تولید Token:**
```python
@database_sync_to_async
def get_jwt_token(self):
    token = AccessToken.for_user(self.user)
    return str(token)
```

---

## 📊 Core API Endpoints Used

### Query Processing:
- `POST /api/v1/query/` - ارسال سوال ساده
- `POST /api/v1/query/stream` - ارسال سوال با streaming ✅
- `POST /api/v1/query/feedback` - ارسال بازخورد

### User Management:
- `GET /api/v1/users/profile` - دریافت پروفایل
- `GET /api/v1/users/conversations` - لیست مکالمات
- `GET /api/v1/users/conversations/{id}/messages` - پیام‌های مکالمه
- `DELETE /api/v1/users/conversations/{id}` - حذف مکالمه
- `GET /api/v1/users/statistics` - آمار کاربر
- `POST /api/v1/users/clear-history` - پاک کردن تاریخچه

---

## 🎯 مزایا

### 1. **Centralized RAG Engine**
- تمام پردازش RAG در یک سیستم مرکزی
- بهینه‌سازی و کش مشترک
- مدیریت یکپارچه vector database (Qdrant)

### 2. **Real-time Streaming**
- پاسخ‌ها به صورت real-time به کاربر نمایش داده می‌شوند
- UX بهتر با نمایش تدریجی پاسخ
- کاهش perceived latency

### 3. **User Context Management**
- Core API مکالمات و تاریخچه را نگه می‌دارد
- Conversation ID برای context multi-turn
- User tier و محدودیت‌های روزانه

### 4. **Feedback Loop**
- ارسال بازخورد کاربران به Core
- بهبود مدل با استفاده از feedback

---

## 🔄 Data Flow

### ارسال سوال:

```
User Question
    ↓
WebSocket (Frontend → Backend)
    ↓
JWT Token Generation
    ↓
HTTPS POST to Core API
    ↓
RAG Processing (Core)
    ↓
Streaming Response
    ↓
WebSocket Forward (Backend → Frontend)
    ↓
Display to User
```

### دریافت مکالمات:

```
User Request
    ↓
REST API (Frontend → Backend)
    ↓
HTTPS GET to Core API
    ↓
Core Database Query
    ↓
JSON Response
    ↓
Display in Sidebar
```

---

## 🐛 Troubleshooting

### خطا: "Connection refused"
**علت:** Core API در دسترس نیست  
**راه‌حل:** بررسی `CORE_API_URL` و اتصال شبکه

### خطا: "Unauthorized"
**علت:** JWT token نامعتبر یا منقضی شده  
**راه‌حل:** بررسی `CORE_API_KEY` و تنظیمات JWT

### خطا: "Timeout"
**علت:** سوال خیلی طولانی یا Core مشغول است  
**راه‌حل:** افزایش `timeout` در `core_service.py`

---

## 📝 لاگ‌ها

### Backend logs:
```bash
docker-compose logs backend --tail 50 -f
```

### Core API logs:
```bash
# در سرور Core
pm2 logs core
```

---

## 🔗 منابع

- Core API Docs: https://core.tejarat.chat/docs
- OpenAPI Schema: https://core.tejarat.chat/openapi.json

---

## ✅ چک لیست تست

- [x] ارسال سوال و دریافت پاسخ streaming
- [ ] دریافت لیست مکالمات
- [ ] حذف مکالمه
- [ ] ارسال بازخورد
- [ ] دریافت آمار کاربر
- [ ] Multi-turn conversation با context

---

**✅ Integration کامل شد - 17 نوامبر 2025**
