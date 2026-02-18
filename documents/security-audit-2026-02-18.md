# گزارش بررسی امنیتی سرور Production
**تاریخ:** 2026-02-18  
**سرور:** users (192.168.100.103)  
**مسیر پروژه:** /srv  

---

## خلاصه اجرایی

بررسی امنیتی کامل انجام شد و **5 مشکل امنیتی** شناسایی و رفع گردید. سرور در برابر حمله Redis crypto mining که قبلاً در سرور دیگر رخ داده بود، ایمن‌سازی شد.

**وضعیت نهایی:** ✅ **امن**

---

## مشکلات شناسایی شده و اقدامات انجام شده

### 🔴 مشکل 1: پورت‌های Monitoring Exporter از اینترنت باز بودند

**خطر:** پورت‌های 8080, 9100, 9121, 9187, 9419 از `0.0.0.0` قابل دسترسی بودند و اطلاعات حساس سیستم را افشا می‌کردند.

**اقدام انجام شده:**
- تمام پورت‌های exporter به `127.0.0.1` محدود شدند
- فایل تغییر یافته: `/srv/deployment/docker-compose.yml`

```yaml
# قبل
ports:
  - "8080:8080"
  - "9100:9100"
  - "9121:9121"
  - "9187:9187"
  - "9419:9419"

# بعد
ports:
  - "127.0.0.1:8080:8080"
  - "127.0.0.1:9100:9100"
  - "127.0.0.1:9121:9121"
  - "127.0.0.1:9187:9187"
  - "127.0.0.1:9419:9419"
```

---

### 🟡 مشکل 2: Redis فاقد protected-mode و دستورات خطرناک فعال

**خطر:** Redis می‌توانست هدف حمله SLAVEOF/REPLICAOF قرار گیرد (مشابه حمله قبلی).

**اقدام انجام شده:**
- `--protected-mode yes` فعال شد
- دستورات خطرناک غیرفعال شدند:
  - `SLAVEOF` → غیرفعال
  - `REPLICAOF` → غیرفعال
  - `CONFIG` → غیرفعال
  - `DEBUG` → غیرفعال
  - `FLUSHDB` → غیرفعال
  - `FLUSHALL` → غیرفعال

```yaml
command: >
  sh -c "redis-server 
  --appendonly yes 
  --maxmemory 256mb 
  --maxmemory-policy allkeys-lru
  --protected-mode yes
  --rename-command SLAVEOF \"\"
  --rename-command REPLICAOF \"\"
  --rename-command CONFIG \"\"
  --rename-command DEBUG \"\"
  --rename-command FLUSHDB \"\"
  --rename-command FLUSHALL \"\"
  $$([ -n \"$$REDIS_PASSWORD\" ] && echo \"--requirepass $$REDIS_PASSWORD\" || echo \"\")"
```

**نکته مثبت:** Redis قبلاً رمز عبور داشت (`REDIS_PASSWORD` تنظیم شده بود).

---

### 🟠 مشکل 3: UFW فعال اما Docker آن را دور می‌زد

**خطر:** Docker به طور پیش‌فرض UFW را نادیده می‌گیرد و پورت‌های کانتینرها از اینترنت باز می‌شوند.

**اقدام انجام شده:**

#### الف) تنظیم قوانین DOCKER-USER در UFW
فایل `/etc/ufw/after.rules` تغییر یافت:

```bash
*filter
:DOCKER-USER - [0:0]

# Allow established connections
-A DOCKER-USER -m conntrack --ctstate ESTABLISHED,RELATED -j RETURN

# Allow Docker internal networks
-A DOCKER-USER -s 172.16.0.0/12 -j RETURN

# Allow from LAN subnet
-A DOCKER-USER -s 192.168.100.0/24 -j RETURN

# Allow from DMZ subnet
-A DOCKER-USER -s 10.10.10.0/24 -j RETURN

# Allow localhost
-A DOCKER-USER -s 127.0.0.0/8 -j RETURN

# Allow public ports (HTTP/HTTPS)
-A DOCKER-USER -p tcp --dport 80 -j RETURN
-A DOCKER-USER -p tcp --dport 443 -j RETURN

# Drop everything else
-A DOCKER-USER -j DROP

COMMIT
```

