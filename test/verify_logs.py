#!/usr/bin/env python3
"""
Script to verify log files are working in Docker environment
"""

import os
import sys
from pathlib import Path

def verify_log_files():
    """Verify that all required log files exist and are writable"""
    
    print("🔍 Verifying Log Files in Docker Environment")
    print("=" * 50)
    
    # Define log files
    log_files = [
        'logs/api.log',
        'logs/http_requests.log', 
        'logs/chat_interactions.log',
        'logs/errors.log'
    ]
    
    # Check if logs directory exists
    logs_dir = Path('../logs')
    if not logs_dir.exists():
        print("❌ logs directory does not exist")
        print("   Creating logs directory...")
        logs_dir.mkdir(parents=True, exist_ok=True)
        print("   ✅ logs directory created")
    else:
        print("✅ logs directory exists")
    
    # Check each log file
    all_good = True
    for log_file in log_files:
        log_path = Path(log_file)
        
        if not log_path.exists():
            print(f"❌ {log_file} does not exist")
            print(f"   Creating {log_file}...")
            try:
                log_path.touch()
                print(f"   ✅ {log_file} created")
            except Exception as e:
                print(f"   ❌ Failed to create {log_file}: {e}")
                all_good = False
        else:
            print(f"✅ {log_file} exists")
            
            # Check if writable
            try:
                with open(log_path, 'a') as f:
                    f.write(f"# Log file verification - {os.getenv('HOSTNAME', 'unknown')}\n")
                print(f"   ✅ {log_file} is writable")
            except Exception as e:
                print(f"   ❌ {log_file} is not writable: {e}")
                all_good = False
    
    # Test logging functionality
    print("\n🧪 Testing logging functionality...")
    try:
        from api.logging_config import setup_logging, log_http_request, log_chat_interaction
        
        # Setup logging
        setup_logging()
        print("   ✅ Logging configuration loaded")
        
        # Test HTTP request logging
        log_http_request(
            method="GET",
            path="",
            client_ip="127.0.0.1",
            status_code=200,
            process_time=0.1,
            body="test body",
            headers={"test": "header"}
        )
        print("   ✅ HTTP request logging test passed")
        
        # Test chat interaction logging
        log_chat_interaction(
            chat_id="test_123",
            user_query="test query",
            agent_type="GENERAL",
            response_message="test response",
            keys_count=0,
            process_time=0.2
        )
        print("   ✅ Chat interaction logging test passed")
        
    except Exception as e:
        print(f"   ❌ Logging functionality test failed: {e}")
        all_good = False
    
    print("\n" + "=" * 50)
    if all_good:
        print("✅ All log files are working correctly!")
        return True
    else:
        print("❌ Some log files have issues!")
        return False

if __name__ == "__main__":
    success = verify_log_files()
    sys.exit(0 if success else 1)
