# 🔍 بررسی تطابق سیستم با مستندات جدید Core API

**تاریخ بررسی:** 17 نوامبر 2025

---

## 📊 خلاصه نتیجه

| بخش | وضعیت | نیاز به تغییر |
|-----|-------|---------------|
| JWT Token Structure | ⚠️ ناقص | بله |
| Query Endpoint | ✅ کامل | خیر |
| Streaming | ✅ کامل | خیر |
| Feedback API | ✅ کامل | خیر |
| User Management APIs | ✅ کامل | خیر |
| Filters Support | ❌ ناموجود | بله |
| Conversation Creation | ❌ ناموجود | بله |
| Error Handling | ⚠️ ساده | بهبود |

---

## ⚠️ موارد نیازمند تغییر:

### 1. JWT Token Payload (مهم ⭐⭐⭐)

#### وضعیت فعلی:
```json
{
  "token_type": "access",
  "exp": 1763365190,
  "iat": 1763361590,
  "jti": "77141996281b4b4296a1d6d5c9db4b4d",
  "sub": "94a371e1-679f-4262-ab35-0acb5a5aac50"
}
```

#### مستندات Core می‌خواهد:
```json
{
  "sub": "user-id",
  "username": "user123",      ← ❌ نداریم
  "email": "user@example.com", ← ❌ نداریم
  "tier": "premium",           ← ❌ نداریم
  "exp": 1700000000,
  "iat": 1699900000,
  "type": "access"
}
```

#### تغییرات لازم در `/srv/backend/core/settings.py`:

**فایل:** `/srv/backend/core/settings.py`

```python
# اضافه کردن custom token claims
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=JWT_ACCESS_TOKEN_LIFETIME),
    'REFRESH_TOKEN_LIFETIME': timedelta(minutes=JWT_REFRESH_TOKEN_LIFETIME),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'UPDATE_LAST_LOGIN': True,
    'ALGORITHM': JWT_ALGORITHM,
    'SIGNING_KEY': JWT_SECRET_KEY,
    'VERIFYING_KEY': None,
    'AUTH_HEADER_TYPES': ('Bearer',),
    'USER_ID_FIELD': 'id',
    'USER_ID_CLAIM': 'sub',
    'AUTH_TOKEN_CLASSES': ('rest_framework_simplejwt.tokens.AccessToken',),
    'TOKEN_TYPE_CLAIM': 'type',  # تغییر از 'token_type' به 'type'
    'JTI_CLAIM': 'jti',
}
```

**ایجاد Custom Token Class:**

فایل جدید: `/srv/backend/accounts/tokens.py`

```python
from rest_framework_simplejwt.tokens import AccessToken as BaseAccessToken


class CustomAccessToken(BaseAccessToken):
    """Custom access token with additional user fields for Core API."""
    
    @classmethod
    def for_user(cls, user):
        """
        Create token with username, email, and tier fields.
        """
        token = super().for_user(user)
        
        # اضافه کردن فیلدهای مورد نیاز Core
        token['username'] = user.username if user.username else f"user_{str(user.id)[:8]}"
        token['email'] = user.email if user.email else None
        
        # تعیین tier بر اساس subscription
        if hasattr(user, 'subscription') and user.subscription:
            token['tier'] = user.subscription.tier
        else:
            token['tier'] = 'free'
        
        return token
```

**استفاده در Consumer:**

فایل: `/srv/backend/chat/consumers.py` (خط 444-452)

```python
from accounts.tokens import CustomAccessToken  # اضافه شود

@database_sync_to_async
def get_jwt_token(self):
    """دریافت JWT token برای کاربر"""
    try:
        token = CustomAccessToken.for_user(self.user)  # تغییر از AccessToken
        return str(token)
    except Exception as e:
        logger.error(f"Error generating JWT token: {str(e)}")
        return None
```

---

### 2. Filters Support (مهم ⭐⭐)

#### وضعیت فعلی:
```python
payload = {
    "query": query,
    "conversation_id": conversation_id,
    "language": language,
    "max_results": 5,
    "use_cache": True,
    "use_reranking": True,
    "stream": stream,
}
# ❌ filters پشتیبانی نمی‌شود
```

#### مستندات Core:
```json
{
  "query": "...",
  "filters": {
    "jurisdiction": "جمهوری اسلامی ایران",
    "category": "قانون مدنی",
    "date_range": {
      "gte": "1370-01-01",
      "lte": "1403-12-29"
    }
  }
}
```

#### تغییرات لازم در `/srv/backend/chat/core_service.py`:

