#!/usr/bin/env python3
"""
Demo script for Router System + Agent 0
Simple interactive demo to test queries
"""

import asyncio
import os
import sys

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from router.config import get_router_config_from_env, validate_config
from router.main_router import MainRouter
from router.base import RouterState


async def demo_interactive():
    """Interactive demo"""
    print("🤖 دستیار خرید هوشمند ترب - نسخه آزمایشی")
    print("=" * 50)
    
    # Setup
    print("⏳ در حال راه‌اندازی...")
    
    if not validate_config():
        print("❌ خطا: فایل .env پیدا نشد یا ناقص است")
        print("لطفا OPENAI_API_KEY را در فایل .env تنظیم کنید")
        return
    
    config = get_router_config_from_env()
    router = MainRouter(config)
    await router.initialize()
    
    print("✅ سیستم آماده است!")
    print("\n💡 مثال‌های سوال:")
    print("  🟢 سوالات عمومی (پاسخ کامل):")
    print("    - سلام خوبی؟")
    print("    - چطور میتونم خرید کنم؟")
    print("    - ساعت کاری پشتیبانی چیه؟")
    print("    - آیا مرجوع کالا امکان داره؟")
    print("    - کمک میخوام")
    print("  🔶 سوالات تخصصی (نیاز به دستیار آینده):")
    print("    - دنبال لپ تاپ خوب هستم")
    print("    - گوشی آیفون 15 پرو مکس میخوام")
    print("    - مقایسه آیفون با سامسونگ")
    print("\n⌨️  سوال خود را بپرسید (برای خروج 'exit' تایپ کنید):")
    
    while True:
        try:
            # Get user input
            query = input("\n🗨️  شما: ").strip()
            
            if not query:
                continue
            
            if query.lower() in ['exit', 'quit', 'خروج']:
                print("👋 خداحافظ!")
                break
            
            # Process query
            print("⏳ در حال پردازش...")
            
            state = RouterState(
                user_query=query,
                session_context={},
                turn_count=0
            )
            
            result = await router.process_complete(state)
            
            # Display results
            routing_decision = result.get("routing_decision")
            final_response = result.get("final_response")
            error = result.get("error")
            
            print(f"\n🎯 مسیریابی: {routing_decision.agent.name if routing_decision else 'نامشخص'}")
            confidence = routing_decision.confidence if routing_decision else 0.0
            print(f"📊 اطمینان: {confidence:.2f}")
            
            if error:
                print(f"⚠️  خطا: {error}")
            elif final_response:
                print(f"\n🤖 دستیار:")
                print(f"   {final_response}")
            else:
                print("📝 این سوال به دستیار تخصصی ارجاع می‌شود (هنوز پیاده‌سازی نشده)")
                if routing_decision:
                    print(f"   نوع دستیار مورد نیاز: {routing_decision.agent.name}")
                    print(f"   دلیل: {routing_decision.reasoning}")
            
        except KeyboardInterrupt:
            print("\n👋 خداحافظ!")
            break
        except Exception as e:
            print(f"❌ خطا: {e}")


async def demo_predefined():
    """Demo with predefined queries"""
    print("🤖 نمایش سوالات از پیش تعریف شده")
    print("=" * 40)
    
    # Setup
    config = get_router_config_from_env()
    router = MainRouter(config)
    await router.initialize()
    
    # Test queries
    test_queries = [
        "سلام، چطور میتونم از سایت خرید کنم؟",
        "ساعت کاری پشتیبانی چیه؟",
        "مرجوع کردن کالا امکانش هست؟",
        "دنبال لپ تاپ خوب برای کار هستم",
        "گوشی آیفون 15 پرو مکس رو میخوام",
        "مقایسه آیفون 15 با سامسونگ S24",
    ]
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n{i}. سوال: {query}")
        print("-" * 40)
        
        state = RouterState(
            user_query=query,
            session_context={},
            turn_count=0
        )
        
        result = await router.process_complete(state)
        
        routing_decision = result.get("routing_decision")
        final_response = result.get("final_response")
        
        print(f"🎯 مسیریابی: {routing_decision.agent.name if routing_decision else 'نامشخص'}")
        confidence = routing_decision.confidence if routing_decision else 0.0
        print(f"📊 اطمینان: {confidence:.2f}")
        
        if final_response:
            print(f"🤖 پاسخ: {final_response[:100]}...")
        else:
            print("📝 نیازمند دستیار تخصصی")


async def main():
    """Main function"""
    if not os.path.exists(".env"):
        print("❌ فایل .env یافت نشد!")
        print("لطفا فایل .env را ایجاد کنید و OPENAI_API_KEY را تنظیم کنید.")
        return
    
    print("انتخاب کنید:")
    print("1. نمایش تعاملی")
    print("2. نمایش سوالات از پیش تعریف شده")
    
    choice = input("شماره انتخاب (1 یا 2): ").strip()
    
    if choice == "1":
        await demo_interactive()
    elif choice == "2":
        await demo_predefined()
    else:
        print("انتخاب نامعتبر!")


if __name__ == "__main__":
    asyncio.run(main())
