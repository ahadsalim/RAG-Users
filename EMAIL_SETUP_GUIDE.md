# راهنمای تنظیم ایمیل Gmail برای ارسال نوتیفیکیشن

## ✅ مرحله 1: فعال‌سازی 2-Step Verification

1. برو به: https://myaccount.google.com/security
2. در بخش "Signing in to Google" روی "2-Step Verification" کلیک کن
3. اگر فعال نیست، آن را فعال کن

## ✅ مرحله 2: ایجاد App Password

1. برو به: https://myaccount.google.com/apppasswords
2. در قسمت "Select app" گزینه "Mail" را انتخاب کن
3. در قسمت "Select device" گزینه "Other (Custom name)" را انتخاب کن
4. نام دلخواه بنویس مثلاً: "Tejarat Chat Server"
5. روی "Generate" کلیک کن
6. یک رمز 16 کاراکتری به شما نشان می‌دهد (مثل: `abcd efgh ijkl mnop`)
7. این رمز را کپی کن (بدون فاصله: `abcdefghijklmnop`)

## ✅ مرحله 3: تنظیم در سرور

در فایل `/srv/deployment/.env` این مقادیر را تنظیم کن:

```bash
# Gmail SMTP Settings
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=ahad.salim@gmail.com
EMAIL_HOST_PASSWORD=abcdefghijklmnop  # رمز 16 کاراکتری بدون فاصله
EMAIL_USE_TLS=true
DEFAULT_FROM_EMAIL=noreply@tejarat.chat
FRONTEND_URL=https://admin.tejarat.chat
```

## ✅ مرحله 4: Restart Backend

```bash
cd /srv/deployment
docker-compose restart backend
```

## ✅ مرحله 5: تست ارسال ایمیل

```bash
docker exec app_backend python manage.py shell -c "
from django.core.mail import send_mail
from django.conf import settings

send_mail(
    subject='تست ایمیل',
    message='این یک ایمیل تست است.',
    from_email=settings.DEFAULT_FROM_EMAIL,
    recipient_list=['ahad.salim@gmail.com'],
    fail_silently=False,
)
print('ایمیل ارسال شد!')
"
```

---

## 📧 سوالات شما:

### 1️⃣ آیا می‌شود ایمیل ارسالی `noreply@tejarat.chat` باشد؟

**پاسخ:** بله! با Gmail SMTP می‌توانید `From` address را `noreply@tejarat.chat` تنظیم کنید.
اما گیرنده در header ایمیل می‌بیند که از طریق Gmail ارسال شده است:

```
From: noreply@tejarat.chat
Via: ahad.salim@gmail.com
```

**راه حل بهتر:** استفاده از سرویس ایمیل حرفه‌ای مثل:
- **SendGrid** (رایگان تا 100 ایمیل/روز)
- **Mailgun** (رایگان تا 5000 ایمیل/ماه)
- **AWS SES** (ارزان و قابل اعتماد)
- یا **SMTP سرور اختصاصی** با دامنه `tejarat.chat`

---

### 2️⃣ اگر کاربر به `info@tejarat.chat` ایمیل بفرستد، کجا دریافت کنم؟

**پاسخ:** برای دریافت ایمیل نیاز به یکی از این کارها دارید:

#### گزینه 1: Gmail Forwarding (ساده‌ترین)
1. یک Gmail account بسازید: `info.tejarat.chat@gmail.com`
2. در تنظیمات Gmail، Forwarding را فعال کنید
3. تمام ایمیل‌ها را به `ahad.salim@gmail.com` forward کنید

#### گزینه 2: Google Workspace (حرفه‌ای)
- هزینه: $6/ماه برای هر کاربر
- ایمیل اختصاصی: `info@tejarat.chat`, `noreply@tejarat.chat`
- مدیریت کامل دامنه
- لینک: https://workspace.google.com

#### گزینه 3: cPanel Email (اگر هاست دارید)
- اکثر هاست‌ها cPanel دارند
- می‌توانید ایمیل‌های نامحدود بسازید
- مثل: `info@tejarat.chat`, `support@tejarat.chat`

#### گزینه 4: Cloudflare Email Routing (رایگان!)
1. برو به Cloudflare Dashboard
2. Email > Email Routing
3. ایمیل‌های `@tejarat.chat` را به Gmail خود forward کن
4. کاملاً رایگان!

**توصیه من:** از **Cloudflare Email Routing** استفاده کنید:
```
info@tejarat.chat → ahad.salim@gmail.com
support@tejarat.chat → ahad.salim@gmail.com
noreply@tejarat.chat → (no forwarding needed)
```

---

## 🔧 تنظیمات پیشنهادی نهایی:

### برای ارسال ایمیل (Outgoing):
```bash
# استفاده از Gmail SMTP
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=ahad.salim@gmail.com
EMAIL_HOST_PASSWORD=your-16-char-app-password
EMAIL_USE_TLS=true
DEFAULT_FROM_EMAIL=noreply@tejarat.chat
```

### برای دریافت ایمیل (Incoming):
- استفاده از **Cloudflare Email Routing** (رایگان)
- یا **Google Workspace** (حرفه‌ای)

---

## 📝 نکات مهم:

1. ✅ رمز App Password را بدون فاصله وارد کنید
2. ✅ 2-Step Verification باید فعال باشد
3. ✅ پس از تغییر `.env` حتماً backend را restart کنید
4. ✅ ایمیل‌های ارسالی ممکن است در Spam قرار بگیرند (با Gmail SMTP)
5. ✅ برای production، از سرویس حرفه‌ای استفاده کنید

---

## 🚀 مراحل بعدی:

1. App Password جدید از Gmail بگیرید
2. در `.env` تنظیم کنید (بدون فاصله)
3. Backend را restart کنید
4. تست ایمیل بفرستید
5. یک کاربر حقوقی ثبت‌نام کنید و ایمیل تایید را چک کنید

---

## 📞 پشتیبانی:

اگر مشکلی داشتید، خطای دقیق را به من نشان دهید.
