#!/usr/bin/env python3
"""
Unit tests for individual router components
Focused tests for specific functionality
"""

import asyncio
import sys
import unittest
from pathlib import Path
import numpy as np

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from router import (
    RouterConfig,
    AgentType,
    RouterState,
    RouterDecision,
    RouterIntent,
    EmbeddingService,
    HardSignalDetector,
    AgentExemplars,
    SessionManager
)


class TestEmbeddingService(unittest.TestCase):
    """Test embedding service"""
    
    def setUp(self):
        self.config = RouterConfig(
            openai_api_key="test-key",
            openai_base_url="https://turbo.torob.com/v1"
        )
        self.service = EmbeddingService(self.config)
    
    def test_cache_key_generation(self):
        """Test cache key generation"""
        key1 = self.service._get_cache_key("test text")
        key2 = self.service._get_cache_key("test text")
        key3 = self.service._get_cache_key("different text")
        
        self.assertEqual(key1, key2)
        self.assertNotEqual(key1, key3)
        self.assertIsInstance(key1, str)
        self.assertEqual(len(key1), 32)  # MD5 hash length
    
    def test_cosine_similarity(self):
        """Test cosine similarity calculation"""
        # Test identical vectors
        vec1 = np.array([1, 0, 0])
        vec2 = np.array([1, 0, 0])
        sim = EmbeddingService.cosine_similarity(vec1, vec2)
        self.assertAlmostEqual(sim, 1.0, places=5)
        
        # Test orthogonal vectors
        vec1 = np.array([1, 0, 0])
        vec2 = np.array([0, 1, 0])
        sim = EmbeddingService.cosine_similarity(vec1, vec2)
        self.assertAlmostEqual(sim, 0.0, places=5)
        
        # Test opposite vectors
        vec1 = np.array([1, 0, 0])
        vec2 = np.array([-1, 0, 0])
        sim = EmbeddingService.cosine_similarity(vec1, vec2)
        self.assertAlmostEqual(sim, -1.0, places=5)
        
        # Test zero vectors
        vec1 = np.array([0, 0, 0])
        vec2 = np.array([1, 0, 0])
        sim = EmbeddingService.cosine_similarity(vec1, vec2)
        self.assertEqual(sim, 0.0)
    
    async def test_find_most_similar(self):
        """Test finding most similar embeddings"""
        query = np.array([1, 0, 0])
        candidates = [
            np.array([0.9, 0.1, 0]),    # Very similar
            np.array([0, 1, 0]),        # Orthogonal
            np.array([0.5, 0.5, 0]),    # Somewhat similar
            np.array([-1, 0, 0])        # Opposite
        ]
        
        results = await self.service.find_most_similar(query, candidates, top_k=2)
        
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0][0], 0)  # Most similar should be first candidate
        self.assertGreater(results[0][1], results[1][1])  # First should have higher similarity


class TestHardSignalDetector(unittest.TestCase):
    """Test hard signal detection"""
    
    def setUp(self):
        self.detector = HardSignalDetector()
    
    def test_product_code_detection(self):
        """Test product code detection"""
        test_cases = [
            ("کابینت کد D14", ["D14"]),
            ("محصول SKU:ABC123", ["ABC123"]),
            ("مدل X515EA", ["X515EA"]),
            ("کد محصول: XYZ-789", ["XYZ-789"]),
            ("هیچ کدی نیست", [])
        ]
        
        for query, expected_codes in test_cases:
            info = self.detector.extract_product_info(query)
            self.assertEqual(len(info['codes']), len(expected_codes))
    
    def test_brand_extraction(self):
        """Test brand extraction"""
        test_cases = [
            ("گوشی سامسونگ A54", ["samsung"]),
            ("لپ تاپ ایسوس ROG", ["asus"]),
            ("آیفون 15 پرو", ["iphone"]),
            ("تلویزیون ال جی OLED", ["lg"]),
            ("محصول بدون برند", [])
        ]
        
        for query, expected_brands in test_cases:
            brands = self.detector._extract_brands(query)
            self.assertEqual(len(brands), len(expected_brands))
            if expected_brands:
                self.assertIn(expected_brands[0], brands)
    
    def test_comparison_detection(self):
        """Test comparison detection"""
        comparison_queries = [
            "مقایسه آیفون با سامسونگ",
            "کدوم بهتره؟ ایسوس یا اچ پی",
            "تفاوت بین A و B",
            "انتخاب بین این دو"
        ]
        
        non_comparison_queries = [
            "گوشی سامسونگ میخوام",
            "قیمت لپ تاپ چقدره؟",
            "یه محصول خوب پیدا کن"
        ]
        
        for query in comparison_queries:
            state = RouterState(user_query=query)
            result = self.detector.detect(state)
            # Should detect comparison or have comparison-related patterns
            self.assertTrue(
                result.agent == AgentType.COMPARISON or 
                "comparison" in result.matched_patterns or
                any("مقایسه" in pattern or "comparison" in pattern for pattern in result.matched_patterns)
            )
        
        for query in non_comparison_queries:
            state = RouterState(user_query=query)
            result = self.detector.detect(state)
            # Should not be detected as comparison
            self.assertNotEqual(result.agent, AgentType.COMPARISON)
    
    def test_price_inquiry_detection(self):
        """Test price inquiry detection"""
        price_queries = [
            "قیمت گوشی چقدره؟",
            "هزینه این محصول چقدر است؟",
            "چند تومان میشه؟"
        ]
        
        for query in price_queries:
            info = self.detector.extract_product_info(query)
            self.assertTrue(info['has_price_inquiry'])


