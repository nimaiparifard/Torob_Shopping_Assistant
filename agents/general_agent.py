"""
Agent 0: General Q&A Agent
Handles everyday and common user questions without database access
"""

from typing import Dict, Any, Optional
from openai import AsyncOpenAI
from dataclasses import dataclass

from router.base import RouterConfig


@dataclass
class GeneralAgentResponse:
    """Response from General Agent"""
    answer: str
    confidence: float = 1.0
    handoff_needed: bool = False
    handoff_agent: Optional[str] = None
    reasoning: str = ""


class GeneralAgent:
    """Agent 0: General Q&A - No database access needed"""
    
    def __init__(self, config: RouterConfig):
        self.config = config
        self.client = AsyncOpenAI(
            api_key=config.openai_api_key,
            base_url=config.openai_base_url
        )
        self.model = config.llm_model
    
    def _create_system_prompt(self) -> str:
        """Create system prompt for general questions"""
        return """شما یک دستیار عمومی هستید که به سوالات مختلف پاسخ می‌دهید.

وظایف شما:
- پاسخ به سوالات عمومی و ساده
- کمک در مواردی که نیاز به راهنمایی دارید
- پاسخ مؤدب و مفید به زبان فارسی

اصول:
1. پاسخ کوتاه و مفید بدهید
2. اگر سوال مشخص نیست، توضیح بخواهید
3. همیشه مؤدب باشید

برای دستورات خاص:
- "ping" → "pong"
- "return base random key: [key]" → کلید را در base_random_keys قرار دهید
- "return member random key: [key]" → کلید را در member_random_keys قرار دهید

هدف: کمک سریع و مؤثر."""
    
    def _create_user_prompt(self, query: str, context: Dict[str, Any]) -> str:
        """Create user prompt with query and context"""
        return f"سوال: {query}"
    
    
    def _should_handoff(self, query: str, response: str) -> tuple[bool, Optional[str], str]:
        """Determine if query should be handed off to another agent"""
        # General agent handles most cases directly now
        # Only handoff for very specific technical cases
        return False, None, "دستیار عمومی پاسخ می‌دهد"
    
    async def process_query(
        self, 
        query: str, 
        context: Optional[Dict[str, Any]] = None
    ) -> GeneralAgentResponse:
        """Process user query and return response"""
        if context is None:
            context = {}
        
        try:
            # Create LLM prompt
            system_prompt = self._create_system_prompt()
            user_prompt = self._create_user_prompt(query, context)
            
            # Call LLM
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.3,
                max_tokens=500
            )
            
            answer = response.choices[0].message.content.strip()
            
            # Check if handoff is needed
            handoff_needed, handoff_agent, reasoning = self._should_handoff(query, answer)
            
            return GeneralAgentResponse(
                answer=answer,
                confidence=0.9,
                handoff_needed=handoff_needed,
                handoff_agent=handoff_agent,
                reasoning=reasoning
            )
            
        except Exception as e:
            print(f"خطا در Agent عمومی: {e}")
            
            # Fallback response
            fallback_answer = "متأسفم، در حال حاضر مشکل فنی دارم. لطفا دوباره تلاش کنید."
            
            return GeneralAgentResponse(
                answer=fallback_answer,
                confidence=0.1,
                handoff_needed=False,
                reasoning="خطا در پردازش"
            )
    
    def get_sample_questions(self) -> list[str]:
        """Get sample questions this agent can handle"""
        return [
            # Simple commands
            "ping",
            "return base random key: f1a4fc11-1188-4bc8-81d1-2d8af2b3793d",
            "return member random key: f2b5fc22-2299-5cd9-92e2-3e9bf3c4804e",
            
            # General questions
            "سلام",
            "کمک میخوام",
            "چطور میتونم کمکتون کنم؟",
            "چه خبر؟",
            "خوبی؟",
            "چیکار می‌کنی؟",
            "کمک می‌خوام",
            "راهنماییم کن"
        ]
