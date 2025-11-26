# سامانه هوشمند کسب و کار تجارت چت

## 📋 معرفی پروژه

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

### Stack Technology:

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

### ساختار پروژه:

```
/srv/
├── backend/              # Django Backend
│   ├── accounts/         # User management & Auth
│   ├── chat/             # Chat system
│   ├── core/             # Core settings
│   ├── payments/         # Payment integration
│   └── templates/        # Email templates
├── frontend/             # Next.js Frontend
│   └── src/
│       ├── app/          # Pages (App Router)
│       ├── components/   # React components
│       ├── lib/          # Utilities
│       └── store/        # Zustand stores
├── deployment/           # Docker configs
│   ├── docker-compose.yml
│   ├── Dockerfile.backend
│   ├── Dockerfile.frontend
│   ├── manager.sh        # Management script
│   └── .env              # Environment variables
└── documents/            # Documentation
```

---

## 🔐 سیستم احراز هویت

### انواع کاربران:
1. **حقیقی (Individual):** شماره موبایل + رمز عبور
2. **حقوقی (Legal):** ایمیل + شماره تماس + تایید ایمیل
3. **تجاری (Business):** مشابه حقوقی با امکانات بیشتر

### فرآیند ثبت‌نام:

**کاربر حقیقی:**
```
ثبت‌نام → OTP (SMS) → فعال‌سازی → ورود
```

**کاربر حقوقی:**
```
ثبت‌نام → ایمیل تایید → کلیک روی لینک → فعال‌سازی → ورود
```

### ویژگی‌های امنیتی:
- ✅ JWT Token Authentication
- ✅ Rate Limiting (OTP، Login)
- ✅ Password Validators (Persian messages)
- ✅ Session Management
- ✅ Audit Logging
- ✅ CORS Protection

---

## 🚀 نصب و راه‌اندازی

### پیش‌نیازها:
```bash
- Docker & Docker Compose
- Git
- Domain با SSL (برای production)
```

### مراحل نصب:

#### 1. Clone Repository:
```bash
cd /srv
git clone <repository-url> .
```

#### 2. تنظیم Environment Variables:
```bash
cd /srv/deployment
cp .env.example .env
nano .env
```

**متغیرهای مهم:**
```env
# Database
DB_NAME=app_db
DB_USER=app_user
DB_PASSWORD=<strong-password>

# Django
SECRET_KEY=<django-secret-key>
DEBUG=false
ALLOWED_HOSTS=tejarat.chat,admin.tejarat.chat

# Email (Gmail SMTP)
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=<app-password>
DEFAULT_FROM_EMAIL=noreply@tejarat.chat

# SMS (Kavenegar)
KAVENEGAR_API_KEY=<your-api-key>
KAVENEGAR_SENDER=<your-sender-number>

# Core API
CORE_API_URL=https://core.tejarat.chat
CORE_API_KEY=<your-api-key>

# Frontend
FRONTEND_URL=https://tejarat.chat
NEXT_PUBLIC_API_URL=https://admin.tejarat.chat
```

#### 3. راه‌اندازی با Docker:
```bash
cd /srv/deployment
docker-compose up -d
```

#### 4. اجرای Migrations:
```bash
./manager.sh migrate
```

#### 5. ایجاد Superuser:
```bash
./manager.sh
# انتخاب گزینه 8
```

#### 6. تنظیم Nginx Proxy Manager:
مراحل کامل در فایل `INSTALLATION_GUIDE.md`

---

## 📊 مدیریت سیستم

### استفاده از Manager Script:

**Interactive Mode:**
```bash
cd /srv/deployment
./manager.sh
```

**Command Line Mode:**
```bash
./manager.sh start          # شروع همه سرویس‌ها
./manager.sh stop           # توقف همه سرویس‌ها
./manager.sh restart        # ری‌استارت همه سرویس‌ها
./manager.sh status         # وضعیت سرویس‌ها
./manager.sh logs           # مشاهده لاگ‌ها
./manager.sh migrate        # اجرای migrations
./manager.sh cache          # پاک کردن cache
./manager.sh rebuild-frontend  # بازسازی frontend
./manager.sh health         # بررسی سلامت سیستم
```

