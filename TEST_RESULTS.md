# 📊 گزارش تست سیستم - 2024-11-29

## 🎯 تست‌های درخواستی:

1. ✅ ذخیره فایل در MinIO
2. ✅ ارسال سوال متنی به سیستم مرکزی
3. ✅ ارسال سوال با 2 فایل به سیستم مرکزی

---

## 📋 نتایج تست‌ها:

### ❌ تست 1: ذخیره فایل در MinIO
**وضعیت:** ناموفق  
**دلیل:** MinIO راه‌اندازی نشده است

**جزئیات:**
- MinIO container وجود ندارد
- تنظیمات MinIO در `/srv/deployment/.env` موجود نیست
- Backend نمی‌تواند به `localhost:9000` متصل شود

**خطا:**
```
ConnectionRefusedError: [Errno 111] Connection refused
Could not connect to the endpoint URL: "http://localhost:9000/shared-storage"
```

---

### ❌ تست 2: ارسال سوال متنی به RAG Core
**وضعیت:** ناموفق  
**دلیل:** RAG Core backend timeout می‌دهد

**جزئیات:**
- URL: `https://core.tejarat.chat`
- API Key: ✅ موجود
- DNS: ✅ Resolve شد (`45.92.219.71`)
- SSL: ✅ معتبر
- اتصال: ✅ برقرار شد
- **Response: ❌ 504 Gateway Timeout**

**زمان:**
- ⏱️ **90.09 ثانیه** (سپس timeout)

**خطا:**
```html
<html>
<head><title>504 Gateway Time-out</title></head>
<body>
<center><h1>504 Gateway Time-out</h1></center>
<hr><center>openresty</center>
</body>
</html>
```

**Query ارسالی:**
```json
{
  "query": "قانون مدنی ایران در مورد مالکیت چه می‌گوید؟",
  "language": "fa",
  "max_results": 5,
  "use_cache": true,
  "use_reranking": true
}
```

---

### ❌ تست 3: ارسال سوال با فایل
**وضعیت:** ناموفق  
**دلیل:** تست 1 و 2 ناموفق بودند

**پیش‌نیازها:**
- ❌ MinIO برای آپلود فایل
- ❌ RAG Core برای پردازش query

---

## 🔍 تحلیل مشکلات:

### 1️⃣ MinIO
**مشکل:** سرویس MinIO راه‌اندازی نشده

**راه‌حل:**
```bash
# نصب و راه‌اندازی MinIO
docker run -d \
  --name minio \
  -p 9000:9000 \
  -p 9001:9001 \
  -e "MINIO_ROOT_USER=minioadmin" \
  -e "MINIO_ROOT_PASSWORD=minioadmin" \
  -v /data/minio:/data \
  minio/minio server /data --console-address ":9001"
```

**تنظیمات .env:**
```bash
MINIO_ENDPOINT=localhost:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin
MINIO_BUCKET_NAME=shared-storage
MINIO_USE_SSL=false
MINIO_REGION=us-east-1
```

---

### 2️⃣ RAG Core Backend
**مشکل:** Backend Python/FastAPI پاسخ نمی‌دهد

**علائم:**
- OpenResty (Nginx) کار می‌کند ✅
- SSL certificate OK ✅
- Backend timeout می‌دهد ❌

**احتمالات:**
1. سرویس RAG Core خاموش است
2. Port 7001 در حال listen نیست
3. Backend crash کرده
4. Database در دسترس نیست
5. CPU/Memory کافی نیست
6. Nginx timeout کوتاه است (~90 ثانیه)

**بررسی‌های لازم در سرور RAG Core:**

```bash
# 1. وضعیت سرویس
systemctl status rag-core
# یا
docker ps | grep rag-core
# یا
pm2 list

# 2. بررسی port
netstat -tulpn | grep 7001
ss -tulpn | grep 7001

# 3. لاگ‌ها
tail -f /var/log/rag-core/error.log
docker logs -f rag-core
pm2 logs rag-core

# 4. تست مستقیم
curl http://localhost:7001/health
curl http://localhost:7001/api/v1/query/ \
  -H "Content-Type: application/json" \
  -d '{"query":"تست","language":"fa"}'

# 5. منابع سیستم
top
free -h
df -h

# 6. افزایش Nginx timeout
# در فایل nginx.conf:
proxy_read_timeout 300s;
proxy_connect_timeout 300s;
proxy_send_timeout 300s;
```

---

## 📊 خلاصه زمان‌ها:

| تست | زمان | وضعیت |
|-----|------|-------|
| MinIO Upload | - | ❌ سرویس نیست |
| Text Query | 90.09s | ❌ Timeout |
| Query + Files | - | ❌ پیش‌نیاز ناموفق |

---

## ✅ اقدامات انجام شده:

### در سمت کد:
1. ✅ URL configuration اصلاح شد
2. ✅ Timeout به 120 ثانیه افزایش یافت
3. ✅ Error handling بهبود یافت
4. ✅ پیام‌های خطا به فارسی
5. ✅ اسکریپت‌های تست نوشته شد

### فایل‌های ایجاد شده:
- `/srv/test_complete_system.py` - تست کامل (MinIO + RAG)
- `/srv/test_rag_only.py` - تست فقط RAG Core
- `/srv/backend/debug_query.py` - دیباگ اتصال

---

## 🔧 اقدامات مورد نیاز:

### فوری (Critical):
1. **راه‌اندازی MinIO**
   - نصب container
   - تنظیم .env
   - ایجاد bucket

2. **بررسی RAG Core Backend**
   - چک کردن سرویس
   - بررسی لاگ‌ها
   - restart سرویس
   - افزایش Nginx timeout

### بعد از برطرف شدن:
3. اجرای مجدد تست‌ها
4. بررسی performance
5. تست end-to-end

---

## 📞 اطلاعات فنی:

### سرور RAG Core:
- **URL:** `https://core.tejarat.chat`
- **IP:** `45.92.219.71`
- **SSL:** ✅ Let's Encrypt (valid)
- **Web Server:** OpenResty (Nginx)
- **Backend:** Python/FastAPI (port 7001) - ❌ Not responding

### Backend Django:
- **Container:** `app_backend`
- **Status:** ✅ Up 4 hours
- **Python:** 3.12
- **Dependencies:** ✅ Installed

### MinIO:
- **Container:** ❌ Not found
- **Expected Port:** 9000
- **Config:** ❌ Missing in .env

---

## 🎯 نتیجه‌گیری:

**هیچ یک از تست‌ها موفق نبود** به دلایل زیر:

1. **MinIO راه‌اندازی نشده** → نمی‌توان فایل آپلود کرد
2. **RAG Core backend پاسخ نمی‌دهد** → نمی‌توان query ارسال کرد

**کد سیستم کاربران آماده است** ولی سرویس‌های زیرساختی (MinIO و RAG Core) مشکل دارند.

---

**تاریخ تست:** 2024-11-29 11:17 UTC  
**مدت زمان کل:** ~90 ثانیه  
**وضعیت:** 🔴 Critical - نیاز به اقدام فوری
