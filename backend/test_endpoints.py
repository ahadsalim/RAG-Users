#!/usr/bin/env python
"""
Test all Core API endpoints to find which one returns 500
"""
import os
import sys
import django
import asyncio
import httpx

# Setup Django
sys.path.insert(0, '/app')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from accounts.models import User
from rest_framework_simplejwt.tokens import AccessToken
from asgiref.sync import sync_to_async


def get_test_user():
    return User.objects.filter(is_active=True).first()


def generate_token(user):
    token = AccessToken.for_user(user)
    return str(token)


async def test_all_endpoints():
    """Test all Core API endpoints."""
    
    print("=" * 70)
    print("🧪 CORE API ENDPOINTS TEST")
    print("=" * 70)
    print()
    
    # Get user and token
    user = await sync_to_async(get_test_user)()
    if not user:
        print("❌ No user found")
        return
    
    token = await sync_to_async(generate_token)(user)
    
    username = await sync_to_async(lambda: user.username or user.email or "Unknown")()
    user_id = await sync_to_async(lambda: str(user.id))()
    
    print(f"User: {username}")
    print(f"User ID: {user_id}")
    print(f"Token: {token[:50]}...")
    print()
    print("=" * 70)
    print()
    
    base_url = "https://core.tejarat.chat"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    # Test endpoints
    tests = [
        {
            "name": "1. Health Check",
            "method": "GET",
            "url": f"{base_url}/api/v1/health",
            "headers": {},  # No auth needed
            "data": None
        },
        {
            "name": "2. User Profile",
            "method": "GET",
            "url": f"{base_url}/api/v1/users/profile",
            "headers": headers,
            "data": None
        },
        {
            "name": "3. User Statistics",
            "method": "GET",
            "url": f"{base_url}/api/v1/users/statistics",
            "headers": headers,
            "data": None
        },
        {
            "name": "4. User Conversations",
            "method": "GET",
            "url": f"{base_url}/api/v1/users/conversations",
            "headers": headers,
            "data": None
        },
        {
            "name": "5. Query (Simple)",
            "method": "POST",
            "url": f"{base_url}/api/v1/query/",
            "headers": headers,
            "data": {
                "query": "سلام",
                "language": "fa",
                "max_results": 3,
                "use_cache": True,
                "use_reranking": False,
                "stream": False
            }
        },
        {
            "name": "6. Query (Full)",
            "method": "POST",
            "url": f"{base_url}/api/v1/query/",
            "headers": headers,
            "data": {
                "query": "قانون کار چیست؟",
                "language": "fa",
                "max_results": 5,
                "use_cache": True,
                "use_reranking": True,
                "stream": False
            }
        }
    ]
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        for test in tests:
            print(f"Testing: {test['name']}")
            print(f"  Method: {test['method']}")
            print(f"  URL: {test['url']}")
            
            try:
                if test['method'] == 'GET':
                    response = await client.get(
                        test['url'],
                        headers=test['headers']
                    )
                else:
                    response = await client.post(
                        test['url'],
                        json=test['data'],
                        headers=test['headers']
                    )
                
                print(f"  ✅ Status: {response.status_code}")
                
                if response.status_code == 200:
                    data = response.json()
                    # Show first few keys
                    if isinstance(data, dict):
                        keys = list(data.keys())[:5]
                        print(f"  📊 Response keys: {keys}")
                    elif isinstance(data, list):
                        print(f"  📊 Response: List with {len(data)} items")
                else:
                    print(f"  ⚠️  Response: {response.text[:200]}")
                
            except httpx.HTTPStatusError as e:
                print(f"  ❌ HTTP Error: {e.response.status_code}")
                print(f"     Response: {e.response.text[:200]}")
            except Exception as e:
                print(f"  ❌ Error: {str(e)}")
            
            print()
    
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(test_all_endpoints())
