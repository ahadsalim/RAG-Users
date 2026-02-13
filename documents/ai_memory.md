# 🧠 حافظه هوش مصنوعی - پروژه تجارت چت

> **این فایل را قبل از هر اقدام بخوانید!**
> آخرین به‌روزرسانی: 2025-12-24

---

## 📋 خلاصه پروژه

**تجارت چت** یک پلتفرم مشاوره هوشمند حقوقی و کسب‌وکار است که با استفاده از RAG (Retrieval-Augmented Generation) کار می‌کند.

### تکنولوژی‌ها
- **Backend**: Django 5.2 + DRF + Channels
- **Frontend**: Next.js 14 + TypeScript + Tailwind
- **Database**: PostgreSQL 16
- **Cache**: Redis 7
- **Message Broker**: RabbitMQ 3
- **Storage**: MinIO
- **Admin Theme**: Jazzmin (RTL customized)
- **Deployment**: Docker Compose

### URLها
| سرویس | آدرس |
|-------|------|
| Frontend | https://www.tejarat.chat |
| Admin Panel | https://admin.tejarat.chat |
| RAG Core | https://core.tejarat.chat |
| API | https://api.tejarat.chat |

---

## 👥 ساختار کاربران (مهم!)

### انواع کاربران

| نوع | زیرنوع | فیلدها |
|-----|--------|--------|
| **حقیقی** | مشتری | `user_type='individual'`, `is_staff=False` |
| **حقیقی** | کارمند | `user_type='individual'`, `is_staff=True`, عضو `staff_groups` |
| **حقیقی** | سوپر ادمین | `is_superuser=True` |
| **حقوقی** | مالک | `user_type='business'`, `organization_role='owner'` |
| **حقوقی** | مدیر | `user_type='business'`, `organization_role='admin'` |
| **حقوقی** | عضو | `user_type='business'`, `organization_role='member'` |

### سیستم دسترسی کارمندان (StaffGroup)

مدل `StaffGroup` در `accounts/models.py` برای گروه‌بندی کارمندان استفاده می‌شود:

```python
class StaffGroup(models.Model):
    name = models.CharField(max_length=100, unique=True)
    can_view_users = models.BooleanField(default=False)
    can_edit_users = models.BooleanField(default=False)
    can_delete_users = models.BooleanField(default=False)
    can_view_financial = models.BooleanField(default=False)
    can_manage_financial = models.BooleanField(default=False)
    can_view_analytics = models.BooleanField(default=False)
    can_export_data = models.BooleanField(default=False)
    can_manage_content = models.BooleanField(default=False)
    can_manage_subscriptions = models.BooleanField(default=False)
    can_view_logs = models.BooleanField(default=False)
    can_manage_support = models.BooleanField(default=False)
```

**بررسی دسترسی:**
```python
# در view
from accounts.permissions import CanViewFinancial
permission_classes = [IsAuthenticated, CanViewFinancial]

# در کد
if user.has_staff_permission('view_financial'):
    pass
```

---

## 🚫 اپ‌های حذف شده

### admin_panel (حذف شده در 2025-12-18)
- **دلیل**: تکراری و بلااستفاده بود
- **جایگزین**: مدل `StaffGroup` در اپ `accounts`
- مدل‌های `Role`, `AdminUser`, `AdminAction` حذف شدند
- `AdminLoginView` به `accounts/admin_views.py` منتقل شد
- permissions به `accounts/permissions.py` منتقل شد

### auth.Group
- از پنل ادمین **unregister** شده (حذف نشده چون بخشی از Django است)
- جایگزین: `StaffGroup`

---

## 📁 ساختار مهم فایل‌ها

```
/srv/backend/
├── accounts/              # مدیریت کاربران
│   ├── models.py          # User, Organization, StaffGroup
│   ├── admin.py           # UserAdmin, StaffGroupAdmin
│   ├── admin_views.py     # AdminLoginView (OTP login)
│   ├── permissions.py     # CanViewFinancial, CanManageSupport, ...
│   ├── signals.py         # تنظیم ارز و timezone پیش‌فرض برای کاربران جدید
│   └── views/             # Auth views
├── chat/                  # سیستم چت
│   ├── core_service.py    # ارتباط با RAG Core
│   └── upload_views.py    # آپلود فایل
├── core/                  # تنظیمات اصلی
│   ├── settings.py        # تنظیمات Django + Jazzmin
│   ├── urls.py            # URL routing
│   ├── models.py          # Language, Timezone, SiteSettings
│   ├── middleware/        # Middleware ها
│   │   ├── timezone_middleware.py      # فعال‌سازی timezone کاربر
│   │   └── admin_title_middleware.py   # عنوان داینامیک admin
│   ├── utils/             # توابع کمکی
│   │   └── timezone_utils.py           # تبدیل UTC به timezone کاربر
│   └── admin.py           # unregister auth.Group, Language, Timezone
├── finance/               # سیستم مالی
│   ├── models.py          # Currency, PaymentGateway, FinancialSettings, Invoice
│   └── admin.py           # CurrencyAdmin (با is_default)
├── subscriptions/         # سیستم اشتراک
│   ├── models.py          # Plan, Subscription, UserUsageReport
│   ├── usage.py           # ModelUsageLog, UsageService
│   └── admin.py           # PlanAdmin, SubscriptionAdmin, ...
├── payments/              # سیستم پرداخت
├── notifications/         # سیستم اعلان‌رسانی
│   ├── models.py          # NotificationTemplate, Notification, NotificationPreference
│   ├── services.py        # NotificationService, EmailService, SMSService
│   ├── admin.py           # مدیریت اعلان‌ها و تنظیمات
│   ├── signals.py         # ایجاد خودکار NotificationPreference
│   └── views.py           # API endpoints
├── analytics/             # گزارشات
│   └── views.py           # استفاده از permissions جدید
├── schedule/              # زمان‌بندی
├── static/admin/css/      # CSS سفارشی
│   └── custom_rtl.css     # استایل RTL برای Jazzmin
└── templates/admin/       # Template overrides
    └── base.html          # حذف برندینگ Jazzmin
```

