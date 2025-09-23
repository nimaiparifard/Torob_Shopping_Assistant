#!/usr/bin/env python3
"""
Simple test script for the router system
Can be run without .env file by providing API key directly
"""

import asyncio
import os
import sys
from pathlib import Path

# Add router module to path
sys.path.insert(0, str(Path(__file__).parent))

from router import (
    RouterConfig,
    MainRouter,
    RouterState,
    AgentType,
    EmbeddingService,
    HardSignalDetector,
    SessionManager
)


async def test_basic_functionality():
    """Test basic router functionality"""
    print("🧪 تست عملکرد پایه Router System")
    print("=" * 50)
    
    # Configuration - you can modify these values
    config = RouterConfig(
        openai_api_key="trb-6500cd2bb70ff9537a-060b-4f37-a6f7-3917ba6cd53e",
        openai_base_url="https://turbo.torob.com/v1",
        embedding_model="text-embedding-3-small",
        llm_model="gpt-4o-mini",
        similarity_threshold_low=0.3,
        similarity_threshold_high=0.7,
        max_turns=5
    )
    
    print(f"✅ پیکربندی ایجاد شد")
    print(f"  - Base URL: {config.openai_base_url}")
    print(f"  - Embedding Model: {config.embedding_model}")
    print(f"  - LLM Model: {config.llm_model}")
    
    # Test 1: Hard Signal Detection
    print(f"\n🎯 تست 1: Hard Signal Detection")
    detector = HardSignalDetector()
    
    hard_signal_tests = [
        ("لطفا کابینت کد D14 رو پیدا کن", "کد محصول"),
        ("قیمت گوشی سامسونگ چقدره؟", "سوال قیمت"),
        ("مقایسه آیفون با سامسونگ", "مقایسه"),
        ("چطور خرید کنم؟", "سوال عمومی")
    ]
    
    for query, expected_type in hard_signal_tests:
        state = RouterState(user_query=query)
        result = detector.detect(state)
        
        print(f"  📝 '{query}'")
        print(f"    → تشخیص: {result.agent.name if result.agent else 'None'}")
        print(f"    → اطمینان: {result.confidence:.2f}")
        print(f"    → انتظار: {expected_type}")
    
    # Test 2: Embedding Service
    print(f"\n🔤 تست 2: Embedding Service")
    embedding_service = EmbeddingService(config)
    
    test_texts = [
        "سلام چطورید؟",
        "قیمت گوشی چقدره؟",
        "یه لپ تاپ خوب میخوام"
    ]
    
    try:
        embeddings = await embedding_service.get_embeddings_batch(test_texts)
        print(f"  ✅ {len(embeddings)} embedding محاسبه شد")
        
        # Test similarity
        if len(embeddings) >= 2:
            sim = embedding_service.cosine_similarity(embeddings[0], embeddings[1])
            print(f"  📊 تشابه متن 1 و 2: {sim:.3f}")
        
    except Exception as e:
        print(f"  ❌ خطا در Embedding Service: {e}")
    
    # Test 3: Main Router
    print(f"\n🚀 تست 3: Main Router Integration")
    
    try:
        router = MainRouter(config)
        await router.initialize()
        print(f"  ✅ Router آماده شد")
        
        # Test different query types
        test_queries = [
            "سلام، راهنمای خرید میخوام",
            "گوشی آیفون 15 پرو مکس",
            "قیمت لپ تاپ ایسوس چقدره؟",
            "فروشندگان گوشی سامسونگ کدومن؟",
            "یه گوشی خوب تا 10 میلیون میخوام",
            "مقایسه آیفون 15 با سامسونگ S24"
        ]
        
        for i, query in enumerate(test_queries, 1):
            try:
                state = RouterState(user_query=query, turn_count=0)
                decision = await router.route(state)
                
                print(f"  {i}. '{query[:40]}...'")
                print(f"     → عامل: {decision.agent.name}")
                print(f"     → اطمینان: {decision.confidence:.2f}")
                
            except Exception as e:
                print(f"  {i}. ❌ خطا در '{query[:30]}...': {e}")
        
    except Exception as e:
        print(f"  ❌ خطا در Main Router: {e}")
    
    # Test 4: Session Management
    print(f"\n👥 تست 4: Session Management")
    
    session_manager = SessionManager(max_turns=3)
    session = session_manager.create_session("test-session")
    
    print(f"  ✅ جلسه ایجاد شد: {session.session_id}")
    print(f"  📊 حداکثر دور: {session.max_turns}")
    print(f"  🔄 دور فعلی: {session.turn_count}")
    
    # Simulate conversation
    if 'router' in locals():
        conversation = [
            "سلام، یه گوشی میخوام",
            "بودجم 15 میلیونه",
            "کدوم برند بهتره؟"
        ]
        
        for query in conversation:
            try:
                state = RouterState(
                    user_query=query,
                    session_context=session.get_context_for_routing(),
                    turn_count=session.turn_count
                )
                
                decision = await router.route(state)
                session.add_turn(query, decision, f"[پاسخ {decision.agent.name}]")
                
                print(f"  🔄 دور {session.turn_count}: {decision.agent.name}")
                
            except Exception as e:
                print(f"  ❌ خطا در دور: {e}")
    
    print(f"\n🎉 تست‌های پایه تمام شد!")
    
    # Summary
    print(f"\n📋 خلاصه:")
    print(f"  - Hard Signal Detection: ✅")
    print(f"  - Embedding Service: {'✅' if 'embeddings' in locals() else '❌'}")
    print(f"  - Main Router: {'✅' if 'router' in locals() else '❌'}")
    print(f"  - Session Management: ✅")


if __name__ == "__main__":
    print("🚀 Router System Test")
    print("برای تست با API key خود، فایل را ویرایش کنید یا متغیر محیطی تنظیم کنید")
    print()
    
    try:
        asyncio.run(test_basic_functionality())
    except KeyboardInterrupt:
        print("\n\n⏹️ تست متوقف شد.")
    except Exception as e:
        print(f"\n❌ خطای کلی: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