### مانیتورینگ:

**بررسی وضعیت Containers:**
```bash
docker ps
docker-compose ps
```

**مشاهده لاگ‌ها:**
```bash
docker-compose logs -f backend
docker-compose logs -f frontend
docker-compose logs -f app_npm
```

**بررسی منابع:**
```bash
docker stats
```

---

## 🔧 عیب‌یابی

### مشکلات رایج:

#### 1. Backend شروع نمی‌شود:
```bash
# بررسی لاگ
docker-compose logs backend

# بررسی database
docker-compose exec postgres pg_isready

# ری‌استارت
docker-compose restart backend
```

#### 2. Frontend خطای 404 می‌دهد:
```bash
# پاک کردن cache
./manager.sh rebuild-frontend

# یا دستی:
rm -rf /srv/frontend/.next
docker-compose restart frontend
```

#### 3. OTP ارسال نمی‌شود:
```bash
# بررسی Kavenegar API Key
# پاک کردن rate limit cache
./manager.sh cache
```

#### 4. Email ارسال نمی‌شود:
```bash
# بررسی Gmail App Password
# تست ارسال:
docker exec app_backend python manage.py shell
>>> from django.core.mail import send_mail
>>> send_mail('Test', 'Test', 'from@example.com', ['to@example.com'])
```

#### 5. NPM کار نمی‌کند:
```bash
# بررسی لاگ
docker logs app_npm

# ری‌استارت
docker-compose restart nginx_proxy_manager

# دسترسی به Admin Panel
http://YOUR_IP:81
```

---

## 📚 API Documentation

### Base URLs:
- **Production:** `https://admin.tejarat.chat/api/v1/`
- **Development:** `http://localhost:8000/api/v1/`

### Authentication Endpoints:

**Register:**
```http
POST /api/v1/auth/register/
Content-Type: application/json

{
  "phone_number": "09123456789",
  "password": "SecurePass123",
  "password_confirm": "SecurePass123",
  "user_type": "individual"
}
```

**Login:**
```http
POST /api/v1/auth/login/
Content-Type: application/json

{
  "phone_number": "09123456789",
  "password": "SecurePass123"
}
```

**OTP Request:**
```http
POST /api/v1/auth/otp/request/
Content-Type: application/json

{
  "phone_number": "09123456789"
}
```

**OTP Verify:**
```http
POST /api/v1/auth/otp/verify/
Content-Type: application/json

{
  "phone_number": "09123456789",
  "otp_code": "123456"
}
```

### Chat Endpoints:

**List Conversations:**
```http
GET /api/v1/chat/conversations/
Authorization: Bearer <access_token>
```

**Send Message:**
```http
POST /api/v1/chat/conversations/{id}/messages/
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "content": "سلام"
}
```

---

## 🔒 امنیت

### Best Practices:
1. ✅ همیشه از HTTPS استفاده کنید
2. ✅ SECRET_KEY را تغییر دهید
3. ✅ DEBUG=false در production
4. ✅ از App Password برای Gmail استفاده کنید
5. ✅ Rate Limiting را فعال نگه دارید
6. ✅ Backup منظم از database
7. ✅ لاگ‌ها را مانیتور کنید
8. ✅ به‌روزرسانی منظم Docker images

### Backup:

**Database Backup:**
```bash
docker-compose exec postgres pg_dump -U app_user app_db > backup_$(date +%Y%m%d).sql
```

**Restore:**
```bash
docker-compose exec -T postgres psql -U app_user app_db < backup_20250126.sql
```

---

## 📞 پشتیبانی

- **Website:** https://tejarat.chat
- **Email:** info@tejarat.chat
- **Documentation:** /srv/documents/

---

## 📝 License

Proprietary - All rights reserved

---

**نسخه:** 1.0.0  
**آخرین بروزرسانی:** 26 نوامبر 2025
