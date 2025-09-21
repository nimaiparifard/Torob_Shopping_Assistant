"""
Intent parsing using LLM for structured extraction
Extracts intent, entities, and confidence from user queries
"""

from typing import Optional, Dict, Any, List
from openai import AsyncOpenAI
import json
from .base import RouterConfig, RouterIntent, RouterState, AgentType


class IntentParser:
    """Parses user intent using LLM"""
    
    def __init__(self, config: RouterConfig):
        self.config = config
        self.client = AsyncOpenAI(
            api_key=config.openai_api_key,
            base_url=config.openai_base_url
        )
        self.model = config.llm_model
    
    def _create_system_prompt(self) -> str:
        """Create system prompt for intent extraction"""
        return """شما یک تحلیلگر قصد (intent) برای دستیار خرید هوشمند هستید.
        
وظیفه شما: تحلیل پرس و جوی کاربر و استخراج اطلاعات ساختاریافته

اطلاعات مورد نیاز برای استخراج:
1. intent: قصد اصلی کاربر (یکی از: general_inquiry, find_product, product_feature, seller_info, exploration, comparison)
2. base_ids: شناسه‌های محصول پایه (base) در صورت وجود
3. product_codes: کدهای محصول (SKU, مدل، کد)
4. attributes: ویژگی‌های درخواستی (رنگ، سایز، حافظه و...)
5. price_inquiry: آیا سوال درباره قیمت است؟
6. brand: برند محصول در صورت ذکر
7. category: دسته‌بندی محصول (گوشی، لپ‌تاپ، یخچال و...)
8. confidence: میزان اطمینان از تشخیص (0.0 تا 1.0)

نکات مهم:
- اگر کاربر دو یا چند محصول را برای مقایسه ذکر کرد، intent باید "comparison" باشد
- اگر کاربر محصول خاصی با کد یا مدل دقیق خواست، intent باید "find_product" باشد
- اگر سوال درباره ویژگی یا قیمت محصول خاص است، intent باید "product_feature" باشد
- اگر سوال درباره فروشندگان است، intent باید "seller_info" باشد
- اگر کاربر به دنبال محصولی با معیارهای کلی است، intent باید "exploration" باشد
- سوالات عمومی درباره قوانین، راهنما و... intent باید "general_inquiry" باشد

پاسخ را به صورت JSON با ساختار دقیق زیر ارائه دهید:
{
  "intent": "string (یکی از مقادیر مشخص شده)",
  "base_ids": ["list of strings یا لیست خالی []"],
  "product_codes": ["list of strings یا لیست خالی []"],
  "attributes": ["list of strings یا لیست خالی []"],
  "price_inquiry": true/false,
  "brand": "string یا null",
  "category": "string یا null",
  "confidence": 0.75
}

نکات مهم برای JSON:
- لیست‌ها همیشه باید [] باشند، هرگز null نباشند
- رشته‌ها باید string باشند، نه list
- confidence باید عددی بین 0.0 تا 1.0 باشد"""

    def _create_user_prompt(self, query: str, context: Optional[Dict[str, Any]] = None) -> str:
        """Create user prompt for intent extraction"""
        prompt = f"پرس و جوی کاربر: {query}"
        
        if context:
            if 'previous_intents' in context:
                prompt += f"\n\nقصدهای قبلی در این جلسه: {context['previous_intents']}"
            if 'turn_count' in context:
                prompt += f"\nتعداد دورهای مکالمه تا کنون: {context['turn_count']}"
        
        prompt += "\n\nلطفا قصد کاربر را تحلیل کرده و اطلاعات را به صورت JSON استخراج کنید."
        
        return prompt
    
    async def parse_intent(self, state: RouterState) -> RouterIntent:
        """Parse intent from user query using LLM"""
        try:
            # Prepare context
            context = {}
            if state.session_context:
                context = state.session_context
            context['turn_count'] = state.turn_count
            
            # Call LLM
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self._create_system_prompt()},
                    {"role": "user", "content": self._create_user_prompt(state.user_query, context)}
                ],
                temperature=0.3,  # Lower temperature for more consistent parsing
                response_format={"type": "json_object"}
            )
            
            # Parse response
            content = response.choices[0].message.content
            parsed_data = json.loads(content)
            
            # Clean and validate data before creating RouterIntent
            cleaned_data = self._clean_parsed_data(parsed_data)
            
            # Create RouterIntent from cleaned data
            intent = RouterIntent(**cleaned_data)
            
            # Post-process and validate
            intent = self._post_process_intent(intent, state)
            
            return intent
            
        except Exception as e:
            print(f"خطا در تحلیل intent: {e}")
            # Return default intent on error
            return RouterIntent(
                intent="exploration",
                confidence=0.1
            )
    
    def _clean_parsed_data(self, data: dict) -> dict:
        """Clean and validate parsed data before creating RouterIntent"""
        cleaned = {}
        
        # Handle required string fields
        cleaned['intent'] = str(data.get('intent', 'exploration'))
        
        # Handle list fields - ensure they are lists, not None
        list_fields = ['base_ids', 'product_codes', 'attributes']
        for field in list_fields:
            value = data.get(field)
            if value is None or (isinstance(value, str) and value.lower() in ['none', 'null']):
                cleaned[field] = []
            elif isinstance(value, list):
                cleaned[field] = [str(item) for item in value if item is not None]
            elif isinstance(value, str):
                # Split comma-separated values if it's a string
                cleaned[field] = [item.strip() for item in value.split(',') if item.strip()]
            else:
                cleaned[field] = []
        
        # Handle string fields that might come as lists
        string_fields = ['brand', 'category']
        for field in string_fields:
            value = data.get(field)
            if value is None or (isinstance(value, str) and value.lower() in ['none', 'null', '']):
                cleaned[field] = None
            elif isinstance(value, list):
                # Take the first non-empty element from the list
                non_empty = [str(item).strip() for item in value if item and str(item).strip()]
                cleaned[field] = non_empty[0] if non_empty else None
            elif isinstance(value, str):
                cleaned_value = str(value).strip()
                cleaned[field] = cleaned_value if cleaned_value and cleaned_value.lower() != 'none' else None
            else:
                cleaned[field] = str(value) if value else None
        
        # Handle boolean field
        price_inquiry = data.get('price_inquiry', False)
        if isinstance(price_inquiry, str):
            cleaned['price_inquiry'] = price_inquiry.lower() in ['true', '1', 'yes', 'بله', 'آری']
        else:
            cleaned['price_inquiry'] = bool(price_inquiry)
        
        # Handle confidence
        confidence = data.get('confidence', 0.0)
        try:
            cleaned['confidence'] = float(confidence)
        except (ValueError, TypeError):
            cleaned['confidence'] = 0.0
        
        # Ensure confidence is in valid range
        cleaned['confidence'] = max(0.0, min(1.0, cleaned['confidence']))
        
        return cleaned
    
    def _post_process_intent(self, intent: RouterIntent, state: RouterState) -> RouterIntent:
        """Post-process and validate extracted intent"""
        # Normalize intent values
        intent_map = {
            'general_inquiry': 'general',
            'find_product': 'specific_product',
            'product_feature': 'feature',
            'seller_info': 'seller',
            'exploration': 'explore',
            'comparison': 'compare'
        }
        
        if intent.intent in intent_map:
            intent.intent = intent_map[intent.intent]
        
        # Validate confidence
        if not 0.0 <= intent.confidence <= 1.0:
            intent.confidence = max(0.0, min(1.0, intent.confidence))
        
        # Handle turn budget constraints
        if state.turn_count >= self.config.force_conclusion_turn:
            # If we're near turn limit and intent is exploration, boost confidence
            if intent.intent == 'explore':
                intent.confidence = min(intent.confidence + 0.2, 1.0)
        
        # Lists should already be cleaned, but double-check as safety net
        if intent.base_ids is None:
            intent.base_ids = []
        if intent.product_codes is None:
            intent.product_codes = []
        if intent.attributes is None:
            intent.attributes = []
        
        return intent
    
    async def extract_entities(self, query: str) -> Dict[str, Any]:
        """Extract entities from query for quick access"""
        prompt = f"""از متن زیر موجودیت‌های مربوط به خرید را استخراج کنید:
        
متن: {query}

موجودیت‌های مورد نیاز:
- products: لیست محصولات ذکر شده
- brands: برندهای ذکر شده
- features: ویژگی‌های مورد نظر
- price_range: محدوده قیمتی (اگر ذکر شده)
- use_case: کاربرد محصول

پاسخ را به صورت JSON ارائه دهید."""

        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "شما یک استخراج‌کننده موجودیت برای سیستم خرید هستید."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                response_format={"type": "json_object"}
            )
            
            entities = json.loads(response.choices[0].message.content)
            return entities
            
        except Exception as e:
            print(f"خطا در استخراج موجودیت: {e}")
            return {
                "products": [],
                "brands": [],
                "features": [],
                "price_range": None,
                "use_case": None
            }
    
    def map_intent_to_agent(self, intent: RouterIntent) -> AgentType:
        """Map parsed intent to agent type"""
        intent_agent_map = {
            'general': AgentType.GENERAL,
            'specific_product': AgentType.SPECIFIC_PRODUCT,
            'feature': AgentType.PRODUCT_FEATURE,
            'seller': AgentType.SELLER_INFO,
            'explore': AgentType.EXPLORATION,
            'compare': AgentType.COMPARISON
        }
        
        # Use mapped agent or default to exploration
        return intent_agent_map.get(intent.intent, AgentType.EXPLORATION)
