# راهنمای استفاده از درگاه تست تجارت

## 📋 خلاصه

درگاه پرداخت مجازی تست تجارت به سیستم اضافه شد. این درگاه برای تست فرآیند پرداخت بدون نیاز به درگاه واقعی استفاده می‌شود.

## 🔧 تنظیمات انجام شده

### 1. مدل‌ها (`/srv/backend/payments/models.py`)
- ✅ اضافه شدن `TEJARAT_TEST` به `PaymentGateway` choices
- ✅ ایجاد مدل `TejaratTestPayment` برای ذخیره اطلاعات پرداخت

### 2. سرویس (`/srv/backend/payments/tejarat_test_service.py`)
- ✅ کلاس `TejaratTestService` با متدهای:
  - `create_payment()`: ایجاد درخواست پرداخت
  - `verify_payment()`: تایید پرداخت

### 3. Views (`/srv/backend/payments/views.py`)
- ✅ اضافه شدن `_process_tejarat_test_payment()` به `TransactionViewSet`
- ✅ ایجاد `TejaratTestCallbackView` برای پردازش callback

### 4. URLs (`/srv/backend/payments/urls.py`)
- ✅ اضافه شدن: `tejarat-test/callback/`

### 5. تنظیمات (`/srv/deployment/.env`)
```env
TEJARAT_TEST_BASE_URL=http://payment.tejarat.chat:8000
TEJARAT_TEST_MERCHANT_ID=MERCHANT_001
```

### 6. Migration
- ✅ Migration اجرا شد و جدول `TejaratTestPayment` ایجاد شد

---

## 🚀 نحوه استفاده

### مرحله 1: ایجاد درخواست پرداخت از Frontend

```javascript
// درخواست پرداخت
const response = await axios.post('/api/v1/payments/create/', {
  gateway: 'tejarat_test',
  plan_id: 'YOUR_PLAN_ID',  // یا subscription_id یا amount
  currency: 'IRR'
});

// پاسخ شامل:
// {
//   "transaction_id": "uuid",
//   "reference_id": "TRX-...",
//   "success": true,
//   "token": "abc-123...",
//   "payment_url": "http://payment.tejarat.chat:8000/payment/gateway/abc-123...",
//   "message": "درخواست پرداخت با موفقیت ایجاد شد"
// }

// هدایت کاربر به صفحه پرداخت
window.location.href = response.data.payment_url;
```

### مرحله 2: کاربر در صفحه درگاه تست

کاربر به صفحه درگاه تست هدایت می‌شود و فرم پرداخت را پر می‌کند:
- شماره کارت
- CVV2
- تاریخ انقضا
- رمز دوم

سیستم به‌صورت رندوم نتیجه را تعیین می‌کند (موفق یا ناموفق).

### مرحله 3: بازگشت به Callback

پس از پرداخت، کاربر به callback برمی‌گردد:

**موفق:**
```
https://tejarat.chat/payment/success?tracking_code=123456&transaction_id=uuid
```

**ناموفق:**
```
https://tejarat.chat/payment/error?message=پرداخت_ناموفق_بود
```

---

## 🧪 تست با cURL

### 1. تست ایجاد درخواست پرداخت

```bash
# لاگین و دریافت token
TOKEN="YOUR_JWT_TOKEN"

# ایجاد پرداخت
curl -X POST https://tejarat.chat/api/v1/payments/create/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "gateway": "tejarat_test",
    "plan_id": "PLAN_UUID",
    "currency": "IRR"
  }'
```

### 2. تست مستقیم با درگاه تست (اگر در دسترس باشد)

```bash
# درخواست پرداخت
curl -X POST http://payment.tejarat.chat:8000/api/payment/request \
  -H "Content-Type: application/json" \
  -d '{
    "merchant_id": "MERCHANT_001",
    "amount": 50000,
    "callback_url": "https://tejarat.chat/api/v1/payments/tejarat-test/callback/"
  }'

# پاسخ:
# {
#   "status": 0,
#   "token": "abc-123...",
#   "message": "درخواست با موفقیت ثبت شد"
# }

# تایید پرداخت
curl -X POST http://payment.tejarat.chat:8000/api/payment/verify \
  -H "Content-Type: application/json" \
  -d '{
    "merchant_id": "MERCHANT_001",
    "token": "abc-123..."
  }'

# پاسخ موفق:
# {
#   "status": 0,
#   "amount": 50000,
#   "tracking_code": "123456",
#   "card_number": "6037-****-****-1234",
#   "message": "پرداخت با موفقیت انجام شد"
# }
```

---

## 📊 جریان کامل پرداخت

