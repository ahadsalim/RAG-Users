#!/usr/bin/env python
"""
Test script for Core API integration
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
from accounts.tokens import CustomAccessToken
from asgiref.sync import sync_to_async


def get_test_user():
    """Get a test user (sync function)."""
    return User.objects.filter(is_active=True).first()


def generate_token(user):
    """Generate JWT token (sync function)."""
    token = CustomAccessToken.for_user(user)
    return str(token)


async def test_core_api():
    """Test Core API connection and query."""
    
    print("=" * 60)
    print("🧪 CORE API TEST")
    print("=" * 60)
    
    # 1. Get a test user
    print("\n1️⃣ Getting test user...")
    user = await sync_to_async(get_test_user)()
    if not user:
        print("❌ No active user found!")
        return False
    
    username = await sync_to_async(lambda: user.username or user.email)()
    user_id = await sync_to_async(lambda: str(user.id))()
    print(f"✅ User: {username}")
    print(f"   ID: {user_id}")
    
    # 2. Generate JWT token
    print("\n2️⃣ Generating JWT token...")
    try:
        token_str = await sync_to_async(generate_token)(user)
        print(f"✅ Token generated (length: {len(token_str)})")
        print(f"   Token preview: {token_str[:50]}...")
    except Exception as e:
        print(f"❌ Token generation failed: {e}")
        return False
    
    # 3. Test health check
    print("\n3️⃣ Testing Core API health...")
    print(f"   URL: {core_service.base_url}")
    
    # 4. Send test query (non-streaming)
    print("\n4️⃣ Sending test query...")
    test_query = "قانون کار چیست؟"
    print(f"   Query: {test_query}")
    
    try:
        response = await core_service.send_query(
            query=test_query,
            token=token_str,
            conversation_id=None,
            language='fa',
            stream=False
        )
        
        print("✅ Response received!")
        print(f"\n📊 Response details:")
        print(f"   Answer length: {len(response.get('answer', ''))} chars")
        print(f"   Sources: {len(response.get('sources', []))} items")
        print(f"   Conversation ID: {response.get('conversation_id', 'N/A')}")
        print(f"   Message ID: {response.get('message_id', 'N/A')}")
        print(f"   Tokens used: {response.get('tokens_used', 0)}")
        print(f"   Processing time: {response.get('processing_time_ms', 0)}ms")
        print(f"   Cached: {response.get('cached', False)}")
        
        print(f"\n💬 Answer preview:")
        answer = response.get('answer', '')
        preview = answer[:200] + "..." if len(answer) > 200 else answer
        print(f"   {preview}")
        
        if response.get('sources'):
            print(f"\n📚 Sources:")
            for idx, source in enumerate(response['sources'][:3], 1):
                print(f"   {idx}. {source}")
        
        return True
        
    except Exception as e:
        print(f"❌ Query failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        print("\n" + "=" * 60)


if __name__ == "__main__":
    success = asyncio.run(test_core_api())
    sys.exit(0 if success else 1)
