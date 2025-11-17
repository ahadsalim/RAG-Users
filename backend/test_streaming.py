#!/usr/bin/env python
"""Test streaming query"""
import os
import sys
import django
import asyncio

sys.path.insert(0, '/app')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from chat.core_service import core_service
from accounts.models import User
from accounts.tokens import CustomAccessToken
from asgiref.sync import sync_to_async


def get_test_user():
    return User.objects.filter(is_active=True).first()


def generate_token(user):
    token = CustomAccessToken.for_user(user)
    return str(token)


async def test_streaming():
    """Test streaming query."""
    
    print("=" * 70)
    print("🧪 STREAMING QUERY TEST")
    print("=" * 70)
    print()
    
    # Get user and token
    user = await sync_to_async(get_test_user)()
    if not user:
        print("❌ No user found")
        return False
    
    token = await sync_to_async(generate_token)(user)
    
    print(f"User ID: {user.id}")
    print(f"Token length: {len(token)} chars")
    print()
    
    # Test streaming
    print("Testing streaming query...")
    print("Query: سلام")
    print()
    print("Response stream:")
    print("-" * 70)
    
    chunk_count = 0
    full_response = ""
    
    try:
        async for chunk in core_service.send_query_stream(
            query="سلام",
            token=token,
            conversation_id=None,
            language='fa'
        ):
            chunk_count += 1
            full_response += chunk
            print(chunk, end='', flush=True)
        
        print()
        print("-" * 70)
        print()
        print(f"✅ Streaming completed!")
        print(f"   Total chunks: {chunk_count}")
        print(f"   Response length: {len(full_response)} chars")
        return True
        
    except Exception as e:
        print()
        print("-" * 70)
        print(f"❌ Streaming failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        print()
        print("=" * 70)


if __name__ == "__main__":
    success = asyncio.run(test_streaming())
    sys.exit(0 if success else 1)
