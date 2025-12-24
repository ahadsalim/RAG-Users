# پلتفرم مشاوره هوشمند حقوقی 🚀

سیستم مشاوره حقوقی و کسب‌وکار مبتنی بر هوش مصنوعی

## 🌟 ویژگی‌ها

### Backend (Django/DRF)
- ✅ **احراز هویت کامل**: JWT، 2FA، OAuth
- ✅ **پنل ادمین با StaffGroup**: سیستم دسترسی سفارشی برای کارمندان
- ✅ **اتصال به RAG Core**: API کامل برای سیستم مرکزی
- ✅ **WebSocket**: چت real-time با Django Channels
- ✅ **مدیریت کاربران**: پروفایل، سازمان‌ها، StaffGroup
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

### پیش‌نیازها
- سرور Ubuntu 20.04+ یا Debian 11+
- حداقل 4GB RAM (توصیه: 8GB+)
- حداقل 50GB فضای دیسک
- دسترسی root یا sudo

### نصب اولیه (سرور جدید)

```bash
# 1. کلون کردن پروژه
cd /srv
git clone <repository-url> .

# 2. اجرای اسکریپت نصب خودکار
cd /srv/deployment
sudo ./start.sh
```

**اسکریپت به صورت تعاملی از شما می‌پرسد:**
- نام دامنه
- تنظیمات RAG Core API
- تنظیمات SMS و Bale
- تنظیمات S3/MinIO (اختیاری)

**اقدامات خودکار:**
- ✅ نصب Docker و Docker Compose
- ✅ تنظیم UFW Firewall (پورت‌های 22, 80, 443, 81)
- ✅ ایجاد فایل `.env` با رمزهای امن
- ✅ ساخت و راه‌اندازی تمام سرویس‌ها
- ✅ اجرای migrations
- ✅ ایجاد داده‌های اولیه (زبان‌ها، ارزها، مناطق زمانی، پلن‌ها، SLA، قالب‌های اعلان)
- ✅ ایجاد کاربر سوپر ادمین
- ✅ تنظیم بکآپ خودکار هر 6 ساعت با انتقال به سرور پشتیبان

### انتقال از سرور قبلی

```bash
# 1. در سرور قبلی: بکآپ کامل
cd /srv/deployment
sudo ./backup_manual.sh backup-full

# 2. انتقال فایل بکآپ
scp /srv/backups/manual/full_backup_*.tar.gz root@NEW_SERVER_IP:/tmp/

# 3. در سرور جدید: نصب
cd /srv/deployment
sudo ./start.sh

# 4. بازیابی بکآپ
sudo mkdir -p /srv/backups/manual
sudo mv /tmp/full_backup_*.tar.gz /srv/backups/manual/
sudo ./backup_manual.sh restore-full
```

برای جزئیات کامل، [راهنمای استقرار](deployment/README.md) را مطالعه کنید.

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

### Backup System

**بکآپ خودکار (هر 6 ساعت):**
```bash
# اجرا می‌شود توسط cron - شامل: PostgreSQL, Redis, NPM Config, .env
# بکآپ‌ها به سرور پشتیبان منتقل می‌شوند
sudo /srv/deployment/backup_auto.sh   # اجرای دستی
tail -f /var/log/backup-auto.log      # مشاهده لاگ
```

**بکآپ دستی:**
```bash
cd /srv/deployment
sudo ./backup_manual.sh               # منوی تعاملی

# یا دستورات مستقیم:
sudo ./backup_manual.sh backup-full   # پشتیبان کامل (شامل SSL و Media)
sudo ./backup_manual.sh backup-db     # فقط دیتابیس
sudo ./backup_manual.sh restore-full  # بازیابی کامل
sudo ./backup_manual.sh restore-db    # بازیابی دیتابیس
```

**تنظیم سرور پشتیبان:**
برای راه‌اندازی بکآپ خودکار به سرور پشتیبان، [راهنمای تنظیم SSH](deployment/BACKUP_SETUP.md) را مطالعه کنید.

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
- Automated Backups (Every 6 hours to remote server)
- SSH Key-based Remote Backup

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
- **بکآپ خودکار**: هر 6 ساعت به سرور پشتیبان (PostgreSQL, Redis, NPM Config)
- **بکآپ دستی**: بکآپ کامل شامل SSL و Media Files
- **سیستم StaffGroup**: گروه‌بندی کارمندان با دسترسی‌های سفارشی
- **داده‌های اولیه**: زبان‌ها، ارزها، مناطق زمانی (590+)، پلن‌ها، قالب‌های اعلان، SLA
- **مدیریت مالی**: ارزها (ریال، تومان)، درگاه زرین‌پال، تنظیمات مالیاتی
- **سیستم اعلان‌ها**: 12 قالب اعلان برای اشتراک، پرداخت، امنیت
- **سیستم پشتیبانی**: 4 سیاست SLA (فوری، بالا، متوسط، کم)

### 🚧 در حال توسعه
- سیستم پرداخت (فعال‌سازی زرین‌پال، اتصال Stripe)
- مدیریت اشتراک و پلن‌ها (توسعه پلن‌های پولی)
- بازارچه مشاوران
- سیستم Push Notification (Firebase)

### 📋 برنامه‌ریزی شده
- اپلیکیشن موبایل (React Native)
- تست‌های Unit و E2E
- مستندات API کامل (Swagger/OpenAPI)
- بهینه‌سازی Performance
- CI/CD Pipeline

## 📚 مستندات

- **[راهنمای کامل استقرار و انتقال سرور](deployment/README.md)** - راهنمای جامع نصب، بکآپ و انتقال
- [مستندات جامع پروژه](documents/0_PROJECT_DOCUMENTATION.md) - معماری، API، و راهنمای توسعه
- [فایل تنظیمات نمونه](deployment/config/.env.example) - تمام متغیرهای محیطی

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