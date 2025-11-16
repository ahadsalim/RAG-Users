#!/usr/bin/env python
"""
Clear OTP cache for testing
Usage: docker-compose exec backend python clear_otp_cache.py
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.core.cache import cache

# Clear all OTP rate limits
rate_limit_keys = [key for key in cache.keys('*') if 'otp_rate_limit_' in key]
for key in rate_limit_keys:
    cache.delete(key)
print(f"✅ Cleared {len(rate_limit_keys)} rate limit keys")

# Clear all OTP codes
otp_keys = [key for key in cache.keys('*') if key.startswith('otp_') and 'rate_limit' not in key]
for key in otp_keys:
    cache.delete(key)
print(f"✅ Cleared {len(otp_keys)} OTP keys")

print("\n🎉 Cache cleared successfully!")
