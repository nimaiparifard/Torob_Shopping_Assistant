#!/usr/bin/env python3
"""
Test script to verify response logging is working
"""

import requests
import json
import time
import os

def test_response_logging():
    """Test the chat API and verify response logging works"""
    
    API_URL = "http://localhost:8000"
    
    print("🧪 Testing Response Logging")
    print("=" * 50)
    
    # Test data
    test_data = {
        "chat_id": "response_test_123",
        "messages": [
            {
                "type": "text",
                "content": "سلام، من دنبال یک گوشی موبایل می‌گردم"
            }
        ]
    }
    
    print("1. Sending chat request...")
    print(f"   Request: {json.dumps(test_data, indent=2, ensure_ascii=False)}")
    
    try:
        # Make POST request to chat endpoint
        response = requests.post(
            f"{API_URL}/chat",
            json=test_data,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"   Response Status: {response.status_code}")
        print(f"   Response: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
        
        # Wait a moment for logging to complete
        time.sleep(2)
        
        # Check log files
        print("\n2. Checking log files for response content...")
        check_response_logs()
        
    except requests.exceptions.ConnectionError:
        print("   ❌ Error: Could not connect to the API. Make sure the server is running on localhost:8000")
    except Exception as e:
        print(f"   ❌ Error: {e}")

def check_response_logs():
    """Check if response content is logged"""
    
    import os
    
    # Check http_requests.log for response content
    if os.path.exists('logs/http_requests.log'):
        with open('logs/http_requests.log', 'r', encoding='utf-8') as f:
            content = f.read()
            if 'response_test_123' in content:
                print("   ✅ http_requests.log: Contains our test request")
                if '"response":' in content:
                    print("   ✅ http_requests.log: Contains response content")
                else:
                    print("   ❌ http_requests.log: Missing response content")
            else:
                print("   ❌ http_requests.log: Does not contain our test request")
    else:
        print("   ❌ http_requests.log: File not found")
    
    # Check chat_interactions.log
    if os.path.exists('logs/chat_interactions.log'):
        with open('logs/chat_interactions.log', 'r', encoding='utf-8') as f:
            content = f.read()
            if 'response_test_123' in content:
                print("   ✅ chat_interactions.log: Contains our test request")
            else:
                print("   ❌ chat_interactions.log: Does not contain our test request")
    else:
        print("   ❌ chat_interactions.log: File not found")

def show_recent_logs():
    """Show recent log entries"""
    
    print("\n3. Recent log entries:")
    print("-" * 40)
    
    log_files = ['logs/http_requests.log', 'logs/chat_interactions.log']
    
    for log_file in log_files:
        if os.path.exists(log_file):
            print(f"\n📄 {log_file}:")
            with open(log_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                # Show last 3 lines
                for line in lines[-3:]:
                    print(f"   {line.strip()}")

if __name__ == "__main__":
    test_response_logging()
    show_recent_logs()
    
    print("\n" + "=" * 50)
    print("✅ Response logging test completed!")
    print("\n💡 The logs should now include:")
    print("   - Request body (JSON)")
    print("   - Response body (JSON)")
    print("   - Processing time")
    print("   - Client IP and headers")
