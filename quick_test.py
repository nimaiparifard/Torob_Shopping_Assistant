#!/usr/bin/env python3
"""
Quick test to verify the router system is working
"""

import asyncio
import os
import sys

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from router.config import get_router_config_from_env, validate_config
from router.main_router import MainRouter
from router.base import RouterState


async def quick_test():
    """Quick test of the router system"""
    print("🧪 Quick Router Test")
    print("=" * 30)
    
    # Check config
    if not validate_config():
        print("❌ Configuration validation failed")
        return
    
    # Initialize router
    config = get_router_config_from_env()
    router = MainRouter(config)
    await router.initialize()
    
    # Test queries
    test_queries = [
        "سلام، چطور میتونم خرید کنم؟",     # Should route to GENERAL
        "سلام خوبی؟",                      # Should route to GENERAL (unclear query)  
        "کمک میخوام",                      # Should route to GENERAL (fallback)
        "یه چیزی میخوام ولی نمیدونم چی",    # Should route to GENERAL (fallback)
        "دنبال لپ تاپ خوب هستم",           # Should route to EXPLORATION or GENERAL
        "گوشی آیفون 15 پرو مکس میخوام",    # Should route to SPECIFIC_PRODUCT
        "مقایسه آیفون با سامسونگ",          # Should route to COMPARISON
    ]
    
    for query in test_queries:
        print(f"\n🔍 Test: {query}")
        
        state = RouterState(
            user_query=query,
            session_context={},
            turn_count=0
        )
        
        try:
            result = await router.process_complete(state)
            
            routing_decision = result.get("routing_decision")
            final_response = result.get("final_response")
            error = result.get("error")
            
            if routing_decision:
                print(f"  ✅ Routed to: {routing_decision.agent.name}")
                print(f"  📊 Confidence: {routing_decision.confidence:.2f}")
                print(f"  💭 Reasoning: {routing_decision.reasoning}")
            
            if final_response:
                print(f"  💬 Response: {final_response[:80]}...")
            elif error:
                print(f"  ❌ Error: {error}")
            else:
                print(f"  📝 No response (needs specialized agent)")
                
        except Exception as e:
            print(f"  ❌ Exception: {e}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    if not os.path.exists(".env"):
        print("❌ .env file not found!")
        print("Please create .env file with OPENAI_API_KEY")
        sys.exit(1)
    
    asyncio.run(quick_test())
