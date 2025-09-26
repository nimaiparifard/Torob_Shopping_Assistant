from agents.exploration_agent import ExplorationAgent
from agents.general_agent import GeneralAgent
from agents.shop_agent import ShoppingAgent
from agents.comparison_agent import ComparisonAgent
from agents.specific_product_agent import SpecificProductAgent
from agents.feature_product_agents import FeatureProductAgent
import os
import json
import sqlite3
from openai import AsyncOpenAI
from langchain.prompts import PromptTemplate

from db.base import DatabaseBaseLoader
from response_format import Response
import dotenv
from agents.image_agent import ImageAgent
from agents.product_image_agent import ProductImageAgent
from system_prompts.router_scenario_type import router_scenario_system_prompt, router_scenario_type_samples
from system_prompts.route_image_task_system_prompt import route_image_task_system_prompt, route_image_task_samples
dotenv.load_dotenv()

class Router:
    def __init__(self, db_path: str | None = None, embedding_similarity=None):
        self.db_path = db_path or os.getenv("PRODUCTS_DB_PATH") or "products.db"
        self._conn = None
        self.client = AsyncOpenAI(
            api_key=os.getenv("OPENAI_API_KEY"),
            base_url=os.getenv("OPENAI_URL"),
        )
        from db.base import DatabaseBaseLoader
        self.db = DatabaseBaseLoader()
    
    def close(self):
        """Close database connection and cleanup resources"""
        if self.db:
            self.db.close()
            self.db = None

    async def _scenario_task(self, query: str) -> str:
        """
        Determine the scenario type for a given query using LLM.
        Returns one of: 'general', 'exploration', 'specific_product', 'feature_product', 'shop', 'comparison'
        """
        try:
            # Prepare few-shot examples for the LLM
            examples_text = ""
            for sample in router_scenario_type_samples[:10]:  # Use first 10 examples
                examples_text += f"Input: {sample['input']}\nOutput: {{\"scenario_type\": \"{sample['scenario_type']}\"}}\n\n"
            
            # Create the prompt
            prompt = f"{router_scenario_system_prompt}\n\nExamples:\n{examples_text}\n\nInput: {query}\nOutput:"
            
            # Call OpenAI API
            response = await self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are a scenario classifier. Always respond with valid JSON only."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=50
            )
            
            # Parse the response
            response_text = response.choices[0].message.content.strip()
            
            # Try to extract JSON from the response
            try:
                result = json.loads(response_text)
                scenario_type = result.get("scenario_type", "general")
                
                # Validate scenario type
                valid_types = ["general", "exploration", "specific_product", "feature_product", "shop", "comparison"]
                if scenario_type not in valid_types:
                    return "general"
                
                return scenario_type
                
            except json.JSONDecodeError:
                # If JSON parsing fails, try to extract scenario type from text
                for valid_type in ["general", "exploration", "specific_product", "feature_product", "shop", "comparison"]:
                    if valid_type in response_text.lower():
                        return valid_type
                
                return "general"
                
        except Exception as e:
            print(f"Error in _scenario_task: {e}")
            return "general"

    def _does_have_any_open_exploration_chat_with_this_id(self, chat_id: str) -> bool:
        """
        Check if this chat_id exists in exploration table and count <= 5.
        Returns True if exploration chat exists and count <= 5, False otherwise.
        """
        try:
            db = DatabaseBaseLoader()
            
            # Check if chat_id exists in exploration table
            result = db.query("SELECT counts FROM exploration WHERE chat_id = ?", (chat_id,))
            db.close()
            if result is None:
                return False  # No exploration chat found
            
            count = result[0]['counts']
            return count <= 5 if count is not None else False
            
        except Exception as e:
            print(f"Error in _does_have_any_open_exploration_chat_with_this_id: {e}")
            return False

    async def _route_image_task(self, query: str) -> str:
        """
        Determine the image task type for a given query using LLM.
        Returns one of: 'find_main_object', 'find_base_product_and_main_object'
        """
        try:
            # Prepare few-shot examples for the LLM
            examples_text = ""
            for sample in route_image_task_samples[:10]:  # Use first 10 examples
                examples_text += f"Input: {sample['input']}\nOutput: {sample['output']}\n\n"
            
            # Create the prompt
            prompt = f"{route_image_task_system_prompt}\n\nExamples:\n{examples_text}\n\nInput: {query}\nOutput:"
            
            # Call OpenAI API
            response = await self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are an image task classifier. Always respond with one of the valid task types only."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=50
            )
            
            # Parse the response
            response_text = response.choices[0].message.content.strip()
            
            # Validate task type
            valid_types = ["find_main_object", "find_base_product_and_main_object"]
            if response_text in valid_types:
                return response_text
            
            # If response doesn't match exactly, try to find a valid type in the response
            for valid_type in valid_types:
                if valid_type in response_text.lower():
                    return valid_type
            
            # Default to find_main_object if no valid type found
            return "find_main_object"
                
        except Exception as e:
            print(f"Error in _route_image_task: {e}")
            return "find_main_object"

    async def route(self, chat_id: str, query: str, image_query: str) -> Response:
        # Create another PromptTemplate for FeatureProductAgent (if needed)
        feature_prompt_template = PromptTemplate(
            input_variables=["query"],
            template="از متن زیر نام محصول و ویژگی‌های خواسته‌شده را استخراج کن و فقط خروجی را به صورت JSON زیر بده:\n{\"product_name\": ..., \"features\": [...]}\nمتن: {{ query }}",
            template_format="jinja2"
        )
        if image_query:
            image_task = await self._route_image_task(query)
            print("image_task:",  image_task)
            if image_task == "find_main_object":
                image_agent = ImageAgent()
                res =  await image_agent.identify_main_object(image_query)
            elif image_task == "find_base_product_and_main_object":
                product_image_agent = ProductImageAgent()
                res =  await product_image_agent.process_query(query, image_query)
            return res
        else:
            does_have_any_open_exploration_chat_with_this_id = self._does_have_any_open_exploration_chat_with_this_id(chat_id)
            scenario_type = await self._scenario_task(query)
            res = Response(message="", base_random_keys=[], member_random_keys=[])
            print(f"scenario_type: {scenario_type} \n for query: {query}")
            if scenario_type == "exploration" or does_have_any_open_exploration_chat_with_this_id:
                exploration_agent = ExplorationAgent(feature_prompt_template)
                res = await exploration_agent.process_query(query, chat_id)
            elif scenario_type == "general":
                config = {
                 "OPENAI_API_KEY": os.getenv("OPENAI_API_KEY"),
                "OPENAI_URL": os.getenv("OPENAI_URL"),
                 "MODEL": os.getenv("MODEL", "gpt-4o-mini")
                }
                general_agent = GeneralAgent(config)
                res =  await general_agent.process_query(query)
            elif scenario_type == "shop":
                shopping_agent = ShoppingAgent()
                return await shopping_agent.process_query(query)
            elif scenario_type == "comparison":
                comparison_agent = ComparisonAgent(feature_prompt_template)
                res = await comparison_agent.process_query(query)
            elif scenario_type == "specific_product":
                specific_product_agent = SpecificProductAgent()
                res =  await specific_product_agent.process_query(query)
            elif scenario_type == "feature_product":
                feature_product_agent = FeatureProductAgent(feature_prompt_template)
                res = await feature_product_agent.process_query(query)
            else:
                res = Response(message="متأسفم، نتوانستم محصولات را برای مقایسه پیدا کنم.", base_random_keys=[], member_random_keys=[])
            return res

