"""
Main router that orchestrates all routing components
Integrates with LangGraph for state management
"""

from typing import Dict, Any, Optional, List, TypedDict
from langgraph.graph import StateGraph, END
import asyncio
from dataclasses import asdict

from .base import (
    RouterBase, RouterConfig, RouterState, RouterDecision, 
    AgentType, RouterIntent
)
from .hard_signals import HardSignalDetector
from .intent_parser import IntentParser
from .semantic_router import SemanticRouter
from .embeddings import EmbeddingService
from agents.general_agent import GeneralAgent
from agents.specific_product import SpecificProductAgent
from agents.features_product import FeaturesProductAgent


class RouterGraphState(TypedDict, total=False):
    """State for LangGraph routing"""
    user_query: str
    session_context: Optional[Dict[str, Any]]
    turn_count: int
    routing_decision: Optional[RouterDecision]
    intent: Optional[RouterIntent]
    hard_signal_result: Optional[Dict[str, Any]]
    semantic_scores: Optional[Dict[str, float]]
    final_agent: Optional[str]
    error: Optional[str]
    # Agent responses
    general_agent_response: Optional[Dict[str, Any]]
    specific_product_response: Optional[Dict[str, Any]]
    features_product_response: Optional[Dict[str, Any]]
    final_response: Optional[str]


