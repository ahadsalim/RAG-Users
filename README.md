# پلتفرم مشاوره هوشمند حقوقی 🚀

سیستم مشاوره حقوقی و کسب‌وکار مبتنی بر هوش مصنوعی

## 🌟 ویژگی‌ها

### Backend (Django/DRF)
- ✅ **احراز هویت کامل**: JWT، 2FA، OAuth
- ✅ **اتصال به RAG Core**: API کامل برای سیستم مرکزی
- ✅ **WebSocket**: چت real-time با Django Channels
- ✅ **مدیریت کاربران**: پروفایل، سازمان‌ها، نقش‌ها
- ✅ **Audit Log**: ردیابی تمام فعالیت‌ها
- 🚧 **پرداخت**: زرین‌پال، بانک‌ها، رمزارز
- 🚧 **اشتراک**: پلن‌ها و محدودیت‌ها
- 🚧 **بازارچه مشاوران**
- 🚧 **اعلان‌ها**: ایمیل، SMS، Push

### Frontend (Next.js 14)
- ✅ **UI شبیه ChatGPT**: طراحی مدرن و کاربرپسند
- ✅ **Streaming Response**: نمایش تدریجی پاسخ
- ✅ **Dark/Light Mode**: تم تاریک و روشن
- ✅ **RTL Support**: پشتیبانی کامل از زبان فارسی
- ✅ **Responsive**: سازگار با تمام دستگاه‌ها
- ✅ **WebSocket**: ارتباط real-time
- ✅ **State Management**: با Zustand

## 📁 ساختار پروژه

```
/srv/
├── backend/              # Django Backend
│   ├── core/            # تنظیمات اصلی
│   ├── accounts/        # احراز هویت و کاربران
│   ├── chat/            # ماژول چت و RAG
│   ├── subscriptions/   # مدیریت اشتراک
│   ├── payments/        # سیستم پرداخت
│   ├── consultants/     # بازارچه مشاوران
│   ├── notifications/   # اعلان‌ها
│   └── analytics/       # گزارش‌گیری
│
├── frontend/            # Next.js Frontend
│   ├── src/
│   │   ├── app/        # صفحات (App Router)
│   │   ├── components/ # کامپوننت‌ها
│   │   ├── store/      # State Management
│   │   ├── hooks/      # Custom Hooks
│   │   ├── types/      # TypeScript Types
│   │   └── utils/      # توابع کمکی
│   │
│   └── public/         # فایل‌های استاتیک
│
├── deployment/         # Docker & Scripts
│   ├── docker-compose.yml
│   ├── Dockerfile.backend
│   ├── Dockerfile.frontend
│   ├── nginx.conf
│   ├── start.sh       # اسکریپت نصب خودکار
│   └── .env           # تنظیمات محیطی
│
└── docs/              # مستندات
```

## 🚀 راه‌اندازی سریع

### روش 1: اسکریپت خودکار (توصیه می‌شود)

```bash
# اجرای اسکریپت نصب
cd /srv/deployment
sudo ./start.sh
```

این اسکریپت به صورت خودکار:
- Docker و Docker Compose را نصب می‌کند
- تمام dependencies را نصب می‌کند
- کانتینرها را build و اجرا می‌کند
- دیتابیس را migrate می‌کند
- Superuser ایجاد می‌کند

### روش 2: Docker Compose دستی

```bash
# تنظیم متغیرهای محیطی
cp /srv/deployment/.env.example /srv/deployment/.env
# ویرایش .env و وارد کردن مقادیر واقعی

# اجرای کانتینرها
cd /srv/deployment
docker-compose up -d

# اجرای migrations
docker-compose exec backend python manage.py migrate

# ایجاد superuser
docker-compose exec backend python manage.py createsuperuser
```

## 🔑 دسترسی به سیستم

پس از راه‌اندازی:

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000/api
- **Django Admin**: http://localhost:8000/admin
- **API Documentation**: http://localhost:8000/api/docs
- **RabbitMQ Management**: http://localhost:15672

### اطلاعات ورود پیش‌فرض:
- **Username**: admin
- **Password**: Admin@123456

## 🛠️ تکنولوژی‌ها

### Backend
- Python 3.12
- Django 5.2
- Django REST Framework
- Django Channels (WebSocket)
- PostgreSQL
- Redis
- Celery + RabbitMQ
- JWT Authentication

### Frontend
- Next.js 14 (App Router)
- React 18
- TypeScript
- Tailwind CSS
- Zustand (State Management)
- React Query
- Socket.io Client

### DevOps
- Docker & Docker Compose
- Nginx (Reverse Proxy)
- GitHub Actions (CI/CD)

## 📝 تنظیمات محیطی

فایل `/srv/deployment/.env` را ویرایش کنید:

```env
# Database
DB_NAME=app_db
DB_USER=app_user
DB_PASSWORD=SuperSecure@DB#2024Pass!

# RAG Core API
RAG_CORE_BASE_URL=https://core.app.ir
RAG_CORE_API_KEY=YOUR_API_KEY_HERE

# Email (Gmail example)
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password

# Payment Gateways
ZARINPAL_MERCHANT_ID=YOUR_MERCHANT_ID
STRIPE_PUBLIC_KEY=YOUR_PUBLIC_KEY
STRIPE_SECRET_KEY=YOUR_SECRET_KEY
```

## 📊 وضعیت پیشرفت

### ✅ تکمیل شده
- ساختار پروژه و تنظیمات اولیه
- سیستم احراز هویت کامل (JWT, 2FA)
- ماژول چت و اتصال به RAG Core
- رابط کاربری شبیه ChatGPT
- WebSocket برای real-time
- Docker و اسکریپت‌های deployment

### 🚧 در حال توسعه
- سیستم پرداخت (زرین‌پال، رمزارز)
- مدیریت اشتراک و پلن‌ها
- پنل ادمین با RBAC کامل
- بازارچه مشاوران
- سیستم اعلان‌ها

### 📋 برنامه‌ریزی شده
- اپلیکیشن موبایل (React Native)
- تست‌های Unit و E2E
- مستندات API کامل
- بهینه‌سازی Performance

## 🤝 مشارکت

برای مشارکت در توسعه:

1. Fork کنید
2. Branch جدید ایجاد کنید (`git checkout -b feature/AmazingFeature`)
3. تغییرات را Commit کنید (`git commit -m 'Add some AmazingFeature'`)
4. Push کنید (`git push origin feature/AmazingFeature`)
5. Pull Request ایجاد کنید