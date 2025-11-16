# راهنمای تغییر دامنه سیستم

## تغییر دامنه (Domain Configuration)

اگر می‌خواهید دامنه سیستم را تغییر دهید، فقط کافی است فایل `.env` را ویرایش کنید:

### مراحل تغییر دامنه:

1. فایل `/srv/.env` را باز کنید
2. مقادیر زیر را با دامنه جدید خود جایگزین کنید:

```env
# ===========================
# Frontend Settings
# ===========================
NEXT_PUBLIC_API_URL=https://YOUR_NEW_ADMIN_DOMAIN.com
NEXT_PUBLIC_WS_URL=wss://YOUR_NEW_ADMIN_DOMAIN.com
BACKEND_URL=https://YOUR_NEW_ADMIN_DOMAIN.com
```

3. سرویس‌ها را restart کنید:

```bash
cd /srv/deployment
docker-compose restart frontend backend
```

### مثال:

اگر دامنه جدید شما `api.mycompany.com` است:

```env
NEXT_PUBLIC_API_URL=https://api.mycompany.com
NEXT_PUBLIC_WS_URL=wss://api.mycompany.com
BACKEND_URL=https://api.mycompany.com
```

### نکات مهم:

1. **NEXT_PUBLIC_API_URL**: استفاده می‌شود برای درخواست‌های مستقیم از مرورگر کاربر
2. **NEXT_PUBLIC_WS_URL**: استفاده می‌شود برای اتصالات WebSocket
3. **BACKEND_URL**: استفاده می‌شود برای درخواست‌های server-side در Next.js API routes

### تنظیمات Nginx Proxy Manager:

بعد از تغییر دامنه، فراموش نکنید که:

1. در Nginx Proxy Manager یک Proxy Host جدید برای دامنه جدید ایجاد کنید
2. SSL Certificate برای دامنه جدید صادر کنید (Let's Encrypt)
3. Forward Hostname/IP را به `app_backend` و Port را `8000` تنظیم کنید

### Default Values:

اگر environment variable تنظیم نشود، مقادیر پیش‌فرض زیر استفاده می‌شوند:

- `BACKEND_URL`: `https://admin.tejarat.chat`
- `NEXT_PUBLIC_API_URL`: `http://localhost:8000`
- `NEXT_PUBLIC_WS_URL`: `ws://localhost:8000`
