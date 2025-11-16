# 📚 مستندات پروژه تجارت چت

**آخرین بروزرسانی:** 16 نوامبر 2025

---

## 📋 فهرست مطالب

1. [نصب و راه‌اندازی](#نصب-و-راه‌اندازی)
2. [تنظیمات دامنه](#تنظیمات-دامنه)
3. [تست OTP](#تست-otp)
4. [مدیریت سیستم](#مدیریت-سیستم)
5. [ساختار پروژه](#ساختار-پروژه)
6. [تغییرات اخیر](#تغییرات-اخیر)

---

## 🚀 نصب و راه‌اندازی

### پیش‌نیازها:
- Ubuntu/Debian Server
- دسترسی Root
- دامنه (اختیاری)

### نصب:
```bash
cd /srv/deployment
sudo bash start.sh
```

**نکات مهم:**
- اسکریپت به صورت خودکار Docker و تمام وابستگی‌ها را نصب می‌کند
- **BACKEND_URL** را درست وارد کنید (مثال: `https://admin.tejarat.chat`)
- رمزهای عبور به صورت خودکار تولید می‌شوند
- فایل `.env` در `/srv/deployment/.env` ذخیره می‌شود

---

## 🌐 تنظیمات دامنه

### دامنه‌های مورد نیاز:
```
Frontend:  https://tejarat.chat
Backend:   https://admin.tejarat.chat
```

### تنظیم در Nginx Proxy Manager:

1. **دسترسی به NPM:**
   ```
   http://YOUR-SERVER-IP:81
   Email: admin@example.com
   Password: changeme
   ```

2. **ایجاد Proxy Host برای Backend:**
   - Domain: `admin.tejarat.chat`
   - Forward to: `backend:8000`
   - WebSocket: ✅ فعال
   - SSL: ✅ Let's Encrypt

3. **ایجاد Proxy Host برای Frontend:**
   - Domain: `tejarat.chat`
   - Forward to: `frontend:3000`
   - SSL: ✅ Let's Encrypt

---

## 🔐 تست OTP

### مشاهده کد OTP:

**روش 1: لاگ‌های Backend**
```bash
cd /srv/deployment
docker-compose logs -f backend | grep "CODE:"
```

خروجی:
```
==================================================
✅ Bale OTP SENT
🔐 CODE: 123456
📱 Phone: 09121234567
==================================================
```

**روش 2: مشاهده لاگ‌های ساده**
```bash
docker-compose logs backend --tail 50 | grep "CODE:"
```

### پاک کردن Cache (برای تست مجدد):

**مشکل:** "لطفا 2 دقیقه صبر کنید"

**راه‌حل:**
```bash
cd /srv/deployment
./manager.sh
# انتخاب گزینه: Clear Cache
```

یا به صورت دستی:
```bash
docker-compose exec -T backend python manage.py shell << 'PYEOF'
from django.core.cache import cache
cache.clear()
print("✅ Cache cleared!")
PYEOF
```

### تست API مستقیم:

```bash
# ارسال OTP
docker-compose exec backend curl -s -X POST \
  http://localhost:8000/api/v1/auth/send-otp/ \
  -H "Content-Type: application/json" \
  -d '{"phone_number": "09121234567", "method": "bale"}'

# تایید OTP
docker-compose exec backend curl -s -X POST \
  http://localhost:8000/api/v1/auth/verify-otp/ \
  -H "Content-Type: application/json" \
  -d '{"phone_number": "09121234567", "otp_code": "123456"}'
```

### تنظیمات OTP:
- **مدت اعتبار:** 300 ثانیه (5 دقیقه)
- **Rate Limit:** 120 ثانیه (2 دقیقه)
- **روش پیش‌فرض:** Bale Messenger
- **Fallback:** SMS (Kavenegar)

---

## 🛠️ مدیریت سیستم

### اسکریپت مدیریت:
```bash
cd /srv/deployment
./manager.sh
```

### دستورات مفید:

**مشاهده وضعیت:**
```bash
docker-compose ps
```

**Restart سرویس‌ها:**
```bash
docker-compose restart backend frontend
```

**مشاهده لاگ‌ها:**
```bash
docker-compose logs -f backend
docker-compose logs -f frontend
```

**پاک کردن Cache:**
```bash
./manager.sh  # انتخاب Clear Cache
```

**اجرای Migration:**
```bash
docker-compose exec backend python manage.py migrate
```

**جمع‌آوری Static Files:**
```bash
docker-compose exec backend python manage.py collectstatic --noinput
```

**ایجاد Superuser:**
```bash
docker-compose exec backend python manage.py createsuperuser
```

---

## 📂 ساختار پروژه

```
/srv/
├── backend/                    # Django Backend
│   ├── accounts/              # مدیریت کاربران
│   ├── chat/                  # سیستم چت
│   ├── core/                  # تنظیمات اصلی
│   ├── notifications/         # اعلان‌ها و SMS
│   ├── scripts/               # اسکریپت‌های کمکی
│   │   ├── clear_otp_cache.py
│   │   └── create_admin.py
│   └── manage.py
│
├── frontend/                   # Next.js Frontend
│   ├── src/
│   │   ├── app/
│   │   │   ├── auth/login/   # صفحه لاگین
│   │   │   └── chat/         # صفحه چت
│   │   ├── components/
│   │   └── store/
│   └── public/
│
├── deployment/                 # Docker & Deployment
│   ├── docker-compose.yml
│   ├── start.sh               # اسکریپت نصب
│   ├── manager.sh             # مدیریت سیستم
│   ├── backup_manager.sh      # مدیریت بکاپ
│   ├── nginx/
│   └── .env                   # تنظیمات محیطی
│
├── documents/                  # مستندات
│   └── README.md              # این فایل
│
└── backups/                    # پشتیبان‌ها
```

---

## 📝 تغییرات اخیر

### نوامبر 2025:

#### ✅ سیستم OTP و احراز هویت:
- **تایمر 5 دقیقه** برای کد OTP
- **دکمه ارسال مجدد** بعد از اتمام تایمر
- **لاگ کد در Console** برای تست
- **پیش‌فرض Bale Messenger** به جای SMS
- **Fallback خودکار** به SMS در صورت خطا

#### ✅ صفحه لاگین:
- **تفکیک کاربر حقیقی/حقوقی**
- **ثبت‌نام خودکار** برای کاربران حقیقی
- **لینک ثبت‌نام** فقط برای کاربران حقوقی
- **UI بهبود یافته** با تایمر و نمایش بهتر

#### ✅ Backend:
- **اصلاح BACKEND_URL** در start.sh
- **بهبود لاگ‌ها** با emoji و فرمت زیبا
- **اسکریپت‌های کمکی** در `/srv/backend/scripts/`

#### ✅ مستندات:
- **تمیزسازی documents**
- **یکپارچه‌سازی** در یک فایل README
- **راهنمای کامل** تست و مدیریت

---

## 🔧 عیب‌یابی

### مشکل: خطای 500 در ارسال OTP
**علت:** BACKEND_URL اشتباه در `.env`  
**راه‌حل:**
```bash
nano /srv/deployment/.env
# تغییر BACKEND_URL به آدرس صحیح
docker-compose restart frontend
```

### مشکل: Rate Limit (429)
**علت:** ارسال مکرر درخواست  
**راه‌حل:**
```bash
./manager.sh  # Clear Cache
```

### مشکل: کد OTP نمایش داده نمی‌شود
**راه‌حل:**
```bash
docker-compose logs -f backend | grep "CODE:"
```

### مشکل: Bale کار نمی‌کند
**علت:** شماره تلفن باید کاربر Bale باشد  
**راه‌حل:** سیستم به صورت خودکار به SMS سوئیچ می‌کند

---

## 📞 پشتیبانی

### لاگ‌ها:
```bash
# همه لاگ‌ها
docker-compose logs -f

# Backend
docker-compose logs -f backend

# Frontend
docker-compose logs -f frontend
```

### Restart:
```bash
# همه سرویس‌ها
docker-compose restart

# یک سرویس خاص
docker-compose restart backend
```

### Backup:
```bash
cd /srv/deployment
./backup_manager.sh backup-full
```

---

## 🎯 دسترسی سریع

### URLs:
- **Frontend:** https://tejarat.chat
- **Backend API:** https://admin.tejarat.chat/api
- **Django Admin:** https://admin.tejarat.chat/admin
- **NPM Admin:** http://SERVER-IP:81

### Credentials:
```
Superadmin:
  Phone: 09121082690
  Email: superadmin@tejarat.chat
  Password: admin123

NPM (اولین ورود):
  Email: admin@example.com
  Password: changeme
```

---

**✅ برای اطلاعات بیشتر به فایل‌های deployment مراجعه کنید:**
- `/srv/deployment/start.sh` - نصب
- `/srv/deployment/manager.sh` - مدیریت
- `/srv/deployment/backup_manager.sh` - بکاپ