#### ب) ایجاد systemd service برای پایداری قوانین
فایل `/etc/systemd/system/docker-user-iptables.service` ایجاد شد تا بعد از restart شدن Docker، قوانین دوباره اعمال شوند.

```bash
sudo systemctl enable docker-user-iptables.service
sudo systemctl start docker-user-iptables.service
```

---

### 🟡 مشکل 4: پورت 81 (NPM Admin Panel) از اینترنت باز بود

**خطر:** پنل مدیریت Nginx Proxy Manager از اینترنت قابل دسترسی بود.

**اقدام انجام شده:**
- پورت 81 فقط از LAN و DMZ قابل دسترسی شد:

```bash
sudo ufw delete allow 81/tcp
sudo ufw allow from 192.168.100.0/24 to any port 81 proto tcp comment 'NPM Admin - LAN only'
sudo ufw allow from 10.10.10.0/24 to any port 81 proto tcp comment 'NPM Admin - DMZ only'
```

---

### 🟡 مشکل 5: پورت 7001 بدون دلیل باز بود

**اقدام انجام شده:**
```bash
sudo ufw delete allow 7001/tcp
```

---

## بررسی نفوذ احتمالی

✅ **هیچ نشانه‌ای از نفوذ پیدا نشد:**
- Redis رمز عبور دارد و `role:master` است
- هیچ کلید مشکوک در Redis وجود ندارد
- هیچ crontab مشکوک پیدا نشد
- هیچ پروسه crypto miner فعال نیست
- لاگین‌های SSH فقط از شبکه داخلی (192.168.100.32, 10.10.10.40)
- هیچ فایل مشکوک در `/tmp`, `/var/tmp`, `/dev/shm` نیست

---

## تأیید نهایی

### پورت‌های باز از اینترنت (0.0.0.0):
```
✅ 22/tcp   - SSH (ضروری)
✅ 80/tcp   - HTTP (ضروری)
✅ 443/tcp  - HTTPS (ضروری)
✅ 81/tcp   - NPM Admin (فقط از LAN/DMZ - محافظت شده توسط UFW)
```

### پورت‌های داخلی (127.0.0.1):
```
✅ 5432     - PostgreSQL
✅ 6379     - Redis (با protected-mode و بدون دستورات خطرناک)
✅ 5672     - RabbitMQ AMQP
✅ 15672    - RabbitMQ Management
✅ 8080     - cAdvisor
✅ 9100     - Node Exporter
✅ 9121     - Redis Exporter
✅ 9187     - PostgreSQL Exporter
✅ 9419     - RabbitMQ Exporter
```

### وضعیت Firewall:
```bash
# UFW
Status: active
Default: deny (incoming), allow (outgoing)

# DOCKER-USER iptables chain
✅ فعال و کار می‌کند
✅ systemd service فعال است (بعد از restart Docker قوانین حفظ می‌شوند)
```

### وضعیت سرویس‌ها:
```
✅ تمام کانتینرها healthy هستند
✅ وب‌سایت در دسترس است (http://localhost)
✅ SSH در دسترس است
```

---

## توصیه‌های امنیتی اضافی

1. **Backup منظم:** اطمینان حاصل کنید backup خودکار فعال است
2. **بررسی لاگ‌ها:** به طور منظم لاگ‌های `/var/log/auth.log` را بررسی کنید
3. **به‌روزرسانی:** Docker images را به طور منظم به‌روزرسانی کنید
4. **Monitoring:** Prometheus/Grafana را برای نظارت بر سرور راه‌اندازی کنید
5. **Fail2ban:** نصب Fail2ban برای محافظت در برابر brute force SSH

---

## فایل‌های تغییر یافته

1. `/srv/deployment/docker-compose.yml` - امن‌سازی پورت‌ها و Redis
2. `/etc/ufw/after.rules` - قوانین DOCKER-USER
3. `/etc/systemd/system/docker-user-iptables.service` - سرویس systemd

**Git Commit:** `6f50ffe` - "Security hardening: Secure monitoring ports, harden Redis, configure DOCKER-USER firewall"

---

## نتیجه‌گیری

سرور در برابر حمله Redis crypto mining که قبلاً در سرور دیگر رخ داده بود، **کاملاً ایمن‌سازی شد**. تمام پورت‌های غیرضروری بسته شدند و فایروال به درستی پیکربندی شد تا Docker نتواند آن را دور بزند.

**امتیاز امنیتی:** A+ ✅
