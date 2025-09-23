"""
Test Agent 1 (Specific Product) and Router Integration

This script tests:
1. Agent 1 standalone functionality
2. Router integration with Agent 1
3. End-to-end workflow from query to response

Usage:
    .venv\\Scripts\\python.exe test_agent1_routing.py

Author: Torob AI Team
"""

import asyncio
import sys
import os

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from router.config import get_router_config_from_env
from router.main_router import MainRouter
from router.base import RouterState, AgentType
from agents.specific_product import SpecificProductAgent


async def test_agent1_standalone():
    """Test Agent 1 independently"""
    print("🧪 تست مستقل Agent 1 (Specific Product)")
    print("=" * 60)
    
    try:
        # Create agent
        config = get_router_config_from_env()
        agent = SpecificProductAgent(config)
        
        # Test queries for Agent 1
        test_queries = [
            "لطفا کمد آویز کیف داخل کمد چهار طبقه دارای هشت خونه را برای من پیدا کنید",
            " این محصول را پیدا رگال لباس با کمد چهار کشو و آینه کن.",
            "لطفا کد کمد چهار طبقه بزرگ مدل C36 (72 عدد باتری 28 یا 42 آمپر) برای من برگردون.",
            "این محصول را پیدا کن: کمد چهار کشو کد D14",
            "برای من محصول کمد چهار درب ونوس طوسی پیدا کن."
        ]
        
        for i, query in enumerate(test_queries, 1):
            print(f"\n📋 تست {i}: {query}")
            print("-" * 50)
            
            result = await agent.process_query(query)
            
            if result.found:
                print(f"✅ محصول یافت شد!")
                print(f"🔑 Random Key: {result.random_key}")
                print(f"📝 نام محصول: {result.product_name}")
                print(f"🔍 روش جستجو: {result.search_method}")
            else:
                print(f"❌ محصول یافت نشد")
                print(f"💬 خطا: {result.error}")
        
        # Clean up
        agent.close()
        print(f"\n✅ تست مستقل Agent 1 تمام شد!")
        return True
        
    except Exception as e:
        print(f"❌ خطا در تست Agent 1: {e}")
        return False


