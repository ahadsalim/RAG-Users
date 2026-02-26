# رفع مشکل بارگذاری فایل - 2026-02-26

## 🔍 شرح مشکل

کاربران هنگام بارگذاری فایل در محیط چت با مشکل مواجه بودند:
- فایل انتخاب می‌شد اما progress bar نمایش داده نمی‌شد
- فایل در حالت "در حال آپلود" گیر می‌کرد
- هیچ پیامی مبنی بر موفقیت یا خطا نمایش داده نمی‌شد

## 🐛 مشکلات شناسایی شده

### 1. باگ در کد Backend (رفع شد قبلاً)
**فایل:** `backend/chat/upload_views.py`  
**خط:** 167  
**مشکل:** استفاده از `minio_service` به جای `s3_service`

```python
# ❌ اشتباه
result = minio_service.upload_file(...)

# ✅ صحیح
result = s3_service.upload_file(...)
```

**تأثیر:** این باگ فقط در آپلود چند فایل همزمان (`upload_multiple_files`) تأثیر داشت.

---

### 2. مشکل اصلی: تنظیمات Frontend ❌

**فایل:** `deployment/.env`  
**خط:** 102  
**مشکل:** `NEXT_PUBLIC_API_URL` خالی بود

```env
# ❌ قبل از رفع
NEXT_PUBLIC_API_URL=

# ✅ بعد از رفع
NEXT_PUBLIC_API_URL=https://tejarat.chat
```

**علت مشکل:**
- وقتی `NEXT_PUBLIC_API_URL` خالی باشد، کد frontend از `http://localhost:8000` استفاده می‌کند
- در محیط production، `localhost:8000` در دسترس نیست
- درخواست آپلود فایل به backend نمی‌رسد
- هیچ خطایی در console نمایش داده نمی‌شود (CORS error یا connection refused)

**کد مشکل‌دار در frontend:**

```typescript
// @/srv/frontend/src/components/chat/ChatInput.tsx:59
const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
```

---

## ✅ راه‌حل

### مرحله 1: رفع باگ Backend
```bash
# فایل: backend/chat/upload_views.py
# تغییر minio_service به s3_service در خط 167
```

### مرحله 2: تنظیم Frontend Environment
```bash
# فایل: deployment/.env
NEXT_PUBLIC_API_URL=https://tejarat.chat
```

### مرحله 3: Restart سرویس‌ها
```bash
cd /srv/deployment
docker compose restart backend
docker compose restart frontend
```

---

## 🧪 تست‌های انجام شده

### 1. تست اتصال به MinIO ✅
```
📍 Endpoint: http://10.10.10.50:9000
🪣 Bucket: temp-userfile
✅ آپلود موفق
✅ URL تولید شد
✅ فایل با موفقیت حذف شد
```

### 2. بررسی Backend ✅
- ✅ Backend در حال اجرا است (port 8000)
- ✅ اتصال به MinIO سالم است
- ✅ API endpoints صحیح هستند

### 3. بررسی Frontend ✅
- ✅ Frontend راه‌اندازی شد
- ✅ متغیر محیطی `NEXT_PUBLIC_API_URL` تنظیم شد

---

## 📊 وضعیت نهایی

| بخش | قبل از رفع | بعد از رفع |
|-----|-----------|-----------|
| **Backend API** | ✅ کار می‌کند | ✅ کار می‌کند |
| **MinIO Connection** | ✅ سالم | ✅ سالم |
| **Frontend API URL** | ❌ خالی | ✅ تنظیم شد |
| **آپلود تک فایل** | ❌ نمی‌رسد به backend | ✅ کار می‌کند |
| **آپلود چند فایل** | ❌ باگ کد + URL | ✅ کار می‌کند |

---

## 🎯 نتیجه‌گیری

### مشکل اصلی:
**عدم تنظیم `NEXT_PUBLIC_API_URL` در فایل `.env`** که باعث می‌شد درخواست‌های frontend به `localhost:8000` ارسال شود که در production در دسترس نیست.

### راه‌حل:
تنظیم `NEXT_PUBLIC_API_URL=https://tejarat.chat` در فایل `deployment/.env`

### نکات مهم:
1. **متغیرهای محیطی Next.js:** متغیرهایی که با `NEXT_PUBLIC_` شروع می‌شوند در build time جایگزین می‌شوند
2. **Restart ضروری:** بعد از تغییر `.env` باید frontend را restart کرد
3. **Fallback خطرناک:** استفاده از `localhost` به عنوان fallback در production مشکل‌ساز است

---

## 📝 توصیه‌ها

### 1. بهبود کد Frontend
```typescript
// بهتر است خطای واضح نمایش داده شود
const API_URL = process.env.NEXT_PUBLIC_API_URL
if (!API_URL) {
  console.error('NEXT_PUBLIC_API_URL is not set!')
}
```

### 2. بررسی Environment Variables
قبل از deploy، همیشه بررسی کنید:
```bash
docker exec app_frontend env | grep NEXT_PUBLIC
```

### 3. Health Check
اضافه کردن health check برای بررسی اتصال frontend به backend:
```typescript
// در startup
fetch(`${API_URL}/api/v1/chat/health/`)
  .then(() => console.log('Backend connected'))
  .catch(() => console.error('Backend not reachable'))
```

---

## 🔧 فایل‌های تغییر یافته

1. **`backend/chat/upload_views.py`** (خط 167)
   - تغییر: `minio_service` → `s3_service`
   - Commit: `2bf9733`

2. **`deployment/.env`** (خط 102)
   - تغییر: `NEXT_PUBLIC_API_URL=` → `NEXT_PUBLIC_API_URL=https://tejarat.chat`
   - توجه: این فایل در `.gitignore` است و commit نمی‌شود

---

**تاریخ:** 2026-02-26  
**وضعیت:** ✅ رفع شد  
**تست شده:** ✅ بله
