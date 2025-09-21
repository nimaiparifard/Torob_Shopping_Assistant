"""
Example usage of the router system
Demonstrates how to integrate the router with your application
"""

import asyncio
import os
from typing import Optional
from .base import RouterConfig, RouterState
from .main_router import MainRouter
from .state_manager import SessionManager, SessionState
from .config import get_router_config_from_env, validate_config, print_config_summary


async def example_single_query():
    """Example of routing a single query"""
    # Configure router from environment variables
    config = get_router_config_from_env()
    
    # Create router
    router = MainRouter(config)
    await router.initialize()
    
    # Example queries
    queries = [
        "سلام، چطور می‌تونم از سایت خرید کنم؟",
        "لطفا کابینت چهار کشو کد D14 رو برام پیدا کن",
        "قیمت پارچه لیکرا حلقوی نوریس 1/30 طلایی چقدره؟",
        "فروشندگان گوشی سامسونگ A54 در ترب کدومن؟",
        "یه لپ تاپ خوب برای برنامه نویسی میخوام",
        "مقایسه آیفون 15 با سامسونگ S24 اولترا"
    ]
    
    print("=== تست روتر با نمونه سوالات ===\n")
    
    for query in queries:
        print(f"سوال: {query}")
        
        # Create state
        state = RouterState(user_query=query)
        
        # Route query
        decision = await router.route(state)
        
        print(f"عامل انتخاب شده: {decision.agent.name}")
        print(f"اطمینان: {decision.confidence:.2f}")
        print(f"دلیل: {decision.reasoning}")
        if decision.extracted_data:
            print(f"داده‌های استخراج شده: {decision.extracted_data}")
        print("-" * 50)


async def example_session_management():
    """Example of managing a conversation session"""
    # Configure router from environment variables
    config = get_router_config_from_env()
    
    router = MainRouter(config)
    await router.initialize()
    
    # Create session manager
    session_manager = SessionManager(max_turns=5)
    
    # Simulate a conversation
    session_id = "user-123"
    session = session_manager.get_or_create_session(session_id)
    
    print("\n=== شبیه‌سازی مکالمه با مدیریت جلسه ===\n")
    
    # Conversation flow
    conversation = [
        "سلام، میخوام یه گوشی خوب بخرم",
        "بودجم حدود 15 میلیون تومانه",
        "ترجیحا سامسونگ یا شیائومی باشه",
        "دوربین خوب برام مهمه",
        "بین Galaxy A54 و Redmi Note 12 Pro کدوم بهتره؟"
    ]
    
    for query in conversation:
        print(f"\nدور {session.turn_count + 1}:")
        print(f"کاربر: {query}")
        
        # Create state with session context
        state = RouterState(
            user_query=query,
            session_context=session.get_context_for_routing(),
            turn_count=session.turn_count
        )
        
        # Route query
        decision = await router.route(state)
        
        print(f"عامل: {decision.agent.name} (اطمینان: {decision.confidence:.2f})")
        
        # Simulate agent response
        agent_response = f"[پاسخ از عامل {decision.agent.name}]"
        
        # Add turn to session
        session.add_turn(query, decision, agent_response)
        
        # Check turn limit
        if session.is_at_turn_limit:
            print("\n⚠️ به حد مجاز دورهای مکالمه رسیدیم!")
            break
        
        if decision.force_conclusion:
            print("\n⚠️ سیستم درخواست نتیجه‌گیری دارد!")
    
    # Show session summary
    print("\n=== خلاصه جلسه ===")
    print(f"تعداد دورها: {session.turn_count}")
    print(f"عامل‌های استفاده شده: {[agent.name for agent in session.get_previous_agents()]}")


async def example_detailed_analysis():
    """Example of getting detailed routing analysis"""
    config = get_router_config_from_env()
    
    router = MainRouter(config)
    await router.initialize()
    
    print("\n=== تحلیل دقیق مسیریابی ===\n")
    
    query = "قیمت لپ تاپ ASUS ROG مدل G15 چقدره؟"
    
    # Get detailed explanation
    explanation = await router.get_routing_explanation(query)
    
    print(f"سوال: {query}\n")
    
    print("تشخیص سیگنال‌های سخت:")
    print(f"  - الگوی تشخیص داده شده: {explanation['hard_signals']['detected']}")
    print(f"  - اطمینان: {explanation['hard_signals']['confidence']}")
    print(f"  - الگوهای منطبق: {explanation['hard_signals']['patterns']}")
    print(f"  - داده‌های استخراجی: {explanation['hard_signals']['extracted']}")
    
    print("\nتحلیل Intent:")
    print(f"  - نوع: {explanation['intent']['type']}")
    print(f"  - اطمینان: {explanation['intent']['confidence']}")
    print(f"  - موجودیت‌ها: {explanation['intent']['entities']}")
    
    print("\nتحلیل معنایی:")
    print(f"  - بهترین عامل: {explanation['semantic']['best_agent']}")
    print(f"  - اطمینان: {explanation['semantic']['confidence']}")
    
    if explanation['semantic']['similar_exemplars']:
        print("\nنمونه‌های مشابه:")
        for agent, exemplars in explanation['semantic']['similar_exemplars'].items():
            if exemplars:
                print(f"  {agent}:")
                for text, score in exemplars[:2]:
                    print(f"    - {text[:50]}... (شباهت: {score:.2f})")


async def run_all_examples():
    """Run all examples"""
    print("🚀 شروع نمونه‌های استفاده از Router\n")
    
    # Validate configuration
    if not validate_config():
        print("⚠️  لطفا فایل .env را بررسی کنید!")
        return
    
    # Print configuration summary
    print_config_summary()
    print()
    
    await example_single_query()
    await example_session_management()
    await example_detailed_analysis()
    
    print("\n✅ نمونه‌ها با موفقیت اجرا شدند!")


if __name__ == "__main__":
    # Run examples
    asyncio.run(run_all_examples())