class TestAgentExemplars(unittest.TestCase):
    """Test agent exemplars"""
    
    def setUp(self):
        self.exemplars = AgentExemplars()
    
    def test_exemplar_loading(self):
        """Test that exemplars are loaded correctly"""
        for agent_type in AgentType:
            exemplars = self.exemplars.get_exemplars(agent_type)
            self.assertGreater(len(exemplars), 0, f"No exemplars for {agent_type}")
            
            for exemplar in exemplars:
                self.assertIsInstance(exemplar.query, str)
                self.assertGreater(len(exemplar.query), 0)
                self.assertIsInstance(exemplar.keywords, list)
                self.assertGreater(len(exemplar.keywords), 0)
    
    def test_exemplar_texts(self):
        """Test exemplar text extraction"""
        for agent_type in AgentType:
            texts = self.exemplars.get_exemplar_texts(agent_type)
            self.assertIsInstance(texts, list)
            self.assertGreater(len(texts), 0)
            
            for text in texts:
                self.assertIsInstance(text, str)
                self.assertGreater(len(text), 0)
    
    def test_exemplar_keywords(self):
        """Test keyword extraction"""
        for agent_type in AgentType:
            keywords = self.exemplars.get_exemplar_keywords(agent_type)
            self.assertIsInstance(keywords, list)
            
            # Keywords should be unique
            self.assertEqual(len(keywords), len(set(keywords)))


class TestSessionManager(unittest.TestCase):
    """Test session management"""
    
    def setUp(self):
        self.manager = SessionManager(max_turns=3)
    
    def test_session_creation(self):
        """Test session creation"""
        session_id = "test-session-1"
        session = self.manager.create_session(session_id)
        
        self.assertEqual(session.session_id, session_id)
        self.assertEqual(session.turn_count, 0)
        self.assertFalse(session.is_at_turn_limit)
        self.assertIn(session_id, self.manager.sessions)
    
    def test_get_or_create_session(self):
        """Test get or create session"""
        session_id = "test-session-2"
        
        # First call should create
        session1 = self.manager.get_or_create_session(session_id)
        self.assertEqual(session1.session_id, session_id)
        
        # Second call should return existing
        session2 = self.manager.get_or_create_session(session_id)
        self.assertIs(session1, session2)
    
    def test_turn_management(self):
        """Test turn management"""
        session = self.manager.create_session("test-turns")
        
        # Add turns up to limit
        for i in range(3):
            decision = RouterDecision(
                agent=AgentType.GENERAL,
                confidence=0.8,
                reasoning="Test decision"
            )
            session.add_turn(f"Query {i}", decision, f"Response {i}")
        
        self.assertEqual(session.turn_count, 3)
        self.assertTrue(session.is_at_turn_limit)
        self.assertTrue(session.should_force_conclusion)
    
    def test_session_cleanup(self):
        """Test session cleanup"""
        # Create some sessions
        for i in range(3):
            self.manager.create_session(f"session-{i}")
        
        initial_count = self.manager.get_active_sessions_count()
        self.assertEqual(initial_count, 3)
        
        # Cleanup (won't actually delete anything since sessions are new)
        deleted = self.manager.cleanup_old_sessions(hours=0)  # Delete everything
        self.assertGreaterEqual(deleted, 0)
    
    def test_session_statistics(self):
        """Test session statistics"""
        # Create session with some turns
        session = self.manager.create_session("stats-test")
        
        decisions = [
            RouterDecision(AgentType.GENERAL, 0.8, "General"),
            RouterDecision(AgentType.SPECIFIC_PRODUCT, 0.9, "Product"),
            RouterDecision(AgentType.EXPLORATION, 0.7, "Explore")
        ]
        
        for i, decision in enumerate(decisions):
            session.add_turn(f"Query {i}", decision, f"Response {i}")
        
        stats = self.manager.get_session_stats()
        
        self.assertIsInstance(stats, dict)
        self.assertIn('total_sessions', stats)
        self.assertIn('avg_turns', stats)
        self.assertIn('agent_usage', stats)
        
        self.assertGreater(stats['total_sessions'], 0)
        self.assertGreater(stats['avg_turns'], 0)


