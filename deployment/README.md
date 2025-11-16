# راهنمای استقرار پلتفرم

## 📋 فهرست

- [نصب اولیه](#نصب-اولیه)
- [مدیریت سیستم](#مدیریت-سیستم)
- [پشتیبان‌گیری و بازیابی](#پشتیبان‌گیری-و-بازیابی)
- [ساختار فایل‌ها](#ساختار-فایل‌ها)

---

## 🚀 نصب اولیه

### پیش‌نیازها
- Ubuntu 20.04+ یا Debian 11+
- دسترسی root
- حداقل 4GB RAM
- حداقل 20GB فضای دیسک

### مراحل نصب

```bash
# 1. رفتن به پوشه deployment
cd /srv/deployment

# 2. اجرای اسکریپت نصب
sudo ./start.sh
```

اسکریپت `start.sh` به صورت خودکار:
- Docker و Docker Compose را نصب می‌کند
- فایل `.env` را از روی `.env.example` می‌سازد
- پسوردهای امن تولید می‌کند
- تمام سرویس‌ها را راه‌اندازی می‌کند
- دیتابیس را migrate می‌کند
- کاربر admin ایجاد می‌کند
- backup خودکار روزانه را تنظیم می‌کند

---

## 🛠️ مدیریت سیستم

### استفاده از Platform Manager

```bash
# حالت تعاملی (منوی کامل)
sudo ./manager.sh

# یا استفاده از دستورات مستقیم:
sudo ./manager.sh start          # راه‌اندازی تمام سرویس‌ها
sudo ./manager.sh stop           # توقف تمام سرویس‌ها
sudo ./manager.sh restart        # راه‌اندازی مجدد
sudo ./manager.sh status         # وضعیت سرویس‌ها
sudo ./manager.sh logs           # مشاهده لاگ‌ها
sudo ./manager.sh migrate        # اجرای migrations
sudo ./manager.sh shell          # Django shell
sudo ./manager.sh dbshell        # PostgreSQL shell
sudo ./manager.sh cache          # پاکسازی cache
sudo ./manager.sh static         # جمع‌آوری static files
sudo ./manager.sh update         # به‌روزرسانی سیستم
sudo ./manager.sh cleanup        # پاکسازی Docker
sudo ./manager.sh info           # اطلاعات سیستم
sudo ./manager.sh health         # بررسی سلامت سرویس‌ها
sudo ./manager.sh fix-otp        # رفع مشکلات OTP
sudo ./manager.sh fix-perms      # اصلاح دسترسی‌ها
```

### عملیات‌های رایج

#### مشاهده لاگ‌های یک سرویس خاص
```bash
cd /srv/deployment
docker-compose logs -f backend
docker-compose logs -f frontend
docker-compose logs -f celery_worker
```

#### راه‌اندازی مجدد یک سرویس
```bash
cd /srv/deployment
docker-compose restart backend
docker-compose restart frontend
```

#### اجرای دستورات Django
```bash
cd /srv/deployment
docker-compose exec backend python manage.py migrate
docker-compose exec backend python manage.py createsuperuser
docker-compose exec backend python manage.py shell
```

---

## 💾 پشتیبان‌گیری و بازیابی

### استفاده از Backup Manager

```bash
# حالت تعاملی (منوی کامل)
sudo ./backup_manager.sh

# یا استفاده از دستورات مستقیم:
sudo ./backup_manager.sh backup-full      # پشتیبان کامل (دیتابیس + فایل‌ها)
sudo ./backup_manager.sh backup-db        # فقط دیتابیس
sudo ./backup_manager.sh restore-full     # بازیابی کامل
sudo ./backup_manager.sh restore-db       # بازیابی فقط دیتابیس
sudo ./backup_manager.sh list             # لیست پشتیبان‌ها
```

### انواع پشتیبان‌گیری

#### 1. پشتیبان کامل (Full Backup)
شامل:
- دیتابیس PostgreSQL
- Redis data
- فایل‌های media
- فایل‌های static
- داده‌های Nginx Proxy Manager
- فایل `.env`

```bash
sudo ./backup_manager.sh backup-full
```

#### 2. پشتیبان فقط دیتابیس
شامل:
- دیتابیس PostgreSQL
- Redis data

```bash
sudo ./backup_manager.sh backup-db
```

### بازیابی

#### بازیابی کامل
```bash
sudo ./backup_manager.sh restore-full
# سپس شماره backup را انتخاب کنید
```

#### بازیابی فقط دیتابیس
```bash
sudo ./backup_manager.sh restore-db
# سپس شماره backup را انتخاب کنید
```

### پشتیبان‌گیری خودکار

پشتیبان‌گیری کامل به صورت خودکار هر روز ساعت 2 صبح انجام می‌شود.

برای تغییر زمان:
```bash
crontab -e
# سپس خط زیر را ویرایش کنید:
# 0 2 * * * /srv/deployment/backup_manager.sh backup-full
```

### مدیریت فضای backup

پشتیبان‌های قدیمی‌تر از 30 روز به صورت خودکار حذف می‌شوند.

برای تغییر این مدت، فایل `.env` را ویرایش کنید:
```bash
BACKUP_RETENTION_DAYS=30
```

---

## 📁 ساختار فایل‌ها

```
/srv/deployment/
├── start.sh                  # اسکریپت نصب اولیه
├── manager.sh                # مدیریت سیستم
├── backup_manager.sh         # مدیریت backup/restore
├── docker-compose.yml        # تعریف سرویس‌ها
├── Dockerfile.backend        # تصویر Docker برای Backend
├── Dockerfile.frontend       # تصویر Docker برای Frontend
├── nginx.conf                # پیکربندی Nginx
├── .env                      # تنظیمات محیطی (ایجاد می‌شود)
├── config/
│   └── .env.example         # نمونه تنظیمات
└── README.md                 # این فایل
```

---

## 🔧 عیب‌یابی

### سرویس‌ها راه‌اندازی نمی‌شوند

```bash
# بررسی وضعیت
sudo ./manager.sh status

# مشاهده لاگ‌ها
sudo ./manager.sh logs

# بررسی سلامت
sudo ./manager.sh health
```

### مشکلات OTP

```bash
sudo ./manager.sh fix-otp
```

### مشکلات دسترسی فایل‌ها

```bash
sudo ./manager.sh fix-perms
```

### پاکسازی Docker

```bash
sudo ./manager.sh cleanup
```

### راه‌اندازی مجدد کامل

```bash
cd /srv/deployment
sudo docker-compose down
sudo docker-compose up -d --build
```

---

## 📞 پشتیبانی

برای مشکلات و سوالات:
1. لاگ‌های سیستم را بررسی کنید
2. فایل `.env` را چک کنید
3. وضعیت سرویس‌ها را بررسی کنید
4. از دستور `health` استفاده کنید

---

## 🔐 امنیت

- فایل `.env` حاوی اطلاعات حساس است - هرگز آن را commit نکنید
- پسوردهای پیش‌فرض را حتماً تغییر دهید
- از JWT_SECRET_KEY یکسان در تمام سیستم‌ها استفاده کنید
- backup‌ها را در مکان امن نگهداری کنید
- دسترسی SSH را محدود کنید
- از firewall استفاده کنید (UFW به صورت خودکار تنظیم می‌شود)
