"""
Base classes and types for the router module
"""

from enum import Enum
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from pydantic import BaseModel, Field


class AgentType(Enum):
    """Types of agents in the system"""
    GENERAL = 0  # عامل عمومی برای سوالات روزمره
    SPECIFIC_PRODUCT = 1  # یافتن محصول خاص
    PRODUCT_FEATURE = 2  # ویژگی های محصول
    SELLER_INFO = 3  # اطلاعات فروشندگان
    EXPLORATION = 4  # کاوش و تعامل با کاربر
    COMPARISON = 5  # مقایسه محصولات


class RouterIntent(BaseModel):
    """Extracted intent from user query"""
    intent: str = Field(description="نوع درخواست کاربر")
    base_ids: List[str] = Field(default_factory=list, description="شناسه های محصول پایه")
    product_codes: List[str] = Field(default_factory=list, description="کدهای محصول")
    attributes: List[str] = Field(default_factory=list, description="ویژگی های درخواستی")
    price_inquiry: bool = Field(default=False, description="آیا سوال درباره قیمت است")
    brand: Optional[str] = Field(default=None, description="برند درخواستی")
    category: Optional[str] = Field(default=None, description="دسته بندی محصول")
    confidence: float = Field(default=0.0, description="میزان اطمینان از تشخیص")


class RouterState(BaseModel):
    """State information for routing decision"""
    user_query: str = Field(description="متن درخواست کاربر")
    session_context: Optional[Dict[str, Any]] = Field(default=None, description="اطلاعات جلسه")
    turn_count: int = Field(default=0, description="تعداد دورهای مکالمه")
    previous_agent: Optional[AgentType] = Field(default=None, description="عامل قبلی")
    extracted_intent: Optional[RouterIntent] = Field(default=None, description="اینتنت استخراج شده")


@dataclass
class RouterConfig:
    """Configuration for the router"""
    # OpenAI settings
    openai_api_key: str
    openai_base_url: str = "https://api.openai.com/v1"
    embedding_model: str = "text-embedding-3-small"
    llm_model: str = "gpt-4o-mini"
    
    # Similarity thresholds
    similarity_threshold_low: float = 0.3  # آستانه پایین تشابه
    similarity_threshold_high: float = 0.7  # آستانه بالا تشابه
    
    # K-NN settings
    top_k_exemplars: int = 3  # تعداد نمونه های مشابه برای هر عامل
    
    # Turn budget
    max_turns: int = 5  # حداکثر تعداد دورهای مکالمه
    force_conclusion_turn: int = 4  # در این دور به نتیجه گیری برسیم
    
    # Vector store settings
    use_qdrant: bool = False  # استفاده از Qdrant یا FAISS
    qdrant_url: Optional[str] = None
    qdrant_collection: str = "router_exemplars"


class RouterDecision(BaseModel):
    """Decision made by the router"""
    agent: AgentType = Field(description="عامل انتخاب شده")
    confidence: float = Field(description="میزان اطمینان از تصمیم")
    reasoning: str = Field(description="دلیل انتخاب این عامل")
    extracted_data: Optional[Dict[str, Any]] = Field(default=None, description="داده های استخراج شده")
    force_conclusion: bool = Field(default=False, description="آیا باید به نتیجه برسیم")


class RouterBase:
    """Base class for router components"""
    
    def __init__(self, config: RouterConfig):
        self.config = config
    
    async def route(self, state: RouterState) -> RouterDecision:
        """Route the user query to appropriate agent"""
        raise NotImplementedError("Subclasses must implement route method")
