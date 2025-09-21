#!/usr/bin/env python3
"""
Test script for Torob AI Assistant API
"""

import requests
import json
import time
import sys

API_BASE_URL = "http://localhost:8000"

def test_health():
    """Test health endpoint"""
    print("🔍 Testing health endpoint...")
    try:
        response = requests.get(f"{API_BASE_URL}/health")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Health check passed: {data['status']}")
            return True
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Health check error: {e}")
        return False

def test_chat_endpoint():
    """Test chat endpoint with sample requests"""
    print("\n🔍 Testing chat endpoint...")
    
    test_cases = [
        {
            "name": "General Question",
            "request": {
                "chat_id": "test-123",
                "messages": [
                    {
                        "type": "text",
                        "content": "سلام، چطور می‌تونم از سایت خرید کنم؟"
                    }
                ]
            }
        },
        {
            "name": "Product Search",
            "request": {
                "chat_id": "test-456",
                "messages": [
                    {
                        "type": "text",
                        "content": "آیفون 16 پرو مکس می‌خوام"
                    }
                ]
            }
        },
        {
            "name": "Invalid Message Type",
            "request": {
                "chat_id": "test-789",
                "messages": [
                    {
                        "type": "invalid",
                        "content": "test message"
                    }
                ]
            },
            "expect_error": True
        },
        {
            "name": "Empty Message",
            "request": {
                "chat_id": "test-000",
                "messages": [
                    {
                        "type": "text",
                        "content": ""
                    }
                ]
            },
            "expect_error": True
        }
    ]
    
    for test_case in test_cases:
        print(f"\n📝 Testing: {test_case['name']}")
        try:
            response = requests.post(
                f"{API_BASE_URL}/chat",
                json=test_case['request'],
                headers={"Content-Type": "application/json"}
            )
            
            if test_case.get('expect_error', False):
                if response.status_code >= 400:
                    print(f"✅ Expected error received: {response.status_code}")
                else:
                    print(f"❌ Expected error but got success: {response.status_code}")
            else:
                if response.status_code == 200:
                    data = response.json()
                    print(f"✅ Success: {data.get('message', 'No message')[:50]}...")
                    if data.get('base_random_keys'):
                        print(f"   📦 Base keys: {data['base_random_keys']}")
                    if data.get('member_random_keys'):
                        print(f"   👥 Member keys: {data['member_random_keys']}")
                else:
                    print(f"❌ Failed: {response.status_code} - {response.text}")
                    
        except Exception as e:
            print(f"❌ Error: {e}")

def wait_for_api():
    """Wait for API to be ready"""
    print("⏳ Waiting for API to be ready...")
    max_attempts = 30
    for attempt in range(max_attempts):
        try:
            response = requests.get(f"{API_BASE_URL}/health", timeout=5)
            if response.status_code == 200:
                print("✅ API is ready!")
                return True
        except:
            pass
        
        print(f"   Attempt {attempt + 1}/{max_attempts}...")
        time.sleep(2)
    
    print("❌ API not ready after 60 seconds")
    return False

def main():
    """Main test function"""
    print("🚀 Starting Torob AI Assistant API Tests")
    print("=" * 50)
    
    # Wait for API to be ready
    if not wait_for_api():
        print("❌ Cannot proceed with tests - API not available")
        sys.exit(1)
    
    # Run tests
    health_ok = test_health()
    test_chat_endpoint()
    
    print("\n" + "=" * 50)
    if health_ok:
        print("✅ All tests completed!")
    else:
        print("❌ Some tests failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()

