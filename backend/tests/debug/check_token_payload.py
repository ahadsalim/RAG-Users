#!/usr/bin/env python
"""
Check JWT token payload structure
"""
import os
import sys
import django
import base64
import json

# Setup Django
sys.path.insert(0, '/app')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from accounts.models import User
from accounts.tokens import CustomAccessToken

# Get JWT settings
JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', '').strip('"')
JWT_ALGORITHM = os.getenv('JWT_ALGORITHM', 'HS256')

print("=" * 60)
print("🔍 JWT TOKEN PAYLOAD CHECK")
print("=" * 60)
print()

print(f"JWT_SECRET_KEY length: {len(JWT_SECRET_KEY)} chars")
print(f"JWT_SECRET_KEY preview: {JWT_SECRET_KEY[:30]}...")
print(f"JWT_ALGORITHM: {JWT_ALGORITHM}")
print()

# Get user
user = User.objects.filter(is_active=True).first()
if not user:
    print("❌ No user found")
    sys.exit(1)

print(f"✅ User found")
print(f"   ID: {user.id}")
print(f"   Email: {user.email}")
print()

# Generate token
token = CustomAccessToken.for_user(user)
token_str = str(token)

print(f"Token generated: {token_str[:80]}...")
print()

# Decode WITHOUT verification to see payload
parts = token_str.split('.')
if len(parts) != 3:
    print("❌ Invalid token format")
    sys.exit(1)

# Decode header
header_b64 = parts[0]
padding = 4 - len(header_b64) % 4
if padding < 4:
    header_b64 += '=' * padding
header_bytes = base64.urlsafe_b64decode(header_b64)
header = json.loads(header_bytes)

print("📋 Token Header:")
print(json.dumps(header, indent=2))
print()

# Decode payload
payload_b64 = parts[1]
padding = 4 - len(payload_b64) % 4
if padding < 4:
    payload_b64 += '=' * padding
payload_bytes = base64.urlsafe_b64decode(payload_b64)
payload = json.loads(payload_bytes)

print("📋 Token Payload:")
print(json.dumps(payload, indent=2))
print()

# Check for required fields
print("✓ Field checks:")
if 'sub' in payload:
    print(f"  ✅ 'sub' field found: {payload['sub']}")
else:
    print("  ❌ 'sub' field NOT found!")
    
if 'user_id' in payload:
    print(f"  ⚠️  'user_id' field found: {payload['user_id']} (should use 'sub' instead)")
    
if 'exp' in payload:
    from datetime import datetime
    exp_time = datetime.fromtimestamp(payload['exp'])
    print(f"  ✅ 'exp' field found: {exp_time}")
    
print()
print("Available fields:", list(payload.keys()))
print()
print("=" * 60)
