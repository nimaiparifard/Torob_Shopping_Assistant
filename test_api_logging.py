#!/usr/bin/env python3
"""
Test script to verify HTTP POST logging works with the actual API
"""

import requests
import json
import time

def test_api_logging():
    """Test the API endpoints and verify logging"""
    
    API_URL = "http://localhost:8000"
    
    print("Testing API logging...")
    print("=" * 50)
    
    # Test 1: Health endpoint (GET request)
    print("1. Testing health endpoint (GET)...")
    try:
        response = requests.get(f"{API_URL}/health")
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.json()}")
    except Exception as e:
        print(f"   Error: {e}")
    
    print()
    
    # Test 2: Chat endpoint (POST request)
    print("2. Testing chat endpoint (POST)...")
    test_data = {
        "chat_id": "logging_test_123",
        "messages": [
            {
                "type": "text",
                "content": "سلام، من دنبال یک گوشی موبایل خوب می‌گردم"
            }
        ]
    }
    
    try:
        response = requests.post(
            f"{API_URL}/chat",
            json=test_data,
            headers={"Content-Type": "application/json"}
        )
        print(f"   Status: {response.status_code}")
        print(f"   Response: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
    except Exception as e:
        print(f"   Error: {e}")
    
    print()
    
    # Test 3: Another POST request with different data
    print("3. Testing another chat request...")
    test_data_2 = {
        "chat_id": "logging_test_456",
        "messages": [
            {
                "type": "text",
                "content": "لطفا یک لپ‌تاپ برای کار پیشنهاد دهید"
            }
        ]
    }
    
    try:
        response = requests.post(
            f"{API_URL}/chat",
            json=test_data_2,
            headers={"Content-Type": "application/json"}
        )
        print(f"   Status: {response.status_code}")
        print(f"   Response: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
    except Exception as e:
        print(f"   Error: {e}")
    
    print()
    print("=" * 50)
    print("Test completed!")
    print()
    print("Check the log files:")
    print("- logs/http_requests.log - Should contain all HTTP requests")
    print("- logs/chat_interactions.log - Should contain chat interactions")
    print("- logs/api.log - Should contain general application logs")
    print()
    print("You can view the logs with:")
    print("- type logs\\http_requests.log")
    print("- type logs\\chat_interactions.log")

if __name__ == "__main__":
    test_api_logging()
