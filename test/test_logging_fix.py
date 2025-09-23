#!/usr/bin/env python3
"""
Test script to verify HTTP POST logging is working
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from api.logging_config import log_http_request, log_chat_interaction

def test_logging_functions():
    """Test the logging functions directly"""
    
    print("Testing HTTP request logging...")
    
    # Test HTTP request logging
    log_http_request(
        method="POST",
        path="/chat",
        client_ip="127.0.0.1",
        status_code=200,
        process_time=0.1234,
        body='{"chat_id": "test_123", "messages": [{"type": "text", "content": "سلام خوبی"}]}',
        headers={"content-type": "application/json"}
    )
    
    print("Testing chat interaction logging...")
    
    # Test chat interaction logging
    log_chat_interaction(
        chat_id="test_123",
        user_query="سلام، من دنبال یک گوشی موبایل می‌گردم",
        agent_type="SPECIFIC_PRODUCT",
        response_message="محصول مورد نظر شما یافت شد",
        keys_count=1,
        process_time=0.5678
    )
    
    print("Logging test completed!")
    print("Check the following files:")
    print("- logs/http_requests.log")
    print("- logs/chat_interactions.log")

if __name__ == "__main__":
    test_logging_functions()
