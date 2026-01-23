#!/usr/bin/env python3
"""
Test script for TrueShift API endpoints with auth bypass enabled.
"""

import requests
import json

BASE_URL = "http://127.0.0.1:8000/api/v1"

def test_register():
    """Test user registration endpoint."""
    print("🧪 Testing /auth/register...")
    
    response = requests.post(
        f"{BASE_URL}/auth/register",
        json={
            "display_name": "Test User",
            "email": "test@example.com"
        },
        headers={
            "Authorization": "Bearer dummy-token"  # Will be bypassed
        }
    )
    
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    return response.json()

def test_get_me(user_id=None):
    """Test get current user endpoint."""
    print("\n🧪 Testing /auth/me...")
    
    response = requests.get(
        f"{BASE_URL}/auth/me",
        headers={
            "Authorization": "Bearer dummy-token"  # Will be bypassed
        }
    )
    
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    return response.json()

def test_update_profile():
    """Test profile update endpoint."""
    print("\n🧪 Testing /auth/me (PUT)...")
    
    response = requests.put(
        f"{BASE_URL}/auth/me",
        json={
            "display_name": "Updated Test User",
            "fitness_goals": ["strength", "endurance"],
            "equipment": ["dumbbells", "resistance_bands"],
            "fitness_level": "intermediate"
        },
        headers={
            "Authorization": "Bearer dummy-token"  # Will be bypassed
        }
    )
    
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    return response.json()

def test_health():
    """Test health check endpoint."""
    print("\n🧪 Testing /health...")
    
    response = requests.get(f"{BASE_URL}/health")
    
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    return response.json()

if __name__ == "__main__":
    print("=" * 60)
    print("TrueShift API Test Suite (Auth Bypass Mode)")
    print("=" * 60)
    
    try:
        # Test health first
        test_health()
        
        # Test registration
        user = test_register()
        
        # Test get current user
        test_get_me()
        
        # Test profile update
        test_update_profile()
        
        print("\n" + "=" * 60)
        print("✅ All tests completed!")
        print("=" * 60)
        
    except requests.exceptions.ConnectionError:
        print("\n❌ Error: Could not connect to the API server.")
        print("Make sure the server is running on http://127.0.0.1:8000")
    except Exception as e:
        print(f"\n❌ Error: {e}")
