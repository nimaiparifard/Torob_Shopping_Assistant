"""
State management for router sessions
Handles turn counting and session context
"""

import os
from typing import Dict, Any, Optional, List
from datetime import datetime
from dataclasses import dataclass, field
from dotenv import load_dotenv
from .base import AgentType, RouterDecision

# Load environment variables
load_dotenv()


@dataclass
class TurnInfo:
    """Information about a single turn in conversation"""
    turn_number: int
    timestamp: datetime
    user_query: str
    routing_decision: RouterDecision
    agent_response: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "turn_number": self.turn_number,
            "timestamp": self.timestamp.isoformat(),
            "user_query": self.user_query,
            "agent": self.routing_decision.agent.name,
            "confidence": self.routing_decision.confidence,
            "reasoning": self.routing_decision.reasoning,
            "response": self.agent_response
        }


@dataclass
class SessionState:
    """Manages state for a routing session"""
    session_id: str
    created_at: datetime = field(default_factory=datetime.now)
    turns: List[TurnInfo] = field(default_factory=list)
    context: Dict[str, Any] = field(default_factory=dict)
    max_turns: int = 5
    
    @property
    def turn_count(self) -> int:
        """Get current turn count"""
        return len(self.turns)
    
    @property
    def is_at_turn_limit(self) -> bool:
        """Check if at turn limit"""
        return self.turn_count >= self.max_turns
    
    @property
    def should_force_conclusion(self) -> bool:
        """Check if should force conclusion"""
        return self.turn_count >= self.max_turns - 1
    
    def add_turn(self, query: str, decision: RouterDecision, response: Optional[str] = None):
        """Add a new turn to the session"""
        turn = TurnInfo(
            turn_number=self.turn_count + 1,
            timestamp=datetime.now(),
            user_query=query,
            routing_decision=decision,
            agent_response=response
        )
        self.turns.append(turn)
    
    def get_previous_agents(self) -> List[AgentType]:
        """Get list of agents used in previous turns"""
        return [turn.routing_decision.agent for turn in self.turns]
    
    def get_conversation_history(self) -> List[Dict[str, str]]:
        """Get conversation history for context"""
        history = []
        for turn in self.turns:
            history.append({
                "role": "user",
                "content": turn.user_query
            })
            if turn.agent_response:
                history.append({
                    "role": "assistant",
                    "content": turn.agent_response
                })
        return history
    
    def update_context(self, key: str, value: Any):
        """Update session context"""
        self.context[key] = value
    
    def get_context_for_routing(self) -> Dict[str, Any]:
        """Get context formatted for router"""
        return {
            "session_id": self.session_id,
            "turn_count": self.turn_count,
            "previous_agents": [agent.name for agent in self.get_previous_agents()],
            "conversation_summary": self._get_conversation_summary(),
            **self.context
        }
    
    def _get_conversation_summary(self) -> str:
        """Get summary of conversation so far"""
        if not self.turns:
            return ""
        
        summary_parts = []
        for turn in self.turns[-3:]:  # Last 3 turns
            agent_name = self._get_agent_display_name(turn.routing_decision.agent)
            summary_parts.append(f"سوال: {turn.user_query[:50]}... -> {agent_name}")
        
        return " | ".join(summary_parts)
    
    def _get_agent_display_name(self, agent: AgentType) -> str:
        """Get display name for agent"""
        names = {
            AgentType.GENERAL: "عمومی",
            AgentType.SPECIFIC_PRODUCT: "محصول خاص",
            AgentType.PRODUCT_FEATURE: "ویژگی محصول",
            AgentType.SELLER_INFO: "فروشندگان",
            AgentType.EXPLORATION: "کاوش",
            AgentType.COMPARISON: "مقایسه"
        }
        return names.get(agent, "نامشخص")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert session to dictionary"""
        return {
            "session_id": self.session_id,
            "created_at": self.created_at.isoformat(),
            "turn_count": self.turn_count,
            "max_turns": self.max_turns,
            "turns": [turn.to_dict() for turn in self.turns],
            "context": self.context
        }


class SessionManager:
    """Manages multiple routing sessions"""
    
    def __init__(self, max_turns: Optional[int] = None):
        self.sessions: Dict[str, SessionState] = {}
        self.max_turns = max_turns or int(os.getenv("MAX_TURNS", "5"))
    
    def create_session(self, session_id: str) -> SessionState:
        """Create a new session"""
        session = SessionState(
            session_id=session_id,
            max_turns=self.max_turns
        )
        self.sessions[session_id] = session
        return session
    
    def get_session(self, session_id: str) -> Optional[SessionState]:
        """Get existing session"""
        return self.sessions.get(session_id)
    
    def get_or_create_session(self, session_id: str) -> SessionState:
        """Get existing session or create new one"""
        session = self.get_session(session_id)
        if not session:
            session = self.create_session(session_id)
        return session
    
    def delete_session(self, session_id: str):
        """Delete a session"""
        if session_id in self.sessions:
            del self.sessions[session_id]
    
    def cleanup_old_sessions(self, hours: Optional[int] = None):
        """Clean up sessions older than specified hours"""
        from datetime import timedelta
        
        if hours is None:
            hours = int(os.getenv("SESSION_CLEANUP_HOURS", "24"))
        
        cutoff = datetime.now() - timedelta(hours=hours)
        to_delete = []
        
        for session_id, session in self.sessions.items():
            if session.created_at < cutoff:
                to_delete.append(session_id)
        
        for session_id in to_delete:
            self.delete_session(session_id)
        
        return len(to_delete)
    
    def get_active_sessions_count(self) -> int:
        """Get count of active sessions"""
        return len(self.sessions)
    
    def get_session_stats(self) -> Dict[str, Any]:
        """Get statistics about sessions"""
        if not self.sessions:
            return {
                "total_sessions": 0,
                "avg_turns": 0,
                "max_turns_reached": 0,
                "agent_usage": {}
            }
        
        total_turns = 0
        max_turns_reached = 0
        agent_usage = {agent: 0 for agent in AgentType}
        
        for session in self.sessions.values():
            total_turns += session.turn_count
            if session.is_at_turn_limit:
                max_turns_reached += 1
            
            for turn in session.turns:
                agent_usage[turn.routing_decision.agent] += 1
        
        return {
            "total_sessions": len(self.sessions),
            "avg_turns": total_turns / len(self.sessions) if self.sessions else 0,
            "max_turns_reached": max_turns_reached,
            "agent_usage": {agent.name: count for agent, count in agent_usage.items()}
        }
