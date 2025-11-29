# 📊 تحلیل متغیرهای محیطی در .env

## 🔍 بررسی متغیرهای خطوط 152-164

### ❌ **متغیرهای استفاده نشده (باید حذف شوند):**

#### 1. متغیرهای BACKUP_*
```bash
BACKUP_RETENTION_DAYS=30
BACKUP_S3_BUCKET=
BACKUP_S3_ACCESS_KEY=
BACKUP_S3_SECRET_KEY=dT4;yMv-_c17?N+JkWo]MUuFiKT%rt=o?[]=dYQ]%imzjSrv*U?f>_m9?=u8#7<
BACKUP_S3_REGION=us-east-1
BACKUP_LOCAL_PATH=/srv/backups
```

**وضعیت:** ❌ **هیچ کجا استفاده نشده‌اند**

**جستجو در کد:**
- ✅ بررسی شد در `/srv/backend/**/*.py`
- ✅ بررسی شد در `/srv/frontend/**/*.{js,ts,tsx}`
- ❌ **هیچ فایلی از این متغیرها استفاده نمی‌کند**

**نکته:** 
- `backup_codes` در `accounts/models.py` برای 2FA است (کدهای پشتیبان احراز هویت)
- **هیچ ربطی به این متغیرهای BACKUP_S3 ندارد**

---

#### 2. متغیرهای S3_*
```bash
S3_ENDPOINT_URL=https://storage.tejarat.chat:9000
S3_ACCESS_KEY_ID=eH01EjH7zdlIHEzlJ9Sb
S3_SECRET_ACCESS_KEY=5mswuxXYnZtNHSWhEDw8WUe51ztiOTlRCQa40r7i
S3_REGION=us-east-1
S3_USE_SSL=true
```

**وضعیت:** ❌ **هیچ کجا استفاده نشده‌اند**

**جستجو در کد:**
- ✅ بررسی شد در `settings.py`
- ✅ بررسی شد در `storage.py`
- ❌ **هیچ فایلی از S3_* استفاده نمی‌کند**

---

### ✅ **متغیرهای صحیح که باید استفاده شوند:**

```bash
# MinIO Configuration (استفاده می‌شود در core/storage.py)
MINIO_ENDPOINT=storage.tejarat.chat:9000
MINIO_ACCESS_KEY=eH01EjH7zdlIHEzlJ9Sb
MINIO_SECRET_KEY=5mswuxXYnZtNHSWhEDw8WUe51ztiOTlRCQa40r7i
MINIO_BUCKET_NAME=shared-storage
MINIO_USE_SSL=true
MINIO_REGION=us-east-1
```

**استفاده در:**
- ✅ `/srv/backend/core/settings.py` (خطوط 493-498)
- ✅ `/srv/backend/core/storage.py` (خطوط 19-32)

---

## 🔧 اقدامات پیشنهادی:

### 1️⃣ حذف متغیرهای استفاده نشده:
```bash
# حذف این خطوط از .env:
BACKUP_RETENTION_DAYS=30
BACKUP_S3_BUCKET=
BACKUP_S3_ACCESS_KEY=
BACKUP_S3_SECRET_KEY=dT4;yMv-_c17?N+JkWo]MUuFiKT%rt=o?[]=dYQ]%imzjSrv*U?f>_m9?=u8#7<
BACKUP_S3_REGION=us-east-1
BACKUP_LOCAL_PATH=/srv/backups

S3_ENDPOINT_URL=https://storage.tejarat.chat:9000
S3_ACCESS_KEY_ID=eH01EjH7zdlIHEzlJ9Sb
S3_SECRET_ACCESS_KEY=5mswuxXYnZtNHSWhEDw8WUe51ztiOTlRCQa40r7i
S3_REGION=us-east-1
S3_USE_SSL=true
```

### 2️⃣ اضافه کردن متغیرهای صحیح MinIO:
```bash
# MinIO Configuration (برای file upload)
MINIO_ENDPOINT=storage.tejarat.chat:9000
MINIO_ACCESS_KEY=eH01EjH7zdlIHEzlJ9Sb
MINIO_SECRET_KEY=5mswuxXYnZtNHSWhEDw8WUe51ztiOTlRCQa40r7i
MINIO_BUCKET_NAME=shared-storage
MINIO_USE_SSL=true
MINIO_REGION=us-east-1
```

---

## 📋 خلاصه:

| متغیر | وضعیت | استفاده | اقدام |
|-------|-------|---------|-------|
| `BACKUP_*` | ❌ استفاده نشده | هیچ کجا | 🗑️ حذف |
| `S3_*` | ❌ استفاده نشده | هیچ کجا | 🗑️ حذف |
| `MINIO_*` | ✅ استفاده می‌شود | `storage.py` | ✅ نگه‌داری |

---

## 💡 توضیحات:

### چرا S3_* استفاده نمی‌شود؟
کد شما از `MINIO_*` استفاده می‌کند نه `S3_*`:

```python
# در settings.py
MINIO_ENDPOINT = config('MINIO_ENDPOINT', default='localhost:9000')
MINIO_ACCESS_KEY = config('MINIO_ACCESS_KEY', default='minioadmin')
MINIO_SECRET_KEY = config('MINIO_SECRET_KEY', default='minioadmin')
```

```python
# در storage.py
endpoint_url = settings.MINIO_ENDPOINT
aws_access_key_id=settings.MINIO_ACCESS_KEY
aws_secret_access_key=settings.MINIO_SECRET_KEY
```

### چرا BACKUP_* استفاده نمی‌شود؟
این متغیرها احتمالاً برای یک feature backup که هنوز پیاده‌سازی نشده تعریف شده‌اند.

---

## ✅ نتیجه‌گیری:

**12 متغیر از 13 متغیر (92%) استفاده نمی‌شوند!**

این متغیرها احتمالاً:
1. از یک template کپی شده‌اند
2. برای feature های آینده تعریف شده‌اند
3. اشتباهی تعریف شده‌اند

**توصیه:** حذف کنید و فقط `MINIO_*` را اضافه کنید.
