# 🧠 حافظه هوش مصنوعی - پروژه تجارت چت

> **این فایل را قبل از هر اقدام بخوانید!**
> آخرین به‌روزرسانی: 2025-12-18

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
- **Deployment**: Docker Compose

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
├── accounts/
│   ├── models.py          # User, Organization, StaffGroup
│   ├── admin.py           # UserAdmin, StaffGroupAdmin
│   ├── admin_views.py     # AdminLoginView (OTP login)
│   ├── permissions.py     # CanViewFinancial, CanManageSupport, ...
│   └── views/             # Auth views
├── chat/
│   ├── core_service.py    # ارتباط با RAG Core
│   └── upload_views.py    # آپلود فایل
├── core/
│   ├── settings.py        # تنظیمات Django
│   ├── urls.py            # URL routing
│   └── admin.py           # unregister auth.Group
└── analytics/
    └── views.py           # استفاده از permissions جدید
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

### 2025-12-18: یکپارچه‌سازی سیستم کاربران
- ✅ حذف اپ `admin_panel`
- ✅ ایجاد مدل `StaffGroup` در accounts
- ✅ اضافه کردن `staff_groups` به User (M2M)
- ✅ اضافه کردن نقش `owner` به `organization_role`
- ✅ انتقال `AdminLoginView` به accounts
- ✅ ایجاد `accounts/permissions.py`
- ✅ به‌روزرسانی `analytics/views.py`
- ✅ Unregister کردن `auth.Group` از admin

---

## 📝 نکات مهم

1. **AUTH_USER_MODEL**: `accounts.User`
2. **احراز هویت ادمین**: OTP-based در `/admin/login/`
3. **MinIO**: برای ذخیره فایل‌های موقت آپلود
4. **RAG Core**: سیستم مرکزی در `core.tejarat.chat`

---

## 🎯 کارهای در انتظار

- [ ] سیستم پرداخت (زرین‌پال، رمزارز)
- [ ] مدیریت اشتراک و پلن‌ها
- [ ] بازارچه مشاوران
- [ ] سیستم اعلان‌ها (Email, SMS, Push)
- [ ] اپلیکیشن موبایل

---

## 📞 اطلاعات تماس

- **Website**: https://tejarat.chat
- **Admin**: https://admin.tejarat.chat
- **Core RAG**: https://core.tejarat.chat