async def test_router_integration():
    """Test Router integration with Agent 1"""
    print("\n🔀 تست ادغام Router با Agent 1")
    print("=" * 60)
    
    try:
        # Create router
        config = get_router_config_from_env()
        router = MainRouter(config)
        await router.initialize()
        
        # Test queries that should route to Agent 1
        agent1_queries = [
            "لطفا کمد چهار کشو را پیدا کنید",
            "گوشی سامسونگ می‌خواهم",
            "محصول XYZ123 را برای من بیابید",
            "پارچه لایکرا زرد طلایی کجاست؟"
        ]
        
        for i, query in enumerate(agent1_queries, 1):
            print(f"\n🎯 تست Routing {i}: {query}")
            print("-" * 50)
            
            # Test routing decision
            state = RouterState(user_query=query, turn_count=0)
            routing_decision = await router.route(state)
            
            print(f"🧭 تصمیم Router:")
            print(f"   Agent: {routing_decision.agent.name}")
            print(f"   اطمینان: {routing_decision.confidence:.2f}")
            print(f"   دلیل: {routing_decision.reasoning}")
            
            # Test complete processing
            complete_result = await router.process_complete(state)
            
            print(f"\n📋 نتیجه نهایی:")
            print(f"   Agent نهایی: {complete_result.get('final_agent')}")
            print(f"   پاسخ: {complete_result.get('final_response')}")
            
            if complete_result.get('specific_product_response'):
                spr = complete_result['specific_product_response']
                print(f"   جزئیات Agent 1:")
                print(f"     یافت شد: {spr.get('found')}")
                if spr.get('found'):
                    print(f"     Random Key: {spr.get('random_key')}")
                    print(f"     نام محصول: {spr.get('product_name')}")
                else:
                    print(f"     خطا: {spr.get('error')}")
            
            if complete_result.get('error'):
                print(f"   ❌ خطا: {complete_result['error']}")
        
        print(f"\n✅ تست ادغام Router تمام شد!")
        return True
        
    except Exception as e:
        print(f"❌ خطا در تست Router: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_routing_accuracy():
    """Test routing accuracy for different query types"""
    print("\n🎯 تست دقت مسیریابی")
    print("=" * 60)
    
    try:
        config = get_router_config_from_env()
        router = MainRouter(config)
        await router.initialize()
        
        # Test cases with expected agents
        test_cases = [
            # Should route to SPECIFIC_PRODUCT (Agent 1)
            ("کمد چهار کشو کد D14 را پیدا کنید", AgentType.SPECIFIC_PRODUCT),
            ("گوشی اپل آیفون 15 می‌خواهم", AgentType.SPECIFIC_PRODUCT),
            ("محصول ABC123 کجاست؟", AgentType.SPECIFIC_PRODUCT),
            
            # Should route to GENERAL (Agent 0)
            ("سلام چطورید؟", AgentType.GENERAL),
            ("ساعت کاری شما چیست؟", AgentType.GENERAL),
            ("راهنمایی کلی می‌خواهم", AgentType.GENERAL),
        ]
        
        correct_routings = 0
        total_tests = len(test_cases)
        
        for i, (query, expected_agent) in enumerate(test_cases, 1):
            print(f"\n📝 تست {i}: {query}")
            print(f"   انتظار: {expected_agent.name}")
            
            state = RouterState(user_query=query, turn_count=0)
            routing_decision = await router.route(state)
            
            actual_agent = routing_decision.agent
            print(f"   واقعی: {actual_agent.name}")
            print(f"   اطمینان: {routing_decision.confidence:.2f}")
            
            if actual_agent == expected_agent:
                print(f"   ✅ صحیح")
                correct_routings += 1
            else:
                print(f"   ❌ نادرست")
        
        accuracy = (correct_routings / total_tests) * 100
        print(f"\n📊 دقت مسیریابی: {accuracy:.1f}% ({correct_routings}/{total_tests})")
        
        return accuracy >= 70  # Accept 70% accuracy as good
        
    except Exception as e:
        print(f"❌ خطا در تست دقت: {e}")
        return False


async def main():
    """Run all tests"""
    print("🚀 شروع تست‌های جامع Agent 1 و Router")
    print("=" * 80)
    
    # Track test results
    results = {}
    
    # Test 1: Agent 1 standalone
    results['agent1_standalone'] = await test_agent1_standalone()
    
    # Test 2: Router integration
    results['router_integration'] = await test_router_integration()
    
    # Test 3: Routing accuracy
    results['routing_accuracy'] = await test_routing_accuracy()
    
    # Summary
    print(f"\n" + "=" * 80)
    print("📊 خلاصه نتایج تست‌ها:")
    print("-" * 40)
    
    for test_name, passed in results.items():
        status = "✅ موفق" if passed else "❌ ناموفق"
        print(f"   {test_name}: {status}")
    
    all_passed = all(results.values())
    if all_passed:
        print(f"\n🎉 همه تست‌ها موفقیت‌آمیز بودند!")
        print(f"✅ Agent 1 آماده استفاده است.")
    else:
        print(f"\n⚠️  برخی تست‌ها ناموفق بودند.")
        print(f"🔧 لطفا مشکلات را بررسی کنید.")
    
    return all_passed


if __name__ == "__main__":
    # Set up environment
    print("🔧 بررسی محیط...")
    
    # Check if database exists
    from db.create_db import DB_PATH
    import os
    
    if not os.path.exists(DB_PATH):
        print(f"⚠️  پایگاه داده یافت نشد: {DB_PATH}")
        print(f"💡 لطفا ابتدا دستورات زیر را اجرا کنید:")
        print(f"   python -m db.create_db")
        print(f"   python -m db.load_db")
        sys.exit(1)
    
    # Check if .env exists
    env_path = "../.env"
    if not os.path.exists(env_path):
        print(f"⚠️  فایل .env یافت نشد")
        print(f"💡 لطفا فایل .env را با کلید OpenAI ایجاد کنید")
        # Continue anyway for now
    
    print(f"✅ محیط آماده است!")
    
    # Run tests
    try:
        success = asyncio.run(main())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print(f"\n⏹️  تست توسط کاربر متوقف شد.")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 خطای غیرمنتظره: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
