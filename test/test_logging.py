#!/usr/bin/env python3
"""
Test script to demonstrate HTTP POST logging in FastAPI
"""

import requests
import json
import time

# API endpoint
API_URL = "http://localhost:8000"

def test_chat_endpoint():
    """Test the chat endpoint with logging"""
    
    # Test data
    test_data = {
        "chat_id": "test_chat_123",
        "messages": [
            {
                "type": "text",
                "content": "سلام، من دنبال یک گوشی موبایل خوب می‌گردم"
            }
        ]
    }
    
    print("Testing chat endpoint with logging...")
    print(f"Request data: {json.dumps(test_data, indent=2, ensure_ascii=False)}")
    print("-" * 50)
    
    try:
        # Make POST request
        response = requests.post(
            f"{API_URL}/chat",
            json=test_data,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"Response Status: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        print(f"Response Body: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
        
    except requests.exceptions.ConnectionError:
        print("Error: Could not connect to the API. Make sure the server is running on localhost:8000")
    except Exception as e:
        print(f"Error: {e}")

def test_health_endpoint():
    """Test the health endpoint"""
    
    print("\nTesting health endpoint...")
    print("-" * 50)
    
    try:
        response = requests.get(f"{API_URL}/health")
        print(f"Response Status: {response.status_code}")
        print(f"Response Body: {json.dumps(response.json(), indent=2)}")
        
    except requests.exceptions.ConnectionError:
        print("Error: Could not connect to the API. Make sure the server is running on localhost:8000")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    print("FastAPI HTTP POST Logging Test")
    print("=" * 50)
    
    # Test health endpoint first
    test_health_endpoint()
    
    # Test chat endpoint
    test_chat_endpoint()
    
    print("\n" + "=" * 50)
    print("Test completed! Check the logs directory for detailed logs:")
    print("- logs/api.log - General application logs")
    print("- logs/http_requests.log - HTTP request/response logs")
    print("- logs/chat_interactions.log - Chat-specific logs")
    print("- logs/errors.log - Error logs")
