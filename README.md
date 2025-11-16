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
│   └── public/         # فایل‌های استاتیک
│
├── deployment/         # Docker & Scripts
│   ├── docker-compose.yml      # تعریف سرویس‌ها
│   ├── Dockerfile.backend      # تصویر Docker برای Backend
│   ├── Dockerfile.frontend     # تصویر Docker برای Frontend
│   ├── nginx.conf              # پیکربندی Nginx
│   ├── start.sh                # اسکریپت نصب اولیه
│   ├── manager.sh              # مدیریت سیستم
│   ├── backup_manager.sh       # مدیریت backup/restore
│   ├── README.md               # راهنمای deployment
│   └── config/
│       └── .env.example        # نمونه تنظیمات محیطی
│
└── documents/          # مستندات
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
- UFW Firewall را پیکربندی می‌کند
- فایل `.env` را از روی `.env.example` می‌سازد
- پسوردهای امن تولید می‌کند
- تمام سرویس‌ها را build و راه‌اندازی می‌کند
- دیتابیس را migrate می‌کند
- Superuser ایجاد می‌کند
- Backup خودکار روزانه را تنظیم می‌کند

برای جزئیات بیشتر، [راهنمای deployment](deployment/README.md) را مطالعه کنید.

## 🛠️ مدیریت سیستم

### Platform Manager
برای مدیریت سیستم از اسکریپت `manager.sh` استفاده کنید:

```bash
cd /srv/deployment
sudo ./manager.sh              # منوی تعاملی

# یا دستورات مستقیم:
sudo ./manager.sh start        # راه‌اندازی سرویس‌ها
sudo ./manager.sh stop         # توقف سرویس‌ها
sudo ./manager.sh restart      # راه‌اندازی مجدد
sudo ./manager.sh status       # وضعیت سرویس‌ها
sudo ./manager.sh logs         # مشاهده لاگ‌ها
sudo ./manager.sh health       # بررسی سلامت
sudo ./manager.sh migrate      # اجرای migrations
sudo ./manager.sh update       # به‌روزرسانی سیستم
```

### Backup Manager
برای پشتیبان‌گیری و بازیابی:

```bash
cd /srv/deployment
sudo ./backup_manager.sh              # منوی تعاملی

# یا دستورات مستقیم:
sudo ./backup_manager.sh backup-full  # پشتیبان کامل
sudo ./backup_manager.sh backup-db    # فقط دیتابیس
sudo ./backup_manager.sh restore-full # بازیابی کامل
sudo ./backup_manager.sh restore-db   # بازیابی دیتابیس
sudo ./backup_manager.sh list         # لیست پشتیبان‌ها
```

## 🔑 دسترسی به سیستم

پس از راه‌اندازی، سرویس‌ها در آدرس‌های زیر در دسترس هستند:

- **Frontend**: http://YOUR-SERVER-IP:3000 (از طریق NPM)
- **Backend API**: http://YOUR-SERVER-IP:8000/api (از طریق NPM)
- **Django Admin**: http://YOUR-SERVER-IP/admin
- **Nginx Proxy Manager**: http://YOUR-SERVER-IP:81
- **RabbitMQ Management**: http://localhost:15672 (فقط از سرور)

### اطلاعات ورود:
اطلاعات ورود به صورت خودکار تولید می‌شود و در پایان نصب نمایش داده می‌شود.

**نکته مهم:** برای دسترسی عمومی، باید از Nginx Proxy Manager استفاده کنید و دامنه‌ها و SSL را تنظیم کنید.

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
- Nginx Proxy Manager (Reverse Proxy + SSL)
- UFW Firewall
- Automated Backups

## 📝 تنظیمات محیطی

فایل `.env` به صورت خودکار از روی `config/.env.example` ساخته می‌شود.

برای تنظیمات دستی، فایل `/srv/deployment/.env` را ویرایش کنید:

```env
# Domain
DOMAIN=yourdomain.com
ADMIN_EMAIL=admin@yourdomain.com

# Database (auto-generated)
DB_NAME=app_db
DB_USER=app_user
DB_PASSWORD=auto-generated-secure-password

# RAG Core API (مهم!)
RAG_CORE_BASE_URL=https://core.example.com
RAG_CORE_API_KEY=YOUR_REAL_API_KEY_HERE

# JWT Secret (باید با سیستم مرکزی یکسان باشد)
JWT_SECRET_KEY=your-jwt-secret-key

# Email
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password

# SMS (Kavenegar)
KAVENEGAR_API_KEY=your-api-key
KAVENEGAR_SENDER=your-sender-number

# Bale Messenger
BALE_USERNAME=your-bale-username
BALE_PASSWORD=your-bale-password

# Payment Gateways
ZARINPAL_MERCHANT_ID=YOUR_MERCHANT_ID
```

برای لیست کامل تنظیمات، فایل [`deployment/config/.env.example`](deployment/config/.env.example) را مشاهده کنید.

## 📊 وضعیت پیشرفت

### ✅ تکمیل شده
- ساختار پروژه و تنظیمات اولیه
- سیستم احراز هویت کامل (JWT, 2FA, OTP)
- ماژول چت و اتصال به RAG Core
- رابط کاربری شبیه ChatGPT
- WebSocket برای real-time
- Docker و deployment کامل
- اسکریپت‌های مدیریت و backup
- Nginx Proxy Manager با SSL
- UFW Firewall
- Backup خودکار روزانه

### 🚧 در حال توسعه
- سیستم پرداخت (زرین‌پال، رمزارز)
- مدیریت اشتراک و پلن‌ها
- پنل ادمین با RBAC کامل
- بازارچه مشاوران
- سیستم اعلان‌ها (Email, SMS, Push)

### 📋 برنامه‌ریزی شده
- اپلیکیشن موبایل (React Native)
- تست‌های Unit و E2E
- مستندات API کامل
- بهینه‌سازی Performance
- CI/CD Pipeline

## 📚 مستندات

- [راهنمای نصب و استقرار](deployment/README.md)
- [راهنمای نصب کامل](deployment/INSTALLATION_GUIDE.md)
- [چک‌لیست استقرار](deployment/DEPLOYMENT_CHECKLIST.md)
- [تاریخچه تغییرات](deployment/CHANGELOG.md)
- [پیکربندی دامنه](documents/DOMAIN_CONFIGURATION.md)

## 🔒 امنیت

- تمام پسوردها به صورت خودکار و امن تولید می‌شوند
- JWT Secret باید در تمام سیستم‌ها یکسان باشد
- فایل `.env` در `.gitignore` قرار دارد
- UFW Firewall به صورت خودکار تنظیم می‌شود
- SSL از طریق Let's Encrypt (Nginx Proxy Manager)
- Backup‌های رمزنگاری شده (اختیاری)

## 🤝 مشارکت

برای مشارکت در توسعه:

1. Fork کنید
2. Branch جدید ایجاد کنید (`git checkout -b feature/AmazingFeature`)
3. تغییرات را Commit کنید (`git commit -m 'Add some AmazingFeature'`)
4. Push کنید (`git push origin feature/AmazingFeature`)
5. Pull Request ایجاد کنید

## 📞 پشتیبانی

برای گزارش مشکلات یا پیشنهادات:
- از بخش Issues در GitHub استفاده کنید
- مستندات را مطالعه کنید
- از دستور `./manager.sh health` برای بررسی سلامت سیستم استفاده کنید