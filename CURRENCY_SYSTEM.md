# 💰 سیستم مدیریت واحد پولی و تنظیمات سایت

## 📋 فهرست مطالب

1. [معرفی](#معرفی)
2. [ساختار Backend](#ساختار-backend)
3. [ساختار Frontend](#ساختار-frontend)
4. [نحوه استفاده](#نحوه-استفاده)
5. [API Endpoints](#api-endpoints)
6. [مثال‌های کاربردی](#مثالهای-کاربردی)

---

## معرفی

این سیستم امکان مدیریت چند واحد پولی، درگاه‌های پرداخت، و تنظیمات کلی سایت را فراهم می‌کند.

### ویژگی‌های اصلی:

✅ **مدیریت چند ارز** با نرخ تبدیل خودکار
✅ **پشتیبانی از اعشار** (قابل تنظیم برای هر ارز)
✅ **فرمت‌بندی خودکار** قیمت‌ها
✅ **مدیریت درگاه‌های پرداخت**
✅ **تنظیمات متمرکز سایت** (Singleton)
✅ **Cache** برای بهینه‌سازی عملکرد

---

## ساختار Backend

### 🗄️ Models

#### 1. **Currency** (ارز)
```python
from core.models import Currency

# Create a currency
toman = Currency.objects.create(
    code='IRT',
    name='تومان',
    symbol='تومان',
    has_decimals=False,
    decimal_places=0,
    exchange_rate=10,  # 1 Toman = 10 Rials
    is_active=True,
    display_order=1
)

# Format price
formatted = toman.format_price(50000)
# Output: "50,000 تومان"

# Convert to base currency
base_amount = toman.convert_from_base(1000)
```

**فیلدها:**
- `code`: کد ISO ارز (IRR, USD, EUR, IRT)
- `name`: نام فارسی ارز
- `symbol`: نماد ارز (﷼, $, €, تومان)
- `has_decimals`: آیا ارز دارای اعشار است؟
- `decimal_places`: تعداد ارقام اعشار (0 برای تومان/ریال، 2 برای دلار)
- `exchange_rate`: نرخ تبدیل به واحد پایه (1 = واحد پایه)
- `is_active`: فعال/غیرفعال
- `display_order`: ترتیب نمایش

#### 2. **PaymentGateway** (درگاه پرداخت)
```python
from core.models import PaymentGateway

# Create payment gateway
zarinpal = PaymentGateway.objects.create(
    name='زرین‌پال',
    gateway_type='zarinpal',
    merchant_id='YOUR_MERCHANT_ID',
    api_key='YOUR_API_KEY',
    is_active=True,
    is_sandbox=True,
    commission_percentage=2.5
)

# Add supported currencies
zarinpal.supported_currencies.add(irr, irt)
```

**نوع درگاه‌های پشتیبانی شده:**
- `zarinpal`: زرین‌پال
- `idpay`: آیدی‌پی
- `nextpay`: نکست‌پی
- `parsian`: پارسیان
- `mellat`: ملت
- `saman`: سامان
- `pasargad`: پاسارگاد
- `stripe`: Stripe
- `paypal`: PayPal

#### 3. **SiteSettings** (تنظیمات سایت - Singleton)
```python
from core.models import SiteSettings

# Get settings (always returns the same instance)
settings = SiteSettings.get_settings()

# Update settings
settings.base_currency = toman
settings.default_payment_gateway = zarinpal
settings.site_name = 'تجارت چت'
settings.save()
```

**فیلدهای مهم:**
- `base_currency`: واحد پولی پایه سایت
- `default_payment_gateway`: درگاه پیش‌فرض
- `site_name`, `site_url`, `site_description`: اطلاعات سایت
- `support_email`, `support_phone`: اطلاعات تماس
- `maintenance_mode`: حالت تعمیر و نگهداری
- `allow_registration`: امکان ثبت‌نام
- `require_email_verification`: الزام تأیید ایمیل
- `enable_two_factor`: احراز هویت دو مرحله‌ای

### 🔌 Admin Interface

**مسیر:** `/admin/`

**بخش‌های جدید:**
1. **تنظیمات پایه** → **ارزها**
   - افزودن/ویرایش ارزها
   - تنظیم نرخ تبدیل
   - فعال/غیرفعال کردن

2. **تنظیمات پایه** → **درگاه‌های پرداخت**
   - مدیریت درگاه‌ها
   - تنظیم API Keys
   - انتخاب ارزهای پشتیبانی شده

3. **تنظیمات پایه** → **تنظیمات سایت**
   - انتخاب واحد پولی پایه
   - انتخاب درگاه پیش‌فرض
   - تنظیمات عمومی سایت

---

## ساختار Frontend

### 📁 Files

```
frontend/src/
├── types/
│   └── settings.ts          # TypeScript types
├── services/
│   └── settingsService.ts   # API calls
├── contexts/
│   └── SettingsContext.tsx  # React Context
├── hooks/
│   └── useCurrency.ts       # Currency hook
└── utils/
    └── currency.ts          # Utility functions
```

### 🎯 Usage in Components

#### 1. **استفاده از Hook:**
```tsx
import { useCurrency } from '@/hooks/useCurrency'

function PricingCard({ price }: { price: number }) {
  const { formatPrice, baseCurrency } = useCurrency()
  
  return (
    <div>
      <p>قیمت: {formatPrice(price)}</p>
      <p>واحد: {baseCurrency?.name}</p>
    </div>
  )
}
```

#### 2. **استفاده از Context:**
```tsx
import { useSettings } from '@/contexts/SettingsContext'

function SiteInfo() {
  const { settings, isLoading } = useSettings()
  
  if (isLoading) return <div>در حال بارگذاری...</div>
  
  return (
    <div>
      <h1>{settings?.site_name}</h1>
      <p>{settings?.site_description}</p>
      <p>واحد پولی: {settings?.base_currency?.name}</p>
    </div>
  )
}
```

#### 3. **استفاده از Utility:**
```tsx
import { formatPrice, convertCurrency } from '@/utils/currency'

// Format price
const formatted = formatPrice(50000, currency)

// Convert between currencies
const converted = convertCurrency(100, fromCurrency, toCurrency)
```

### 🔄 Context Provider

**در `app/layout.tsx` یا `providers.tsx`:**
```tsx
import { SettingsProvider } from '@/contexts/SettingsContext'

export function Providers({ children }) {
  return (
    <SettingsProvider>
      {children}
    </SettingsProvider>
  )
}
```

---

## API Endpoints

### 📡 Available Endpoints

#### 1. **دریافت تنظیمات سایت**
```bash
GET /api/v1/settings/
```

**Response:**
```json
{
  "site_name": "تجارت چت",
  "site_url": "https://tejarat.chat",
  "base_currency": {
    "code": "IRT",
    "name": "تومان",
    "symbol": "تومان",
    "has_decimals": false,
    "decimal_places": 0,
    "exchange_rate": "10.000000"
  },
  "default_payment_gateway": {...},
  ...
}
```

#### 2. **لیست ارزهای فعال**
```bash
GET /api/v1/currencies/
```

**Response:**
```json
{
  "count": 4,
  "results": [
    {
      "id": 1,
      "code": "IRR",
      "name": "ریال ایران",
      "symbol": "﷼",
      "has_decimals": false,
      "decimal_places": 0,
      "exchange_rate": "1.000000",
      "is_active": true
    },
    ...
  ]
}
```

#### 3. **تبدیل ارز**
```bash
POST /api/v1/currencies/convert/
Content-Type: application/json

{
  "from_currency": "IRT",
  "to_currency": "IRR",
  "amount": 1000
}
```

**Response:**
```json
{
  "from_currency": "IRT",
  "to_currency": "IRR",
  "amount": 1000,
  "converted_amount": 10000,
  "formatted": "10,000 ﷼"
}
```

#### 4. **لیست درگاه‌های پرداخت**
```bash
GET /api/v1/payment-gateways/
```

---

## مثال‌های کاربردی

### 🎨 Backend Examples

#### 1. **نمایش قیمت پلن با فرمت صحیح:**
```python
from subscriptions.models import Plan
from core.models import SiteSettings

plan = Plan.objects.first()
settings = SiteSettings.get_settings()

# Method 1: Using Plan method
formatted_price = plan.get_formatted_price()
# Output: "59,900,000 تومان"

# Method 2: Using Currency directly
currency = settings.base_currency
formatted_price = currency.format_price(plan.price)
```

#### 2. **تبدیل قیمت بین ارزها:**
```python
from core.models import Currency

irt = Currency.objects.get(code='IRT')
usd = Currency.objects.get(code='USD')

# Convert 1000 Toman to USD
base_amount = 1000 / float(irt.exchange_rate)
usd_amount = base_amount * float(usd.exchange_rate)

# Or using currency method
usd_amount = usd.convert_from_base(1000 / float(irt.exchange_rate))
```

#### 3. **ایجاد ارز جدید:**
```python
from core.models import Currency

aed = Currency.objects.create(
    code='AED',
    name='درهم امارات',
    symbol='د.إ',
    has_decimals=True,
    decimal_places=2,
    exchange_rate=136000,  # 1 AED = 136,000 IRR
    is_active=True,
    display_order=5
)
```

### 🖼️ Frontend Examples

#### 1. **صفحه قیمت‌گذاری:**
```tsx
import { useCurrency } from '@/hooks/useCurrency'

function PricingPage() {
  const { formatPrice } = useCurrency()
  const [plans, setPlans] = useState([])
  
  useEffect(() => {
    // Fetch plans
    fetchPlans().then(setPlans)
  }, [])
  
  return (
    <div className="grid grid-cols-3 gap-4">
      {plans.map(plan => (
        <div key={plan.id} className="border rounded p-4">
          <h3>{plan.name}</h3>
          <p className="text-2xl font-bold">
            {plan.price === 0 ? 'رایگان' : formatPrice(plan.price)}
          </p>
          <button>خرید پلن</button>
        </div>
      ))}
    </div>
  )
}
```

#### 2. **نمایش اطلاعات سایت:**
```tsx
import { useSettings } from '@/contexts/SettingsContext'

function Footer() {
  const { settings } = useSettings()
  
  return (
    <footer>
      <p>{settings?.site_name}</p>
      <p>ایمیل: {settings?.support_email}</p>
      <p>تلفن: {settings?.support_phone}</p>
    </footer>
  )
}
```

#### 3. **محاسبه‌گر تبدیل ارز:**
```tsx
import { useState } from 'react'
import { convertCurrency } from '@/services/settingsService'

function CurrencyConverter() {
  const [amount, setAmount] = useState(1000)
  const [result, setResult] = useState(null)
  
  const handleConvert = async () => {
    const data = await convertCurrency({
      from_currency: 'IRT',
      to_currency: 'USD',
      amount
    })
    setResult(data)
  }
  
  return (
    <div>
      <input 
        type="number" 
        value={amount} 
        onChange={e => setAmount(Number(e.target.value))}
      />
      <button onClick={handleConvert}>تبدیل</button>
      {result && <p>{result.formatted}</p>}
    </div>
  )
}
```

---

## 🚀 دستورات مفید

### Backend

```bash
# اجرای migrations
docker exec app_backend python manage.py migrate core

# ایجاد داده‌های پیش‌فرض
docker exec app_backend python manage.py init_site_settings

# تست فرمت‌بندی قیمت
docker exec app_backend python manage.py shell -c "
from core.models import Currency
toman = Currency.objects.get(code='IRT')
print(toman.format_price(50000))
"

# به‌روزرسانی نرخ ارز
docker exec app_backend python manage.py shell -c "
from core.models import Currency
usd = Currency.objects.get(code='USD')
usd.exchange_rate = 520000
usd.save()
"
```

### Frontend

```bash
# Build frontend
docker-compose -f deployment/docker-compose.yml build frontend

# Restart services
docker-compose -f deployment/docker-compose.yml restart frontend backend
```

---

## 📝 نکات مهم

### ⚠️ توجه:

1. **واحد پولی پایه:** همیشه یک ارز را به عنوان واحد پایه (exchange_rate=1) تعریف کنید
2. **Cache:** تنظیمات سایت به مدت 1 ساعت cache می‌شوند
3. **Singleton:** فقط یک نمونه از `SiteSettings` وجود دارد
4. **Decimal Places:** برای ارزهای بدون اعشار (تومان/ریال)، `has_decimals=False` قرار دهید

### ✅ Best Practices:

1. از `Currency.format_price()` برای فرمت‌بندی استفاده کنید
2. از `SiteSettings.get_settings()` برای دریافت تنظیمات استفاده کنید
3. نرخ ارز را به‌طور دوره‌ای به‌روزرسانی کنید
4. برای production، `is_sandbox=False` قرار دهید

---

## 🔐 امنیت

- API Keys درگاه‌ها را **هرگز** در کد hard-code نکنید
- از environment variables استفاده کنید
- برای production، SSL را فعال کنید
- دسترسی به Admin Panel را محدود کنید

---

## 📞 پشتیبانی

در صورت بروز مشکل:
1. لاگ‌های Docker را بررسی کنید
2. Cache را پاک کنید
3. Migrations را مجدداً اجرا کنید

```bash
# Clear cache
docker exec app_backend python manage.py shell -c "from django.core.cache import cache; cache.clear()"

# View logs
docker logs app_backend --tail 100
docker logs app_frontend --tail 100
```

---

**✨ سیستم آماده است!**