```python
async def send_query(
    self,
    query: str,
    token: str,
    conversation_id: Optional[str] = None,
    language: str = 'fa',
    stream: bool = False,
    filters: Optional[Dict[str, Any]] = None,  # ← اضافه شود
    max_results: int = 5,                       # ← اضافه شود
) -> Dict[str, Any]:
    """Send a query to Core API."""
    
    url = f"{self.base_url}/api/v1/query/stream" if stream else f"{self.base_url}/api/v1/query/"
    
    payload = {
        "query": query,
        "conversation_id": conversation_id,
        "language": language,
        "max_results": max_results,
        "use_cache": True,
        "use_reranking": True,
        "stream": stream,
    }
    
    # اضافه کردن filters اگر وجود داشت
    if filters:
        payload["filters"] = filters
    
    # ...
```

---

### 3. Create Conversation API (مهم ⭐)

#### وضعیت فعلی:
```python
# ❌ endpoint برای ایجاد conversation نداریم
```

#### مستندات Core:
```
POST /api/v1/users/conversations
```

#### تغییرات لازم در `/srv/backend/chat/core_service.py`:

```python
async def create_conversation(
    self,
    token: str,
    title: str,
    context: Optional[Dict[str, Any]] = None,
    llm_model: Optional[str] = None,
    temperature: Optional[float] = None,
    max_tokens: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Create a new conversation in Core.
    
    Args:
        token: JWT token
        title: Conversation title
        context: Optional context data
        llm_model: Optional LLM model to use
        temperature: Optional temperature setting
        max_tokens: Optional max tokens limit
        
    Returns:
        Conversation data with ID
    """
    url = f"{self.base_url}/api/v1/users/conversations"
    
    payload = {
        "title": title,
    }
    
    if context:
        payload["context"] = context
    if llm_model:
        payload["llm_model"] = llm_model
    if temperature is not None:
        payload["temperature"] = temperature
    if max_tokens:
        payload["max_tokens"] = max_tokens
    
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(
                url,
                json=payload,
                headers=self._get_headers(token),
            )
            response.raise_for_status()
            return response.json()
            
    except Exception as e:
        logger.error(f"Error creating conversation: {str(e)}")
        raise
```

---

### 4. Enhanced Error Handling (مهم ⭐⭐)

#### وضعیت فعلی:
```python
except httpx.HTTPStatusError as e:
    logger.error(f"Core API HTTP error: {e.response.status_code} - {e.response.text}")
    raise
```

#### مستندات Core - Error Codes:
- `AUTH_INVALID`
- `AUTH_EXPIRED`
- `RATE_LIMIT_EXCEEDED`
- `QUOTA_EXCEEDED`
- `INVALID_REQUEST`
- `SERVER_ERROR`

#### تغییرات لازم - ایجاد Custom Exceptions:

فایل جدید: `/srv/backend/chat/exceptions.py`

```python
"""Custom exceptions for Core API integration."""


class CoreAPIException(Exception):
    """Base exception for Core API errors."""
    pass


class AuthInvalidError(CoreAPIException):
    """Invalid authentication token."""
    pass


class AuthExpiredError(CoreAPIException):
    """Expired authentication token."""
    pass


class RateLimitExceededError(CoreAPIException):
    """Rate limit exceeded."""
    def __init__(self, limit: int, used: int, reset_time: str):
        self.limit = limit
        self.used = used
        self.reset_time = reset_time
        super().__init__(f"Rate limit exceeded: {used}/{limit}")


class QuotaExceededError(CoreAPIException):
    """Daily quota exceeded."""
    def __init__(self, limit: int, used: int, reset_time: str):
        self.limit = limit
        self.used = used
        self.reset_time = reset_time
        super().__init__(f"Daily quota exceeded: {used}/{limit}")


class InvalidRequestError(CoreAPIException):
    """Invalid request parameters."""
    pass


class CoreServerError(CoreAPIException):
    """Internal server error in Core."""
    pass


def parse_core_error(status_code: int, response_data: dict) -> CoreAPIException:
    """Parse Core API error response and return appropriate exception."""
    
    error_code = response_data.get('error', {}).get('code')
    message = response_data.get('error', {}).get('message', 'Unknown error')
    details = response_data.get('error', {}).get('details', {})
    
    if status_code == 401:
        if error_code == 'AUTH_EXPIRED':
            return AuthExpiredError(message)
        return AuthInvalidError(message)
    
    elif status_code == 429:
        if error_code == 'RATE_LIMIT_EXCEEDED':
            return RateLimitExceededError(
                limit=details.get('limit', 0),
                used=details.get('used', 0),
                reset_time=details.get('reset_time', 'Unknown')
            )
        elif error_code == 'QUOTA_EXCEEDED':
            return QuotaExceededError(
                limit=details.get('limit', 0),
                used=details.get('used', 0),
                reset_time=details.get('reset_time', 'Unknown')
            )
    
    elif status_code == 400:
        return InvalidRequestError(message)
    
    elif status_code >= 500:
        return CoreServerError(message)
    
    return CoreAPIException(message)
```

