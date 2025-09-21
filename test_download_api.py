#!/usr/bin/env python3
"""
Test script for log file download API endpoints
"""

import requests
import json
import os

def test_download_endpoints():
    """Test the download API endpoints"""
    
    API_URL = "http://localhost:8000"
    
    print("Testing Log Download API Endpoints")
    print("=" * 50)
    
    # Test 1: List available logs
    print("1. Testing /logs/list endpoint...")
    try:
        response = requests.get(f"{API_URL}/logs/list")
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            logs_info = response.json()
            print("   Available logs:")
            for log_type, info in logs_info.items():
                if 'status' not in info:
                    print(f"     - {log_type}: {info['size_mb']} MB")
                    print(f"       Download URL: {API_URL}{info['download_url']}")
                else:
                    print(f"     - {log_type}: Not found")
        else:
            print(f"   Error: {response.text}")
    except Exception as e:
        print(f"   Error: {e}")
    
    print()
    
    # Test 2: Download specific log file
    print("2. Testing /download/logs/api endpoint...")
    try:
        response = requests.get(f"{API_URL}/download/logs/api")
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            # Save the downloaded file
            with open("downloaded_api_log.log", "wb") as f:
                f.write(response.content)
            print(f"   Downloaded {len(response.content)} bytes")
            print("   Saved as: downloaded_api_log.log")
        else:
            print(f"   Error: {response.text}")
    except Exception as e:
        print(f"   Error: {e}")
    
    print()
    
    # Test 3: Download all logs as zip
    print("3. Testing /download/logs endpoint (zip download)...")
    try:
        response = requests.get(f"{API_URL}/download/logs")
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            # Save the downloaded zip file
            with open("downloaded_logs.zip", "wb") as f:
                f.write(response.content)
            print(f"   Downloaded {len(response.content)} bytes")
            print("   Saved as: downloaded_logs.zip")
        else:
            print(f"   Error: {response.text}")
    except Exception as e:
        print(f"   Error: {e}")
    
    print()
    
    # Test 4: Test invalid log type
    print("4. Testing invalid log type...")
    try:
        response = requests.get(f"{API_URL}/download/logs/invalid")
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.json()}")
    except Exception as e:
        print(f"   Error: {e}")
    
    print()
    print("=" * 50)
    print("Download API test completed!")
    print()
    print("You can also test these URLs directly in your browser:")
    print(f"- {API_URL}/logs/list")
    print(f"- {API_URL}/download/logs")
    print(f"- {API_URL}/download/logs/api")
    print(f"- {API_URL}/download/logs/http")
    print(f"- {API_URL}/download/logs/chat")
    print(f"- {API_URL}/download/logs/errors")

if __name__ == "__main__":
    test_download_endpoints()