```
/srv/frontend/
├── src/
│   ├── app/               # Next.js App Router
│   │   ├── auth/          # صفحات احراز هویت
│   │   ├── dashboard/     # داشبورد کاربر
│   │   └── about/         # صفحه درباره ما
│   ├── components/        # کامپوننت‌های React
│   │   └── SiteName.tsx   # نمایش داینامیک نام سایت
│   ├── contexts/          # React Contexts
│   │   └── SettingsContext.tsx  # تنظیمات سایت
│   ├── services/          # API Services
│   └── types/             # TypeScript Types
│       └── settings.ts    # SiteSettings, Currency, ...
└── public/                # فایل‌های استاتیک
```

---

## ⚙️ قوانین کار

### 1. Git Commit
بعد از هر تغییر موفق:
```bash
git add -A
git commit -m "<پیام توصیفی>"
```

### 2. مستندات
- فایل‌های `.md` فقط در صورت درخواست صریح کاربر ایجاد/ویرایش شوند
- مستندات در پوشه `documents/` قرار گیرند

### 3. تست‌ها
- فایل‌های تست در پوشه `tests/` قرار گیرند

### 4. اجرای دستورات Django
```bash
docker exec app_backend python manage.py <command>
```

### 5. Migrations
```bash
docker exec app_backend python manage.py makemigrations <app_name>
docker exec app_backend python manage.py migrate
```

---

## 🔧 تغییرات اخیر

### 2025-12-24: سیستم بکآپ خودکار با SSH (نسخه 1.2.0)
- ✅ **تفکیک اسکریپت‌های بکآپ**
  - حذف `backup_manager.sh`
  - ایجاد `backup_auto.sh` برای بکآپ خودکار هر 6 ساعت
  - ایجاد `backup_manual.sh` برای بکآپ دستی کامل
  
- ✅ **بکآپ خودکار به سرور پشتیبان**
  - انتقال خودکار بکآپ‌ها به سرور پشتیبان از طریق SSH
  - استفاده از SSH Key برای احراز هویت بدون رمز
  - پشتیبانی از rsync برای انتقال سریع و ایمن
  - نگهداری بکآپ‌های محلی فقط 3 روز (صرفه‌جویی در فضا)
  - نگهداری بکآپ‌های ریموت 30 روز (قابل تنظیم)
  
- ✅ **محتویات بکآپ خودکار**
  - PostgreSQL Database (pg_dump با فشرده‌سازی)
  - Redis Data (dump.rdb)
  - Nginx Proxy Manager Config (npm_data volume)
  - فایل .env (تنظیمات محیطی)
  - حجم: ~100KB (فشرده شده)
  
