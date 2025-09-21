#!/usr/bin/env python3
"""
Test script for Router System + Agent 0 (General Q&A)
Tests the complete workflow from query input to agent response
"""

import asyncio
import os
import sys
from typing import Dict, Any

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from router.config import get_router_config_from_env, validate_config
from router.main_router import MainRouter
from router.base import RouterState, AgentType


class RouterSystemTester:
    """Test the complete router system with Agent 0"""
    
    def __init__(self):
        self.router = None
        self.test_queries = self._get_test_queries()
    
    def _get_test_queries(self) -> Dict[str, Dict[str, Any]]:
        """Define test queries for different scenarios"""
        return {
            "general_questions": {
                "queries": [
                    "سلام، چطور می‌تونم از سایت خرید کنم؟",
                    "ساعت کاری پشتیبانی چیه؟",
                    "آیا امکان مرجوع کردن کالا وجود دارد؟",
                    "نحوه پرداخت چگونه است؟",
                    "آیا ضمانت اصالت کالا دارید؟",
                    "هزینه ارسال چقدر است؟",
                    "چطور با پشتیبانی تماس بگیرم؟",
                ],
                "expected_agent": AgentType.GENERAL,
                "description": "سوالات عمومی که باید به Agent 0 هدایت شوند"
            },
            "product_search": {
                "queries": [
                    "دنبال لپ تاپ خوب برای کار هستم",
                    "یه گوشی تا 10 میلیون میخوام",
                    "بهترین یخچال برای خانواده 4 نفره؟",
                ],
                "expected_agent": AgentType.EXPLORATION,
                "description": "جستجوی محصول که باید به Agent 4 هدایت شود"
            },
            "specific_product": {
                "queries": [
                    "لپ تاپ ASUS مدل X515EA رو میخوام",
                    "گوشی آیفون 15 پرو مکس 256 گیگ",
                    "محصول با کد SKU-12345 رو نشان بده",
                ],
                "expected_agent": AgentType.SPECIFIC_PRODUCT,
                "description": "محصول خاص که باید به Agent 1 هدایت شود"
            },
            "comparison": {
                "queries": [
                    "مقایسه آیفون 15 با سامسونگ S24",
                    "کدوم بهتره: لپ تاپ ایسوس یا لنوو؟",
                    "تفاوت بین ماشین لباسشویی بوش و سامسونگ",
                ],
                "expected_agent": AgentType.COMPARISON,
                "description": "مقایسه محصولات که باید به Agent 5 هدایت شود"
            },
            "handoff_scenarios": {
                "queries": [
                    "چطور میتونم گوشی خوب پیدا کنم؟",  # Should start with General, then handoff to Exploration
                    "راهنمایی برای خرید لپ تاپ میخوام",   # Should start with General, then handoff to Exploration
                ],
                "expected_agent": AgentType.GENERAL,  # Initially, then handoff
                "description": "سوالات که از General به Exploration هدایت می‌شوند"
            }
        }
    
    async def setup(self):
        """Setup the router system"""
        print("🔧 در حال راه‌اندازی سیستم...")
        
        # Validate configuration
        if not validate_config():
            raise Exception("تنظیمات نامعتبر - لطفا فایل .env را بررسی کنید")
        
        # Get configuration
        config = get_router_config_from_env()
        
        # Initialize router
        self.router = MainRouter(config)
        await self.router.initialize()
        
        print("✅ سیستم آماده است!")
    
    async def test_single_query(self, query: str, expected_agent: AgentType = None) -> Dict[str, Any]:
        """Test a single query through the complete system"""
        print(f"\n📝 تست سوال: {query}")
        
        # Create router state
        state = RouterState(
            user_query=query,
            session_context={},
            turn_count=0
        )
        
        # Process complete workflow
        result = await self.router.process_complete(state)
        
        # Extract results
        routing_decision = result.get("routing_decision")
        final_agent = result.get("final_agent")
        final_response = result.get("final_response")
        error = result.get("error")
        
        test_result = {
            "query": query,
            "routed_agent": routing_decision.agent.name if routing_decision else "UNKNOWN",
            "confidence": routing_decision.confidence if routing_decision else 0.0,
            "reasoning": routing_decision.reasoning if routing_decision else "",
            "final_response": final_response,
            "error": error,
            "expected_agent": expected_agent.name if expected_agent else None,
            "correct_routing": (routing_decision.agent == expected_agent) if (routing_decision and expected_agent) else None
        }
        
        # Print results
        print(f"  🎯 هدایت شده به: {test_result['routed_agent']}")
        print(f"  📊 اطمینان: {test_result['confidence']:.2f}")
        print(f"  💭 دلیل: {test_result['reasoning']}")
        
        if expected_agent:
            if test_result['correct_routing']:
                print(f"  ✅ مسیریابی صحیح")
            else:
                print(f"  ❌ مسیریابی نادرست (انتظار: {expected_agent.name})")
        
        if final_response:
            print(f"  💬 پاسخ نهایی: {final_response[:100]}...")
        
        if error:
            print(f"  ⚠️ خطا: {error}")
        
        return test_result
    
    async def test_general_agent_directly(self):
        """Test General Agent directly"""
        print("\n🔄 تست مستقیم Agent عمومی...")
        
        general_queries = [
            "چطور میتونم خرید کنم؟",
            "ساعت کاری چیه؟",
            "مرجوع کردن کالا امکانش هست؟",
            "راهنمایی برای خرید گوشی میخوام",  # Should trigger handoff
        ]
        
        for query in general_queries:
            print(f"\n  📝 {query}")
            
            try:
                response = await self.router.general_agent.process_query(query, {})
                
                print(f"    💬 پاسخ: {response.answer[:80]}...")
                print(f"    📊 اطمینان: {response.confidence:.2f}")
                print(f"    🔄 نیاز به انتقال: {response.handoff_needed}")
                
                if response.handoff_needed:
                    print(f"    👉 انتقال به: {response.handoff_agent}")
                    print(f"    💭 دلیل: {response.reasoning}")
                    
            except Exception as e:
                print(f"    ❌ خطا: {e}")
    
    async def test_category(self, category_name: str, category_data: Dict[str, Any]):
        """Test a category of queries"""
        print(f"\n\n📋 تست دسته: {category_data['description']}")
        print(f"📋 انتظار مسیریابی به: {category_data['expected_agent'].name}")
        print("=" * 60)
        
        results = []
        correct_count = 0
        
        for query in category_data["queries"]:
            result = await self.test_single_query(query, category_data["expected_agent"])
            results.append(result)
            
            if result["correct_routing"]:
                correct_count += 1
        
        accuracy = correct_count / len(results) if results else 0.0
        print(f"\n📊 دقت مسیریابی در این دسته: {accuracy:.1%} ({correct_count}/{len(results)})")
        
        return results
    
    async def run_all_tests(self):
        """Run all tests"""
        print("🚀 شروع تست‌های جامع سیستم Router + Agent 0")
        print("=" * 70)
        
        all_results = {}
        total_correct = 0
        total_queries = 0
        
        # Test each category
        for category_name, category_data in self.test_queries.items():
            results = await self.test_category(category_name, category_data)
            all_results[category_name] = results
            
            # Count correct routing
            category_correct = sum(1 for r in results if r["correct_routing"])
            total_correct += category_correct
            total_queries += len(results)
        
        # Test General Agent directly
        await self.test_general_agent_directly()
        
        # Overall statistics
        print(f"\n\n📈 آمار کلی:")
        print("=" * 30)
        overall_accuracy = total_correct / total_queries if total_queries > 0 else 0.0
        print(f"🎯 دقت کلی مسیریابی: {overall_accuracy:.1%} ({total_correct}/{total_queries})")
        
        # Detailed results
        print(f"\n📊 نتایج تفصیلی:")
        for category_name, results in all_results.items():
            category_correct = sum(1 for r in results if r["correct_routing"])
            category_accuracy = category_correct / len(results) if results else 0.0
            print(f"  - {category_name}: {category_accuracy:.1%} ({category_correct}/{len(results)})")
        
        return all_results
    
    async def test_workflow_explanation(self, query: str):
        """Get detailed explanation of routing decision"""
        print(f"\n🔍 تحلیل تفصیلی برای: {query}")
        print("=" * 50)
        
        try:
            explanation = await self.router.get_routing_explanation(query)
            
            print("🤖 Hard Signals:")
            print(f"  - تشخیص: {explanation['hard_signals']['detected']}")
            print(f"  - اطمینان: {explanation['hard_signals']['confidence']:.2f}")
            print(f"  - الگوها: {explanation['hard_signals']['patterns']}")
            
            print("\n🧠 Intent Analysis:")
            print(f"  - نوع: {explanation['intent']['type']}")
            print(f"  - اطمینان: {explanation['intent']['confidence']:.2f}")
            print(f"  - موجودیت‌ها: {explanation['intent']['entities']}")
            
            print("\n🎯 Semantic Routing:")
            print(f"  - بهترین Agent: {explanation['semantic']['best_agent']}")
            print(f"  - اطمینان: {explanation['semantic']['confidence']:.2f}")
            
            print("\n📝 نمونه‌های مشابه:")
            for agent, exemplars in explanation['semantic']['similar_exemplars'].items():
                if exemplars:
                    print(f"  {agent}:")
                    for exemplar, score in exemplars:
                        print(f"    - {exemplar[:50]}... (امتیاز: {score:.2f})")
                        
        except Exception as e:
            print(f"❌ خطا در تحلیل: {e}")


async def main():
    """Main test function"""
    tester = RouterSystemTester()
    
    try:
        # Setup
        await tester.setup()
        
        # Run all tests
        await tester.run_all_tests()
        
        # Detailed workflow analysis for a sample query
        await tester.test_workflow_explanation("چطور میتونم از سایت خرید کنم؟")
        await tester.test_workflow_explanation("دنبال لپ تاپ خوب برای کار هستم")
        
        print("\n✅ همه تست‌ها تکمیل شد!")
        
    except Exception as e:
        print(f"\n❌ خطای کلی: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    # Check if .env file exists
    if not os.path.exists(".env"):
        print("❌ فایل .env یافت نشد!")
        print("لطفا فایل .env را ایجاد کنید و OPENAI_API_KEY را تنظیم کنید.")
        print("\nمثال:")
        print("OPENAI_API_KEY=your_key_here")
        sys.exit(1)
    
    # Run tests
    asyncio.run(main())

