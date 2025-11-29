# 🔴 گزارش مشکل: RAG Core Timeout

## 📋 خلاصه مشکل

**علت اصلی:** سرور RAG Core (`https://core.tejarat.chat`) با خطای **504 Gateway Timeout** پاسخ می‌دهد.

---

## 🔍 تست‌های انجام شده

### 1️⃣ تست اتصال به سرور
```bash
curl -v https://core.tejarat.chat/health
```

**نتیجه:**
- ✅ DNS resolve شد: `45.92.219.71`
- ✅ SSL certificate معتبر است
- ✅ اتصال برقرار شد
- ❌ **504 Gateway Time-out** از OpenResty

```html
<html>
<head><title>504 Gateway Time-out</title></head>
<body>
<center><h1>504 Gateway Time-out</h1></center>
<hr><center>openresty</center>
</body>
</html>
```

### 2️⃣ تست API Endpoint
```bash
curl -X POST https://core.tejarat.chat/api/v1/query/ \
  -H "Content-Type: application/json" \
  -d '{"query":"تست","language":"fa","max_results":5}'
```

**نتیجه:**
- ❌ **504 Gateway Time-out**

---

## 🎯 تحلیل مشکل

### مشکل در سمت RAG Core است:

1. **OpenResty (Nginx) در حال اجرا است**
   - Reverse proxy کار می‌کند
   - SSL certificate OK
   - Port 443 باز است

2. **Backend RAG Core پاسخ نمی‌دهد**
   - احتمالاً سرویس Python/FastAPI خاموش است
   - یا در حال crash است
   - یا timeout خیلی کوتاه است

3. **Nginx timeout settings**
   - OpenResty بعد از مدت زمانی (احتمالاً 60 ثانیه) قطع می‌کند
   - Backend پاسخ نمی‌دهد

---

## 🔧 راه‌حل‌های پیشنهادی

### در سمت RAG Core (سیستم مرکزی):

#### 1. بررسی وضعیت سرویس
```bash
# بررسی کنید که سرویس RAG Core در حال اجرا است
systemctl status rag-core
# یا
docker ps | grep rag-core
# یا
pm2 list
```

#### 2. بررسی لاگ‌ها
```bash
# لاگ‌های سرویس RAG Core
tail -f /var/log/rag-core/error.log
# یا
docker logs -f rag-core
# یا
pm2 logs rag-core
```

#### 3. بررسی Port
```bash
# بررسی کنید که پورت 7001 در حال گوش دادن است
netstat -tulpn | grep 7001
# یا
ss -tulpn | grep 7001
```

#### 4. تست مستقیم Backend
```bash
# اگر RAG Core روی localhost:7001 است
curl http://localhost:7001/health
curl http://localhost:7001/api/v1/query/ \
  -H "Content-Type: application/json" \
  -d '{"query":"تست","language":"fa"}'
```

#### 5. افزایش Nginx Timeout
در فایل nginx config:
```nginx
location /api/ {
    proxy_pass http://localhost:7001;
    proxy_read_timeout 300s;  # 5 minutes
    proxy_connect_timeout 300s;
    proxy_send_timeout 300s;
}
```

#### 6. بررسی Resource Usage
```bash
# CPU و Memory
top
htop

# Disk space
df -h

# Memory
free -h
```

---

## 📊 اطلاعات فنی

### سرور RAG Core:
- **URL:** `https://core.tejarat.chat`
- **IP:** `45.92.219.71`
- **SSL:** ✅ Let's Encrypt (valid until Feb 12, 2026)
- **Web Server:** OpenResty (Nginx)
- **Backend:** احتمالاً FastAPI/Python روی port 7001

### خطاهای دریافتی:
- **504 Gateway Time-out** - Backend پاسخ نمی‌دهد
- **OpenResty** - Reverse proxy در حال اجرا است

### Timeout Settings:
- **Frontend:** 120 seconds
- **Backend (Django):** 120 seconds
- **OpenResty:** احتمالاً 60 seconds (باید افزایش یابد)

---

## ✅ چک‌لیست برای Admin سیستم مرکزی

- [ ] سرویس RAG Core در حال اجرا است؟
- [ ] Port 7001 باز است و در حال listen است؟
- [ ] لاگ‌ها چه خطایی نشان می‌دهند؟
- [ ] CPU/Memory/Disk کافی است؟
- [ ] Database در دسترس است؟
- [ ] Dependencies نصب شده‌اند؟
- [ ] Environment variables تنظیم شده‌اند؟
- [ ] Nginx timeout settings کافی است؟

---

## 🔄 مراحل بعدی

1. **Admin سیستم مرکزی باید:**
   - سرویس RAG Core را restart کند
   - لاگ‌ها را بررسی کند
   - مشکل را برطرف کند

2. **بعد از برطرف شدن مشکل:**
   - تست مجدد با curl
   - تست از طریق UI
   - بررسی performance

---

## 📞 تماس با تیم

اگر مشکل ادامه داشت:
- لاگ‌های کامل RAG Core را ارسال کنید
- خروجی `systemctl status` یا `docker logs` را بفرستید
- خروجی `netstat -tulpn | grep 7001` را بفرستید

---

**تاریخ گزارش:** 2024-11-29  
**وضعیت:** 🔴 Critical - سرویس در دسترس نیست
