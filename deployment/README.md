# 🚀 راهنمای جامع استقرار و انتقال سرور

این راهنما برای انتقال پروژه به سرور جدید و راه‌اندازی کامل سیستم طراحی شده است.

---

## 📋 فهرست مطالب

1. [پیش‌نیازها](#پیش‌نیازها)
2. [مراحل انتقال سرور](#مراحل-انتقال-سرور)
3. [نصب اولیه در سرور جدید](#نصب-اولیه-در-سرور-جدید)
4. [مدیریت بکآپ و بازیابی](#مدیریت-بکآپ-و-بازیابی)
5. [داده‌های اولیه سیستم](#داده‌های-اولیه-سیستم)
6. [مدیریت سیستم](#مدیریت-سیستم)
7. [تنظیمات پس از نصب](#تنظیمات-پس-از-نصب)
8. [عیب‌یابی](#عیب‌یابی)

---

## 🔧 پیش‌نیازها

### سرور جدید
- **سیستم عامل**: Ubuntu 20.04+ یا Debian 11+
- **RAM**: حداقل 4GB (توصیه: 8GB+)
- **فضای دیسک**: حداقل 50GB (توصیه: 100GB+)
- **CPU**: حداقل 2 هسته (توصیه: 4 هسته+)
- **دسترسی**: Root یا sudo access

### نرم‌افزارهای مورد نیاز
اسکریپت `start.sh` به صورت خودکار موارد زیر را نصب می‌کند:
- Docker & Docker Compose
- Git
- UFW Firewall
- ابزارهای ضروری سیستم

---

## 📦 مراحل انتقال سرور

### مرحله 1️⃣: بکآپ از سرور قبلی

```bash
# در سرور قبلی
cd /srv/deployment

# بکآپ کامل (دیتابیس + فایل‌ها)
sudo ./backup_manager.sh backup-full

# یا فقط بکآپ دیتابیس (سریع‌تر)
sudo ./backup_manager.sh backup-db

# لیست بکآپ‌ها
sudo ./backup_manager.sh list
```

**فایل‌های بکآپ در**: `/srv/backups/`

**انواع بکآپ:**
- `full_backup_YYYYMMDD_HHMMSS.tar.gz` - بکآپ کامل (دیتابیس + فایل‌ها + تنظیمات)
- `db_backup_YYYYMMDD_HHMMSS.tar.gz` - فقط دیتابیس و Redis

### مرحله 2️⃣: انتقال فایل بکآپ

```bash
# از سرور قبلی به سرور جدید
scp /srv/backups/full_backup_*.tar.gz root@NEW_SERVER_IP:/tmp/

# یا استفاده از rsync (برای فایل‌های بزرگ)
rsync -avz --progress /srv/backups/full_backup_*.tar.gz root@NEW_SERVER_IP:/tmp/
```

### مرحله 3️⃣: کلون کردن پروژه در سرور جدید

```bash
# در سرور جدید
cd /srv
git clone https://github.com/YOUR_USERNAME/YOUR_REPO.git .

# یا اگر repository خصوصی است
git clone https://YOUR_TOKEN@github.com/YOUR_USERNAME/YOUR_REPO.git .
```

### مرحله 4️⃣: نصب و راه‌اندازی اولیه

```bash
cd /srv/deployment
sudo ./start.sh
```

**اسکریپت start.sh به صورت تعاملی از شما می‌پرسد:**
- نام دامنه (مثال: `example.com`)
- آدرس و کلید API سیستم RAG Core
- تنظیمات SMS (Kavenegar)
- تنظیمات Bale Messenger
- تنظیمات S3/MinIO (اختیاری)
- آدرس Backend

**اقدامات خودکار اسکریپت:**
- ✅ نصب Docker و Docker Compose
- ✅ تنظیم UFW Firewall
- ✅ ایجاد فایل `.env` با رمزهای امن
- ✅ ساخت و راه‌اندازی تمام سرویس‌ها
- ✅ اجرای migrations
- ✅ ایجاد داده‌های اولیه (ارزها، زبان‌ها، پلن‌ها، و...)
- ✅ ایجاد کاربر سوپر ادمین
- ✅ تنظیم بکآپ خودکار روزانه

### مرحله 5️⃣: بازیابی بکآپ (اختیاری)

اگر می‌خواهید داده‌های سرور قبلی را بازیابی کنید:

```bash
# انتقال فایل بکآپ به پوشه backups
sudo mkdir -p /srv/backups
sudo mv /tmp/full_backup_*.tar.gz /srv/backups/

# بازیابی کامل
cd /srv/deployment
sudo ./backup_manager.sh restore-full

# یا فقط بازیابی دیتابیس
sudo ./backup_manager.sh restore-db
```

**⚠️ هشدار**: بازیابی تمام داده‌های فعلی را جایگزین می‌کند!

---

## 💾 مدیریت بکآپ و بازیابی

### استفاده از Backup Manager

```bash
cd /srv/deployment
sudo ./backup_manager.sh
```

**منوی تعاملی:**
```
1) Full Backup (Database + Files)      - بکآپ کامل
2) Database-Only Backup                - فقط دیتابیس
3) Full Restore (Database + Files)     - بازیابی کامل
4) Database-Only Restore               - بازیابی دیتابیس
5) List All Backups                    - لیست بکآپ‌ها
6) Exit                                - خروج
```

### دستورات مستقیم

```bash
# بکآپ کامل
sudo ./backup_manager.sh backup-full

# بکآپ دیتابیس
sudo ./backup_manager.sh backup-db

# بازیابی کامل
sudo ./backup_manager.sh restore-full

# بازیابی دیتابیس
sudo ./backup_manager.sh restore-db

# لیست بکآپ‌ها
sudo ./backup_manager.sh list
```

### بکآپ خودکار

بکآپ خودکار روزانه در ساعت 2 صبح تنظیم شده است:

```bash
# مشاهده cron job
crontab -l

# ویرایش زمان بکآپ
crontab -e
```

### محل ذخیره بکآپ‌ها

- **مسیر**: `/srv/backups/`
- **نگهداری**: 30 روز (قابل تنظیم در `.env` با `BACKUP_RETENTION_DAYS`)
- **فرمت**: فایل‌های فشرده `.tar.gz`

### محتویات بکآپ کامل

- ✅ PostgreSQL Database (فرمت custom dump)
- ✅ Redis Data (dump.rdb)
- ✅ Media Files (فایل‌های آپلود شده کاربران)
- ✅ Static Files (فایل‌های استاتیک Django)
- ✅ Nginx Proxy Manager Data
- ✅ فایل `.env` (تنظیمات محیطی)

---

## 🗄️ داده‌های اولیه سیستم

اسکریپت `start.sh` به صورت خودکار داده‌های زیر را در دیتابیس ایجاد می‌کند:

### 1️⃣ زبان‌ها (Languages)

| کد | نام | پیش‌فرض | RTL |
|----|-----|---------|-----|
| `fa` | فارسی | ✅ | ✅ |
| `en` | English | ❌ | ❌ |

### 2️⃣ مناطق زمانی (Timezones)

تمام مناطق زمانی رسمی از `pytz` (حدود 590 منطقه):
- **پیش‌فرض**: `Asia/Tehran`
- **مرتب‌سازی**: بر اساس UTC offset
- **فرمت**: `Asia/Tehran (UTC+03:30)`

### 3️⃣ ارزها (Currencies)

| کد | نام | نماد | نرخ تبدیل | پیش‌فرض | ارز پایه |
|----|-----|------|-----------|---------|----------|
| `IRR` | ریال | ریال | 1 | ❌ | ✅ |
| `IRT` | تومان ایرانی | تومان | 10 | ✅ | ❌ |

### 4️⃣ پلن‌های اشتراک (Subscription Plans)

**پلن رایگان:**
- قیمت: 0 تومان
- مدت: 30 روز
- محدودیت روزانه: 10 سوال
- محدودیت ماهانه: 200 سوال
- ویژگی‌ها: پایه

**پلن نامحدود (برای ادمین‌ها):**
- قیمت: 0 تومان
- مدت: 100 سال
- محدودیت: نامحدود
- ویژگی‌ها: کامل

### 5️⃣ درگاه‌های پرداخت (Payment Gateways)

**زرین‌پال:**
- وضعیت: غیرفعال (نیاز به تنظیم `merchant_id`)
- کمیسیون: 0%
- پیش‌فرض: ✅

### 6️⃣ تنظیمات سایت (Site Settings)

- نام سایت: "مشاور هوشمند کسب و کار"
- تلفن پشتیبانی: `021-91097737`
- ایمیل پشتیبانی: `support@tejarat.chat`

### 7️⃣ تنظیمات مالی (Financial Settings)

- نام شرکت: "شرکت تجارت چت"
- نرخ مالیات: 10%
- سایر فیلدها: نیاز به تکمیل توسط ادمین

### 8️⃣ قالب‌های اعلان (Notification Templates)

**دسته‌بندی‌ها:**
- اشتراک (Subscription): 6 قالب
- پرداخت (Payment): 2 قالب
- امنیت (Security): 2 قالب
- حساب کاربری (Account): 1 قالب
- سیستم (System): 1 قالب

**نمونه قالب‌ها:**
- `subscription_expiring` - نزدیک به انقضای اشتراک
- `subscription_expired` - انقضای اشتراک
- `payment_success` - پرداخت موفق
- `quota_exceeded` - اتمام سهمیه
- `welcome` - خوش‌آمدگویی

### 9️⃣ سیاست‌های SLA (Support)

| نام | اولویت | زمان پاسخ | زمان حل |
|-----|--------|-----------|---------|
| فوری | Urgent | 30 دقیقه | 4 ساعت |
| بالا | High | 2 ساعت | 8 ساعت |
| متوسط | Medium | 4 ساعت | 24 ساعت |
| کم | Low | 8 ساعت | 48 ساعت |

### 🔟 کاربر سوپر ادمین

**اطلاعات ورود:**
- شماره تلفن: `09121082690`
- ایمیل: `admin@tejarat.chat`
- رمز عبور: مطابق `DJANGO_ADMIN_PASSWORD` در `.env`
- اشتراک: نامحدود (100 سال)

---

## 🎛️ مدیریت سیستم

### Platform Manager

```bash
cd /srv/deployment
sudo ./manager.sh
```

**دستورات موجود:**

```bash
# راه‌اندازی و کنترل
sudo ./manager.sh start          # شروع تمام سرویس‌ها
sudo ./manager.sh stop           # توقف تمام سرویس‌ها
sudo ./manager.sh restart        # راه‌اندازی مجدد
sudo ./manager.sh status         # وضعیت سرویس‌ها

# لاگ‌ها و مانیتورینگ
sudo ./manager.sh logs           # مشاهده لاگ‌ها
sudo ./manager.sh health         # بررسی سلامت سیستم

# دیتابیس
sudo ./manager.sh migrate        # اجرای migrations
sudo ./manager.sh shell          # Django shell

# به‌روزرسانی
sudo ./manager.sh update         # به‌روزرسانی از Git
sudo ./manager.sh rebuild        # بازسازی کامل
```

### دسترسی به سرویس‌ها

پس از نصب موفق:

```bash
# مشاهده وضعیت
docker-compose ps

# لاگ سرویس خاص
docker-compose logs -f backend
docker-compose logs -f frontend
docker-compose logs -f postgres

# ری‌استارت سرویس خاص
docker-compose restart backend
docker-compose restart frontend

# دسترسی به shell
docker exec -it app_backend bash
docker exec -it app_frontend sh
```

---

## ⚙️ تنظیمات پس از نصب

### 1️⃣ تنظیم SSL با Nginx Proxy Manager

**دسترسی به NPM:**
- آدرس: `http://SERVER_IP:81`
- ایمیل اولیه: `admin@example.com`
- رمز اولیه: `changeme`

**مراحل:**

1. **تغییر رمز عبور**
   - بعد از اولین ورود، رمز را تغییر دهید

2. **افزودن Proxy Host برای Frontend**
   - Domain Names: `yourdomain.com`, `www.yourdomain.com`
   - Scheme: `http`
   - Forward Hostname/IP: `frontend`
   - Forward Port: `3000`
   - ☑ Cache Assets
   - ☑ Block Common Exploits
   - ☑ Websockets Support

3. **افزودن Proxy Host برای Backend**
   - Domain Names: `admin.yourdomain.com`
   - Scheme: `http`
   - Forward Hostname/IP: `backend`
   - Forward Port: `8000`
   - ☑ Block Common Exploits
   - ☑ Websockets Support

4. **تنظیم SSL**
   - در تب SSL هر Proxy Host
   - Request a new SSL Certificate
   - ☑ Force SSL
   - ☑ HTTP/2 Support
   - ☑ HSTS Enabled

**⚠️ مهم**: CORS را در NPM تنظیم نکنید! Django خودش CORS را مدیریت می‌کند.

### 2️⃣ تنظیم DNS

رکوردهای A را به IP سرور جدید اشاره دهید:

```
yourdomain.com          A    YOUR_SERVER_IP
www.yourdomain.com      A    YOUR_SERVER_IP
admin.yourdomain.com    A    YOUR_SERVER_IP
```

### 3️⃣ تکمیل تنظیمات در فایل .env

```bash
sudo nano /srv/deployment/.env
```

**موارد مهم برای بررسی:**

```env
# دامنه
DOMAIN=yourdomain.com

# RAG Core API (ضروری!)
RAG_CORE_BASE_URL=https://core.example.com
RAG_CORE_API_KEY=your-real-api-key

# S3/MinIO (برای آپلود فایل)
S3_ENDPOINT_URL=https://s3.yourdomain.com
S3_ACCESS_KEY_ID=your_access_key
S3_SECRET_ACCESS_KEY=your_secret_key

# Email
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password

# SMS (Kavenegar)
KAVENEGAR_API_KEY=your-api-key
KAVENEGAR_SENDER=your-sender-number

# Payment Gateway
ZARINPAL_MERCHANT_ID=your-merchant-id
```

بعد از تغییرات:
```bash
cd /srv/deployment
docker-compose restart backend
```

### 4️⃣ فعال‌سازی درگاه پرداخت

```bash
docker exec -it app_backend python manage.py shell
```

```python
from finance.models import PaymentGateway

# فعال‌سازی زرین‌پال
gateway = PaymentGateway.objects.get(name='زرین‌پال')
gateway.merchant_id = 'YOUR_MERCHANT_ID'
gateway.is_active = True
gateway.save()
```

### 5️⃣ تست سیستم

```bash
# بررسی سلامت
cd /srv/deployment
sudo ./manager.sh health

# تست ارسال ایمیل
docker exec -it app_backend python manage.py shell
>>> from django.core.mail import send_mail
>>> send_mail('Test', 'Test message', 'from@example.com', ['to@example.com'])

# تست اتصال به RAG Core
docker-compose logs backend | grep "RAG"
```

---

## 🐛 عیب‌یابی

### مشکل 1: سرویس‌ها start نمی‌شوند

```bash
# بررسی لاگ‌ها
docker-compose logs backend
docker-compose logs frontend

# ری‌استارت
docker-compose down
docker-compose up -d

# بررسی منابع
docker stats
```

### مشکل 2: خطای دیتابیس

```bash
# بررسی وضعیت PostgreSQL
docker exec -it app_postgres psql -U app_user -d app_db -c "SELECT version();"

# اجرای مجدد migrations
docker exec -it app_backend python manage.py migrate

# بررسی لاگ
docker-compose logs postgres
```

### مشکل 3: خطای Redis

```bash
# تست اتصال
docker exec -it app_redis redis-cli ping

# با رمز عبور
docker exec -it app_redis redis-cli -a "YOUR_REDIS_PASSWORD" ping

# پاک کردن cache
docker exec -it app_redis redis-cli FLUSHALL
```

### مشکل 4: فایل‌ها آپلود نمی‌شوند

```bash
# بررسی تنظیمات S3/MinIO در .env
grep S3_ /srv/deployment/.env

# تست اتصال به MinIO
docker exec -it app_backend python manage.py shell
>>> from core.storage import minio_service
>>> minio_service.test_connection()
```

### مشکل 5: OTP ارسال نمی‌شود

```bash
# بررسی تنظیمات Kavenegar
grep KAVENEGAR /srv/deployment/.env

# پاک کردن rate limit
docker exec -it app_redis redis-cli FLUSHDB

# بررسی لاگ
docker-compose logs backend | grep "SMS"
```

### مشکل 6: خطای CORS

**علت**: تنظیمات اشتباه CORS در NPM

**راه حل**:
1. وارد NPM شوید
2. Proxy Host مربوط به Backend را ویرایش کنید
3. در تب Advanced، تمام headerهای CORS را حذف کنید
4. فقط proxy headers استاندارد را نگه دارید

### مشکل 7: SSL کار نمی‌کند

```bash
# بررسی DNS
nslookup yourdomain.com

# بررسی فایروال
sudo ufw status

# بررسی پورت‌ها
sudo netstat -tulpn | grep :80
sudo netstat -tulpn | grep :443
```

### مشکل 8: بکآپ خودکار کار نمی‌کند

```bash
# بررسی cron
crontab -l

# تست دستی
sudo /srv/deployment/backup_manager.sh backup-full

# بررسی لاگ cron
grep CRON /var/log/syslog
```

---

## 📞 دستورات مفید

### مانیتورینگ

```bash
# وضعیت کلی
docker-compose ps
docker stats

# استفاده از دیسک
df -h
du -sh /srv/backups

# لاگ‌های سیستم
journalctl -u docker -f
```

### دیتابیس

```bash
# ورود به PostgreSQL
docker exec -it app_postgres psql -U app_user -d app_db

# بکآپ دستی
docker exec app_postgres pg_dump -U app_user app_db > backup.sql

# بازیابی دستی
docker exec -i app_postgres psql -U app_user app_db < backup.sql
```

### Django Management Commands

```bash
# ایجاد superuser جدید
docker exec -it app_backend python manage.py createsuperuser

# ایجاد داده‌های اولیه (اگر نیاز باشد)
docker exec -it app_backend python manage.py setup_initial_data

# پاک کردن توکن‌های منقضی
docker exec -it app_backend python manage.py cleanup_tokens

# جمع‌آوری فایل‌های استاتیک
docker exec -it app_backend python manage.py collectstatic --noinput
```

---

## 📚 منابع بیشتر

- [مستندات کامل پروژه](/srv/documents/0_PROJECT_DOCUMENTATION.md)
- [راهنمای اصلی](/srv/README.md)
- [فایل تنظیمات نمونه](/srv/deployment/config/.env.example)

---

## ✅ چک‌لیست نهایی

پس از انتقال سرور، موارد زیر را بررسی کنید:

- [ ] تمام سرویس‌ها در حال اجرا هستند (`docker-compose ps`)
- [ ] DNS به IP جدید اشاره می‌کند
- [ ] SSL نصب و فعال است
- [ ] بکآپ خودکار تنظیم شده (`crontab -l`)
- [ ] فایل `.env` تکمیل شده است
- [ ] RAG Core API در دسترس است
- [ ] درگاه پرداخت فعال است
- [ ] SMS و Email کار می‌کنند
- [ ] S3/MinIO متصل است
- [ ] فایروال تنظیم شده (`sudo ufw status`)
- [ ] لاگ‌ها بدون خطای critical هستند
- [ ] تست کامل سیستم انجام شده

---

**نسخه**: 2.0  
**تاریخ**: 2024-12-23  
**نگهدارنده**: تیم توسعه تجارت چت
