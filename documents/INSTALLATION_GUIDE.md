# راهنمای نصب و پیکربندی تجارت چت

## 📋 فهرست مطالب

1. [پیش‌نیازها](#پیش-نیازها)
2. [نصب اولیه](#نصب-اولیه)
3. [تنظیمات Environment](#تنظیمات-environment)
4. [راه‌اندازی Docker](#راه-اندازی-docker)
5. [تنظیم Nginx Proxy Manager](#تنظیم-nginx-proxy-manager)
6. [تنظیم Email](#تنظیم-email)
7. [تنظیم SMS](#تنظیم-sms)
8. [تست سیستم](#تست-سیستم)
9. [عیب‌یابی](#عیب-یابی)

---

## 🔧 پیش‌نیازها

### سرور:
- **OS:** Ubuntu 20.04+ / Debian 11+
- **RAM:** حداقل 4GB (توصیه: 8GB+)
- **Storage:** حداقل 50GB
- **CPU:** 2 Core+ (توصیه: 4 Core+)

### نرم‌افزارها:
```bash
# نصب Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# نصب Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# بررسی نصب
docker --version
docker-compose --version
```

### Domain & DNS:
```
tejarat.chat        → A Record → YOUR_SERVER_IP
admin.tejarat.chat  → A Record → YOUR_SERVER_IP
```

---

## 📦 نصب اولیه

### 1. آماده‌سازی سرور:

```bash
# ایجاد دایرکتوری
sudo mkdir -p /srv
cd /srv

# Clone repository (یا upload فایل‌ها)
git clone <repository-url> .

# یا با rsync:
rsync -avz --progress local-path/ user@server:/srv/
```

### 2. تنظیم Permissions:

```bash
sudo chown -R $USER:$USER /srv
chmod -R 755 /srv/deployment
chmod 600 /srv/deployment/.env
```

---

## ⚙️ تنظیمات Environment

### 1. کپی فایل .env:

```bash
cd /srv/deployment
cp .env.example .env
nano .env
```

### 2. تنظیمات Database:

```env
# PostgreSQL
DB_NAME=tejarat_db
DB_USER=tejarat_user
DB_PASSWORD=<STRONG_PASSWORD_HERE>
```

**تولید رمز قوی:**
```bash
openssl rand -base64 32
```

### 3. تنظیمات Django:

```env
# Django Secret Key
SECRET_KEY=<GENERATE_NEW_SECRET_KEY>

# Debug (فقط در development)
DEBUG=false

# Allowed Hosts
ALLOWED_HOSTS=tejarat.chat,admin.tejarat.chat,localhost,127.0.0.1
```

**تولید SECRET_KEY:**
```bash
python3 -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

### 4. تنظیمات Redis:

```env
# Redis Password (اختیاری اما توصیه می‌شود)
REDIS_PASSWORD=<REDIS_PASSWORD>
REDIS_URL=redis://:${REDIS_PASSWORD}@redis:6379/0
CACHE_URL=redis://:${REDIS_PASSWORD}@redis:6379/1
```

### 5. تنظیمات RabbitMQ:

```env
RABBITMQ_USER=tejarat
RABBITMQ_PASSWORD=<RABBITMQ_PASSWORD>
```

### 6. تنظیمات Email (Gmail):

```env
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=true
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=<APP_PASSWORD>
DEFAULT_FROM_EMAIL=noreply@tejarat.chat
```

**دریافت Gmail App Password:**
1. برو به: https://myaccount.google.com/security
2. فعال کردن 2-Step Verification
3. App Passwords → Select app: Mail → Generate
4. کپی کردن 16-character password

### 7. تنظیمات SMS (Kavenegar):

```env
KAVENEGAR_API_KEY=<YOUR_API_KEY>
KAVENEGAR_SENDER=<YOUR_SENDER_NUMBER>
```

**دریافت API Key:**
1. ثبت‌نام در: https://panel.kavenegar.com
2. تنظیمات → API Key
3. کپی کردن API Key

### 8. تنظیمات Core API:

```env
CORE_API_URL=https://core.tejarat.chat
CORE_API_KEY=<YOUR_CORE_API_KEY>
JWT_SECRET_KEY=<JWT_SECRET>
JWT_ALGORITHM=HS256
```

### 9. تنظیمات Frontend:

```env
FRONTEND_URL=https://tejarat.chat
NEXT_PUBLIC_API_URL=https://admin.tejarat.chat
BACKEND_URL=https://admin.tejarat.chat
```

### 10. تنظیمات Payment (اختیاری):

```env
# Zarinpal
ZARINPAL_MERCHANT_ID=<YOUR_MERCHANT_ID>

# Stripe
STRIPE_PUBLIC_KEY=<YOUR_PUBLIC_KEY>
STRIPE_SECRET_KEY=<YOUR_SECRET_KEY>
```

---

## 🐳 راه‌اندازی Docker

### 1. Build و Start:

```bash
cd /srv/deployment

# Build images
docker-compose build

# Start services
docker-compose up -d

# بررسی وضعیت
docker-compose ps
```

### 2. اجرای Migrations:

```bash
# با manager script
./manager.sh migrate

# یا دستی:
docker-compose exec backend python manage.py migrate
```

### 3. Collect Static Files:

```bash
./manager.sh static

# یا:
docker-compose exec backend python manage.py collectstatic --noinput
```

### 4. ایجاد Superuser:

```bash
./manager.sh
# انتخاب گزینه 8: Create Superuser

# یا:
docker-compose exec backend python manage.py createsuperuser
```

### 5. بررسی لاگ‌ها:

```bash
# همه سرویس‌ها
docker-compose logs -f

# فقط backend
docker-compose logs -f backend

# فقط frontend
docker-compose logs -f frontend
```

---

## 🌐 تنظیم Nginx Proxy Manager

### 1. دسترسی به NPM:

```
URL: http://YOUR_SERVER_IP:81
Email: admin@example.com
Password: changeme
```

**⚠️ حتماً رمز عبور را تغییر دهید!**

### 2. تنظیم Backend (admin.tejarat.chat):

#### Details Tab:
```
Domain Names: admin.tejarat.chat
Scheme: http
Forward Hostname/IP: backend
Forward Port: 8000
Cache Assets: ✗ (غیرفعال)
Block Common Exploits: ✓ (فعال)
Websockets Support: ✓ (فعال)
```

#### SSL Tab:
```
SSL Certificate: Request a new SSL Certificate
Force SSL: ✓
HTTP/2 Support: ✓
HSTS Enabled: ✓
Email: your-email@example.com
```

#### Advanced Tab:
```nginx
# Backend API
# ⚠️ توجه: CORS توسط Django مدیریت می‌شود، نباید در NPM تنظیم شود
location /api {
    proxy_pass http://backend:8000;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
    proxy_redirect off;
    
    proxy_connect_timeout 60s;
    proxy_send_timeout 60s;
    proxy_read_timeout 60s;
}

# Django Admin
location /admin {
    proxy_pass http://backend:8000;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
}

# Static Files
location /static {
    alias /static;
    expires 30d;
    add_header Cache-Control "public, immutable";
}

# Media Files
location /media {
    alias /media;
    expires 7d;
}

# WebSocket
location /ws {
    proxy_pass http://backend:8000;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
    proxy_read_timeout 86400;
}
```

### 3. تنظیم Frontend (tejarat.chat):

#### Details Tab:
```
Domain Names: tejarat.chat
Scheme: http
Forward Hostname/IP: frontend
Forward Port: 3000
Cache Assets: ✓ (فعال)
Block Common Exploits: ✓ (فعال)
Websockets Support: ✓ (فعال)
```

#### SSL Tab:
```
SSL Certificate: Request a new SSL Certificate
Force SSL: ✓
HTTP/2 Support: ✓
HSTS Enabled: ✓
```

#### Advanced Tab:
```nginx
location / {
    proxy_pass http://frontend:3000;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
    
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
}

location /_next/static {
    proxy_pass http://frontend:3000;
    expires 365d;
    add_header Cache-Control "public, immutable";
}

location /_next/image {
    proxy_pass http://frontend:3000;
}
```

---

## 📧 تنظیم Email

### Gmail SMTP:

1. **فعال کردن 2-Step Verification:**
   - https://myaccount.google.com/security
   - 2-Step Verification → Turn On

2. **ایجاد App Password:**
   - App Passwords → Select app: Mail
   - Generate → Copy 16-character password

3. **تست ارسال:**
```bash
docker exec app_backend python manage.py shell

>>> from django.core.mail import send_mail
>>> send_mail(
...     'Test Email',
...     'This is a test',
...     'noreply@tejarat.chat',
...     ['your-email@example.com']
... )
```

### Cloudflare Email Routing (دریافت):

1. برو به: Cloudflare Dashboard → Email Routing
2. Add destination address: your-email@gmail.com
3. Add routing rule:
   - `info@tejarat.chat` → your-email@gmail.com

---

## 📱 تنظیم SMS

### Kavenegar:

1. **ثبت‌نام:**
   - https://panel.kavenegar.com/client/membership/register

2. **دریافت API Key:**
   - تنظیمات → API Key → کپی

3. **تنظیم Sender:**
   - خطوط من → شماره ارسال‌کننده

4. **تست ارسال:**
```bash
docker exec app_backend python manage.py shell

>>> from accounts.utils import send_otp_sms
>>> send_otp_sms('09123456789', '123456')
```

---

## ✅ تست سیستم

### 1. Health Check:

```bash
./manager.sh health

# یا:
curl https://admin.tejarat.chat/health/
curl https://tejarat.chat/
```

### 2. تست API:

```bash
# Register
curl -X POST https://admin.tejarat.chat/api/v1/auth/register/ \
  -H "Content-Type: application/json" \
  -d '{
    "phone_number": "09123456789",
    "password": "Test123456",
    "password_confirm": "Test123456",
    "user_type": "individual"
  }'

# Login
curl -X POST https://admin.tejarat.chat/api/v1/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "phone_number": "09123456789",
    "password": "Test123456"
  }'
```

### 3. تست Frontend:

```bash
# باز کردن در مرورگر:
https://tejarat.chat/
https://tejarat.chat/auth/login
https://tejarat.chat/auth/register
```

### 4. تست Admin Panel:

```bash
# باز کردن در مرورگر:
https://admin.tejarat.chat/admin/
```

---

## 🐛 عیب‌یابی

### مشکل 1: Container شروع نمی‌شود

```bash
# بررسی لاگ
docker-compose logs <service-name>

# بررسی وضعیت
docker-compose ps

# ری‌استارت
docker-compose restart <service-name>
```

### مشکل 2: Database Connection Error

```bash
# بررسی PostgreSQL
docker-compose exec postgres pg_isready

# بررسی credentials در .env
cat /srv/deployment/.env | grep DB_

# ری‌استارت database
docker-compose restart postgres
```

### مشکل 3: Email ارسال نمی‌شود

```bash
# بررسی تنظیمات
docker-compose exec backend python manage.py shell
>>> from django.conf import settings
>>> print(settings.EMAIL_HOST_USER)
>>> print(settings.EMAIL_HOST_PASSWORD[:4] + '****')

# تست SMTP
>>> from django.core.mail import send_mail
>>> send_mail('Test', 'Test', settings.DEFAULT_FROM_EMAIL, ['test@example.com'])
```

### مشکل 4: NPM خطای 502

```bash
# بررسی network
docker network inspect deployment_app_network

# تست اتصال
docker exec app_npm ping backend
docker exec app_npm ping frontend

# ری‌استارت NPM
docker-compose restart nginx_proxy_manager
```

### مشکل 5: Frontend خطای 404

```bash
# پاک کردن cache
./manager.sh rebuild-frontend

# یا دستی:
rm -rf /srv/frontend/.next
docker-compose restart frontend
```

### مشکل 6: خطای CORS در Forgot Password

**علامت:**
```
Access-Control-Allow-Origin header contains multiple values 
'https://tejarat.chat, https://tejarat.chat'
```

**علت:**  
CORS header هم از Django و هم از Nginx Proxy Manager ارسال می‌شود.

**راه‌حل:**

1. ورود به NPM:
   ```
   http://YOUR_SERVER_IP:81
   ```

2. ویرایش `admin.tejarat.chat`:
   ```
   Hosts → Proxy Hosts → admin.tejarat.chat → Edit → Advanced Tab
   ```

3. **حذف خطوط CORS:**
   ```nginx
   # ❌ این خطوط را حذف کن:
   add_header Access-Control-Allow-Origin https://tejarat.chat always;
   add_header Access-Control-Allow-Methods "..." always;
   add_header Access-Control-Allow-Headers "..." always;
   add_header Access-Control-Allow-Credentials true always;
   ```

4. **Configuration صحیح NPM:**
   ```nginx
   # ✅ فقط proxy settings نگه دار:
   location /api {
       proxy_pass http://backend:8000;
       proxy_set_header Host $host;
       proxy_set_header X-Real-IP $remote_addr;
       proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
       proxy_set_header X-Forwarded-Proto $scheme;
       proxy_redirect off;
       
       proxy_connect_timeout 60s;
       proxy_send_timeout 60s;
       proxy_read_timeout 60s;
   }
   ```

5. Save کن و تست کن.

**توضیح:**  
CORS در Django تنظیم شده (`/srv/backend/core/settings.py`) و نباید در NPM تکرار شود.

**تست CORS:**
```bash
curl -X POST https://admin.tejarat.chat/api/v1/auth/forgot-password/ \
  -H "Origin: https://tejarat.chat" \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com"}' \
  -v 2>&1 | grep -i "access-control"

# خروجی صحیح (فقط یک header):
< access-control-allow-origin: https://tejarat.chat
< access-control-allow-credentials: true
```

---

## 📊 مانیتورینگ

### بررسی منابع:

```bash
# CPU & Memory
docker stats

# Disk Usage
df -h
docker system df
```

### بررسی لاگ‌ها:

```bash
# Real-time logs
docker-compose logs -f

# آخرین 100 خط
docker-compose logs --tail=100 backend

# لاگ‌های خاص
docker-compose logs --since 1h backend
```

---

## 🔒 امنیت

### Checklist:

- [ ] DEBUG=false در production
- [ ] SECRET_KEY تغییر کرده
- [ ] رمزهای قوی برای database
- [ ] SSL فعال است
- [ ] Firewall تنظیم شده (فقط 80, 443, 22)
- [ ] Backup منظم
- [ ] به‌روزرسانی منظم
- [ ] لاگ‌ها مانیتور می‌شوند

### Firewall:

```bash
# UFW
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
```

---

## 📝 نکات نهایی

1. **Backup منظم:**
   ```bash
   # Database
   docker-compose exec postgres pg_dump -U tejarat_user tejarat_db > backup.sql
   
   # Media files
   tar -czf media_backup.tar.gz /srv/backend/media
   ```

2. **به‌روزرسانی:**
   ```bash
   ./manager.sh update
   ```

3. **مانیتورینگ:**
   - بررسی روزانه لاگ‌ها
   - مانیتور منابع سرور
   - تست دوره‌ای سیستم

---

**موفق باشید! 🚀**

برای پشتیبانی: info@tejarat.chat
