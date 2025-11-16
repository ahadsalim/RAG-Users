# Backend Scripts

این پوشه شامل اسکریپت‌های کمکی برای مدیریت backend است.

## اسکریپت‌های موجود:

### 1. `clear_otp_cache.py`
پاک کردن cache مربوط به OTP برای تست

**استفاده:**
```bash
docker-compose exec backend python scripts/clear_otp_cache.py
```

### 2. `create_admin.py`
ایجاد کاربر ادمین

**استفاده:**
```bash
docker-compose exec backend python scripts/create_admin.py
```

---

**نکته:** این اسکریپت‌ها برای development و testing هستند.
