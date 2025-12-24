# 🔐 راهنمای تنظیم بکآپ خودکار

این راهنما نحوه تنظیم بکآپ خودکار به سرور پشتیبان را توضیح می‌دهد.

---

## 📋 پیش‌نیازها

1. **سرور پشتیبان**: یک VPS برای نگهداری بکآپ‌ها
2. **دسترسی SSH**: دسترسی root به سرور پشتیبان
3. **فضای دیسک کافی**: حداقل 50GB در سرور پشتیبان

---

## 📝 نکات مهم

### ⏰ نگهداری بکآپ‌ها:

- **بکآپ‌های محلی**: حداکثر 3 روز (برای صرفه‌جویی در فضای دیسک)
- **بکآپ‌های سرور پشتیبان**: 30 روز (قابل تنظیم در `.env`)

### 🔐 محتویات بکآپ خودکار (هر 6 ساعت):

1. **PostgreSQL Database** - تمام داده‌های کاربران
2. **Redis Data** - Cache و Session‌ها
3. **NPM Data** - تنظیمات Nginx Proxy Manager
4. **فایل .env** - تنظیمات محیطی

### 🔐 محتویات بکآپ کامل (دستی):

1. **PostgreSQL Database** - تمام داده‌های کاربران
2. **Redis Data** - Cache و Session‌ها
3. **Media Files** - فایل‌های رسانه‌ای (اگر از S3 استفاده نمی‌کنید)
4. **Static Files** - فایل‌های استاتیک
5. **Nginx Proxy Manager Data** - تنظیمات Nginx Proxy Manager
6. **Nginx Proxy Manager SSL Certificates (Let's Encrypt)** - گواهی‌های SSL
7. **فایل .env** - تنظیمات محیطی

---

## 🔧 مرحله 1: تنظیم SSH Key

### در سرور اصلی (Production):

```bash
# 1. ایجاد SSH Key برای بکآپ (ED25519 - سریع و امن)
ssh-keygen -t ed25519 -f /root/.ssh/backup_key -N ""

# 2. نمایش Public Key
cat /root/.ssh/backup_key.pub
```

**خروجی را کپی کنید** (شبیه این):
```
ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIGx... root@production
```

### در سرور پشتیبان (Backup Server):

```bash
# 1. ایجاد پوشه برای بکآپ‌ها
mkdir -p /backup/users
chmod 755 /backup/users

# 2. اضافه کردن Public Key
mkdir -p /root/.ssh
nano /root/.ssh/authorized_keys
```

**Public Key کپی شده را در فایل `authorized_keys` paste کنید**

```bash
# 3. تنظیم دسترسی‌ها
chmod 700 /root/.ssh
chmod 600 /root/.ssh/authorized_keys
```

### تست اتصال SSH:

```bash
# در سرور اصلی
ssh -i /root/.ssh/backup_key root@BACKUP_SERVER_IP

# اگر بدون پرسیدن رمز وارد شدید، موفق بوده‌اید!
exit
```

---

## ⚙️ مرحله 2: تنظیم Environment Variables

### در سرور اصلی:

```bash
# ویرایش فایل .env
nano /srv/deployment/.env
```

**اضافه کردن تنظیمات زیر:**

```env
# ===========================
# Backup Server Configuration
# ===========================
BACKUP_SERVER_HOST=YOUR_BACKUP_SERVER_IP
BACKUP_SERVER_USER=root
BACKUP_SERVER_PATH=/backup/users
BACKUP_SSH_KEY=/root/.ssh/backup_key
BACKUP_RETENTION_DAYS=30
BACKUP_KEEP_LOCAL=false
```

**جایگزین کنید:**
- `YOUR_BACKUP_SERVER_IP` → IP سرور پشتیبان شما

---

## 🕐 مرحله 3: تنظیم Timezone و Cron Job

### تنظیم Timezone به UTC:

```bash
# تنظیم timezone سرور به UTC
sudo timedatectl set-timezone UTC

# بررسی تنظیمات
timedatectl

# Restart cron service
sudo systemctl restart cron
```

### تنظیم Cron Job (بکآپ هر 6 ساعت):

```bash
# ویرایش crontab
crontab -e
```

**اضافه کردن خط زیر:**

```cron
# بکآپ خودکار هر 6 ساعت به وقت UTC (ساعت 0، 6، 12، 18 UTC)
# معادل: 03:30، 09:30، 15:30، 21:30 به وقت تهران (زمستان)
0 */6 * * * /srv/deployment/backup_auto.sh >> /var/log/backup-auto.log 2>&1
```

**ذخیره و خروج** (Ctrl+X, Y, Enter)

### تست دستی:

```bash
# اجرای دستی برای تست
sudo /srv/deployment/backup_auto.sh

# بررسی لاگ
tail -f /var/log/backup-auto.log
```

---

## 📊 مرحله 4: بررسی بکآپ‌ها

### در سرور اصلی:

```bash
# مشاهده بکآپ‌های محلی
ls -lh /srv/backups/auto/

# مشاهده لاگ بکآپ
tail -20 /var/log/backup-auto.log
```

### در سرور پشتیبان:

```bash
# مشاهده بکآپ‌های دریافتی
ls -lh /backup/tejarat-chat/

# بررسی حجم
du -sh /backup/tejarat-chat/
```

---

## 🛠️ استفاده از اسکریپت‌های بکآپ

### 1️⃣ بکآپ خودکار (backup_auto.sh)

**اجرا می‌شود:** هر 6 ساعت توسط cron

**عملکرد:**
- بکآپ PostgreSQL + Redis + NPM Config + .env
- فشرده‌سازی
- انتقال به سرور پشتیبان
- پاکسازی بکآپ‌های قدیمی

**اجرای دستی:**
```bash
sudo /srv/deployment/backup_auto.sh
```

---

### 2️⃣ بکآپ دستی (backup_manual.sh)

**اجرا می‌شود:** توسط شما به صورت دستی

**حالت‌های کاری:**

#### 🔹 بکآپ کامل:
```bash
cd /srv/deployment
sudo ./backup_manual.sh backup-full
```

**شامل:**
- PostgreSQL Database
- Redis Data
- Media Files (اگر از S3 استفاده نمی‌کنید)
- Static Files
- Nginx Proxy Manager Data
- Nginx Proxy Manager SSL Certificates (Let's Encrypt)
- فایل .env

**محل ذخیره:** `/srv/backups/manual/full_backup_YYYYMMDD_HHMMSS.tar.gz`

---

#### 🔹 بکآپ فقط دیتابیس:
```bash
cd /srv/deployment
sudo ./backup_manual.sh backup-db
```

**شامل:**
- PostgreSQL Database
- Redis Data
- فایل .env

**محل ذخیره:** `/srv/backups/manual/db_backup_YYYYMMDD_HHMMSS.tar.gz`

---

#### 🔹 بازیابی کامل:
```bash
cd /srv/deployment
sudo ./backup_manual.sh restore-full
```

**مراحل:**
1. لیست بکآپ‌های موجود نمایش داده می‌شود
2. مسیر فایل بکآپ را وارد کنید
3. تایید با تایپ `yes`
4. تمام سرویس‌ها متوقف می‌شوند
5. داده‌ها بازیابی می‌شوند
6. سرویس‌ها راه‌اندازی می‌شوند

---

#### 🔹 بازیابی فقط دیتابیس:
```bash
cd /srv/deployment
sudo ./backup_manual.sh restore-db
```

**مراحل:**
1. لیست بکآپ‌های دیتابیس نمایش داده می‌شود
2. مسیر فایل بکآپ را وارد کنید
3. تایید با تایپ `yes`
4. PostgreSQL و Redis بازیابی می‌شوند
5. سرویس‌های backend ری‌استارت می‌شوند

---

#### 🔹 منوی تعاملی:
```bash
cd /srv/deployment
sudo ./backup_manual.sh
```

منوی زیر نمایش داده می‌شود:
```
========================================
Manual Backup & Restore
========================================

Backup Options:
  1) Full Backup (Database + Files + Settings)
  2) Database-Only Backup (PostgreSQL + Redis + .env)

Restore Options:
  3) Full Restore (Database + Files + Settings)
  4) Database-Only Restore (PostgreSQL + Redis)

  5) Exit
```

---

## 🔍 عیب‌یابی

### مشکل 1: خطای SSH Connection

```bash
# تست اتصال SSH
ssh -i /root/.ssh/backup_key -v root@BACKUP_SERVER_IP

# بررسی دسترسی‌های کلید
ls -la /root/.ssh/backup_key
# باید: -rw------- (600)

# اصلاح دسترسی
chmod 600 /root/.ssh/backup_key
```

### مشکل 2: بکآپ انتقال نمی‌یابد

```bash
# بررسی لاگ
tail -50 /var/log/backup-auto.log

# تست rsync دستی
rsync -avz -e "ssh -i /root/.ssh/backup_key" \
    /srv/backups/auto/ \
    root@BACKUP_SERVER_IP:/backup/users/
```

### مشکل 3: فضای دیسک کم

```bash
# بررسی فضای دیسک
df -h

# پاکسازی بکآپ‌های قدیمی
find /srv/backups/auto -name "*.tar.gz" -mtime +7 -delete
find /srv/backups/manual -name "*.tar.gz" -mtime +30 -delete
```

### مشکل 4: Cron اجرا نمی‌شود

```bash
# بررسی وضعیت cron
systemctl status cron

# بررسی لاگ cron
grep CRON /var/log/syslog | tail -20

# تست دستی
sudo /srv/deployment/backup_auto.sh
```

---

## مانیتورینگ بکآپ‌ها

### بررسی روزانه:

```bash
# آخرین بکآپ خودکار
ls -lht /srv/backups/auto/ | head -5

# آخرین بکآپ در سرور پشتیبان
ssh -i /root/.ssh/backup_key root@BACKUP_SERVER_IP \
    "ls -lht /backup/tejarat-chat/ | head -5"

# لاگ بکآپ امروز
grep "$(date +%Y-%m-%d)" /var/log/backup-auto.log
```

### اسکریپت چک روزانه:

```bash
#!/bin/bash
# /root/check_backup.sh

LAST_BACKUP=$(ls -t /srv/backups/auto/*.tar.gz 2>/dev/null | head -1)
BACKUP_AGE=$(stat -c %Y "$LAST_BACKUP" 2>/dev/null)
NOW=$(date +%s)
AGE_HOURS=$(( ($NOW - $BACKUP_AGE) / 3600 ))

if [ $AGE_HOURS -gt 7 ]; then
    echo "⚠️ WARNING: Last backup is $AGE_HOURS hours old!"
else
    echo "✓ Backup is up to date (${AGE_HOURS}h ago)"
fi
```

---

## 🔒 امنیت

### توصیه‌های امنیتی:

1. **محدود کردن دسترسی SSH Key:**
```bash
# در سرور پشتیبان: /root/.ssh/authorized_keys
command="/usr/bin/rsync --server -vlogDtprze.iLsfxC . /backup/tejarat-chat/",no-port-forwarding,no-X11-forwarding,no-agent-forwarding ssh-rsa AAAAB3NzaC1yc2...
```

2. **رمزنگاری بکآپ‌ها (اختیاری):**
```bash
# رمزنگاری بکآپ
gpg --symmetric --cipher-algo AES256 backup.tar.gz

# رمزگشایی
gpg --decrypt backup.tar.gz.gpg > backup.tar.gz
```

3. **فایروال:**
```bash
# فقط اجازه SSH از IP سرور اصلی
ufw allow from PRODUCTION_SERVER_IP to any port 22
```

---

## 📞 دستورات مفید

```bash
# مشاهده تمام بکآپ‌ها
ls -lh /srv/backups/auto/
ls -lh /srv/backups/manual/

# حجم کل بکآپ‌ها
du -sh /srv/backups/

# تعداد بکآپ‌ها
ls /srv/backups/auto/*.tar.gz | wc -l

# قدیمی‌ترین بکآپ
ls -lt /srv/backups/auto/*.tar.gz | tail -1

# جدیدترین بکآپ
ls -lt /srv/backups/auto/*.tar.gz | head -1

# پاکسازی بکآپ‌های بیش از 30 روز
find /srv/backups -name "*.tar.gz" -mtime +30 -delete
```

---

## ✅ چک‌لیست راه‌اندازی

- [ ] SSH Key ایجاد شد
- [ ] Public Key به سرور پشتیبان اضافه شد
- [ ] اتصال SSH بدون رمز تست شد
- [ ] متغیرهای محیطی در `.env` تنظیم شدند
- [ ] Cron job اضافه شد
- [ ] بکآپ دستی تست شد
- [ ] بکآپ خودکار تست شد
- [ ] بکآپ در سرور پشتیبان بررسی شد
- [ ] بازیابی تست شد (در محیط تست)
- [ ] مانیتورینگ روزانه تنظیم شد

---

**نسخه**: 1.0  
**تاریخ**: 2024-12-24  
**نگهدارنده**: تیم توسعه تجارت چت
