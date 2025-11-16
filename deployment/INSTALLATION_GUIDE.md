# راهنمای نصب کامل پلتفرم

این راهنما برای نصب پلتفرم روی سرور جدید آماده شده است.

## پیش‌نیازها

- سیستم‌عامل: Ubuntu 20.04+ یا Debian 11+
- دسترسی root (sudo)
- حداقل 4GB RAM
- حداقل 20GB فضای دیسک
- اتصال به اینترنت

## مراحل نصب

### 1. آماده‌سازی سرور

```bash
# کپی کردن فایل‌ها به سرور
scp -r /srv your-user@your-server-ip:/tmp/

# اتصال به سرور
ssh your-user@your-server-ip

# انتقال به مسیر صحیح
sudo mv /tmp/srv /srv
sudo chown -R $USER:$USER /srv
```

### 2. اجرای اسکریپت نصب

```bash
cd /srv/deployment
sudo ./start.sh
```

اسکریپت به صورت خودکار موارد زیر را انجام می‌دهد:

#### ✅ چک‌های پیش‌نیاز
- بررسی دسترسی root
- بررسی سیستم‌عامل (Ubuntu/Debian)

#### ✅ نصب ابزارها
- به‌روزرسانی سیستم
- نصب Docker و Docker Compose
- نصب ابزارهای ضروری (curl, wget, git, etc.)
- پیکربندی UFW Firewall

#### ✅ پیکربندی محیط
- ایجاد فایل `.env` از روی `.env.example`
- درخواست اطلاعات دامنه و ایمیل
- تولید پسوردهای امن برای تمام سرویس‌ها
- ذخیره اطلاعات ورود در `/srv/deployment/config/credentials.txt`

#### ✅ راه‌اندازی سرویس‌ها
- ساخت و راه‌اندازی PostgreSQL
- ساخت و راه‌اندازی Redis (با پشتیبانی password)
- ساخت و راه‌اندازی RabbitMQ
- ساخت و راه‌اندازی Backend (Django)
- اجرای migrations و collectstatic
- ایجاد کاربر admin
- راه‌اندازی Celery Worker و Beat
- راه‌اندازی Frontend (Next.js)
- راه‌اندازی Nginx Proxy Manager

#### ✅ تنظیمات نهایی
- تنظیم backup خودکار روزانه (ساعت 2 صبح)
- نمایش اطلاعات دسترسی

### 3. پیکربندی دامنه و SSL

پس از نصب، باید Nginx Proxy Manager را پیکربندی کنید:

1. به آدرس `http://YOUR-SERVER-IP:81` بروید
2. با اطلاعات پیش‌فرض وارد شوید:
   - Email: `admin@example.com`
   - Password: `changeme`
3. رمز عبور را به password داخل فایل `.env` تغییر دهید
4. Proxy Host جدید برای backend ایجاد کنید:
   - Domain: `admin.yourdomain.com`
   - Forward to: `backend:8000`
   - SSL: Let's Encrypt (auto)
5. Proxy Host جدید برای frontend ایجاد کنید:
   - Domain: `yourdomain.com`
   - Forward to: `frontend:3000`
   - SSL: Let's Encrypt (auto)

### 4. تنظیمات نهایی .env

قبل از اجرای اسکریپت یا بعد از آن، موارد زیر را در `/srv/deployment/.env` حتماً تنظیم کنید:

```bash
# Domain - دامنه اصلی شما
DOMAIN=yourdomain.com

# Admin Email
ADMIN_EMAIL=admin@yourdomain.com

# RAG Core API - اتصال به سیستم مرکزی
RAG_CORE_BASE_URL=https://core.example.com
RAG_CORE_API_KEY=YOUR_REAL_API_KEY_HERE

# JWT Secret Key - باید با سیستم مرکزی یکسان باشد
JWT_SECRET_KEY=your-jwt-secret-key-from-central-system

# Email Configuration
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-specific-password

# Payment Gateways
ZARINPAL_MERCHANT_ID=your-merchant-id
```

## اطلاعات مهم

### 🔐 فایل اطلاعات محرمانه

تمام پسوردهای تولید شده در فایل زیر ذخیره می‌شوند:
```
/srv/deployment/config/credentials.txt
```

**⚠️ این فایل را در جای امن نگهداری کنید!**

### 🔥 Firewall (UFW)

پورت‌های باز شده:
- **22** - SSH
- **80** - HTTP
- **443** - HTTPS  
- **81** - Nginx Proxy Manager Admin Panel

### 🗄️ Backup خودکار

