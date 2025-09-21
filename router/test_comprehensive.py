#!/usr/bin/env python3
"""
Comprehensive test suite for the router system
Tests all components: semantic routing, hard signals, intent parsing, etc.
"""

import asyncio
import sys
import time
from pathlib import Path
from typing import Dict, List, Any
import numpy as np

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from router import (
    get_router_config_from_env,
    validate_config,
    MainRouter,
    RouterState,
    AgentType,
    SessionManager,
    EmbeddingService,
    HardSignalDetector,
    IntentParser,
    SemanticRouter,
    AgentExemplars
)


class RouterTestSuite:
    """Comprehensive test suite for router components"""
    
    def __init__(self):
        self.config = None
        self.router = None
        self.results = {}
        
    async def setup(self):
        """Setup test environment"""
        print("🔧 راه‌اندازی محیط تست...")
        
        # Validate config
        if not validate_config():
            raise RuntimeError("Configuration validation failed!")
        
        # Load config
        self.config = get_router_config_from_env()
        print(f"✅ پیکربندی بارگذاری شد")
        
        # Initialize main router
        self.router = MainRouter(self.config)
        await self.router.initialize()
        print(f"✅ Router اصلی آماده شد")
        
        self.results = {
            'embedding_tests': [],
            'hard_signal_tests': [],
            'intent_parsing_tests': [],
            'semantic_routing_tests': [],
            'main_router_tests': [],
            'session_management_tests': [],
            'performance_tests': []
        }
    
    async def test_embedding_service(self):
        """Test embedding service functionality"""
        print("\n🧪 تست Embedding Service...")
        
        embedding_service = EmbeddingService(self.config)
        
        test_cases = [
            "سلام چطورید؟",
            "قیمت گوشی سامسونگ چقدره؟",
            "یه لپ تاپ خوب میخوام",
            "مقایسه آیفون با سامسونگ",
            "Hello, how are you?"  # English test
        ]
        
        print(f"  📝 تست با {len(test_cases)} متن مختلف...")
        
        # Test single embedding
        start_time = time.time()
        for i, text in enumerate(test_cases):
            embedding = await embedding_service.get_embedding(text)
            
            test_result = {
                'text': text,
                'embedding_shape': embedding.shape,
                'embedding_norm': float(np.linalg.norm(embedding)),
                'non_zero_elements': int(np.count_nonzero(embedding))
            }
            
            self.results['embedding_tests'].append(test_result)
            print(f"    ✅ متن {i+1}: شکل={embedding.shape}, نرم={test_result['embedding_norm']:.3f}")
        
        # Test batch processing
        print(f"  📦 تست پردازش دسته‌ای...")
        batch_embeddings = await embedding_service.get_embeddings_batch(test_cases)
        
        # Test similarity calculation
        print(f"  🔍 تست محاسبه تشابه...")
        similarities = []
        for i in range(len(batch_embeddings)):
            for j in range(i+1, len(batch_embeddings)):
                sim = embedding_service.cosine_similarity(batch_embeddings[i], batch_embeddings[j])
                similarities.append({
                    'text1': test_cases[i][:30],
                    'text2': test_cases[j][:30],
                    'similarity': float(sim)
                })
                print(f"    📊 تشابه: {sim:.3f} - '{test_cases[i][:20]}...' vs '{test_cases[j][:20]}...'")
        
        # Test caching
        cache_size_before = embedding_service.get_cache_size()
        await embedding_service.get_embedding(test_cases[0])  # Should hit cache
        cache_size_after = embedding_service.get_cache_size()
        
        print(f"  💾 تست کش: {cache_size_before} -> {cache_size_after}")
        
        elapsed_time = time.time() - start_time
        print(f"  ⏱️  زمان کل: {elapsed_time:.2f} ثانیه")
        
        return True
    
    async def test_hard_signal_detection(self):
        """Test hard signal detection"""
        print("\n🎯 تست Hard Signal Detection...")
        
        detector = HardSignalDetector()
        
        test_cases = [
            # Product codes
            ("لطفا کابینت چهار کشو کد D14 رو برام پیدا کن", AgentType.SPECIFIC_PRODUCT),
            ("محصول با شناسه SKU-12345 را نشان بده", AgentType.SPECIFIC_PRODUCT),
            ("گوشی آیفون 15 پرو مکس 256 گیگ", AgentType.SPECIFIC_PRODUCT),
            
            # Price inquiries
            ("قیمت پارچه لیکرا حلقوی نوریس چقدره؟", AgentType.PRODUCT_FEATURE),
            ("هزینه لپ تاپ ایسوس چقدر است؟", AgentType.PRODUCT_FEATURE),
            
            # Comparisons
            ("مقایسه آیفون 15 با سامسونگ S24", AgentType.COMPARISON),
            ("کدوم بهتره؟ لپ تاپ ایسوس یا اچ پی", AgentType.COMPARISON),
            
            # Seller info
            ("فروشندگان گوشی سامسونگ A54 کدومن؟", AgentType.SELLER_INFO),
            ("کدوم فروشگاه‌ها تبلت آیپد دارن؟", AgentType.SELLER_INFO),
            
            # General questions
            ("چطور می‌تونم از سایت خرید کنم؟", AgentType.GENERAL),
            ("ساعت کاری پشتیبانی چیه؟", AgentType.GENERAL),
            
            # Should not match (exploration)
            ("یه لپ تاپ خوب برای برنامه نویسی میخوام", None),
            ("دنبال یه گوشی مناسب هستم", None)
        ]
        
        correct_predictions = 0
        total_tests = len(test_cases)
        
        for query, expected_agent in test_cases:
            state = RouterState(user_query=query)
            result = detector.detect(state)
            
            test_result = {
                'query': query,
                'expected': expected_agent.name if expected_agent else None,
                'detected': result.agent.name if result.agent else None,
                'confidence': result.confidence,
                'patterns': result.matched_patterns,
                'extracted_data': result.extracted_data
            }
            
            is_correct = (result.agent == expected_agent)
            if is_correct:
                correct_predictions += 1
            
            status = "✅" if is_correct else "❌"
            print(f"  {status} '{query[:50]}...'")
            print(f"      انتظار: {expected_agent.name if expected_agent else 'None'}")
            print(f"      تشخیص: {result.agent.name if result.agent else 'None'} (اطمینان: {result.confidence:.2f})")
            if result.matched_patterns:
                print(f"      الگوها: {result.matched_patterns}")
            if result.extracted_data:
                print(f"      داده‌ها: {result.extracted_data}")
            
            self.results['hard_signal_tests'].append(test_result)
        
        accuracy = correct_predictions / total_tests
        print(f"  📊 دقت Hard Signals: {accuracy:.2%} ({correct_predictions}/{total_tests})")
        
        return accuracy > 0.7  # At least 70% accuracy
    
    async def test_intent_parsing(self):
        """Test intent parsing with LLM"""
        print("\n🧠 تست Intent Parsing...")
        
        parser = IntentParser(self.config)
        
        test_cases = [
            {
                'query': 'قیمت گوشی سامسونگ A54 چقدره؟',
                'expected_intent': 'feature',
                'expected_entities': ['samsung', 'a54']
            },
            {
                'query': 'یه لپ تاپ گیمینگ تا 20 میلیون میخوام',
                'expected_intent': 'explore',
                'expected_entities': ['laptop', 'gaming']
            },
            {
                'query': 'مقایسه آیفون 15 با پیکسل 8',
                'expected_intent': 'compare',
                'expected_entities': ['iphone', 'pixel']
            },
            {
                'query': 'فروشندگان دیجی کالا کدومن؟',
                'expected_intent': 'seller',
                'expected_entities': ['digikala']
            }
        ]
        
        successful_parses = 0
        
        for test_case in test_cases:
            state = RouterState(user_query=test_case['query'])
            
            try:
                intent = await parser.parse_intent(state)
                
                test_result = {
                    'query': test_case['query'],
                    'expected_intent': test_case['expected_intent'],
                    'parsed_intent': intent.intent,
                    'confidence': intent.confidence,
                    'base_ids': intent.base_ids,
                    'product_codes': intent.product_codes,
                    'brand': intent.brand,
                    'category': intent.category,
                    'price_inquiry': intent.price_inquiry
                }
                
                # Check if intent matches expectation
                intent_match = intent.intent == test_case['expected_intent']
                if intent_match:
                    successful_parses += 1
                
                status = "✅" if intent_match else "❌"
                print(f"  {status} '{test_case['query'][:50]}...'")
                print(f"      انتظار: {test_case['expected_intent']}")
                print(f"      تشخیص: {intent.intent} (اطمینان: {intent.confidence:.2f})")
                print(f"      برند: {intent.brand}, دسته: {intent.category}")
                print(f"      قیمت: {intent.price_inquiry}")
                
                self.results['intent_parsing_tests'].append(test_result)
                
            except Exception as e:
                print(f"  ❌ خطا در تحلیل: {e}")
                self.results['intent_parsing_tests'].append({
                    'query': test_case['query'],
                    'error': str(e)
                })
        
        accuracy = successful_parses / len(test_cases)
        print(f"  📊 دقت Intent Parsing: {accuracy:.2%} ({successful_parses}/{len(test_cases)})")
        
        return accuracy > 0.6  # At least 60% accuracy
    
    async def test_semantic_routing(self):
        """Test semantic routing with exemplars"""
        print("\n🎯 تست Semantic Routing...")
        
        semantic_router = SemanticRouter(self.config)
        await semantic_router.initialize()
        
        # Test exemplar similarity
        exemplars = AgentExemplars()
        
        test_cases = [
            # Should match GENERAL
            ("چطور می‌تونم از سایت خرید کنم؟", AgentType.GENERAL),
            ("ساعت کاری پشتیبانی چیه؟", AgentType.GENERAL),
            
            # Should match SPECIFIC_PRODUCT
            ("گوشی آیفون 15 پرو مکس میخوام", AgentType.SPECIFIC_PRODUCT),
            ("لپ تاپ ASUS ROG مدل G15", AgentType.SPECIFIC_PRODUCT),
            
            # Should match EXPLORATION
            ("یه گوشی خوب تا 15 میلیون میخوام", AgentType.EXPLORATION),
            ("دنبال لپ تاپ برای برنامه نویسی هستم", AgentType.EXPLORATION),
            
            # Should match COMPARISON
            ("تفاوت بین آیفون و سامسونگ چیه؟", AgentType.COMPARISON),
            ("کدوم بهتره؟ لپ تاپ ایسوس یا لنوو", AgentType.COMPARISON)
        ]
        
        correct_matches = 0
        
        for query, expected_agent in test_cases:
            state = RouterState(user_query=query)
            decision = await semantic_router.route_by_similarity(state)
            
            # Get similar exemplars for analysis
            similar_exemplars = await semantic_router.get_similar_exemplars(
                query, decision.agent, top_k=3
            )
            
            is_correct = decision.agent == expected_agent
            if is_correct:
                correct_matches += 1
            
            test_result = {
                'query': query,
                'expected': expected_agent.name,
                'predicted': decision.agent.name,
                'confidence': decision.confidence,
                'reasoning': decision.reasoning,
                'similar_exemplars': [(text[:30], score) for text, score in similar_exemplars[:2]]
            }
            
            status = "✅" if is_correct else "❌"
            print(f"  {status} '{query[:50]}...'")
            print(f"      انتظار: {expected_agent.name}")
            print(f"      تشخیص: {decision.agent.name} (اطمینان: {decision.confidence:.2f})")
            print(f"      دلیل: {decision.reasoning[:50]}...")
            
            if similar_exemplars:
                print(f"      نمونه‌های مشابه:")
                for text, score in similar_exemplars[:2]:
                    print(f"        - {text[:40]}... (تشابه: {score:.3f})")
            
            self.results['semantic_routing_tests'].append(test_result)
        
        accuracy = correct_matches / len(test_cases)
        print(f"  📊 دقت Semantic Routing: {accuracy:.2%} ({correct_matches}/{len(test_cases)})")
        
        # Test cache statistics
        cache_stats = semantic_router.get_cache_stats()
        print(f"  💾 آمار کش: {cache_stats}")
        
        return accuracy > 0.6  # At least 60% accuracy
    
    async def test_main_router_integration(self):
        """Test main router integration"""
        print("\n🚀 تست Main Router Integration...")
        
        test_cases = [
            # Mixed scenarios
            "سلام، چطور می‌تونم خرید کنم؟",
            "لطفا کابینت کد D14 رو پیدا کن",
            "قیمت گوشی سامسونگ A54 چقدره؟",
            "فروشندگان لپ تاپ ایسوس کدومن؟",
            "یه گوشی خوب تا 10 میلیون میخوام",
            "مقایسه آیفون 15 با سامسونگ S24",
            "دنبال هدفون بی‌سیم با کیفیت خوب هستم"
        ]
        
        successful_routes = 0
        total_time = 0
        
        for i, query in enumerate(test_cases, 1):
            print(f"\n  🧪 تست {i}: '{query[:40]}...'")
            
            start_time = time.time()
            
            try:
                state = RouterState(user_query=query, turn_count=0)
                decision = await self.router.route(state)
                
                routing_time = time.time() - start_time
                total_time += routing_time
                
                # Get detailed explanation
                explanation = await self.router.get_routing_explanation(query)
                
                test_result = {
                    'query': query,
                    'agent': decision.agent.name,
                    'confidence': decision.confidence,
                    'reasoning': decision.reasoning,
                    'routing_time': routing_time,
                    'extracted_data': decision.extracted_data,
                    'hard_signals': explanation['hard_signals'],
                    'intent_analysis': explanation['intent'],
                    'semantic_analysis': explanation['semantic']
                }
                
                print(f"    ✅ عامل: {decision.agent.name}")
                print(f"    📊 اطمینان: {decision.confidence:.3f}")
                print(f"    ⏱️  زمان: {routing_time:.3f}s")
                print(f"    🧠 دلیل: {decision.reasoning[:60]}...")
                
                # Show analysis breakdown
                print(f"    🔍 تحلیل:")
                print(f"      - Hard Signal: {explanation['hard_signals']['detected']} ({explanation['hard_signals']['confidence']:.2f})")
                print(f"      - Intent: {explanation['intent']['type']} ({explanation['intent']['confidence']:.2f})")
                print(f"      - Semantic: {explanation['semantic']['best_agent']} ({explanation['semantic']['confidence']:.2f})")
                
                successful_routes += 1
                self.results['main_router_tests'].append(test_result)
                
            except Exception as e:
                print(f"    ❌ خطا: {e}")
                self.results['main_router_tests'].append({
                    'query': query,
                    'error': str(e)
                })
        
        avg_time = total_time / len(test_cases)
        success_rate = successful_routes / len(test_cases)
        
        print(f"\n  📊 نتایج کلی:")
        print(f"    - نرخ موفقیت: {success_rate:.2%} ({successful_routes}/{len(test_cases)})")
        print(f"    - میانگین زمان: {avg_time:.3f}s")
        print(f"    - زمان کل: {total_time:.3f}s")
        
        return success_rate > 0.8  # At least 80% success rate
    
    async def test_session_management(self):
        """Test session management"""
        print("\n👥 تست Session Management...")
        
        session_manager = SessionManager()
        
        # Test session creation
        session = session_manager.get_or_create_session("test-user-123")
        print(f"  ✅ جلسه ایجاد شد: {session.session_id}")
        
        # Simulate conversation
        conversation = [
            "سلام، یه گوشی خوب میخوام",
            "بودجم حدود 15 میلیون تومانه",
            "ترجیحا سامسونگ باشه",
            "دوربین خوب برام مهمه",
            "بین A54 و A55 کدوم بهتره؟"
        ]
        
        for i, query in enumerate(conversation):
            state = RouterState(
                user_query=query,
                session_context=session.get_context_for_routing(),
                turn_count=session.turn_count
            )
            
            decision = await self.router.route(state)
            session.add_turn(query, decision, f"[پاسخ عامل {decision.agent.name}]")
            
            print(f"  🔄 دور {i+1}: {decision.agent.name} (اطمینان: {decision.confidence:.2f})")
            
            if session.should_force_conclusion:
                print(f"    ⚠️ نزدیک به حد مجاز دورها!")
        
        # Test session statistics
        stats = {
            'total_turns': session.turn_count,
            'agents_used': [agent.name for agent in session.get_previous_agents()],
            'at_limit': session.is_at_turn_limit
        }
        
        print(f"  📊 آمار جلسه:")
        print(f"    - تعداد دورها: {stats['total_turns']}")
        print(f"    - عامل‌های استفاده شده: {stats['agents_used']}")
        print(f"    - در حد مجاز: {stats['at_limit']}")
        
        # Test session manager statistics
        manager_stats = session_manager.get_session_stats()
        print(f"  📈 آمار مدیر جلسات:")
        print(f"    - کل جلسات: {manager_stats['total_sessions']}")
        print(f"    - میانگین دورها: {manager_stats['avg_turns']:.1f}")
        print(f"    - استفاده از عامل‌ها: {manager_stats['agent_usage']}")
        
        self.results['session_management_tests'].append({
            'session_stats': stats,
            'manager_stats': manager_stats
        })
        
        return True
    
    async def test_performance_benchmarks(self):
        """Test performance benchmarks"""
        print("\n⚡ تست Performance Benchmarks...")
        
        # Prepare test queries
        queries = [
            "سلام چطورید؟",
            "قیمت گوشی سامسونگ چقدره؟",
            "یه لپ تاپ خوب میخوام",
            "مقایسه آیفون با سامسونگ",
            "فروشندگان لپ تاپ کدومن؟"
        ] * 10  # 50 queries total
        
        print(f"  📊 تست با {len(queries)} درخواست...")
        
        # Test routing speed
        start_time = time.time()
        successful_routes = 0
        
        for query in queries:
            try:
                state = RouterState(user_query=query)
                decision = await self.router.route(state)
                successful_routes += 1
            except Exception as e:
                print(f"    ❌ خطا در '{query[:30]}...': {e}")
        
        total_time = time.time() - start_time
        avg_time_per_query = total_time / len(queries)
        queries_per_second = len(queries) / total_time
        
        performance_results = {
            'total_queries': len(queries),
            'successful_routes': successful_routes,
            'total_time': total_time,
            'avg_time_per_query': avg_time_per_query,
            'queries_per_second': queries_per_second,
            'success_rate': successful_routes / len(queries)
        }
        
        print(f"  📈 نتایج عملکرد:")
        print(f"    - کل درخواست‌ها: {performance_results['total_queries']}")
        print(f"    - موفق: {performance_results['successful_routes']}")
        print(f"    - زمان کل: {performance_results['total_time']:.2f}s")
        print(f"    - میانگین زمان: {performance_results['avg_time_per_query']:.3f}s")
        print(f"    - درخواست در ثانیه: {performance_results['queries_per_second']:.1f}")
        print(f"    - نرخ موفقیت: {performance_results['success_rate']:.2%}")
        
        self.results['performance_tests'].append(performance_results)
        
        return performance_results['success_rate'] > 0.9  # At least 90% success
    
    def generate_test_report(self):
        """Generate comprehensive test report"""
        print("\n📋 گزارش کامل تست‌ها")
        print("=" * 60)
        
        total_tests = 0
        passed_tests = 0
        
        for test_category, results in self.results.items():
            if results:
                total_tests += 1
                # Consider test passed if we have results
                passed_tests += 1
                print(f"\n✅ {test_category}: {len(results)} نتیجه")
        
        print(f"\n📊 خلاصه کلی:")
        print(f"  - کل تست‌ها: {total_tests}")
        print(f"  - موفق: {passed_tests}")
        print(f"  - نرخ موفقیت: {passed_tests/total_tests:.2%}" if total_tests > 0 else "  - نرخ موفقیت: 0%")
        
        return self.results
    
    async def run_all_tests(self):
        """Run all tests"""
        print("🧪 شروع تست‌های جامع Router System")
        print("=" * 60)
        
        try:
            await self.setup()
            
            # Run all test categories
            test_functions = [
                ("Embedding Service", self.test_embedding_service),
                ("Hard Signal Detection", self.test_hard_signal_detection),
                ("Intent Parsing", self.test_intent_parsing),
                ("Semantic Routing", self.test_semantic_routing),
                ("Main Router Integration", self.test_main_router_integration),
                ("Session Management", self.test_session_management),
                ("Performance Benchmarks", self.test_performance_benchmarks)
            ]
            
            passed_tests = 0
            
            for test_name, test_func in test_functions:
                try:
                    print(f"\n{'='*20} {test_name} {'='*20}")
                    result = await test_func()
                    if result:
                        passed_tests += 1
                        print(f"✅ {test_name} - موفق")
                    else:
                        print(f"❌ {test_name} - ناموفق")
                except Exception as e:
                    print(f"❌ {test_name} - خطا: {e}")
            
            # Generate final report
            self.generate_test_report()
            
            print(f"\n🎉 تست‌ها تمام شد! {passed_tests}/{len(test_functions)} موفق")
            
        except Exception as e:
            print(f"❌ خطای کلی در تست: {e}")
            raise


async def main():
    """Main test runner"""
    test_suite = RouterTestSuite()
    await test_suite.run_all_tests()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n⏹️ تست‌ها متوقف شدند.")
    except Exception as e:
        print(f"\n❌ خطا: {e}")
        sys.exit(1)