```
1. کاربر انتخاب پلن → Frontend
2. ارسال درخواست به /api/v1/payments/create/ → Backend
3. ایجاد Transaction در دیتابیس
4. ارسال درخواست به درگاه تست → payment.tejarat.chat
5. دریافت token و payment_url
6. هدایت کاربر به صفحه پرداخت → payment.tejarat.chat/payment/gateway/{token}
7. کاربر فرم را پر می‌کند
8. درگاه تست نتیجه را تعیین می‌کند (رندوم)
9. بازگشت به callback → /api/v1/payments/tejarat-test/callback/?token=...
10. تایید پرداخت با verify API
11. به‌روزرسانی Transaction و فعال‌سازی Subscription
12. هدایت به صفحه موفقیت/خطا
```

---

## 🔍 بررسی وضعیت

### چک کردن تراکنش‌ها

```bash
# لیست تراکنش‌های کاربر
curl -X GET https://tejarat.chat/api/v1/payments/transactions/ \
  -H "Authorization: Bearer $TOKEN"

# جزئیات یک تراکنش
curl -X GET https://tejarat.chat/api/v1/payments/transactions/{transaction_id}/ \
  -H "Authorization: Bearer $TOKEN"
```

### چک کردن در دیتابیس

```bash
docker exec -it app_backend python manage.py shell

# در shell
from payments.models import Transaction, TejaratTestPayment

# لیست تراکنش‌های درگاه تست
Transaction.objects.filter(gateway='tejarat_test')

# جزئیات پرداخت
payment = TejaratTestPayment.objects.last()
print(f"Token: {payment.token}")
print(f"Tracking Code: {payment.tracking_code}")
print(f"Transaction: {payment.transaction.reference_id}")
```

---

## ⚠️ نکات مهم

### 1. دسترسی به درگاه تست
اطمینان حاصل کنید که:
- سرور `payment.tejarat.chat` در دسترس است
- پورت 8000 باز است
- Firewall مشکلی ایجاد نمی‌کند

### 2. Callback URL
- Callback URL باید از خارج قابل دسترسی باشد
- اگر از localhost استفاده می‌کنید، از ngrok یا مشابه استفاده کنید

### 3. HTTPS vs HTTP
- درگاه تست روی HTTP است
- سیستم اصلی روی HTTPS
- مطمئن شوید که مرورگر mixed content را مسدود نمی‌کند

### 4. لاگ‌ها
برای دیباگ مشکلات:
```bash
# لاگ‌های backend
docker logs app_backend --tail 100 -f

# فیلتر لاگ‌های پرداخت
docker logs app_backend 2>&1 | grep -i "tejarat\|payment"
```

---

## 🐛 عیب‌یابی

### مشکل: درگاه تست در دسترس نیست

```bash
# تست اتصال
curl -I http://payment.tejarat.chat:8000

# اگر 404 یا timeout:
# 1. بررسی کنید سرور درگاه تست راه‌اندازی شده
# 2. بررسی کنید DNS صحیح است
# 3. بررسی کنید firewall مشکلی ندارد
```

### مشکل: خطای 500 در callback

```bash
# چک کردن لاگ‌ها
docker logs app_backend --tail 50

# بررسی تنظیمات
docker exec app_backend python -c "
from django.conf import settings
print(f'TEJARAT_TEST_BASE_URL: {settings.TEJARAT_TEST_BASE_URL}')
print(f'TEJARAT_TEST_MERCHANT_ID: {settings.TEJARAT_TEST_MERCHANT_ID}')
"
```

### مشکل: Transaction ایجاد می‌شود اما پرداخت انجام نمی‌شود

```python
# در Django shell
from payments.models import Transaction
from payments.tejarat_test_service import TejaratTestService

# یافتن آخرین تراکنش
tx = Transaction.objects.filter(gateway='tejarat_test').last()

# تست دستی
result = TejaratTestService.create_payment(
    transaction=tx,
    callback_url='https://tejarat.chat/api/v1/payments/tejarat-test/callback/'
)
print(result)
```

---

## 📝 TODO برای تکمیل

- [ ] اطمینان از در دسترس بودن سرور `payment.tejarat.chat`
- [ ] تست کامل فرآیند پرداخت از frontend
- [ ] اضافه کردن صفحات success/error در frontend
- [ ] تست با مبالغ مختلف
- [ ] تست callback در حالت‌های مختلف (موفق/ناموفق)
- [ ] اضافه کردن logging بیشتر برای دیباگ

---

## 📞 پشتیبانی

اگر مشکلی پیش آمد:
1. لاگ‌های backend را بررسی کنید
2. وضعیت Transaction در دیتابیس را چک کنید
3. اتصال به درگاه تست را تست کنید
4. تنظیمات .env را بررسی کنید
