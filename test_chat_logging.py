#!/usr/bin/env python3
"""
Test script to verify chat API logging is working properly
"""

import requests
import json
import time
import os

def test_chat_logging():
    """Test the chat API and verify logging works"""
    
    API_URL = "http://localhost:8000"
    
    print("🧪 Testing Chat API Logging")
    print("=" * 50)
    
    # Test data
    test_data = {
        "chat_id": "logging_test_123",
        "messages": [
            {
                "type": "text",
                "content": "سلام، من دنبال یک گوشی موبایل خوب می‌گردم"
            }
        ]
    }
    
    print("1. Sending chat request...")
    print(f"   Request data: {json.dumps(test_data, indent=2, ensure_ascii=False)}")
    
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
        time.sleep(1)
        
        # Check log files
        print("\n2. Checking log files...")
        check_log_files()
        
    except requests.exceptions.ConnectionError:
        print("   ❌ Error: Could not connect to the API. Make sure the server is running on localhost:8000")
    except Exception as e:
        print(f"   ❌ Error: {e}")

def check_log_files():
    """Check if log files exist and have content"""
    
    log_files = {
        'api.log': 'logs/api.log',
        'http_requests.log': 'logs/http_requests.log',
        'chat_interactions.log': 'logs/chat_interactions.log',
        'errors.log': 'logs/errors.log'
    }
    
    for log_name, log_path in log_files.items():
        if os.path.exists(log_path):
            with open(log_path, 'r', encoding='utf-8') as f:
                content = f.read().strip()
                if content:
                    lines = content.split('\n')
                    print(f"   ✅ {log_name}: {len(lines)} lines")
                    # Show last few lines
                    if len(lines) > 0:
                        print(f"      Last line: {lines[-1][:100]}...")
                else:
                    print(f"   ⚠️ {log_name}: Empty file")
        else:
            print(f"   ❌ {log_name}: File not found")

def test_multiple_requests():
    """Test multiple chat requests to see logging accumulation"""
    
    API_URL = "http://localhost:8000"
    
    print("\n3. Testing multiple requests...")
    
    test_requests = [
        {
            "chat_id": "test_1",
            "messages": [{"type": "text", "content": "گوشی موبایل"}]
        },
        {
            "chat_id": "test_2", 
            "messages": [{"type": "text", "content": "لپ‌تاپ"}]
        },
        {
            "chat_id": "test_3",
            "messages": [{"type": "text", "content": "کامپیوتر"}]
        }
    ]
    
    for i, test_data in enumerate(test_requests, 1):
        print(f"   Request {i}: {test_data['messages'][0]['content']}")
        try:
            response = requests.post(
                f"{API_URL}/chat",
                json=test_data,
                headers={"Content-Type": "application/json"}
            )
            print(f"      Status: {response.status_code}")
        except Exception as e:
            print(f"      Error: {e}")
        
        # Small delay between requests
        time.sleep(0.5)
    
    print("\n4. Final log file check...")
    check_log_files()

def show_log_content():
    """Show the actual content of log files"""
    
    print("\n5. Log file contents:")
    print("=" * 30)
    
    log_files = ['logs/api.log', 'logs/http_requests.log', 'logs/chat_interactions.log']
    
    for log_file in log_files:
        if os.path.exists(log_file):
            print(f"\n📄 {log_file}:")
            print("-" * 40)
            with open(log_file, 'r', encoding='utf-8') as f:
                content = f.read().strip()
                if content:
                    lines = content.split('\n')
                    # Show last 5 lines
                    for line in lines[-5:]:
                        print(f"   {line}")
                else:
                    print("   (empty)")

if __name__ == "__main__":
    print("🔍 Chat API Logging Test")
    print("=" * 50)
    
    # Test single request
    test_chat_logging()
    
    # Test multiple requests
    test_multiple_requests()
    
    # Show log content
    show_log_content()
    
    print("\n" + "=" * 50)
    print("✅ Test completed!")
    print("\n💡 If logging is working, you should see:")
    print("   - HTTP requests in logs/http_requests.log")
    print("   - Chat interactions in logs/chat_interactions.log")
    print("   - General logs in logs/api.log")
