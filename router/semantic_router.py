"""
Semantic routing using embedding similarity
Compares user query to agent exemplars
"""

import numpy as np
from typing import List, Dict, Tuple, Optional
import asyncio
from collections import defaultdict
from .base import RouterConfig, RouterState, AgentType, RouterDecision
from .embeddings import EmbeddingService
from .exemplars import AgentExemplars


class SemanticRouter:
    """Routes queries based on semantic similarity to exemplars"""
    
    def __init__(self, config: RouterConfig):
        self.config = config
        self.embedding_service = EmbeddingService(config)
        self.exemplars = AgentExemplars()
        self._exemplar_embeddings_cache: Dict[AgentType, List[np.ndarray]] = {}
        self._initialized = False
    
    async def initialize(self):
        """Initialize by computing exemplar embeddings"""
        if self._initialized:
            return
        
        print("در حال آماده‌سازی semantic router...")
        
        # Compute embeddings for all exemplars
        tasks = []
        for agent_type in AgentType:
            exemplar_texts = self.exemplars.get_exemplar_texts(agent_type)
            if exemplar_texts:
                task = self._compute_exemplar_embeddings(agent_type, exemplar_texts)
                tasks.append(task)
        
        await asyncio.gather(*tasks)
        self._initialized = True
        print("Semantic router آماده است.")
    
    async def _compute_exemplar_embeddings(self, agent_type: AgentType, texts: List[str]):
        """Compute and cache embeddings for exemplars of an agent type"""
        embeddings = await self.embedding_service.get_embeddings_batch(texts)
        self._exemplar_embeddings_cache[agent_type] = embeddings
    
    async def route_by_similarity(self, state: RouterState) -> RouterDecision:
        """Route based on semantic similarity to exemplars"""
        # Ensure initialization
        if not self._initialized:
            await self.initialize()
        
        # Get query embedding
        query_embedding = await self.embedding_service.get_embedding(state.user_query)
        
        # Calculate similarities for each agent type
        agent_scores = await self._calculate_agent_scores(query_embedding)
        
        # Select best agent based on scores
        decision = self._select_best_agent(agent_scores, state)
        
        return decision
    
    async def _calculate_agent_scores(self, query_embedding: np.ndarray) -> Dict[AgentType, float]:
        """Calculate similarity scores for each agent type"""
        scores = {}
        
        for agent_type, exemplar_embeddings in self._exemplar_embeddings_cache.items():
            if not exemplar_embeddings:
                scores[agent_type] = 0.0
                continue
            
            # Find top-k most similar exemplars
            similarities = []
            for exemplar_emb in exemplar_embeddings:
                sim = self.embedding_service.cosine_similarity(query_embedding, exemplar_emb)
                similarities.append(sim)
            
            # Use average of top-k similarities as agent score
            similarities.sort(reverse=True)
            top_k = min(self.config.top_k_exemplars, len(similarities))
            avg_score = sum(similarities[:top_k]) / top_k if top_k > 0 else 0.0
            
            scores[agent_type] = avg_score
        
        return scores
    
    def _select_best_agent(self, scores: Dict[AgentType, float], state: RouterState) -> RouterDecision:
        """Select best agent based on scores and thresholds"""
        # Sort agents by score
        sorted_agents = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        
        if not sorted_agents:
            # No scores available, default to general agent
            return RouterDecision(
                agent=AgentType.GENERAL,
                confidence=0.0,
                reasoning="هیچ امتیاز تشابهی محاسبه نشد، به دستیار عمومی می‌روم"
            )
        
        best_agent, best_score = sorted_agents[0]
        
        # Check if score meets thresholds
        if best_score < self.config.similarity_threshold_low:
            # Score too low, route to general agent as fallback
            return RouterDecision(
                agent=AgentType.GENERAL,
                confidence=0.3,
                reasoning=f"امتیاز تشابه ({best_score:.2f}) کمتر از آستانه ({self.config.similarity_threshold_low}) است - هدایت به دستیار عمومی"
            )
        
        # Calculate confidence based on score and gap to second best
        confidence = best_score
        if len(sorted_agents) > 1:
            second_best_score = sorted_agents[1][1]
            score_gap = best_score - second_best_score
            
            # Higher gap means higher confidence
            if score_gap > 0.2:
                confidence = min(confidence + 0.1, 1.0)
            elif score_gap < 0.1:
                confidence = max(confidence - 0.1, 0.0)
        
        # Check turn budget
        force_conclusion = False
        if state.turn_count >= self.config.force_conclusion_turn:
            if best_agent in [AgentType.EXPLORATION, AgentType.GENERAL]:
                force_conclusion = True
                confidence = min(confidence + 0.2, 1.0)
        
        # Create reasoning
        reasoning = self._create_reasoning(best_agent, best_score, sorted_agents[:3])
        
        return RouterDecision(
            agent=best_agent,
            confidence=confidence,
            reasoning=reasoning,
            force_conclusion=force_conclusion
        )
    
    def _create_reasoning(self, agent: AgentType, score: float, top_agents: List[Tuple[AgentType, float]]) -> str:
        """Create human-readable reasoning for the decision"""
        agent_names = {
            AgentType.GENERAL: "پاسخ به سوالات عمومی",
            AgentType.SPECIFIC_PRODUCT: "یافتن محصول خاص",
            AgentType.PRODUCT_FEATURE: "ویژگی‌های محصول",
            AgentType.SELLER_INFO: "اطلاعات فروشندگان",
            AgentType.EXPLORATION: "کاوش و تعامل",
            AgentType.COMPARISON: "مقایسه محصولات"
        }
        
        reasoning = f"بیشترین تشابه با نمونه‌های '{agent_names.get(agent, 'نامشخص')}' (امتیاز: {score:.2f})"
        
        if len(top_agents) > 1:
            reasoning += "\nسایر گزینه‌ها: "
            for other_agent, other_score in top_agents[1:3]:
                reasoning += f"{agent_names.get(other_agent, 'نامشخص')} ({other_score:.2f}), "
            reasoning = reasoning.rstrip(", ")
        
        return reasoning
    
    async def get_similar_exemplars(self, query: str, agent_type: AgentType, top_k: int = 3) -> List[Tuple[str, float]]:
        """Get most similar exemplars for a specific agent type"""
        if not self._initialized:
            await self.initialize()
        
        query_embedding = await self.embedding_service.get_embedding(query)
        exemplar_texts = self.exemplars.get_exemplar_texts(agent_type)
        exemplar_embeddings = self._exemplar_embeddings_cache.get(agent_type, [])
        
        if not exemplar_embeddings:
            return []
        
        # Calculate similarities
        similarities = []
        for i, (text, embedding) in enumerate(zip(exemplar_texts, exemplar_embeddings)):
            sim = self.embedding_service.cosine_similarity(query_embedding, embedding)
            similarities.append((text, sim))
        
        # Sort and return top-k
        similarities.sort(key=lambda x: x[1], reverse=True)
        return similarities[:top_k]
    
    def get_cache_stats(self) -> Dict[str, int]:
        """Get statistics about cached embeddings"""
        stats = {
            "exemplar_embeddings": sum(len(embs) for embs in self._exemplar_embeddings_cache.values()),
            "query_embeddings": self.embedding_service.get_cache_size(),
            "agent_types_cached": len(self._exemplar_embeddings_cache)
        }
        return stats
