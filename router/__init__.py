"""
Router module for AI Shopping Assistant
Handles semantic routing of user queries to appropriate agents
"""

from .base import RouterBase, AgentType, RouterConfig, RouterState, RouterDecision, RouterIntent
from .embeddings import EmbeddingService
from .exemplars import AgentExemplars
from .hard_signals import HardSignalDetector
from .intent_parser import IntentParser
from .semantic_router import SemanticRouter
from .simple_router import SimpleMainRouter as MainRouter
from .state_manager import SessionManager
from .config import get_router_config_from_env, validate_config, print_config_summary

__all__ = [
    'RouterBase',
    'AgentType',
    'RouterConfig',
    'RouterState',
    'RouterDecision',
    'RouterIntent',
    'EmbeddingService',
    'AgentExemplars',
    'HardSignalDetector',
    'IntentParser',
    'SemanticRouter',
    'MainRouter',
    'SessionManager',
    'get_router_config_from_env',
    'validate_config',
    'print_config_summary'
]
