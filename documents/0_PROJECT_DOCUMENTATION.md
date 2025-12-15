# 📚 مستندات جامع پروژه تجارت چت

---

## 📋 فهرست مطالب

1. [معرفی پروژه](#معرفی-پروژه)
2. [معماری سیستم](#معماری-سیستم)
3. [ساختار پروژه](#ساختار-پروژه)
4. [نصب و راه‌اندازی](#نصب-و-راه‌اندازی)
5. [تنظیمات Environment](#تنظیمات-environment)
6. [سیستم احراز هویت](#سیستم-احراز-هویت)
7. [یکپارچه‌سازی با Core RAG](#یکپارچه‌سازی-با-core-rag)
8. [API Documentation](#api-documentation)
9. [مدیریت سیستم](#مدیریت-سیستم)
10. [عیب‌یابی](#عیب‌یابی)
11. [امنیت](#امنیت)

---

## 🎯 معرفی پروژه

**تجارت چت** یک پلتفرم هوشمند کسب و کار است که با استفاده از هوش مصنوعی و RAG (Retrieval-Augmented Generation)، خدمات چت‌بات پیشرفته برای کسب‌وکارها ارائه می‌دهد.

### ویژگی‌های اصلی:
- ✅ سیستم احراز هویت چندمرحله‌ای (OTP، Email Verification)
- ✅ پنل مدیریت کاربران (حقیقی، حقوقی، تجاری)
- ✅ یکپارچه‌سازی با Core API (RAG System)
- ✅ سیستم پرداخت (Zarinpal، Stripe)
- ✅ ارسال SMS (Kavenegar)
- ✅ اتصال به Bale Messenger
- ✅ WebSocket برای چت real-time
- ✅ Celery برای task های async
- ✅ Multi-language support (فارسی، انگلیسی)

---

## 🏗️ معماری سیستم

### Technology Stack

**Backend:**
- Django 5.1 + Django REST Framework
- PostgreSQL 16
- Redis 7 (Cache & Session)
- RabbitMQ 3 (Message Broker)
- Celery (Task Queue)
- Daphne (ASGI Server)

**Frontend:**
- Next.js 14 (App Router)
- React 18
- TypeScript
- Tailwind CSS
- Zustand (State Management)
- Lucide Icons

**Infrastructure:**
- Docker & Docker Compose
- Nginx Proxy Manager
- Let's Encrypt SSL
- MinIO (Object Storage)

### نمودار معماری

```
┌─────────────────────────────────────────────────────────────┐
│                        Internet                              │
└─────────────────────────┬───────────────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────────────┐
│              Nginx Proxy Manager (SSL)                       │
│         tejarat.chat    admin.tejarat.chat                   │
└──────────┬─────────────────────────────────┬────────────────┘
           │                                 │
┌──────────▼──────────┐         ┌───────────▼─────────────────┐
│   Frontend (3000)   │         │      Backend (8000)          │
│     Next.js 14      │         │   Django + DRF + Daphne      │
└─────────────────────┘         └──────────────┬──────────────┘
                                               │
                    ┌──────────────────────────┼──────────────────────────┐
                    │                          │                          │
           ┌────────▼────────┐      ┌──────────▼──────────┐    ┌─────────▼─────────┐
           │  PostgreSQL 16  │      │     Redis 7         │    │   RabbitMQ 3      │
           │   (Database)    │      │  (Cache/Session)    │    │ (Message Broker)  │
           └─────────────────┘      └─────────────────────┘    └─────────┬─────────┘
                                                                         │
                                                               ┌─────────▼─────────┐
                                                               │   Celery Worker   │
                                                               │  (Async Tasks)    │
                                                               └───────────────────┘
                                               │
                                    ┌──────────▼──────────┐
                                    │    Core RAG API     │
                                    │ core.tejarat.chat   │
                                    └─────────────────────┘
```

---

## 📁 ساختار پروژه

```
/srv/
├── backend/                    # Django Backend
│   ├── accounts/               # User management & Auth
│   │   ├── models.py           # User, OTP models
│   │   ├── views.py            # Auth views
│   │   ├── serializers.py      # DRF serializers
│   │   └── utils.py            # SMS, Email utilities
│   ├── chat/                   # Chat system
│   │   ├── models.py           # Conversation, Message
│   │   ├── views.py            # Query views
│   │   ├── core_service.py     # Core RAG integration
│   │   ├── upload_views.py     # File upload
│   │   └── signals.py          # Delete signals
│   ├── core/                   # Core settings
│   │   ├── settings.py         # Django settings
│   │   ├── urls.py             # URL routing
│   │   └── storage.py          # MinIO service
│   ├── payments/               # Payment integration
│   │   ├── models.py           # Transaction model
│   │   └── views.py            # Payment views
│   ├── subscriptions/          # Subscription system
│   │   ├── models.py           # Plan, Subscription
│   │   └── usage.py            # Usage tracking
│   └── templates/              # Email templates
├── frontend/                   # Next.js Frontend
│   └── src/
│       ├── app/                # Pages (App Router)
│       │   ├── auth/           # Login, Register
│       │   ├── chat/           # Chat page
│       │   └── checkout/       # Payment checkout
│       ├── components/         # React components
│       ├── lib/                # Utilities
│       └── store/              # Zustand stores
├── deployment/                 # Docker configs
│   ├── docker-compose.yml
│   ├── Dockerfile.backend
│   ├── Dockerfile.frontend
│   ├── manager.sh              # Management script
│   └── .env                    # Environment variables
└── documents/                  # Documentation
```

---

## 🚀 نصب و راه‌اندازی

### پیش‌نیازها

**سرور:**
- OS: Ubuntu 20.04+ / Debian 11+
- RAM: حداقل 4GB (توصیه: 8GB+)
- Storage: حداقل 50GB
- CPU: 2 Core+ (توصیه: 4 Core+)

**نرم‌افزارها:**
```bash
# نصب Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# نصب Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

### مراحل نصب

#### 1. Clone Repository
```bash
cd /srv
git clone <repository-url> .
```

#### 2. تنظیم Environment Variables
```bash
cd /srv/deployment
cp .env.example .env
nano .env
```

#### 3. راه‌اندازی Docker
```bash
docker-compose up -d
```

#### 4. اجرای Migrations
```bash
./manager.sh migrate
```

#### 5. ایجاد Superuser
```bash
./manager.sh
# انتخاب گزینه 8
```

---

## ⚙️ تنظیمات Environment

### متغیرهای اصلی

```env
# Database
DB_NAME=tejarat_db
DB_USER=tejarat_user
DB_PASSWORD=<STRONG_PASSWORD>

# Django
SECRET_KEY=<DJANGO_SECRET_KEY>
DEBUG=false
ALLOWED_HOSTS=tejarat.chat,admin.tejarat.chat

# Email (Gmail SMTP)
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=<APP_PASSWORD>
DEFAULT_FROM_EMAIL=noreply@tejarat.chat

# SMS (Kavenegar)
KAVENEGAR_API_KEY=<YOUR_API_KEY>
KAVENEGAR_SENDER=<YOUR_SENDER_NUMBER>

# Core RAG API
RAG_CORE_BASE_URL=https://core.tejarat.chat
RAG_CORE_API_KEY=<YOUR_API_KEY>

# MinIO
MINIO_ENDPOINT=storage.tejarat.chat:9000
MINIO_ACCESS_KEY=<ACCESS_KEY>
MINIO_SECRET_KEY=<SECRET_KEY>
MINIO_BUCKET_NAME=shared-storage
MINIO_USE_SSL=true

# Frontend
FRONTEND_URL=https://tejarat.chat
NEXT_PUBLIC_API_URL=https://admin.tejarat.chat
```

---

## 🔐 سیستم احراز هویت

### انواع کاربران

| نوع | روش احراز هویت | ویژگی‌ها |
|-----|----------------|----------|
| حقیقی (Individual) | موبایل + OTP | شماره موبایل + رمز عبور |
| حقوقی (Legal) | ایمیل + تایید | ایمیل + شماره تماس |
| تجاری (Business) | ایمیل + تایید | مشابه حقوقی با امکانات بیشتر |

### فرآیند ثبت‌نام

**کاربر حقیقی:**
```
ثبت‌نام → OTP (SMS) → فعال‌سازی → ورود
```

**کاربر حقوقی:**
```
ثبت‌نام → ایمیل تایید → کلیک روی لینک → فعال‌سازی → ورود
```

### ویژگی‌های امنیتی
- ✅ JWT Token Authentication
- ✅ Rate Limiting (OTP، Login)
- ✅ Password Validators (Persian messages)
- ✅ Session Management
- ✅ Audit Logging
- ✅ CORS Protection

---

## 🔗 یکپارچه‌سازی با Core RAG

### ارسال Query

**Endpoint:** `POST https://core.tejarat.chat/api/v1/query/`

```json
{
  "query": "متن سوال",
  "language": "fa",
  "conversation_id": "uuid",
  "file_attachments": [
    {
      "filename": "document.pdf",
      "minio_url": "temp_uploads/user/file.pdf",
      "file_type": "application/pdf"
    }
  ]
}
```

### حذف خودکار Conversation

وقتی یک Conversation در سیستم کاربران حذف می‌شود، به صورت خودکار از Core RAG نیز حذف می‌شود:

```python
@receiver(pre_delete, sender=Conversation)
def delete_conversation_from_rag_core(sender, instance, **kwargs):
    if instance.rag_conversation_id:
        core_service.delete_conversation(
            conversation_id=instance.rag_conversation_id,
            token=access_token
        )
```

---

## 📡 API Documentation

### Base URLs
- **Production:** `https://admin.tejarat.chat/api/v1/`
- **Development:** `http://localhost:8000/api/v1/`

### Authentication Endpoints

| Method | Endpoint | توضیح |
|--------|----------|-------|
| POST | `/auth/register/` | ثبت‌نام |
| POST | `/auth/login/` | ورود |
| POST | `/auth/otp/request/` | درخواست OTP |
| POST | `/auth/otp/verify/` | تایید OTP |
| POST | `/auth/forgot-password/` | فراموشی رمز |
| POST | `/auth/reset-password/` | بازنشانی رمز |

### Chat Endpoints

| Method | Endpoint | توضیح |
|--------|----------|-------|
| GET | `/chat/conversations/` | لیست مکالمات |
| POST | `/chat/query/` | ارسال سوال |
| POST | `/chat/upload/` | آپلود فایل |
| DELETE | `/chat/conversations/{id}/` | حذف مکالمه |

### Subscription Endpoints

| Method | Endpoint | توضیح |
|--------|----------|-------|
| GET | `/subscriptions/plans/` | لیست پلن‌ها |
| GET | `/subscriptions/usage/stats/` | آمار مصرف |
| POST | `/payments/create/` | ایجاد پرداخت |

---

## 🔧 مدیریت سیستم

### استفاده از Manager Script

```bash
cd /srv/deployment
./manager.sh
```

**دستورات:**
```bash
./manager.sh start          # شروع سرویس‌ها
./manager.sh stop           # توقف سرویس‌ها
./manager.sh restart        # ری‌استارت
./manager.sh status         # وضعیت
./manager.sh logs           # لاگ‌ها
./manager.sh migrate        # اجرای migrations
./manager.sh cache          # پاک کردن cache
./manager.sh rebuild-frontend  # بازسازی frontend
./manager.sh health         # بررسی سلامت
```

### مانیتورینگ

```bash
# وضعیت Containers
docker ps
docker-compose ps

# لاگ‌ها
docker-compose logs -f backend
docker-compose logs -f frontend

# منابع
docker stats
```

---

## 🐛 عیب‌یابی

### مشکلات رایج

#### 1. Backend شروع نمی‌شود
```bash
docker-compose logs backend
docker-compose restart backend
```

#### 2. خطای CORS
- CORS فقط در Django تنظیم شود
- از NPM حذف کنید

#### 3. Email ارسال نمی‌شود
```bash
docker exec app_backend python manage.py shell
>>> from django.core.mail import send_mail
>>> send_mail('Test', 'Test', 'from@example.com', ['to@example.com'])
```

#### 4. OTP ارسال نمی‌شود
```bash
./manager.sh cache  # پاک کردن rate limit
```

#### 5. خطای 502 از Core RAG
- بررسی وضعیت سرویس Core
- بررسی لاگ‌ها

---

## 🔒 امنیت

### Checklist

- [ ] `DEBUG=false` در production
- [ ] `SECRET_KEY` تغییر کرده
- [ ] رمزهای قوی برای database
- [ ] SSL فعال است
- [ ] Firewall تنظیم شده (فقط 80, 443, 22)
- [ ] Backup منظم
- [ ] لاگ‌ها مانیتور می‌شوند

### Firewall

```bash
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
```

### Backup

```bash
# Database
docker-compose exec postgres pg_dump -U tejarat_user tejarat_db > backup.sql

# Restore
docker-compose exec -T postgres psql -U tejarat_user tejarat_db < backup.sql
```

---

## 📞 پشتیبانی

- **Website:** https://tejarat.chat
- **Email:** info@tejarat.chat

---

**نسخه:** 1.0.0  
**آخرین به‌روزرسانی:** 2025-12-15