async def main():
    router = Router()
    prompts = [
        "آیا محصول باکس 60لیتری سایز همه مدل سایز - نارنجی / ۱۰اینچ به صورت نو موجود است یا دست دوم؟",
        # " متوسط قیمت پکیج دیواری لورچ مدل آدنا ظرفیت ۳۲ هزار چقدر است؟",
    #         "سلام! من به دنبال یک دستگاه بخور و رطوبت ساز هستم. می‌خواهم از آن برای بهبود کیفیت هوای خانه‌ام استفاده کنم. آیا می‌توانید به من کمک کنید تا یک فروشنده مناسب پیدا کنم؟",

            # "کدامیک از محصولات 'دراور فایل کمدی پلاستیکی طرح کودک' با شناسه \"ebolgl\" و 'دراور هوم کت ۴ طبقه بزرگ طرح دار از پلاستیک' با شناسه \"nihvhq\" در فروشگاه‌های بیشتری موجود است و آسان‌تر می‌توان آن را خرید؟",
            #    "ping",
            #    "return base random key: abc123",
            #    "درخواست محصول فلاور بگ شامل رز سفید، آفتابگردان، عروس و ورونیکا.",
            #    "وضوح تلویزیون ال جی مدل UT80006 سایز ۵۰ اینچ Ultra HD 4K LED به من بگو",
            #    "این ست کابینت و روشویی دلفین مدل ZN-R13-W-6040 به همراه آینه و باکس در چند فروشگاه موجود است؟",
            #     "ویژگی مبرد کولر گازی پاکشوما مدل MPF 18CH با ظرفیت ۱۸ هزار چیست؟"
        ]
    for prompt in prompts:
        response = await router.route("1ghhh21", prompt, "")
        print(response)
    # image_prompt = "شیء و مفهوم اصلی در تصویر چیست؟"
    # image_url = "https://image.torob.com/base/images/7i/p6/7ip6Yt4qrJWb_ra8.jpg"
    # response = await router.route("b", image_prompt, image_url)
    # print(response)


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