- Backup روزانه ساعت 2 صبح
- ذخیره‌سازی در `/srv/backups`
- نگهداری 30 روز اخیر
- شامل: PostgreSQL, Redis, Media Files, Static Files, .env

برای backup دستی:
```bash
sudo /srv/backups/backup.sh
```

## دستورات مفید

### مشاهده وضعیت سرویس‌ها
```bash
cd /srv/deployment
docker-compose ps
```

### مشاهده لاگ‌ها
```bash
# همه سرویس‌ها
docker-compose logs -f

# یک سرویس خاص
docker-compose logs -f backend
docker-compose logs -f frontend
docker-compose logs -f celery_worker
```

### ری‌استارت سرویس‌ها
```bash
# همه سرویس‌ها
docker-compose restart

# یک سرویس خاص
docker-compose restart backend
```

### توقف و شروع
```bash
# توقف همه
docker-compose down

# شروع همه
docker-compose up -d
```

### دسترسی به Django Shell
```bash
docker-compose exec backend python manage.py shell
```

### اجرای migrations
```bash
docker-compose exec backend python manage.py migrate
```

### ایجاد superuser جدید
```bash
docker-compose exec backend python manage.py createsuperuser
```

## عیب‌یابی

### Backend راه‌اندازی نمی‌شود
```bash
# چک کردن لاگ‌ها
docker-compose logs backend

# چک کردن اتصال به database
docker-compose exec backend python manage.py dbshell
```

### Frontend راه‌اندازی نمی‌شود
```bash
# چک کردن لاگ‌ها
docker-compose logs frontend

# rebuild کردن
docker-compose up -d --build frontend
```

### Redis خطا می‌دهد
```bash
# چک کردن اتصال
docker-compose exec redis redis-cli -a YOUR_REDIS_PASSWORD ping

# اگر password ندارید
docker-compose exec redis redis-cli ping
```

### مشکل در Migrations
```bash
# بازسازی database (خطرناک - فقط برای development)
docker-compose down
docker volume rm deployment_postgres_data
docker-compose up -d postgres
# صبر کنید تا postgres آماده شود
docker-compose up -d backend
docker-compose exec backend python manage.py migrate
```

## تغییرات نسبت به نسخه قبلی

### اصلاحات در start.sh
1. ✅ اضافه شدن متغیرهای `DB_NAME`, `DB_USER`, `RABBITMQ_USER`
2. ✅ اصلاح مسیر `.env` در credentials.txt
3. ✅ اصلاح خواندن `ADMIN_EMAIL` از فایل `.env`
4. ✅ اضافه شدن wait برای آماده شدن NPM
5. ✅ اصلاح backup script با مسیرهای صحیح
6. ✅ اصلاح دستور backup Redis

### اصلاحات در docker-compose.yml
1. ✅ پشتیبانی از Redis password (اختیاری)
2. ✅ اضافه شدن متغیرهای محیطی Redis به همه سرویس‌ها
3. ✅ بهبود healthcheck برای Redis

### اصلاحات در settings.py
1. ✅ پشتیبانی کامل از Redis password
2. ✅ استفاده از `REDIS_URL` و `CACHE_URL` از environment
3. ✅ Fallback به ساخت URL با password

### اصلاحات در .env.example
1. ✅ اضافه شدن `BACKEND_URL` برای Next.js SSR
2. ✅ اضافه شدن `BALE_CLIENT_ID` و `BALE_CLIENT_SECRET`

## امنیت

### توصیه‌های امنیتی

1. **تغییر پسوردها**: همه پسوردهای تولید شده را یادداشت کرده و فایل credentials را حذف کنید
2. **SSL**: حتماً برای دامنه اصلی SSL فعال کنید
3. **Firewall**: فقط پورت‌های لازم را باز نگه دارید
4. **Backup**: backupها را در مکان امن خارج از سرور نیز نگه دارید
5. **Updates**: به‌طور منظم سیستم و Docker images را به‌روز کنید

### به‌روزرسانی سیستم
```bash
# به‌روزرسانی سیستم‌عامل
sudo apt update && sudo apt upgrade -y

# به‌روزرسانی Docker images
cd /srv/deployment
docker-compose pull
docker-compose up -d --build
```

## پشتیبانی

در صورت بروز مشکل:
1. لاگ‌های سرویس‌ها را بررسی کنید
2. وضعیت سلامت کانتینرها را چک کنید
3. اتصالات شبکه و firewall را بررسی کنید
4. فایل `.env` را برای تنظیمات صحیح بررسی کنید

---

**نکته**: این پلتفرم برای production آماده است ولی توصیه می‌شود در محیط development ابتدا تست شود.
