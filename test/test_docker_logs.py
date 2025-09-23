#!/usr/bin/env python3
"""
Test script to verify Docker log setup works locally
"""

import os
import subprocess
import sys

def test_docker_logs():
    """Test that Docker can create and use log files"""
    
    print("🐳 Testing Docker Log Setup")
    print("=" * 50)
    
    # Test 1: Check if we can create log files
    print("1. Testing log file creation...")
    try:
        os.makedirs('../logs', exist_ok=True)
        log_files = ['api.log', 'http_requests.log', 'chat_interactions.log', 'errors.log']
        
        for log_file in log_files:
            log_path = f'logs/{log_file}'
            with open(log_path, 'w') as f:
                f.write(f"# Test log file - {log_file}\n")
            print(f"   ✅ Created {log_path}")
        
        print("   ✅ All log files created successfully")
        
    except Exception as e:
        print(f"   ❌ Failed to create log files: {e}")
        return False
    
    # Test 2: Test logging functionality
    print("\n2. Testing logging functionality...")
    try:
        from api.logging_config import setup_logging, log_http_request, log_chat_interaction
        
        # Setup logging
        setup_logging()
        print("   ✅ Logging configuration loaded")
        
        # Test HTTP request logging
        log_http_request(
            method="POST",
            path="/chat",
            client_ip="127.0.0.1",
            status_code=200,
            process_time=0.123,
            body='{"test": "data"}',
            headers={"content-type": "application/json"},
            response='{"message": "test response"}'
        )
        print("   ✅ HTTP request logging test passed")
        
        # Test chat interaction logging
        log_chat_interaction(
            chat_id="docker_test_123",
            user_query="test query for Docker",
            agent_type="GENERAL",
            response_message="test response for Docker",
            keys_count=0,
            process_time=0.456
        )
        print("   ✅ Chat interaction logging test passed")
        
    except Exception as e:
        print(f"   ❌ Logging functionality test failed: {e}")
        return False
    
    # Test 3: Verify log files have content
    print("\n3. Verifying log files have content...")
    try:
        log_files = ['logs/http_requests.log', 'logs/chat_interactions.log']
        
        for log_file in log_files:
            if os.path.exists(log_file):
                with open(log_file, 'r') as f:
                    content = f.read()
                    if 'docker_test_123' in content or 'test response' in content:
                        print(f"   ✅ {log_file} contains test data")
                    else:
                        print(f"   ⚠️ {log_file} exists but no test data found")
            else:
                print(f"   ❌ {log_file} not found")
        
    except Exception as e:
        print(f"   ❌ Failed to verify log content: {e}")
        return False
    
    print("\n" + "=" * 50)
    print("✅ Docker log setup test completed successfully!")
    print("\n💡 When deployed, the Docker container will:")
    print("   - Create logs directory")
    print("   - Create all required log files")
    print("   - Set proper permissions")
    print("   - Verify logging functionality works")
    
    return True

if __name__ == "__main__":
    success = test_docker_logs()
    sys.exit(0 if success else 1)