- ✅ **محتویات بکآپ دستی کامل**
  - همه موارد بکآپ خودکار
  - Nginx Proxy Manager SSL Certificates (Let's Encrypt)
  - Media Files (اگر از S3 استفاده نمی‌شود)
  - Static Files
  
- ✅ **تنظیمات SSH و امنیت**
  - راهنمای کامل تنظیم SSH Key در `deployment/BACKUP_SETUP.md`
  - استفاده از ED25519 (مدرن، سریع، امن‌تر از RSA)
  - محدودیت دسترسی SSH Key به فقط rsync
  - تست اتصال قبل از فعال‌سازی
  
- ✅ **مستندات کامل**
  - `deployment/BACKUP_SETUP.md` - راهنمای جامع تنظیم SSH و بکآپ
  - `README.md` - به‌روزرسانی بخش Backup System
  - `documents/0_PROJECT_DOCUMENTATION.md` - نسخه 1.2.0
  
- ✅ **بهبود امنیت .env**
  - پشتیبانی از کاراکترهای خاص در SECRET_KEY و STRIPE_SECRET_KEY
  - استفاده از quotes برای جلوگیری از خطای bash syntax
  - حذف تکراری‌ها (Timezone, Core RAG API)

### 2025-12-23: حذف سیستم آپلود عکس پروفایل
- ✅ **حذف کامل قابلیت آپلود عکس پروفایل**
  - حذف فیلدهای `avatar` و `bio` از UserAdmin در backend
  - حذف کامل بخش آپلود عکس از SettingsPage.tsx در frontend
  - حذف توابع handleAvatarUpload و handleAvatarDelete
  - حذف UI مربوط به انتخاب، نمایش و حذف عکس
  - حذف فیلد `avatar` از UserSettings interface
  - نگهداری فیلد `national_id` در User interface برای استفاده‌های آینده
  
- ✅ **دلیل حذف**
  - مشکلات متعدد در پیاده‌سازی
  - خطای 403 Forbidden در دسترسی به MinIO
  - عدم تنظیم متغیر محیطی S3_USERS_BUCKET
  - درخواست کاربر برای حذف این قابلیت

### 2025-12-23: سیستم SLA و بستن خودکار تیکت‌ها
- ✅ **پیاده‌سازی کامل سیستم SLA برای تیکت‌ها**
  - تغییر فیلد `department` در `SLAPolicy` از ForeignKey به ManyToManyField
  - امکان تعریف یک سیاست SLA برای چند دپارتمان
  - جستجوی خودکار سیاست SLA بر اساس `department` و `priority`
  - اگر سیاست با دپارتمان پیدا نشد، سیاست‌های بدون دپارتمان (global) اعمال می‌شوند
  
- ✅ **بروزرسانی خودکار response_due**
  - وقتی کاربر پیام جدید می‌فرستد، `response_due` بروز می‌شود
  - `resolution_due` ثابت می‌ماند (از زمان ایجاد تیکت)
  - محاسبه و نمایش تمام تاخیرها (اگر چند بار با تاخیر پاسخ داده شده)
  
- ✅ **بستن خودکار تیکت‌های answered**
  - ایجاد Celery task: `auto_close_answered_tickets`
  - تیکت‌های با وضعیت `answered` که `resolution_due` گذشته خودکار به `closed` تغییر می‌کنند
  - اجرای هر 30 دقیقه
  - ثبت در تاریخچه با `action='auto_closed'`
  
- ✅ **اصلاح تشخیص تیکت جدید**
  - استفاده از `self._state.adding` به جای `self.pk is None`
  - چون `UUIDField` قبل از save مقدار می‌گیرد
  - حالا تیکت‌های جدید SLA دریافت می‌کنند
  
- ✅ **بهبود نمایش تاخیر در admin**
  - انتقال نمایش تاخیر از "زمان آخرین پاسخ" به "مهلت پاسخ‌دهی"
  - نمایش تمام تاخیرها با فرمت: `میزان تاخیر: 12 دقیقه تاخیر + 45 دقیقه تاخیر`
  - رنگ زمینه قرمز وقتی تاخیر دارد
  - استفاده از `vertical-align: middle` برای همتراز کردن
  - انتقال لیبل "تأخیر در حل" به ستون جداگانه

### 2025-12-21: سیستم Timezone و مدیریت ارز
- ✅ **حذف ارز TMN و تنظیم IRT به عنوان ارز پیش‌فرض**
  - ارز TMN (تومان) حذف شد
  - ارز IRT (تومان ایرانی) به عنوان ارز پیش‌فرض تنظیم شد
  - کاربران جدید به صورت خودکار IRT را دریافت می‌کنند
  
- ✅ **پیاده‌سازی کامل سیستم Timezone**
  - ایجاد `core/utils/timezone_utils.py` با توابع تبدیل UTC به timezone کاربر
  - ایجاد `core/middleware/TimezoneMiddleware` برای فعال‌سازی خودکار timezone کاربر
  - همه زمان‌ها در دیتابیس به UTC ذخیره می‌شوند (`USE_TZ=True`)
  - نمایش زمان به کاربر بر اساس timezone انتخابی او
  - پشتیبانی از تقویم شمسی با `format_datetime_jalali()`
  - تنظیم تهران به عنوان timezone پیش‌فرض برای همه کاربران
  - کاربران جدید به صورت خودکار timezone تهران را دریافت می‌کنند
  
- ✅ **فیلدهای اجباری تیکت پشتیبانی**
  - فیلدهای `category` و `department` در مدل Ticket اجباری شدند
  - حذف `null=True, blank=True` از این فیلدها
  - تغییر `on_delete` به `PROTECT` برای جلوگیری از حذف تصادفی
  - دکمه "ایجاد تیکت" در frontend تا انتخاب هر دو فیلد غیرفعال است
  - اضافه کردن `required` attribute به select ها
  
- ✅ **بهبود Admin Panel برای Currency**
  - اضافه کردن فیلد `is_default` به list_display با نشانگر آبی
  - اضافه کردن `is_default` به list_filter
  - حذف fieldsets و نمایش همه فیلدها در یک صفحه
  - فیلد "ارز پیش‌فرض" حالا قابل مشاهده و ویرایش است

### 2025-12-18: سیستم گزارش مصرف
- ✅ تغییر نام `UsageLog` به `ModelUsageLog`
- ✅ تفکیک `tokens_used` به `input_tokens` و `output_tokens`
- ✅ ایجاد `UserUsageReport` (proxy model) برای گزارش مصرف کاربران
- ✅ نمایش تاریخ شمسی در گزارشات
- ✅ نمایش سهمیه ماهانه به جای روزانه

### 2025-12-18: بهبود تنظیمات سایت
- ✅ اضافه کردن `copyright_text` به SiteSettings
- ✅ ایجاد `DynamicAdminTitleMiddleware` برای تنظیمات داینامیک admin
- ✅ Override کردن `templates/admin/base.html` برای حذف برندینگ Jazzmin
- ✅ اضافه کردن `connected_account` به PaymentGateway
- ✅ حذف فیلدهای بلااستفاده: `base_currency`, `gateway_type`

### 2025-12-18: یکپارچه‌سازی سیستم کاربران
- ✅ حذف اپ `admin_panel`
- ✅ ایجاد مدل `StaffGroup` در accounts
- ✅ اضافه کردن `staff_groups` به User (M2M)
- ✅ اضافه کردن نقش `owner` به `organization_role`
- ✅ انتقال `AdminLoginView` به accounts
- ✅ ایجاد `accounts/permissions.py`
- ✅ به‌روزرسانی `analytics/views.py`
- ✅ Unregister کردن `auth.Group` از admin

### 2025-12-18: سیستم مدیریت جلسات (Sessions)
- ✅ اضافه کردن `max_active_sessions` به مدل `Plan`
- ✅ ایجاد تب "جلسات فعال" در تنظیمات کاربر
- ✅ API برای نمایش و مدیریت sessions (`/api/v1/auth/sessions/`)
- ✅ محدودیت session: اگر بیش از حد مجاز login شود، قدیمی‌ترین session غیرفعال می‌شود
- ✅ اصلاح LogoutView برای غیرفعال کردن session با refresh_token
- ✅ Forward کردن User-Agent و IP از Next.js به backend

### 2025-12-18: تسک‌های زمان‌بندی شده (Celery Beat)
- ✅ ایجاد `core/tasks.py` با تسک‌های cleanup
- ✅ اضافه کردن `cleanup-tokens-and-sessions` (هر شب ساعت 3)
- ✅ اضافه کردن `cleanup-old-files` (هر شب ساعت 2)
- ✅ اضافه کردن S3 env vars به Celery containers
- ✅ ایجاد management command `cleanup_tokens`

### 2025-12-18: یکپارچه‌سازی OTP
- ✅ اضافه کردن `OTP_EXPIRE_SECONDS` به `.env`
- ✅ Backend از settings می‌خواند، Frontend از API response

### 2025-12-20: سیستم اعلان‌رسانی کامل
- ✅ ایجاد ۱۲ قالب اعلان (subscription, payment, account, security)
- ✅ ساده‌سازی مدل NotificationPreference (حذف quiet_hours, digest, custom_preferences)
- ✅ ایجاد خودکار NotificationPreference برای همه کاربران
- ✅ Signal برای ارسال SMS به سوپر ادمین‌ها هنگام ثبت‌نام کاربر جدید
- ✅ بهبود UI پنل ادمین: نمایش تاریخ شمسی، فیلد کاربر readonly
- ✅ اضافه کردن همه قالب‌ها به setup_initial_data.py
- ✅ NotificationService از تنظیمات کاربر استفاده می‌کند (کانال‌ها و دسته‌ها)
- ✅ دوطرفه بودن تنظیمات بین پنل کاربر و مدیر

---

## 📝 نکات مهم

1. **AUTH_USER_MODEL**: `accounts.User`
2. **احراز هویت ادمین**: OTP-based در `/admin/login/`
3. **MinIO**: برای ذخیره فایل‌های موقت آپلود
4. **RAG Core**: سیستم مرکزی در `core.tejarat.chat`
5. **Timezone**: همه زمان‌ها به UTC در دیتابیس، نمایش بر اساس timezone کاربر
6. **Currency**: IRR (ریال) برای محاسبات، IRT (تومان) برای کاربران جدید

---

## 🌍 سیستم Timezone

### نحوه کار
- **ذخیره**: همه datetime ها به UTC در دیتابیس (`USE_TZ=True`)
- **نمایش**: تبدیل به timezone انتخابی کاربر
- **پیش‌فرض**: Asia/Tehran برای همه کاربران

### فایل‌های کلیدی
```python
# Utilities
from core.utils import convert_to_user_timezone, format_datetime_jalali

# تبدیل UTC به timezone کاربر
user_dt = convert_to_user_timezone(utc_datetime, user.timezone.code)

# نمایش تاریخ شمسی
jalali = format_datetime_jalali(datetime_obj, user)
```

### Middleware
- `TimezoneMiddleware` به صورت خودکار timezone کاربر را فعال می‌کند
- برای کاربران لاگین شده: timezone انتخابی
- برای کاربران مهمان: تهران (پیش‌فرض)

### Signal
```python
# در accounts/signals.py
# کاربران جدید به صورت خودکار timezone تهران و ارز IRT را دریافت می‌کنند
@receiver(post_save, sender=User)
def set_default_currency_and_timezone_for_new_user(...)
```

---

## 💰 سیستم اشتراک و پلن‌ها

### مدل‌های اصلی (در `subscriptions/`)

#### Plan (پلن اشتراک)
```python
# فیلدهای کلیدی:
- name: نام پلن
- plan_type: 'individual' (حقیقی) | 'business' (حقوقی)
- price: قیمت به ارز پایه (تومان)
- duration_days: مدت اشتراک به روز
- max_queries_per_day: سهمیه روزانه سوال
- max_queries_per_month: سهمیه ماهانه سوال
- max_organization_members: حداکثر اعضا (برای حقوقی)
- features: JSONField برای ویژگی‌های اضافی
```

#### Subscription (اشتراک کاربر)
```python
# فیلدهای کلیدی:
- user: کاربر
- plan: پلن
- status: 'active' | 'expired' | 'cancelled' | 'pending'
- start_date, end_date: تاریخ شروع و پایان
- auto_renew: تمدید خودکار
```

#### ModelUsageLog (گزارش مصرف مدل‌ها)
```python
# لاگ هر درخواست به مدل‌های AI
- user, subscription
- action_type: 'query' | 'file_upload' | 'file_download' | 'api_call'
- input_tokens: توکن ورودی
- output_tokens: توکن خروجی
- plan_name: نام پلن در زمان ثبت
- metadata: JSONField
```

#### UserUsageReport (گزارش مصرف کاربران)
- Proxy model از Subscription
- نمایش خلاصه مصرف هر کاربر در admin

### UsageService (سرویس مصرف)
```python
from subscriptions.usage import UsageService

# ثبت مصرف
UsageService.log_usage(user, action_type='query', input_tokens=100, output_tokens=500)

# بررسی سهمیه
can_query, message, usage_info = UsageService.check_quota(user)

# آمار مصرف
stats = UsageService.get_usage_stats(user, days=30)
```

---

## 💵 سیستم ارز و پرداخت

### مدل‌های اصلی (در `finance/models.py`)

#### Currency (ارز)
```python
# فیلدهای کلیدی:
- code: کد ارز (IRR, IRT, USD, EUR)
- name: نام ارز
- symbol: نماد (﷼, تومان, $, €)
- is_base: آیا ارز پایه است؟ (فقط یکی می‌تواند باشد) - برای محاسبات
- is_default: آیا ارز پیش‌فرض است؟ (فقط یکی می‌تواند باشد) - برای کاربران جدید
- exchange_rate: نرخ تبدیل به ارز پایه
- has_decimals, decimal_places: تنظیمات اعشار

# متدها:
Currency.get_base_currency()     # دریافت ارز پایه (IRR)
Currency.get_default_currency()  # دریافت ارز پیش‌فرض (IRT)
currency.format_price(amount)    # فرمت قیمت
currency.convert_from_base(amount)  # تبدیل از ارز پایه

# ارزهای پیش‌فرض:
- IRR (ریال): is_base=True, exchange_rate=1 - برای ذخیره قیمت‌ها
- IRT (تومان ایرانی): is_default=True, exchange_rate=10 - برای کاربران جدید
```

#### PaymentGateway (درگاه پرداخت)
```python
# فیلدهای کلیدی:
- name: نام درگاه
- connected_account: شماره حساب متصل
- merchant_id, api_key, api_secret
- is_active, is_sandbox
- supported_currencies: M2M به Currency
- commission_percentage: درصد کارمزد
```

---

## ⚙️ تنظیمات سایت (Singleton)

### SiteSettings (در `core/models.py`)
```python
# دسترسی:
from core.models import SiteSettings
settings = SiteSettings.get_settings()

# فیلدهای کلیدی:
- frontend_site_name: نام سایت در فرانت‌اند
- admin_site_name: نام پنل مدیریت
- copyright_text: متن کپی‌رایت
- support_email, support_phone
- telegram_url, instagram_url, twitter_url
- default_payment_gateway
- maintenance_mode, maintenance_message
```

### DynamicAdminTitleMiddleware
- در `core/middleware.py`
- به صورت داینامیک عنوان و کپی‌رایت admin را از SiteSettings می‌خواند
- تنظیمات Jazzmin را هم به‌روز می‌کند

---

## 🎨 تنظیمات Admin Panel

### Jazzmin Theme
- فایل تنظیمات: `core/settings.py` → `JAZZMIN_SETTINGS`
- CSS سفارشی RTL: `static/admin/css/custom_rtl.css`
- Template override: `templates/admin/base.html` (برای حذف برندینگ Jazzmin)

### نکات مهم Admin
1. تاریخ‌ها به شمسی نمایش داده می‌شوند (با `jdatetime`)
2. `auth.Group` از admin حذف شده (جایگزین: `StaffGroup`)
3. فیلدهای عددی در لیست Plan عرض کم دارند (CSS)

---

## 🔐 سیستم مدیریت جلسات (Sessions)

### محدودیت Session
- هر پلن دارای `max_active_sessions` است (پیش‌فرض: 3)
- اگر کاربر بیش از حد مجاز login کند، **قدیمی‌ترین session غیرفعال می‌شود**
- توکن refresh قدیمی blacklist می‌شود

### API Endpoints
```
GET  /api/v1/auth/sessions/           # لیست sessions
GET  /api/v1/auth/sessions/with_limit/ # با اطلاعات محدودیت پلن
POST /api/v1/auth/sessions/{id}/revoke/ # حذف یک session
POST /api/v1/auth/sessions/revoke_all/  # حذف همه sessions دیگر
```

### فایل‌های مرتبط
- `accounts/otp_views.py` - منطق محدودیت در VerifyOTPView
- `accounts/views.py` - UserSessionViewSet
- `subscriptions/models.py` - فیلد max_active_sessions در Plan
- `frontend/src/components/SettingsPage.tsx` - تب جلسات فعال

---

## ⏰ تسک‌های زمان‌بندی شده (Celery Beat)

### لیست تسک‌ها
| تسک | زمان | توضیحات |
|-----|------|---------|
| `check-expiring-subscriptions` | 09:00 روزانه | اعلان انقضای اشتراک |
| `check-expired-subscriptions` | 00:30 روزانه | بررسی اشتراک‌های منقضی |
| `check-quota-warnings` | هر 6 ساعت | هشدار سهمیه 80% |
| `cleanup-tokens-and-sessions` | 03:00 روزانه | پاکسازی توکن‌ها |
| `cleanup-old-files` | 02:00 روزانه | پاکسازی فایل‌های موقت |
| `auto-close-answered-tickets` | هر 30 دقیقه | بستن خودکار تیکت‌های answered |

### فایل‌های مرتبط
- `core/settings.py` → `CELERY_BEAT_SCHEDULE`
- `core/tasks.py` - تسک‌های cleanup
- `subscriptions/tasks.py` - تسک‌های اشتراک

### دستورات دستی
```bash
# پاکسازی توکن‌ها
docker exec app_backend python manage.py cleanup_tokens

# با پارامترها
docker exec app_backend python manage.py cleanup_tokens --max-tokens-per-user 3 --session-days 30
```

---

## 🔑 تنظیمات OTP

### متغیر محیطی
```env
OTP_EXPIRE_SECONDS=120  # 2 دقیقه
```

### نحوه کار
1. Backend از `settings.OTP_EXPIRE_SECONDS` می‌خواند
2. API در response فیلد `expires_in` برمی‌گرداند
3. Frontend تایمر را از response تنظیم می‌کند

### فایل‌های مرتبط
- `.env` → `OTP_EXPIRE_SECONDS`
- `core/settings.py` → خواندن از env
- `accounts/otp_views.py` → استفاده در cache و response
- `frontend/src/app/auth/login/page.tsx` → تایمر UI

---

---

## 🔔 سیستم اعلان‌رسانی

### مدل‌های اصلی (در `notifications/`)

#### NotificationTemplate (قالب اعلان)
```python
# فیلدهای کلیدی:
- code: کد یکتا (subscription_expiring, payment_success, ...)
- name: نام قالب
- category: دسته (system, payment, subscription, chat, account, security, marketing, support)
- title_template, body_template: قالب عنوان و متن
- sms_template: قالب مخصوص SMS (کوتاه‌تر)
- email_subject_template, email_html_template: قالب ایمیل
- channels: لیست کانال‌ها ['sms', 'email', 'push', 'in_app']
- default_priority: اولویت پیش‌فرض
```

#### NotificationPreference (تنظیمات کاربر)
```python
# کانال‌ها:
- email_enabled, sms_enabled, push_enabled, in_app_enabled

# دسته‌بندی‌ها:
- system_notifications, payment_notifications
- subscription_notifications, chat_notifications
- account_notifications, security_notifications
- marketing_notifications, support_notifications
```

#### Notification (اعلان ارسال شده)
```python
# فیلدهای کلیدی:
- user: گیرنده
- template: قالب استفاده شده
- title, body: محتوای رندر شده
- channels: کانال‌های ارسال
- sent_via_email, sent_via_sms, sent_via_push: وضعیت ارسال
- is_read, read_at: وضعیت خواندن
```

### قالب‌های موجود (۱۲ عدد)

| کد | نام | دسته | کانال‌ها |
|----|-----|-------|----------|
| `subscription_expiring` | نزدیک به انقضای اشتراک | subscription | sms, in_app |
| `subscription_expired` | انقضای اشتراک | subscription | sms, in_app |
| `subscription_renewed` | تمدید اشتراک | subscription | sms, in_app |
| `subscription_activated` | فعال‌سازی اشتراک | subscription | sms, in_app |
| `quota_warning` | هشدار سهمیه | subscription | in_app |
| `quota_exceeded` | اتمام سهمیه | subscription | sms, in_app |
| `payment_success` | پرداخت موفق | payment | sms, in_app |
| `payment_failed` | پرداخت ناموفق | payment | sms, in_app |
| `new_user_registered` | عضویت کاربر جدید | system | sms |
| `welcome` | خوش‌آمدگویی | account | sms, in_app |
| `login_from_new_device` | ورود از دستگاه جدید | security | sms, in_app |
| `password_changed` | تغییر رمز عبور | security | sms, in_app |

### NotificationService
```python
from notifications.services import NotificationService

# ارسال اعلان
NotificationService.create_notification(
    user=user,
    template_code='subscription_expiring',
    context={'days_remaining': 3, 'plan_name': 'پایه'},
    channels=['sms', 'in_app'],
    priority='high'
)
```

### نکات مهم
1. **تنظیمات کاربر**: سرویس اعلان از `NotificationPreference` استفاده می‌کند
2. **فیلتر کانال‌ها**: اگر کاربر SMS را غیرفعال کرده، پیامک ارسال نمی‌شود
3. **فیلتر دسته‌ها**: اگر دسته غیرفعال باشد، فقط in_app ارسال می‌شود
4. **SMS Template**: برای صرفه‌جویی در هزینه، از `sms_template` کوتاه‌تر استفاده می‌شود
5. **دوطرفه**: تغییرات در پنل کاربر یا مدیر برای طرف مقابل قابل مشاهده است

### Signal ثبت‌نام کاربر جدید
```python
# در subscriptions/signals.py
@receiver(post_save, sender=User)
def notify_admins_new_user(sender, instance, created, **kwargs):
    # ارسال SMS به همه سوپر ادمین‌ها
    if created and not instance.is_superuser:
        for admin in User.objects.filter(is_superuser=True, is_active=True):
            NotificationService.create_notification(
                user=admin,
                template_code='new_user_registered',
                context={'user_phone': instance.phone_number},
                channels=['sms']
            )
```

---

## 🎯 کارهای در انتظار

- [ ] سیستم پرداخت (زرین‌پال، رمزارز)
- [x] مدیریت اشتراک و پلن‌ها ✅
- [x] مدیریت جلسات فعال ✅
- [x] تسک‌های زمان‌بندی شده ✅
- [x] سیستم اعلان‌ها (SMS, Email, Push, In-App) ✅
- [x] سیستم Timezone (UTC storage + user timezone display) ✅
- [x] مدیریت ارز (IRR base + IRT default) ✅
- [x] فیلدهای اجباری تیکت پشتیبانی ✅
- [ ] بازارچه مشاوران
- [ ] اپلیکیشن موبایل

---

## 🎫 سیستم پشتیبانی (Support)

### مدل‌های اصلی (در `support/`)

#### Ticket (تیکت)
```python
# فیلدهای کلیدی:
- ticket_number: شماره تیکت (خودکار)
- user: کاربر ایجادکننده
- subject: موضوع (required)
- description: توضیحات (required)
- category: دسته‌بندی (required, PROTECT)
- department: دپارتمان (required, PROTECT)
- status: وضعیت (open, in_progress, waiting, answered, closed)
- priority: اولویت (low, medium, high, urgent)
- assigned_to: کارمند مسئول
- response_due: مهلت پاسخ‌دهی (بروز می‌شود با هر پیام کاربر)
- resolution_due: مهلت حل مشکل (ثابت از زمان ایجاد)
- first_response_at: زمان اولین پاسخ کارشناس
```

#### SLAPolicy (سیاست SLA)
```python
# فیلدهای کلیدی:
- name: نام سیاست
- departments: M2M به TicketDepartment (چند انتخابی)
- priority: JSONField - لیست اولویت‌ها ['low', 'medium', 'high', 'urgent']
- response_time: زمان پاسخ‌دهی (دقیقه)
- resolution_time: زمان حل مشکل (دقیقه)
- is_active: فعال/غیرفعال

# سیاست‌های پیش‌فرض:
- فوری: 30 دقیقه پاسخ، 4 ساعت حل
- بالا: 2 ساعت پاسخ، 8 ساعت حل
- متوسط: 4 ساعت پاسخ، 24 ساعت حل
- کم: 8 ساعت پاسخ، 48 ساعت حل
```

#### TicketCategory (دسته‌بندی)
- نمونه: مشکل فنی، سوال، پیشنهاد، شکایت
- فیلد `category` در Ticket اجباری است

#### TicketDepartment (دپارتمان)
- نمونه: فنی، مالی، فروش، عمومی
- فیلد `department` در Ticket اجباری است
- ارتباط M2M با SLAPolicy

### منطق SLA
1. **تنظیم اولیه**: هنگام ایجاد تیکت، `response_due` و `resolution_due` بر اساس سیاست SLA تنظیم می‌شوند
2. **جستجوی سیاست**: ابتدا سیاست با department مشخص، سپس سیاست‌های global (بدون department)
3. **بروزرسانی response_due**: وقتی کاربر پیام جدید می‌فرستد، فقط `response_due` بروز می‌شود
4. **resolution_due ثابت**: از زمان ایجاد تیکت تا بسته شدن ثابت می‌ماند
5. **بستن خودکار**: تیکت‌های `answered` که `resolution_due` گذشته به `closed` تغییر می‌کنند

### نمایش تاخیر در Admin
- **زمان آخرین پاسخ**: فقط زمان نمایش داده می‌شود
- **مهلت پاسخ‌دهی**: زمان مهلت + میزان تاخیر (اگر وجود دارد)
- **مهلت حل مشکل**: زمان مهلت + لیبل "تأخیر در حل" (اگر وجود دارد)
- **رنگ زمینه**: قرمز برای تاخیر، سبز برای به موقع
- **تاخیرهای متعدد**: نمایش همه تاخیرها با `+` (مثلاً: `12 دقیقه تاخیر + 45 دقیقه تاخیر`)

### نکات مهم
1. **فیلدهای اجباری**: category و department باید حتماً انتخاب شوند
2. **Frontend validation**: دکمه "ایجاد تیکت" تا انتخاب هر دو فیلد غیرفعال است
3. **PROTECT**: حذف category یا department با تیکت‌های مرتبط امکان‌پذیر نیست
4. **تشخیص تیکت جدید**: استفاده از `_state.adding` به جای `pk is None` (به دلیل UUIDField)
5. **Celery task**: بستن خودکار تیکت‌های answered هر 30 دقیقه

---

---

## 💾 سیستم بکآپ و بازیابی

### اسکریپت‌های بکآپ

#### backup_auto.sh (بکآپ خودکار)
- **زمان اجرا**: هر 6 ساعت (توسط cron)
- **محتویات**: PostgreSQL, Redis, NPM Config, .env
- **مقصد**: سرور پشتیبان از طریق SSH
- **نگهداری**: محلی 3 روز، ریموت 30 روز
- **حجم**: ~100KB (فشرده شده)

```bash
# اجرای دستی
sudo /srv/deployment/backup_auto.sh

# مشاهده لاگ
tail -f /var/log/backup-auto.log
```

#### backup_manual.sh (بکآپ دستی)
- **محتویات کامل**: همه موارد خودکار + SSL Certificates + Media + Static Files
- **مقصد**: محلی در `/srv/backups/manual/`

```bash
cd /srv/deployment
sudo ./backup_manual.sh backup-full   # بکآپ کامل
sudo ./backup_manual.sh backup-db     # فقط دیتابیس
sudo ./backup_manual.sh restore-full  # بازیابی کامل
sudo ./backup_manual.sh restore-db    # بازیابی دیتابیس
```

### تنظیمات SSH برای بکآپ ریموت

**در سرور اصلی (Production):**
```bash
# ایجاد SSH Key
ssh-keygen -t ed25519 -f /root/.ssh/backup_key -N ""

# نمایش Public Key
cat /root/.ssh/backup_key.pub
```

**در سرور پشتیبان (Backup Server):**
```bash
# ایجاد پوشه بکآپ
mkdir -p /backup/users
chmod 755 /backup/users

# اضافه کردن Public Key
mkdir -p /root/.ssh
nano /root/.ssh/authorized_keys
# (paste کردن public key)

# تنظیم دسترسی‌ها
chmod 700 /root/.ssh
chmod 600 /root/.ssh/authorized_keys
```

**تست اتصال:**
```bash
# در سرور اصلی
ssh -i /root/.ssh/backup_key root@BACKUP_SERVER_IP
```

### متغیرهای محیطی بکآپ

در فایل `/srv/deployment/.env`:
```env
BACKUP_SERVER_HOST=backup.example.com
BACKUP_SERVER_USER=root
BACKUP_SERVER_PATH=/backup/users
BACKUP_SSH_KEY=/root/.ssh/backup_key
BACKUP_RETENTION_DAYS=30
BACKUP_KEEP_LOCAL=false
```

### Timezone سرور

**مهم:** همه سرورها باید روی UTC تنظیم شوند:

```bash
# تنظیم timezone به UTC
sudo timedatectl set-timezone UTC

# Restart cron
sudo systemctl restart cron
```

### Cron Job

```bash
# بکآپ خودکار هر 6 ساعت به وقت UTC (0، 6، 12، 18 UTC)
# معادل: 03:30، 09:30، 15:30، 21:30 تهران (زمستان)
0 */6 * * * /srv/deployment/backup_auto.sh >> /var/log/backup-auto.log 2>&1
```

### مستندات کامل
- `deployment/BACKUP_SETUP.md` - راهنمای جامع تنظیم SSH و بکآپ
- `deployment/backup_auto.sh` - اسکریپت بکآپ خودکار
- `deployment/backup_manual.sh` - اسکریپت بکآپ دستی

---

## � اتصال به سیستم مرکزی RAG Core — تجربیات و نکات مهم

> آخرین به‌روزرسانی: 2026-02-13

### قانون طلایی
- **سیستم مرکزی (RAG Core) مرجع اصلی است** — هرگز تنظیمات سیستم مرکزی را تغییر ندهید
- سیستم‌های دیگر (بکند/فرانت) باید خودشان را با سیستم مرکزی هماهنگ کنند
- تغییر سیستم مرکزی باعث بهم ریختن بقیه سیستم‌ها می‌شود

### معماری شبکه
| سرور | IP | نقش |
|------|-----|------|
| RAG Core (مرکزی) | `10.10.10.20:7001` | سیستم هوش مصنوعی و RAG |
| Backend/Frontend | `10.10.10.30` | بکند Django + فرانت Next.js |
| MinIO/S3 | `10.10.10.50:9000` | ذخیره‌سازی فایل |

### JWT_SECRET_KEY — هماهنگی بین سیستم‌ها
- **مرجع**: کلید JWT سیستم مرکزی (`/srv/.env` روی `10.10.10.20`)
- **این سیستم**: باید همان کلید در `/srv/deployment/.env` خط `JWT_SECRET_KEY` باشد
- Backend از `djangorestframework-simplejwt` استفاده می‌کند (`SIMPLE_JWT.SIGNING_KEY`)
- RAG Core از `python-jose` استفاده می‌کند (`settings.jwt_secret_key`)
- **هر دو باید کلید یکسان داشته باشند** وگرنه خطای 401 از RAG Core دریافت می‌شود
- تنظیمات simplejwt در `backend/core/settings.py`:
  - `USER_ID_CLAIM = 'sub'` (سازگار با RAG Core)
  - `TOKEN_TYPE_CLAIM = 'type'` (سازگار با RAG Core)

### مشکلات رایج اتصال و راه‌حل‌ها

#### 1. خطای "زمان پردازش تمام شد" (Timeout)
- **علت معمول**: JWT_SECRET_KEY ناهماهنگ → RAG Core پاسخ 401 می‌دهد → backend timeout به کاربر
- **تشخیص**: تست مستقیم از داخل container:
  ```bash
  docker exec app_backend python -c "
  import os; os.environ.setdefault('DJANGO_SETTINGS_MODULE','core.settings')
  os.environ['DJANGO_ALLOW_ASYNC_UNSAFE']='true'
  import django; django.setup()
  import httpx, asyncio
  from django.conf import settings as s
  from rest_framework_simplejwt.tokens import RefreshToken
  from accounts.models import User
  async def t():
      u=User.objects.first(); tk=str(RefreshToken.for_user(u).access_token)
      async with httpx.AsyncClient(timeout=30,follow_redirects=True) as c:
          r=await c.post(f'{s.RAG_CORE_BASE_URL}/api/v1/query',json={'query':'سلام','language':'fa'},headers={'Authorization':f'Bearer {tk}','Content-Type':'application/json'})
          print(f'{r.status_code}: {r.text[:300]}')
  asyncio.run(t())
  "
  ```
- **رفع**: کلید JWT این سیستم را با سیستم مرکزی یکسان کنید

#### 2. خطای "Invalid host header" (400)
- **علت**: `TrustedHostMiddleware` در RAG Core — IP سرور بکند در لیست allowed hosts نیست
- **رفع**: در سیستم مرکزی `/srv/app/main.py` → IP های داخلی شبکه به `allowed_hosts` اضافه شود
- **فایل**: `/srv/app/main.py` خط ~101

#### 3. خطای 307 Redirect
- **علت**: FastAPI trailing slash redirect — URL بدون `/` به URL با `/` redirect می‌شود
- **رفع**: در `backend/chat/core_service.py` → `follow_redirects=True` به همه `httpx.AsyncClient` ها اضافه شود
- **یا**: trailing slash از URL ها حذف شود (FastAPI بدون آن کار می‌کند)

#### 4. خطای `AttributeError: 'Settings' object has no attribute 'llm_fallback_api_key'`
- **علت**: بعد از refactor LLM به سیستم LLM1/LLM2، property های backward compatibility فراموش شده بود
- **رفع**: در سیستم مرکزی `/srv/app/config/settings.py` → property های `llm_fallback_api_key`, `llm_fallback_base_url`, `llm_fallback_model` اضافه شد که به `llm1_fallback_*` map می‌کنند

### تنظیمات مهم `core_service.py`
- فایل: `backend/chat/core_service.py`
- **همیشه** `follow_redirects=True` در `httpx.AsyncClient` باشد
- `RAG_CORE_BASE_URL` باید با پورت `7001` باشد (نه 80)
- URL query: `{base_url}/api/v1/query` (بدون trailing slash)
- URL health: `{base_url}/health` (بدون trailing slash)

### تغییر تنظیمات بعد از ویرایش `.env`
- `docker restart app_backend` کافی **نیست** — env variables قدیمی cache می‌شوند
- باید container را recreate کنید:
  ```bash
  cd /srv/deployment && docker compose up -d backend
  ```

### تنظیمات production سیستم مرکزی
- `ENVIRONMENT="production"`, `DEBUG=false`, `RELOAD=false`
- بعد از `RELOAD=false`، تغییرات کد خودکار اعمال نمی‌شوند — باید container ریستارت شود:
  ```bash
  # روی سرور مرکزی (10.10.10.20):
  docker stop core-api && docker rm core-api
  cd /srv/deployment/docker && docker compose up -d --no-build core-api
  ```

---

## �📞 اطلاعات تماس

- **Website**: https://tejarat.chat
- **Admin**: https://admin.tejarat.chat
- **Core RAG**: https://core.tejarat.chat
