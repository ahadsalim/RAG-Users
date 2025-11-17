#!/usr/bin/env python
"""
Test Core API user profile endpoint
"""
import os
import sys
import django
import asyncio

# Setup Django
sys.path.insert(0, '/app')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from chat.core_service import core_service
from accounts.models import User
from rest_framework_simplejwt.tokens import AccessToken
from asgiref.sync import sync_to_async


def get_test_user():
    return User.objects.filter(is_active=True).first()


def generate_token(user):
    token = AccessToken.for_user(user)
    return str(token)


async def test_profile():
    """Test user profile endpoint."""
    
    print("=" * 60)
    print("🧪 CORE API PROFILE TEST")
    print("=" * 60)
    print()
    
    # Get user and token
    user = await sync_to_async(get_test_user)()
    if not user:
        print("❌ No user found")
        return False
    
    username = await sync_to_async(lambda: user.username or user.email or "Unknown")()
    user_id = await sync_to_async(lambda: str(user.id))()
    
    print(f"✅ User: {username}")
    print(f"   ID: {user_id}")
    print()
    
    token_str = await sync_to_async(generate_token)(user)
    print(f"✅ Token generated")
    print()
    
    # Test profile endpoint
    print("Testing /api/v1/users/profile...")
    try:
        profile = await core_service.get_user_profile(token_str)
        
        if profile:
            print("✅ Profile retrieved successfully!")
            print()
            print("📊 Profile data:")
            print(f"   User ID: {profile.get('id')}")
            print(f"   External User ID: {profile.get('external_user_id')}")
            print(f"   Username: {profile.get('username')}")
            print(f"   Email: {profile.get('email')}")
            print(f"   Tier: {profile.get('tier')}")
            print(f"   Daily limit: {profile.get('daily_query_limit')}")
            print(f"   Daily count: {profile.get('daily_query_count')}")
            print(f"   Total queries: {profile.get('total_query_count')}")
            print(f"   Created: {profile.get('created_at')}")
            return True
        else:
            print("❌ Profile not found (user may be auto-created)")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        print()
        print("=" * 60)


if __name__ == "__main__":
    success = asyncio.run(test_profile())
    sys.exit(0 if success else 1)
