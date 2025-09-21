#!/usr/bin/env python3
"""
Startup script for the router system
Demonstrates complete setup with environment variables
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from router import (
    get_router_config_from_env,
    validate_config,
    print_config_summary,
    MainRouter,
    RouterState,
    SessionManager
)


async def main():
    """Main startup function"""
    print("🚀 راه‌اندازی سیستم Router\n")
    
    # Step 1: Validate environment variables
    print("1️⃣ بررسی متغیرهای محیطی...")
    if not validate_config():
        print("❌ لطفا فایل .env را بررسی کنید!")
        return
    
    # Step 2: Load configuration
    print("\n2️⃣ بارگذاری پیکربندی...")
    config = get_router_config_from_env()
    print_config_summary()
    
    # Step 3: Initialize router
    print("\n3️⃣ راه‌اندازی Router...")
    router = MainRouter(config)
    await router.initialize()
    print("✅ Router آماده است!")
    
    # Step 4: Initialize session manager
    print("\n4️⃣ راه‌اندازی Session Manager...")
    session_manager = SessionManager()
    print(f"✅ Session Manager آماده است! (حداکثر {session_manager.max_turns} دور)")
    
    # Step 5: Test with sample queries
    print("\n5️⃣ تست با نمونه سوالات...")
    
    sample_queries = [
        "سلام، چطور می‌تونم خرید کنم؟",
        "قیمت گوشی سامسونگ A54 چقدره؟",
        "یه لپ تاپ خوب برای کار میخوام"
    ]
    
    for i, query in enumerate(sample_queries, 1):
        print(f"\n  تست {i}: {query}")
        
        state = RouterState(user_query=query, turn_count=0)
        decision = await router.route(state)
        
        print(f"    → عامل: {decision.agent.name}")
        print(f"    → اطمینان: {decision.confidence:.2f}")
        print(f"    → دلیل: {decision.reasoning}")
    
    print("\n🎉 سیستم Router با موفقیت راه‌اندازی شد!")
    print("\n📚 برای استفاده:")
    print("  from router import get_router_config_from_env, MainRouter")
    print("  config = get_router_config_from_env()")
    print("  router = MainRouter(config)")
    print("  await router.initialize()")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n⏹️  روند متوقف شد.")
    except Exception as e:
        print(f"\n❌ خطا: {e}")
        sys.exit(1)
