# 🧪 Tests Directory

این پوشه شامل تمام تست‌ها و ابزارهای کمکی سیستم است.

## 📁 ساختار پوشه

```
tests/
├── integration/          # تست‌های یکپارچه‌سازی
│   └── test_system.py   # تست جامع سیستم (MinIO + RAG Core)
├── utils/               # ابزارهای کمکی
│   ├── cleanup_old_files.py        # پاک‌سازی فایل‌های قدیمی MinIO
│   └── clear_all_conversations.py  # حذف تمام مکالمات
└── debug/               # ابزارهای دیباگ
    ├── debug_query.py           # دیباگ اتصال به RAG Core
    └── check_token_payload.py   # بررسی JWT token
```

---

## 🚀 استفاده

### تست جامع سیستم

```bash
# اجرا در Docker
docker exec app_backend python3 /app/tests/integration/test_system.py

# یا مستقیم
cd /srv/backend
python3 tests/integration/test_system.py
```

**تست‌های انجام شده:**
- ✅ آپلود فایل به MinIO
- ✅ Query عادی به RAG Core
- ✅ Streaming query به RAG Core

---

### ابزارهای Utility

#### 1. پاک‌سازی فایل‌های قدیمی MinIO

```bash
# حذف فایل‌های قدیمی‌تر از 24 ساعت
docker exec app_backend python3 /app/tests/utils/cleanup_old_files.py --hours 24

# حذف تمام فایل‌ها (خطرناک!)
docker exec app_backend python3 /app/tests/utils/cleanup_old_files.py --all
```

#### 2. حذف تمام مکالمات

```bash
docker exec app_backend python3 /app/tests/utils/clear_all_conversations.py
```

---

### ابزارهای Debug

#### 1. دیباگ اتصال RAG Core

```bash
docker exec app_backend python3 /app/tests/debug/debug_query.py
```

#### 2. بررسی JWT Token

```bash
docker exec app_backend python3 /app/tests/debug/check_token_payload.py
```

---

## 📝 نکات مهم

### برای توسعه‌دهندگان:

1. **قبل از commit:**
   - تست جامع را اجرا کنید
   - مطمئن شوید همه تست‌ها موفق هستند

2. **اضافه کردن تست جدید:**
   - تست‌های integration در `integration/`
   - تست‌های unit در `unit/` (در آینده)
   - ابزارهای کمکی در `utils/`
   - ابزارهای debug در `debug/`

3. **نام‌گذاری:**
   - فایل‌های تست: `test_*.py`
   - فایل‌های utility: نام توصیفی
   - همیشه docstring اضافه کنید

---

## 🔧 Cron Jobs

برای اجرای خودکار cleanup:

```bash
# در crontab اضافه کنید:
0 2 * * * docker exec app_backend python3 /app/tests/utils/cleanup_old_files.py --hours 24
```

---

## 📊 CI/CD

در آینده می‌توان این تست‌ها را در pipeline CI/CD اضافه کرد:

```yaml
# مثال برای GitLab CI
test:
  script:
    - docker exec app_backend python3 /app/tests/integration/test_system.py
```

---

## 🐛 گزارش مشکلات

اگر تستی fail شد:

1. لاگ‌های Docker را بررسی کنید
2. از ابزارهای debug استفاده کنید
3. مطمئن شوید سرویس‌های خارجی (MinIO, RAG Core) در دسترس هستند

---

**آخرین به‌روزرسانی:** 2025-11-30
