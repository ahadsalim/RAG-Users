#!/usr/bin/env python
"""Test CustomAccessToken implementation"""
import os
import sys
import django

sys.path.insert(0, '/app')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from accounts.models import User
from accounts.tokens import CustomAccessToken
import base64
import json

print("=" * 70)
print("🧪 CUSTOM ACCESS TOKEN TEST")
print("=" * 70)
print()

# Get user
user = User.objects.filter(is_active=True).first()
if not user:
    print("❌ No user found")
    sys.exit(1)

print(f"User ID: {user.id}")
print(f"Username: {user.username}")
print(f"Email: {user.email}")
print(f"Is Staff: {user.is_staff}")
print(f"Is Superuser: {user.is_superuser}")
print()

# Generate token
token = CustomAccessToken.for_user(user)
token_str = str(token)

print(f"✅ Token generated")
print(f"Token: {token_str[:100]}...")
print()

# Decode payload
parts = token_str.split('.')
if len(parts) != 3:
    print("❌ Invalid token format")
    sys.exit(1)

# Decode payload (add padding if needed)
payload_encoded = parts[1]
padding = 4 - len(payload_encoded) % 4
if padding != 4:
    payload_encoded += '=' * padding

payload_bytes = base64.urlsafe_b64decode(payload_encoded)
payload = json.loads(payload_bytes)

print("📋 Token Payload:")
print(json.dumps(payload, indent=2, ensure_ascii=False))
print()

# Check required fields
print("✓ Field checks:")
required_fields = ['sub', 'username', 'email', 'tier', 'type', 'exp', 'iat']
for field in required_fields:
    if field in payload:
        print(f"  ✅ '{field}': {payload[field]}")
    else:
        print(f"  ❌ '{field}': MISSING")

print()
print("=" * 70)
