# راهنمای سریع تنظیم NPM

## 🚀 تنظیم سریع در 5 دقیقه

### مرحله 1: ورود به NPM
```
آدرس: http://YOUR_IP:81
ورود اولیه: admin@example.com / changeme
```

---

### مرحله 2: تنظیم Frontend (tejarat.chat)

1. **Hosts → Proxy Hosts → Add Proxy Host**

2. **Details:**
   - Domain: `tejarat.chat`
   - Forward to: `app_frontend` port `3000`
   - ✓ Cache Assets
   - ✓ Block Exploits
   - ✓ Websockets

3. **SSL:**
   - ✓ Request SSL Certificate
   - ✓ Force SSL
   - ✓ HTTP/2

4. **Advanced:**
   - کپی کنید: `/srv/npm-frontend-config.conf`

5. **Save**

---

### مرحله 3: تنظیم Backend (admin.tejarat.chat)

1. **Hosts → Proxy Hosts → Add Proxy Host**

2. **Details:**
   - Domain: `admin.tejarat.chat`
   - Forward to: `app_backend` port `8000`
   - ✗ Cache Assets (برای API)
   - ✓ Block Exploits
   - ✓ Websockets

3. **SSL:**
   - ✓ Request SSL Certificate
   - ✓ Force SSL
   - ✓ HTTP/2

4. **Advanced:**
   - کپی کنید: `/srv/npm-backend-config.conf`

5. **Save**

---

## ✅ تست

```bash
# Frontend
curl -I https://tejarat.chat/

# Backend API
curl -I https://admin.tejarat.chat/api/v1/auth/login/

# Admin Panel
curl -I https://admin.tejarat.chat/admin/
```

---

## 🔧 عیب‌یابی سریع

### خطای 502:
```bash
docker ps | grep app_backend
docker ps | grep app_frontend
docker logs app_npm --tail 20
```

### خطای SSL:
- مطمئن شوید DNS به IP سرور اشاره می‌کند
- پورت 80 و 443 باز باشند

### خطای CORS:
- مطمئن شوید config backend را درست کپی کرده‌اید
- Origin باید `https://tejarat.chat` باشد

---

## 📝 نکات مهم

1. **Container Names:** دقیقاً `app_backend` و `app_frontend`
2. **Ports:** داخلی 8000 و 3000 (نه external)
3. **Network:** همه در `app_network`
4. **SSL:** Let's Encrypt رایگان است
5. **CORS:** فقط برای backend لازم است

---

برای جزئیات بیشتر: `/srv/NPM_CONFIGURATION_GUIDE.md`
