# 🧠 حافظه هوش مصنوعی - پروژه تجارت چت

> **این فایل را قبل از هر اقدام بخوانید!**
> آخرین به‌روزرسانی: 2025-12-20

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
│   └── views/             # Auth views
├── chat/                  # سیستم چت
│   ├── core_service.py    # ارتباط با RAG Core
│   └── upload_views.py    # آپلود فایل
├── core/                  # تنظیمات اصلی
│   ├── settings.py        # تنظیمات Django + Jazzmin
│   ├── urls.py            # URL routing
│   ├── models.py          # Currency, PaymentGateway, SiteSettings
│   ├── middleware.py      # DynamicAdminTitleMiddleware
│   └── admin.py           # unregister auth.Group
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

### مدل‌های اصلی (در `core/models.py`)

#### Currency (ارز)
```python
# فیلدهای کلیدی:
- code: کد ارز (IRR, USD, EUR)
- name: نام ارز
- symbol: نماد (﷼, $, €)
- is_base: آیا ارز پایه است؟ (فقط یکی می‌تواند باشد)
- exchange_rate: نرخ تبدیل به ارز پایه
- has_decimals, decimal_places: تنظیمات اعشار

# متدها:
Currency.get_base_currency()  # دریافت ارز پایه
currency.format_price(amount)  # فرمت قیمت
currency.convert_from_base(amount)  # تبدیل از ارز پایه
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
- [ ] بازارچه مشاوران
- [ ] اپلیکیشن موبایل

---

## 📞 اطلاعات تماس

- **Website**: https://tejarat.chat
- **Admin**: https://admin.tejarat.chat
- **Core RAG**: https://core.tejarat.chat
