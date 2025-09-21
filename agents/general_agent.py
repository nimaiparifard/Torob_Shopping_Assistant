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
        
        # Static knowledge base for common policies and information
        self.static_kb = self._initialize_static_knowledge()
    
    def _initialize_static_knowledge(self) -> Dict[str, str]:
        """Initialize static knowledge base for common questions"""
        return {
            "payment_methods": """روش‌های پرداخت قابل قبول:
            • پرداخت آنلاین با کارت‌های بانکی
            • پرداخت اقساطی (برای خریدهای بالای یک میلیون تومان)
            • پرداخت در محل (تحویل درب منزل)
            • کیف پول دیجیتال
            • انتقال بانکی""",
            
            "return_policy": """قوانین مرجوع کالا:
            • امکان مرجوع تا 7 روز پس از خرید
            • کالا باید در بسته‌بندی اصلی و سالم باشد
            • لوازم الکترونیکی: تا 14 روز
            • پوشاک و کفش: تا 7 روز (در صورت عدم پوشیدن)
            • کالاهای فاسدشدنی قابل مرجوع نیستند""",
            
            "warranty": """ضمانت اصالت کالا:
            • تمام کالاها دارای ضمانت اصالت
            • گارانتی رسمی از شرکت‌های معتبر
            • خدمات پس از فروش در سراسر کشور
            • بازگشت 100% وجه در صورت غیراصل بودن""",
            
            "working_hours": """ساعت کاری پشتیبانی:
            • شنبه تا چهارشنبه: 8 صبح تا 8 شب
            • پنج‌شنبه: 8 صبح تا 6 عصر
            • جمعه: تعطیل
            • پشتیبانی آنلاین 24/7 در دسترس""",
            
            "delivery": """نحوه ارسال و تحویل:
            • ارسال رایگان برای خریدهای بالای 500 هزار تومان
            • تحویل سریع در تهران: 24 ساعته
            • تحویل در سایر شهرها: 2-5 روز کاری
            • امکان انتخاب زمان دلخواه برای تحویل
            • تحویل درب منزل یا دفتر""",
            
            "how_to_shop": """نحوه خرید:
            1. جستجوی محصول مورد نظر
            2. مقایسه قیمت‌ها و انتخاب فروشنده
            3. اضافه کردن به سبد خرید  
            4. تکمیل اطلاعات ارسال
            5. انتخاب روش پرداخت
            6. تأیید نهایی سفارش
            7. پیگیری از طریق پیامک""",
            
            "account_benefits": """مزایای عضویت:
            • دریافت تخفیف‌های ویژه اعضا
            • امتیاز برای هر خرید
            • اولویت در ارسال و تحویل
            • دسترسی به پیشنهادات شخصی‌سازی شده
            • پیگیری آسان سفارشات""",
            
            "contact_info": """راه‌های تماس:
            • تلفن پشتیبانی: 021-91000000
            • ایمیل: support@torob.com  
            • چت آنلاین در سایت
            • شبکه‌های اجتماعی: @torob_official
            • دفتر مرکزی: تهران، خیابان ولیعصر"""
        }
    
    def _create_system_prompt(self) -> str:
        """Create system prompt for general questions"""
        return """شما دستیار خرید هوشمند ترب هستید که به عنوان دستیار عمومی و پیش‌فرض عمل می‌کنید.

شما باید هر نوع سوالی را که کاربر می‌پرسد پاسخ دهید، حتی اگر مشخص نباشد به کدام دسته تعلق دارد.

مسئولیت‌های شما:
- پاسخ به سوالات عمومی درباره قوانین، نحوه خرید، پشتیبانی
- کمک در سوالات غیرمشخص یا ابهام‌آمیز
- راهنمایی کلی برای هر نوع درخواست
- پاسخ مؤدب، واضح و مفید به زبان فارسی

اصول مهم:
1. همیشه سعی کنید پاسخی ارائه دهید، حتی اگر سوال مشخص نباشد
2. اگر سوال مبهم است، سوال توضیحی بپرسید تا بهتر کمک کنید
3. اگر به اطلاعات خاص نیاز دارید، کاربر را راهنمایی کنید
4. همیشه مؤدب و صبور باشید
5. تلاش کنید حداکثر کمک را ارائه دهید

برای سوالات تخصصی:
- محصول خاص: "برای یافتن محصول دقیق، لطفا مدل یا کد محصول را ذکر کنید"
- مقایسه: "برای مقایسه دقیق، نام محصولات مورد نظر را بگویید"
- فروشندگان: "برای اطلاعات فروشندگان، نام محصول یا دسته‌بندی را مشخص کنید"
- جستجو: "می‌توانید محصول مورد نظر و معیارهای انتخاب را توضیح دهید؟"

هدف: ارائه بهترین کمک ممکن در هر شرایطی."""
    
    def _create_user_prompt(self, query: str, context: Dict[str, Any]) -> str:
        """Create user prompt with query and context"""
        prompt = f"سوال کاربر: {query}"
        
        # Add relevant static knowledge if available
        relevant_kb = self._find_relevant_knowledge(query)
        if relevant_kb:
            prompt += f"\n\nاطلاعات مرتبط:\n{relevant_kb}"
        
        # Add context information
        if context.get('turn_count', 0) > 0:
            prompt += f"\n\nاین دور {context['turn_count']} مکالمه است."
        
        if context.get('previous_interactions'):
            prompt += f"\nتعامل قبلی: {context['previous_interactions'][-1]}"
        
        prompt += "\n\nلطفا پاسخ مناسب و کاملی ارائه دهید."
        
        return prompt
    
    def _find_relevant_knowledge(self, query: str) -> str:
        """Find relevant static knowledge based on query keywords"""
        query_lower = query.lower()
        relevant_info = []
        
        # Keywords to knowledge mapping
        knowledge_keywords = {
            "payment_methods": ["پرداخت", "پول", "کارت", "اقساط", "حساب", "payment"],
            "return_policy": ["مرجوع", "برگشت", "عودت", "return", "refund"],
            "warranty": ["ضمانت", "اصالت", "گارانتی", "warranty", "guarantee"],
            "working_hours": ["ساعت", "زمان", "کی", "hours", "time", "پشتیبانی", "support"],
            "delivery": ["ارسال", "تحویل", "delivery", "shipping", "رسیدن"],
            "how_to_shop": ["چطور", "چگونه", "نحوه", "خرید", "how", "shop", "buy"],
            "account_benefits": ["عضویت", "اکانت", "حساب", "مزایا", "benefits", "account"],
            "contact_info": ["تماس", "آدرس", "شماره", "contact", "phone", "email"]
        }
        
        for kb_key, keywords in knowledge_keywords.items():
            if any(keyword in query_lower for keyword in keywords):
                if kb_key in self.static_kb:
                    relevant_info.append(self.static_kb[kb_key])
        
        return "\n\n".join(relevant_info) if relevant_info else ""
    
    def _should_handoff(self, query: str, response: str) -> tuple[bool, Optional[str], str]:
        """Determine if query should be handed off to another agent"""
        query_lower = query.lower()
        
        # Only handoff for very specific and clear cases
        # Since General Agent is now the fallback, be more conservative about handoffs
        
        # Very specific product codes/SKUs
        specific_product_indicators = [
            "کد ", "sku", "model", "مدل ", " کد", "شناسه"
        ]
        
        # Very clear comparison requests
        clear_comparison_indicators = [
            "مقایسه", "تفاوت", "کدوم بهتره", "versus", "در مقابل"
        ]
        
        # Check for very specific product requests with codes
        if any(indicator in query_lower for indicator in specific_product_indicators):
            return True, "SPECIFIC_PRODUCT", "درخواست محصول خاص با کد"
        
        # Check for clear comparison requests with multiple products mentioned
        if any(indicator in query_lower for indicator in clear_comparison_indicators):
            # Check if multiple product names or brands are mentioned
            brands = ["سامسونگ", "آیفون", "اپل", "شیائومی", "ایسوس", "لنوو"]
            mentioned_brands = [brand for brand in brands if brand in query_lower]
            if len(mentioned_brands) >= 2:
                return True, "COMPARISON", "مقایسه چند محصول/برند"
        
        # For now, General Agent handles everything else
        # This makes it truly general and able to help with unclear queries
        return False, None, "دستیار عمومی می‌تواند کمک کند"
    
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
            fallback_answer = """متأسفم، در حال حاضر مشکل فنی دارم. لطفا دوباره سوال کنید یا با پشتیبانی تماس بگیرید.
            
راه‌های تماس:
• تلفن: 021-91000000
• ایمیل: support@torob.com"""
            
            return GeneralAgentResponse(
                answer=fallback_answer,
                confidence=0.1,
                handoff_needed=False,
                reasoning="خطا در پردازش"
            )
    
    def get_sample_questions(self) -> list[str]:
        """Get sample questions this agent can handle"""
        return [
            # Policy and general questions
            "چطور می‌تونم از سایت خرید کنم؟",
            "ساعت کاری پشتیبانی چیه؟",
            "آیا امکان مرجوع کردن کالا وجود دارد؟",
            "نحوه پرداخت چگونه است؟",
            "آیا ضمانت اصالت کالا دارید؟",
            "مزایای عضویت چیست؟",
            "چطور با پشتیبانی تماس بگیرم؟",
            "هزینه ارسال چقدر است؟",
            
            # General/unclear questions that should be handled here
            "سلام خوبی؟",
            "یه چیزی میخوام ولی نمیدونم چی",
            "کمک میخوام",
            "نمیدونم چطور شروع کنم",
            "توضیح بده این سایت چیکار میکنه",
            "راهنماییم کن",
            "احتیاج به کمک دارم",
            "چه خدماتی ارائه میدین؟"
        ]