class MainRouter(RouterBase):
    """Main router that combines all routing strategies"""
    
    def __init__(self, config: RouterConfig):
        super().__init__(config)
        self.hard_signal_detector = HardSignalDetector()
        self.intent_parser = IntentParser(config)
        self.semantic_router = SemanticRouter(config)
        self.general_agent = GeneralAgent(config)
        self.specific_product_agent = SpecificProductAgent(config)
        self.features_product_agent = FeaturesProductAgent(config)
        self.graph = self._build_graph()
        self._initialized = False
    
    async def initialize(self):
        """Initialize all components"""
        if self._initialized:
            return
        
        print("در حال آماده‌سازی router اصلی...")
        await self.semantic_router.initialize()
        self._initialized = True
        print("Router آماده است!")
    
    def _build_graph(self) -> StateGraph:
        """Build LangGraph workflow"""
        workflow = StateGraph(RouterGraphState)
        
        # Add routing nodes
        workflow.add_node("detect_hard_signals", self._detect_hard_signals_node)
        workflow.add_node("parse_intent", self._parse_intent_node)
        workflow.add_node("semantic_routing", self._semantic_routing_node)
        workflow.add_node("combine_decisions", self._combine_decisions_node)
        workflow.add_node("route_to_agent", self._route_to_agent_node)
        
        # Add agent nodes
        workflow.add_node("general_agent", self._general_agent_node)
        workflow.add_node("specific_product_agent", self._specific_product_agent_node)
        workflow.add_node("features_product_agent", self._features_product_agent_node)
        workflow.add_node("finalize", self._finalize_node)
        
        # Add edges
        workflow.set_entry_point("detect_hard_signals")
        
        # Conditional routing based on hard signals
        workflow.add_conditional_edges(
            "detect_hard_signals",
            self._route_after_hard_signals,
            {
                "high_confidence": "route_to_agent",
                "need_more_analysis": "parse_intent",
                "finalize": "finalize"
            }
        )
        
        workflow.add_edge("parse_intent", "semantic_routing")
        workflow.add_edge("semantic_routing", "combine_decisions")
        workflow.add_edge("combine_decisions", "route_to_agent")
        
        # Conditional routing to appropriate agent
        workflow.add_conditional_edges(
            "route_to_agent",
            self._decide_agent,
            {
                "GENERAL": "general_agent",
                "SPECIFIC_PRODUCT": "specific_product_agent",
                "PRODUCT_FEATURE": "features_product_agent",
                "EXPLORATION": "general_agent",  # Route exploration to general agent for now
                "OTHER": "finalize"  # For now, other agents just go to finalize
            }
        )
        
        workflow.add_edge("general_agent", "finalize")
        workflow.add_edge("specific_product_agent", "finalize")
        workflow.add_edge("features_product_agent", "finalize")
        workflow.add_edge("finalize", END)
        
        return workflow.compile()
    
    async def route(self, state: RouterState) -> RouterDecision:
        """Main routing method"""
        # Ensure initialization
        if not self._initialized:
            await self.initialize()
        
        # Convert RouterState to graph state
        graph_state: RouterGraphState = {
            "user_query": state.user_query,
            "session_context": state.session_context,
            "turn_count": state.turn_count
        }
        
        # Run the graph
        try:
            result = await self.graph.ainvoke(graph_state)
            
            if result.get("error"):
                print(f"خطا در routing: {result['error']}")
                # Return default decision on error
                return RouterDecision(
                    agent=AgentType.GENERAL,
                    confidence=0.0,
                    reasoning=f"خطا در پردازش - هدایت به دستیار عمومی: {result['error']}"
                )
            
            # Return routing decision (may have been updated by agent)
            return result["routing_decision"]
            
        except Exception as e:
            print(f"خطای غیرمنتظره در routing: {e}")
            return RouterDecision(
                agent=AgentType.GENERAL,
                confidence=0.0,
                reasoning="خطای غیرمنتظره در سیستم - هدایت به دستیار عمومی"
            )
    
    async def process_complete(self, state: RouterState) -> Dict[str, Any]:
        """Complete processing including agent execution"""
        # Run the full graph
        graph_state: RouterGraphState = {
            "user_query": state.user_query,
            "session_context": state.session_context,
            "turn_count": state.turn_count
        }
        
        try:
            result = await self.graph.ainvoke(graph_state)
            
            return {
                "routing_decision": result.get("routing_decision"),
                "final_agent": result.get("final_agent"),
                "final_response": result.get("final_response"),
                "base_random_keys": result.get("base_random_keys"),
                "member_random_keys": result.get("member_random_keys"),
                "general_agent_response": result.get("general_agent_response"),
                "specific_product_response": result.get("specific_product_response"),
                "error": result.get("error")
            }
            
        except Exception as e:
            print(f"خطا در پردازش کامل: {e}")
            return {
                "routing_decision": RouterDecision(
                    agent=AgentType.GENERAL,
                    confidence=0.0,
                    reasoning="خطا در پردازش - هدایت به دستیار عمومی"
                ),
                "final_agent": "GENERAL",
                "final_response": "متأسفم، مشکل فنی رخ داده است. لطفا دوباره تلاش کنید.",
                "error": str(e)
            }
    
    async def _detect_hard_signals_node(self, state: RouterGraphState) -> RouterGraphState:
        """Node for hard signal detection"""
        try:
            user_query = state["user_query"].strip().lower()
            
            # Check for simple commands first
            simple_command_result = self._detect_simple_commands(user_query)
            if simple_command_result:
                state["hard_signal_result"] = simple_command_result
                return state
            
            router_state = RouterState(
                user_query=state["user_query"],
                session_context=state.get("session_context"),
                turn_count=state.get("turn_count", 0)
            )
            
            result = self.hard_signal_detector.detect(router_state)
            state["hard_signal_result"] = {
                "agent": result.agent.value if result.agent else None,
                "confidence": result.confidence,
                "matched_patterns": result.matched_patterns,
                "extracted_data": result.extracted_data
            }
            
        except Exception as e:
            state["error"] = f"خطا در تشخیص سیگنال‌های سخت: {e}"
        
        return state
    
    async def _parse_intent_node(self, state: RouterGraphState) -> RouterGraphState:
        """Node for intent parsing"""
        try:
            router_state = RouterState(
                user_query=state["user_query"],
                session_context=state.get("session_context"),
                turn_count=state.get("turn_count", 0)
            )
            
            intent = await self.intent_parser.parse_intent(router_state)
            state["intent"] = intent
            
        except Exception as e:
            state["error"] = f"خطا در تحلیل intent: {e}"
        
        return state
    
    async def _semantic_routing_node(self, state: RouterGraphState) -> RouterGraphState:
        """Node for semantic routing"""
        try:
            router_state = RouterState(
                user_query=state["user_query"],
                session_context=state.get("session_context"),
                turn_count=state.get("turn_count", 0)
            )
            
            decision = await self.semantic_router.route_by_similarity(router_state)
            state["semantic_scores"] = {
                "agent": decision.agent.value,
                "confidence": decision.confidence,
                "reasoning": decision.reasoning
            }
            
        except Exception as e:
            state["error"] = f"خطا در مسیریابی معنایی: {e}"
        
        return state
    
    async def _combine_decisions_node(self, state: RouterGraphState) -> RouterGraphState:
        """Combine all routing decisions"""
        try:
            # Extract all available information
            hard_signal = state.get("hard_signal_result", {})
            intent = state.get("intent")
            semantic = state.get("semantic_scores", {})
            
            # Weighted decision making
            decisions = []
            
            # Hard signal decision (highest weight)
            if hard_signal.get("agent") is not None and hard_signal.get("confidence", 0) >= 0.6:
                decisions.append({
                    "agent": AgentType(hard_signal["agent"]),
                    "confidence": hard_signal["confidence"],
                    "weight": 0.6,  # Increased weight for hard signals
                    "source": "hard_signal"
                })
            
            # Intent-based decision
            if intent:
                agent = self.intent_parser.map_intent_to_agent(intent)
                decisions.append({
                    "agent": agent,
                    "confidence": intent.confidence,
                    "weight": 0.3,
                    "source": "intent"
                })
            
            # Semantic decision
            if semantic.get("agent") is not None:
                decisions.append({
                    "agent": AgentType(semantic["agent"]),
                    "confidence": semantic["confidence"],
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
                if hard_signal.get("matched_patterns"):
                    reasoning += f"\nالگوهای تطابق: {', '.join(hard_signal['matched_patterns'])}"
                
                # Handle turn budget
                force_conclusion = state.get("turn_count", 0) >= self.config.force_conclusion_turn
                
                state["routing_decision"] = RouterDecision(
                    agent=final_agent,
                    confidence=final_confidence,
                    reasoning=reasoning,
                    extracted_data=hard_signal.get("extracted_data", {}),
                    force_conclusion=force_conclusion
                )
            else:
                # No decisions available, default to general agent
                state["routing_decision"] = RouterDecision(
                    agent=AgentType.GENERAL,
                    confidence=0.0,
                    reasoning="هیچ تصمیمی در دسترس نیست، به دستیار عمومی می‌روم"
                )
            
        except Exception as e:
            state["error"] = f"خطا در ترکیب تصمیمات: {e}"
        
        return state
    
    async def _finalize_node(self, state: RouterGraphState) -> RouterGraphState:
        """Finalize routing decision"""
        # Handle simple commands first - these take priority
        if state.get("hard_signal_result"):
            hard_signal = state["hard_signal_result"]
            if hard_signal.get("confidence", 0) >= 0.8:
                # Handle simple commands directly
                if hard_signal.get("simple_response") is not None:
                    # For ping command, return the simple response
                    state["final_response"] = hard_signal["simple_response"]
                    state["final_agent"] = "GENERAL"
                    return state
                elif hard_signal.get("base_random_keys") or hard_signal.get("member_random_keys"):
                    # For random key commands, set message to None and store the keys
                    state["final_response"] = None
                    if hard_signal.get("base_random_keys"):
                        state["base_random_keys"] = hard_signal["base_random_keys"]
                    if hard_signal.get("member_random_keys"):
                        state["member_random_keys"] = hard_signal["member_random_keys"]
                    state["final_agent"] = "GENERAL"
                    return state
        
        # If we got here from hard signals with high confidence but not simple commands
        if not state.get("routing_decision") and state.get("hard_signal_result"):
            hard_signal = state["hard_signal_result"]
            if hard_signal.get("agent") is not None and hard_signal.get("confidence", 0) > 0.8:
                # Create RouterDecision for other hard signals
                state["routing_decision"] = RouterDecision(
                    agent=AgentType(hard_signal["agent"]),
                    confidence=hard_signal["confidence"],
                    reasoning=f"تشخیص قطعی بر اساس الگوهای مشخص: {', '.join(hard_signal.get('matched_patterns', []))}",
                    extracted_data=hard_signal.get("extracted_data", {})
                )
        
        # Ensure we have a routing decision
        if not state.get("routing_decision"):
            state["routing_decision"] = RouterDecision(
                agent=AgentType.GENERAL,
                confidence=0.0,
                reasoning="تصمیم پیش‌فرض - دستیار عمومی"
            )
        
        # Set final agent for easy access
        if state.get("routing_decision"):
            state["final_agent"] = state["routing_decision"].agent.name
        
        return state
    
    async def _route_to_agent_node(self, state: RouterGraphState) -> RouterGraphState:
        """Node to prepare for agent routing"""
        # This node ensures we have a routing decision before proceeding to agents
        if not state.get("routing_decision"):
            # This shouldn't happen, but as a fallback
            state["routing_decision"] = RouterDecision(
                agent=AgentType.GENERAL,
                confidence=0.0,
                reasoning="پیش‌فرض: هدایت به دستیار عمومی"
            )
        
        # Set final agent for easier access
        state["final_agent"] = state["routing_decision"].agent.name
        
        return state
    
    def _decide_agent(self, state: RouterGraphState) -> str:
        """Decide which agent to route to based on routing decision"""
        routing_decision = state.get("routing_decision")
        
        if not routing_decision:
            return "OTHER"
        
        agent_type = routing_decision.agent
        
        # Debug logging
        print(f"🎯 Routing decision: {agent_type.name} with confidence {routing_decision.confidence:.2f}")

        # Route to appropriate agent
        if agent_type == AgentType.GENERAL:
            return "GENERAL"
        elif agent_type == AgentType.SPECIFIC_PRODUCT:
            return "SPECIFIC_PRODUCT"
        elif agent_type == AgentType.PRODUCT_FEATURE:
            return "PRODUCT_FEATURE"
        elif agent_type == AgentType.EXPLORATION:
            # Route EXPLORATION to GENERAL agent for now since EXPLORATION agent is not implemented
            print("🔄 EXPLORATION -> GENERAL (EXPLORATION agent not implemented)")
            return "GENERAL"
        else:
            # For now, all other agents go to general agent as fallback
            print(f"🔄 {agent_type.name} -> GENERAL (agent not implemented)")
            return "GENERAL"

    async def _general_agent_node(self, state: RouterGraphState) -> RouterGraphState:
        """Node for General Agent (Agent 0)"""
        try:
            query = state["user_query"]
            session_context = state.get("session_context", {})
            turn_count = state.get("turn_count", 0)
            
            # Prepare context for the general agent
            routing_decision = state.get("routing_decision")
            routing_confidence = 0.0
            if routing_decision and hasattr(routing_decision, 'confidence'):
                routing_confidence = routing_decision.confidence
            
            context = {
                "turn_count": turn_count,
                "previous_interactions": session_context.get("previous_interactions", []),
                "routing_confidence": routing_confidence
            }
            
            # Process the query with General Agent
            agent_response = await self.general_agent.process_query(query, context)
            
            # Store the response
            state["general_agent_response"] = {
                "answer": agent_response.answer,
                "confidence": agent_response.confidence,
                "handoff_needed": agent_response.handoff_needed,
                "handoff_agent": agent_response.handoff_agent,
                "reasoning": agent_response.reasoning
            }
            
            # Set final response
            state["final_response"] = agent_response.answer
            
            # If handoff is needed, we might need to update routing decision
            if agent_response.handoff_needed and agent_response.handoff_agent:
                # Create new routing decision for handoff
                handoff_agent_map = {
                    "EXPLORATION": AgentType.EXPLORATION,
                    "SPECIFIC_PRODUCT": AgentType.SPECIFIC_PRODUCT,
                    "PRODUCT_FEATURE": AgentType.PRODUCT_FEATURE,
                    "SELLER_INFO": AgentType.SELLER_INFO,
                    "COMPARISON": AgentType.COMPARISON
                }
                
                if agent_response.handoff_agent in handoff_agent_map:
                    state["routing_decision"] = RouterDecision(
                        agent=handoff_agent_map[agent_response.handoff_agent],
                        confidence=0.8,
                        reasoning=f"هدایت از طریق Agent عمومی: {agent_response.reasoning}",
                        force_conclusion=False
                    )
            
        except Exception as e:
            state["error"] = f"خطا در Agent عمومی: {e}"
            state["final_response"] = """متأسفم، مشکل فنی رخ داده است. لطفا دوباره تلاش کنید.
            
برای کمک بیشتر با پشتیبانی تماس بگیرید:
تلفن: 021-91000000"""
        
        return state
    
    async def _specific_product_agent_node(self, state: RouterGraphState) -> RouterGraphState:
        """Node for Specific Product Agent (Agent 1)"""
        try:
            query = state["user_query"]
            session_context = state.get("session_context", {})
            turn_count = state.get("turn_count", 0)
            
            # Prepare context for the specific product agent
            routing_decision = state.get("routing_decision")
            routing_confidence = 0.0
            if routing_decision and hasattr(routing_decision, 'confidence'):
                routing_confidence = routing_decision.confidence
            
            context = {
                "turn_count": turn_count,
                "previous_interactions": session_context.get("previous_interactions", []),
                "routing_confidence": routing_confidence
            }
            
            # Process the query with Specific Product Agent
            agent_result = await self.specific_product_agent.process_query(query, context)
            
            # Handle None result
            if agent_result is None:
                state["error"] = "خطا در Agent محصول خاص: نتیجه None برگردانده شد"
                state["specific_product_response"] = {
                    "found": False,
                    "random_key": None,
                    "product_name": None,
                    "search_method": None,
                    "error": "Agent نتیجه‌ای برنگرداند"
                }
                state["final_response"] = "متأسفم، مشکل فنی در یافتن محصول رخ داده است. لطفا دوباره تلاش کنید."
                return state

            # Validate result object has required attributes
            if not hasattr(agent_result, 'found'):
                state["error"] = f"خطا در Agent محصول خاص: نتیجه نامعتبر - نوع: {type(agent_result)}"
                state["specific_product_response"] = {
                    "found": False,
                    "random_key": None,
                    "product_name": None,
                    "search_method": None,
                    "error": "نتیجه نامعتبر از Agent"
                }
                state["final_response"] = "متأسفم، مشکل فنی در یافتن محصول رخ داده است. لطفا دوباره تلاش کنید."
                return state

            # Store the response safely
            state["specific_product_response"] = {
                "found": getattr(agent_result, 'found', False),
                "random_key": getattr(agent_result, 'random_key', None),
                "product_name": getattr(agent_result, 'product_name', None),
                "search_method": getattr(agent_result, 'search_method', None),
                "error": getattr(agent_result, 'error', None)
            }
            
            # Set final response - only return random_key as requested
            if getattr(agent_result, 'found', False):
                state["final_response"] = getattr(agent_result, 'random_key', 'کلید محصول یافت نشد')
            else:
                error_msg = getattr(agent_result, 'error', '')
                state["final_response"] = f"متأسفم، محصول مورد نظر شما یافت نشد. {error_msg}"

        except Exception as e:
            state["error"] = f"خطا در Agent محصول خاص: {str(e)}"
            state["specific_product_response"] = {
                "found": False,
                "random_key": None,
                "product_name": None,
                "search_method": None,
                "error": str(e)
            }
            state["final_response"] = "متأسفم، مشکل فنی در یافتن محصول رخ داده است. لطفا دوباره تلاش کنید."
        
        return state
    
    async def _features_product_agent_node(self, state: RouterGraphState) -> RouterGraphState:
        """Node for Features Product Agent (Agent 2)"""
        try:
            query = state["user_query"]
            session_context = state.get("session_context", {})
            turn_count = state.get("turn_count", 0)
            
            # Prepare context for the features product agent
            routing_decision = state.get("routing_decision")
            routing_confidence = 0.0
            if routing_decision and hasattr(routing_decision, 'confidence'):
                routing_confidence = routing_decision.confidence
            
            context = {
                "turn_count": turn_count,
                "previous_interactions": session_context.get("previous_interactions", []),
                "routing_confidence": routing_confidence
            }
            
            # Process the query with Features Product Agent
            agent_result = await self.features_product_agent.process_query(query, context)
            
            # Handle None result
            if agent_result is None:
                state["error"] = "خطا در Agent ویژگی‌های محصول: نتیجه None برگردانده شد"
                state["features_product_response"] = {
                    "found": False,
                    "product_name": None,
                    "random_key": None,
                    "features": None,
                    "formatted_features": None,
                    "error": "Agent نتیجه‌ای برنگرداند"
                }
                state["final_response"] = "متأسفم، مشکل فنی در دریافت ویژگی‌های محصول رخ داده است. لطفا دوباره تلاش کنید."
                return state

            # Validate result object has required attributes
            if not hasattr(agent_result, 'found'):
                state["error"] = f"خطا در Agent ویژگی‌های محصول: نتیجه نامعتبر - نوع: {type(agent_result)}"
                state["features_product_response"] = {
                    "found": False,
                    "product_name": None,
                    "random_key": None,
                    "features": None,
                    "formatted_features": None,
                    "error": "نتیجه نامعتبر از Agent"
                }
                state["final_response"] = "متأسفم، مشکل فنی در دریافت ویژگی‌های محصول رخ داده است. لطفا دوباره تلاش کنید."
                return state

            # Store the response safely
            state["features_product_response"] = {
                "found": getattr(agent_result, 'found', False),
                "product_name": getattr(agent_result, 'product_name', None),
                "random_key": getattr(agent_result, 'random_key', None),
                "features": getattr(agent_result, 'features', None),
                "formatted_features": getattr(agent_result, 'formatted_features', None),
                "error": getattr(agent_result, 'error', None)
            }
            
            # Set final response - return formatted features
            if getattr(agent_result, 'found', False):
                formatted_features = getattr(agent_result, 'formatted_features', None)
                if formatted_features:
                    state["final_response"] = formatted_features
                else:
                    state["final_response"] = "ویژگی‌های محصول یافت شد اما فرمت‌بندی نشد."
            else:
                error_msg = getattr(agent_result, 'error', '')
                state["final_response"] = f"متأسفم، ویژگی‌های محصول مورد نظر شما یافت نشد. {error_msg}"

        except Exception as e:
            state["error"] = f"خطا در Agent ویژگی‌های محصول: {str(e)}"
            state["features_product_response"] = {
                "found": False,
                "product_name": None,
                "random_key": None,
                "features": None,
                "formatted_features": None,
                "error": str(e)
            }
            state["final_response"] = "متأسفم، مشکل فنی در دریافت ویژگی‌های محصول رخ داده است. لطفا دوباره تلاش کنید."
        
        return state
    
    def _detect_simple_commands(self, query: str) -> Optional[Dict[str, Any]]:
        """Detect simple commands that don't need complex routing"""
        query = query.strip().lower()
        
        # Ping command
        if query == "ping":
            return {
                "agent": "GENERAL",
                "confidence": 1.0,
                "matched_patterns": ["ping_command"],
                "extracted_data": {"command": "ping"},
                "simple_response": "pong"
            }
        
        # Return base random key command
        if query.startswith("return base random key:"):
            key = query.replace("return base random key:", "").strip()
            if key:
                return {
                    "agent": "GENERAL", 
                    "confidence": 1.0,
                    "matched_patterns": ["return_base_key"],
                    "extracted_data": {"command": "return_base_key", "key": key},
                    "base_random_keys": [key],
                    "simple_response": None  # No message, just keys
                }
        
        # Return member random key command
        if query.startswith("return member random key:"):
            key = query.replace("return member random key:", "").strip()
            if key:
                return {
                    "agent": "GENERAL",
                    "confidence": 1.0, 
                    "matched_patterns": ["return_member_key"],
                    "extracted_data": {"command": "return_member_key", "key": key},
                    "member_random_keys": [key],
                    "simple_response": None  # No message, just keys
                }
        
        # Combined command - return both base and member keys
        if "return base random key:" in query and "return member random key:" in query:
            base_key = None
            member_key = None
            
            # Extract base key
            base_match = query.split("return base random key:")[1].split("return member random key:")[0].strip()
            if base_match:
                base_key = base_match
            
            # Extract member key  
            member_match = query.split("return member random key:")[1].strip()
            if member_match:
                member_key = member_match
            
            if base_key or member_key:
                return {
                    "agent": "GENERAL",
                    "confidence": 1.0,
                    "matched_patterns": ["return_combined_keys"],
                    "extracted_data": {"command": "return_combined_keys", "base_key": base_key, "member_key": member_key},
                    "base_random_keys": [base_key] if base_key else None,
                    "member_random_keys": [member_key] if member_key else None,
                    "simple_response": None  # No message, just keys
                }
        
        return None

    def _route_after_hard_signals(self, state: RouterGraphState) -> str:
        """Decide whether to continue analysis after hard signals"""
        hard_signal = state.get("hard_signal_result", {})
        
        # If we have high confidence hard signal, go directly to route_to_agent
        if hard_signal.get("confidence", 0) >= 0.8 and hard_signal.get("agent") is not None:
            # For simple commands, go directly to finalize instead of routing to agent
            if (hard_signal.get("simple_response") is not None or 
                hard_signal.get("base_random_keys") or 
                hard_signal.get("member_random_keys")):
                return "finalize"
            return "high_confidence"
        
        # Otherwise, continue with more analysis
        return "need_more_analysis"
    
    async def get_routing_explanation(self, query: str) -> Dict[str, Any]:
        """Get detailed explanation of routing decision"""
        state = RouterState(user_query=query)
        
        # Run all components
        hard_signal = self.hard_signal_detector.detect(state)
        intent = await self.intent_parser.parse_intent(state)
        semantic_decision = await self.semantic_router.route_by_similarity(state)
        
        # Get similar exemplars for each agent
        exemplar_similarities = {}
        for agent in AgentType:
            similar = await self.semantic_router.get_similar_exemplars(query, agent, top_k=2)
            if similar:
                exemplar_similarities[agent.name] = similar
        
        return {
            "query": query,
            "hard_signals": {
                "detected": hard_signal.agent.name if hard_signal.agent else None,
                "confidence": hard_signal.confidence,
                "patterns": hard_signal.matched_patterns,
                "extracted": hard_signal.extracted_data
            },
            "intent": {
                "type": intent.intent,
                "confidence": intent.confidence,
                "entities": {
                    "base_ids": intent.base_ids,
                    "product_codes": intent.product_codes,
                    "brand": intent.brand,
                    "category": intent.category
                }
            },
            "semantic": {
                "best_agent": semantic_decision.agent.name,
                "confidence": semantic_decision.confidence,
                "similar_exemplars": exemplar_similarities
            }
        }