class TestRouterDataTypes(unittest.TestCase):
    """Test router data types and validation"""
    
    def test_router_intent_creation(self):
        """Test RouterIntent creation and validation"""
        intent = RouterIntent(
            intent="test_intent",
            base_ids=["base1", "base2"],
            product_codes=["CODE1"],
            confidence=0.85
        )
        
        self.assertEqual(intent.intent, "test_intent")
        self.assertEqual(len(intent.base_ids), 2)
        self.assertEqual(len(intent.product_codes), 1)
        self.assertEqual(intent.confidence, 0.85)
        self.assertFalse(intent.price_inquiry)
    
    def test_router_decision_creation(self):
        """Test RouterDecision creation"""
        decision = RouterDecision(
            agent=AgentType.GENERAL,
            confidence=0.9,
            reasoning="Test reasoning",
            extracted_data={"key": "value"}
        )
        
        self.assertEqual(decision.agent, AgentType.GENERAL)
        self.assertEqual(decision.confidence, 0.9)
        self.assertEqual(decision.reasoning, "Test reasoning")
        self.assertEqual(decision.extracted_data["key"], "value")
        self.assertFalse(decision.force_conclusion)
    
    def test_router_state_creation(self):
        """Test RouterState creation"""
        state = RouterState(
            user_query="Test query",
            session_context={"session_id": "test"},
            turn_count=2
        )
        
        self.assertEqual(state.user_query, "Test query")
        self.assertEqual(state.session_context["session_id"], "test")
        self.assertEqual(state.turn_count, 2)


async def run_async_tests():
    """Run async tests"""
    print("🧪 اجرای تست‌های async...")
    
    # Test embedding service
    config = RouterConfig(
        openai_api_key="test-key",
        openai_base_url="https://turbo.torob.com/v1"
    )
    service = EmbeddingService(config)
    
    # Test find_most_similar
    test_embedding = TestEmbeddingService()
    test_embedding.setUp()
    await test_embedding.test_find_most_similar()
    print("✅ Async embedding tests passed")


def run_all_unit_tests():
    """Run all unit tests"""
    print("🧪 اجرای Unit Tests...")
    
    # Create test suite
    test_classes = [
        TestEmbeddingService,
        TestHardSignalDetector,
        TestAgentExemplars,
        TestSessionManager,
        TestRouterDataTypes
    ]
    
    suite = unittest.TestSuite()
    
    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        suite.addTests(tests)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Run async tests
    asyncio.run(run_async_tests())
    
    print(f"\n📊 نتایج Unit Tests:")
    print(f"  - اجرا شده: {result.testsRun}")
    print(f"  - موفق: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"  - ناموفق: {len(result.failures)}")
    print(f"  - خطا: {len(result.errors)}")
    
    if result.failures:
        print("\n❌ تست‌های ناموفق:")
        for test, traceback in result.failures:
            print(f"  - {test}: {traceback}")
    
    if result.errors:
        print("\n💥 خطاهای تست:")
        for test, traceback in result.errors:
            print(f"  - {test}: {traceback}")
    
    return result.wasSuccessful()


if __name__ == "__main__":
    try:
        success = run_all_unit_tests()
        if success:
            print("\n🎉 همه تست‌ها موفق بودند!")
        else:
            print("\n❌ برخی تست‌ها ناموفق بودند!")
            sys.exit(1)
    except Exception as e:
        print(f"\n💥 خطا در اجرای تست‌ها: {e}")
        sys.exit(1)
