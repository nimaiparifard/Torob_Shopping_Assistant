"""
Simplified main router without LangGraph dependencies
Direct implementation for better compatibility
"""

from typing import Dict, Any, Optional
import asyncio

from .base import (
    RouterBase, RouterConfig, RouterState, RouterDecision, 
    AgentType, RouterIntent
)
from .hard_signals import HardSignalDetector
from .intent_parser import IntentParser
from .semantic_router import SemanticRouter


class SimpleMainRouter(RouterBase):
    """Simplified main router without LangGraph"""
    
    def __init__(self, config: RouterConfig):
        super().__init__(config)
        self.hard_signal_detector = HardSignalDetector()
        self.intent_parser = IntentParser(config)
        self.semantic_router = SemanticRouter(config)
        self._initialized = False
    
    async def initialize(self):
        """Initialize all components"""
        if self._initialized:
            return
        
        print("در حال آماده‌سازی router اصلی...")
        await self.semantic_router.initialize()
        self._initialized = True
        print("Router آماده است!")
    
    async def route(self, state: RouterState) -> RouterDecision:
        """Main routing method"""
        # Ensure initialization
        if not self._initialized:
            await self.initialize()
        
        try:
            # Step 1: Hard signal detection
            hard_signal_result = self.hard_signal_detector.detect(state)
            
            # If hard signal has high confidence, use it directly
            if hard_signal_result.agent and hard_signal_result.confidence > 0.85:
                return RouterDecision(
                    agent=hard_signal_result.agent,
                    confidence=hard_signal_result.confidence,
                    reasoning=f"تشخیص قطعی بر اساس الگوهای مشخص: {', '.join(hard_signal_result.matched_patterns)}",
                    extracted_data=hard_signal_result.extracted_data
                )
            
            # Step 2: Intent parsing
            intent = None
            try:
                intent = await self.intent_parser.parse_intent(state)
            except Exception as e:
                print(f"خطا در تحلیل intent: {e}")
            
            # Step 3: Semantic routing
            semantic_decision = None
            try:
                semantic_decision = await self.semantic_router.route_by_similarity(state)
            except Exception as e:
                print(f"خطا در مسیریابی معنایی: {e}")
            
            # Step 4: Combine decisions
            return self._combine_decisions(
                hard_signal_result, 
                intent, 
                semantic_decision, 
                state
            )
            
        except Exception as e:
            print(f"خطای غیرمنتظره در routing: {e}")
            return RouterDecision(
                agent=AgentType.EXPLORATION,
                confidence=0.0,
                reasoning="خطای غیرمنتظره در سیستم"
            )
    
    def _combine_decisions(
        self, 
        hard_signal_result, 
        intent: Optional[RouterIntent], 
        semantic_decision: Optional[RouterDecision],
        state: RouterState
    ) -> RouterDecision:
        """Combine all routing decisions"""
        
        decisions = []
        
        # Hard signal decision (highest weight)
        if hard_signal_result.agent and hard_signal_result.confidence > 0.7:
            decisions.append({
                "agent": hard_signal_result.agent,
                "confidence": hard_signal_result.confidence,
                "weight": 0.5,
                "source": "hard_signal"
            })
        
        # Intent-based decision
        if intent and intent.confidence > 0.3:
            agent = self.intent_parser.map_intent_to_agent(intent)
            decisions.append({
                "agent": agent,
                "confidence": intent.confidence,
                "weight": 0.3,
                "source": "intent"
            })
        
        # Semantic decision
        if semantic_decision and semantic_decision.confidence > 0.3:
            decisions.append({
                "agent": semantic_decision.agent,
                "confidence": semantic_decision.confidence,
                "weight": 0.2,
                "source": "semantic"
            })
        
        # Calculate weighted scores
        agent_scores = {}
        for decision in decisions:
            agent = decision["agent"]
            score = decision["confidence"] * decision["weight"]
            
            if agent not in agent_scores:
                agent_scores[agent] = {"score": 0, "sources": []}
            
            agent_scores[agent]["score"] += score
            agent_scores[agent]["sources"].append(decision["source"])
        
        # Select best agent
        if agent_scores:
            best_agent = max(agent_scores.items(), key=lambda x: x[1]["score"])
            final_agent = best_agent[0]
            final_confidence = min(best_agent[1]["score"] / 0.5, 1.0)  # Normalize
            
            # Create reasoning
            sources = best_agent[1]["sources"]
            reasoning = f"تصمیم بر اساس: {', '.join(sources)}"
            if hard_signal_result.matched_patterns:
                reasoning += f"\nالگوهای تطابق: {', '.join(hard_signal_result.matched_patterns)}"
            
            # Handle turn budget
            force_conclusion = state.turn_count >= self.config.force_conclusion_turn
            
            return RouterDecision(
                agent=final_agent,
                confidence=final_confidence,
                reasoning=reasoning,
                extracted_data=hard_signal_result.extracted_data or {},
                force_conclusion=force_conclusion
            )
        else:
            # No decisions available, default to exploration
            return RouterDecision(
                agent=AgentType.EXPLORATION,
                confidence=0.0,
                reasoning="هیچ تصمیمی در دسترس نیست، به حالت اکتشاف می‌روم"
            )
    
    async def get_routing_explanation(self, query: str) -> Dict[str, Any]:
        """Get detailed explanation of routing decision"""
        state = RouterState(user_query=query)
        
        # Run all components
        hard_signal = self.hard_signal_detector.detect(state)
        
        intent = None
        try:
            intent = await self.intent_parser.parse_intent(state)
        except Exception as e:
            intent = RouterIntent(intent="error", confidence=0.0)
        
        semantic_decision = None
        try:
            semantic_decision = await self.semantic_router.route_by_similarity(state)
        except Exception as e:
            semantic_decision = RouterDecision(
                agent=AgentType.EXPLORATION,
                confidence=0.0,
                reasoning="خطا در مسیریابی معنایی"
            )
        
        # Get similar exemplars for each agent
        exemplar_similarities = {}
        try:
            for agent in AgentType:
                similar = await self.semantic_router.get_similar_exemplars(query, agent, top_k=2)
                if similar:
                    exemplar_similarities[agent.name] = similar
        except Exception as e:
            print(f"خطا در دریافت نمونه‌های مشابه: {e}")
        
        return {
            "query": query,
            "hard_signals": {
                "detected": hard_signal.agent.name if hard_signal.agent else None,
                "confidence": hard_signal.confidence,
                "patterns": hard_signal.matched_patterns,
                "extracted": hard_signal.extracted_data
            },
            "intent": {
                "type": intent.intent if intent else "unknown",
                "confidence": intent.confidence if intent else 0.0,
                "entities": {
                    "base_ids": intent.base_ids if intent else [],
                    "product_codes": intent.product_codes if intent else [],
                    "brand": intent.brand if intent else None,
                    "category": intent.category if intent else None
                } if intent else {}
            },
            "semantic": {
                "best_agent": semantic_decision.agent.name if semantic_decision else "unknown",
                "confidence": semantic_decision.confidence if semantic_decision else 0.0,
                "similar_exemplars": exemplar_similarities
            }
        }