**استفاده در core_service.py:**

```python
from .exceptions import parse_core_error

async def send_query(self, ...):
    try:
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(...)
            response.raise_for_status()
            return response.json()
            
    except httpx.HTTPStatusError as e:
        # Parse error response
        try:
            error_data = e.response.json()
        except:
            error_data = {"error": {"message": e.response.text}}
        
        # Raise appropriate exception
        exception = parse_core_error(e.response.status_code, error_data)
        logger.error(f"Core API error: {exception}")
        raise exception
        
    except Exception as e:
        logger.error(f"Core API error: {str(e)}")
        raise CoreServerError(str(e))
```

---

## ✅ موارد تطابق کامل:

### 1. Query Endpoint ✅
```python
POST /api/v1/query/
```
پیاده‌سازی شده در `core_service.send_query()`

### 2. Streaming Endpoint ✅
```python
POST /api/v1/query/stream
```
پیاده‌سازی شده در `core_service.send_query_stream()`

### 3. Feedback Endpoint ✅
```python
POST /api/v1/query/feedback
```
پیاده‌سازی شده در `core_service.submit_feedback()`

### 4. User Profile ✅
```python
GET /api/v1/users/profile
PATCH /api/v1/users/profile
```
پیاده‌سازی شده در `core_service.get_user_profile()`

### 5. Conversations List ✅
```python
GET /api/v1/users/conversations
```
پیاده‌سازی شده در `core_service.get_conversations()`

### 6. Conversation Messages ✅
```python
GET /api/v1/users/conversations/{id}/messages
```
پیاده‌سازی شده در `core_service.get_conversation_messages()`

### 7. Delete Conversation ✅
```python
DELETE /api/v1/users/conversations/{id}
```
پیاده‌سازی شده در `core_service.delete_conversation()`

---

## 📝 چک لیست پیاده‌سازی:

### فوری (Priority 1):
- [ ] **JWT Token با username, email, tier** (فایل: `accounts/tokens.py` + `core/settings.py`)
- [ ] **Filters Support** (فایل: `chat/core_service.py`)
- [ ] **Enhanced Error Handling** (فایل: `chat/exceptions.py`)

### متوسط (Priority 2):
- [ ] **Create Conversation API** (فایل: `chat/core_service.py`)
- [ ] **Request Validation** (استفاده از Pydantic)
- [ ] **Rate Limiting Client-Side** (جلوگیری از 429)

### اختیاری (Priority 3):
- [ ] **Caching Strategy** (Redis برای cache محلی)
- [ ] **Request Batching** (بهینه‌سازی performance)
- [ ] **User Analytics** (ثبت رویدادها)
- [ ] **Monitoring Metrics** (Prometheus/Grafana)

---

## 🔧 فایل‌های نیازمند تغییر:

| فایل | تغییرات | اولویت |
|------|---------|--------|
| `/srv/backend/accounts/tokens.py` | ایجاد CustomAccessToken | ⭐⭐⭐ |
| `/srv/backend/core/settings.py` | تغییر SIMPLE_JWT | ⭐⭐⭐ |
| `/srv/backend/chat/consumers.py` | استفاده از CustomAccessToken | ⭐⭐⭐ |
| `/srv/backend/chat/core_service.py` | اضافه filters و create_conversation | ⭐⭐ |
| `/srv/backend/chat/exceptions.py` | ایجاد custom exceptions | ⭐⭐ |

---

## 📊 نتیجه‌گیری:

### وضعیت کلی: 70% تطابق ✅

**نقاط قوت:**
- ✅ تمام Endpoints اصلی پیاده شده
- ✅ JWT Authentication کار می‌کند
- ✅ Streaming پشتیبانی می‌شود

**نقاط ضعف:**
- ⚠️ JWT Token فیلدهای کامل ندارد
- ⚠️ Filters پشتیبانی نمی‌شود
- ⚠️ Error Handling ساده است

**زمان تخمینی برای تکمیل: 4-6 ساعت**

---

## 🚀 مراحل بعدی:

1. پیاده‌سازی JWT Token کامل (1-2 ساعت)
2. اضافه کردن Filters Support (1 ساعت)
3. بهبود Error Handling (1-2 ساعت)
4. تست کامل تمام تغییرات (1 ساعت)

**✅ بعد از این تغییرات، سیستم 100% با مستندات Core تطابق خواهد داشت.**
