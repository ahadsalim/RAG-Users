# 🔧 رفع خطای CORS در Frontend

## 🐛 مشکل

Frontend با خطای CORS مواجه می‌شد:

```
Access to fetch at 'https://admin.tejarat.chat/api/v1/chat/query/stream/' 
from origin 'https://tejarat.chat' has been blocked by CORS policy: 
No 'Access-Control-Allow-Origin' header is present on the requested resource.
```

### علت:
- `NEXT_PUBLIC_API_URL` به `https://admin.tejarat.chat` تنظیم شده بود
- Frontend به جای backend اصلی، به admin panel درخواست می‌فرستاد
- Admin panel CORS header برای domain اصلی ندارد

---

## ✅ راه‌حل

### 1. تغییر Environment Variable

در فایل `/srv/deployment/.env`:

```bash
# ❌ قبل
NEXT_PUBLIC_API_URL=https://admin.tejarat.chat

# ✅ بعد
NEXT_PUBLIC_API_URL=https://api.tejarat.chat
```

### 2. Restart Docker Stack

```bash
cd /srv/deployment
docker-compose down
docker-compose up -d
```

### 3. تأیید تغییرات

```bash
docker exec app_frontend env | grep NEXT_PUBLIC_API_URL
# خروجی: NEXT_PUBLIC_API_URL=https://api.tejarat.chat
```

---

## 🎯 نتیجه

حالا frontend به backend صحیح متصل می‌شود:

```
Frontend (https://tejarat.chat)
        ↓
Backend API (https://api.tejarat.chat)
        ↓
RAG Core (https://core.tejarat.chat)
```

---

## 📝 نکات مهم

### Environment Variables در Next.js

متغیرهایی که با `NEXT_PUBLIC_` شروع می‌شوند:
- در **build time** جایگزین می‌شوند
- در **client-side** قابل دسترسی هستند
- برای تغییر آنها باید **rebuild** یا **restart** کنید

### تنظیمات مربوطه

در `/srv/deployment/.env`:

```bash
# Backend API URL (برای frontend)
NEXT_PUBLIC_API_URL=https://api.tejarat.chat

# WebSocket URL (برای real-time features)
NEXT_PUBLIC_WS_URL=wss://api.tejarat.chat

# Backend URL (برای SSR)
BACKEND_URL=https://admin.tejarat.chat
```

---

## 🔍 Debug

اگر هنوز خطای CORS دیدید:

### 1. چک کردن Environment Variable

```bash
docker exec app_frontend env | grep NEXT_PUBLIC
```

### 2. چک کردن Network Tab

در Browser DevTools (F12):
- Network tab را باز کنید
- درخواست را پیدا کنید
- URL را بررسی کنید

### 3. چک کردن CORS Headers

```bash
curl -I https://api.tejarat.chat/api/v1/chat/query/stream/ \
  -H "Origin: https://tejarat.chat"
```

باید header زیر را ببینید:
```
Access-Control-Allow-Origin: https://tejarat.chat
```

---

## 🚀 تست

1. صفحه را refresh کنید (Ctrl+Shift+R)
2. یک سوال بپرسید
3. در Console نباید خطای CORS ببینید
4. پاسخ باید به درستی نمایش داده شود

---

**تاریخ:** 2025-12-01  
**وضعیت:** ✅ حل شد
