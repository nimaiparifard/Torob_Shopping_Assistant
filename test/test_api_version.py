#!/usr/bin/env python3
"""
Test script to check if API is using updated code
"""

import requests
import json

def test_api_version():
    """Test if the API is using the updated code with logging"""
    
    API_URL = "http://localhost:8000"
    
    print("🔍 Testing API Version and Logging")
    print("=" * 50)
    
    # Test 1: Check if download endpoints exist (new feature)
    print("1. Testing download endpoints (new feature)...")
    try:
        response = requests.get(f"{API_URL}/logs/list")
        if response.status_code == 200:
            print("   ✅ Download endpoints are available - API is using updated code")
        else:
            print(f"   ❌ Download endpoints not available - Status: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Test 2: Make a chat request and check if it gets logged
    print("\n2. Testing chat request logging...")
    test_data = {
        "chat_id": "version_test_123",
        "messages": [
            {
                "type": "text",
                "content": "test message for logging"
            }
        ]
    }
    
    try:
        response = requests.post(
            f"{API_URL}/chat",
            json=test_data,
            headers={"Content-Type": "application/json"}
        )
        print(f"   Response Status: {response.status_code}")
        
        # Wait a moment for logging
        import time
        time.sleep(1)
        
        # Check if logs were updated
        print("\n3. Checking if logs were updated...")
        check_recent_logs()
        
    except Exception as e:
        print(f"   ❌ Error: {e}")

def check_recent_logs():
    """Check if recent logs contain our test request"""
    
    import os
    from datetime import datetime, timedelta
    
    log_files = ['logs/http_requests.log', 'logs/chat_interactions.log']
    
    for log_file in log_files:
        if os.path.exists(log_file):
            with open(log_file, 'r', encoding='utf-8') as f:
                content = f.read()
                if 'version_test_123' in content:
                    print(f"   ✅ {log_file}: Contains our test request")
                else:
                    print(f"   ❌ {log_file}: Does not contain our test request")
        else:
            print(f"   ❌ {log_file}: File not found")

if __name__ == "__main__":
    test_api_version()
