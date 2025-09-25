import asyncio
import json
import os
from typing import Dict, Any
from langchain.prompts import PromptTemplate
from response_format import Response
import dotenv
from agents.specific_product_agent import SpecificProductAgent
from system_prompts.shop_system_prompts import route_task_shop_system_prompt, route_task_shop_samples
dotenv.load_dotenv()


class ShoppingAgent(SpecificProductAgent):
    def __init__(self, db_path: str | None = None):
        super().__init__(db_path)

    async def _route_shop_agent_task(self, query: str) -> Dict[str, Any]:
        """
        در این تابع LLM نوع وظیفه‌ای که کاربر از فروشگاه‌ها می‌خواهد را تشخیص می‌دهد:
        وظایف:
            - یافتن فروشگاه خاص یا مرکز خرید
            - یافتن میانگین قیمت یک محصول
            - یافتن حداکثر قیمت یک محصول
            - یافتن حداقل قیمت یک محصول
            - شمارش تعداد فروشگاه‌هایی که محصول را دارند
            - یافتن محدوده قیمت محصول
            - لیست فروشگاه‌های دارای محصول
        """
        if not query or not query.strip():
            return {
                "task_type": "general",
                "product_name": "نامشخص",
                "shop_name": None,
                "location": None,
                "has_warranty": None
            }

        try:
            # استفاده از نمونه‌ها برای few-shot learning
            few_shot_examples = "\n".join([
                f"ورودی: {sample['input']}\nخروجی: {json.dumps(sample, ensure_ascii=False, separators=(',', ':'))}"
                for sample in route_task_shop_samples[:3]  # استفاده از 3 نمونه اول
            ])
            
            user_content = f"{few_shot_examples}\n\nورودی: {query}\nخروجی:"
            
            model_name = os.getenv("OPENAI_MODEL") or os.getenv("CHAT_MODEL") or "gpt-4o-mini"
            
            resp = await self.client.chat.completions.create(
                model=model_name,
                messages=[
                    {"role": "system", "content": route_task_shop_system_prompt},
                    {"role": "user", "content": user_content}
                ],
                temperature=0
            )
            
            response_text = (resp.choices[0].message.content or "").strip()
            
            # تلاش برای پارس کردن JSON
            try:
                result = json.loads(response_text)
                # اعتبارسنجی ساختار مورد انتظار
                if all(key in result for key in ["task_type", "product_name", "shop_name", "location", "has_warranty"]):
                    return result
            except json.JSONDecodeError:
                pass
            
            # در صورت خطا در پارس، تلاش برای استخراج JSON از متن
            import re
            json_match = re.search(r'\{[^}]*\}', response_text)
            if json_match:
                try:
                    result = json.loads(json_match.group())
                    if all(key in result for key in ["task_type", "product_name", "shop_name", "location", "has_warranty"]):
                        return result
                except json.JSONDecodeError:
                    pass
            
        except Exception as e:
            print(f"Error in _route_shop_agent_task: {e}")
        
        # در صورت خطا، بازگشت به حالت پیش‌فرض
        return {
            "task_type": "general",
            "product_name": "نامشخص",
            "shop_name": None,
            "location": None,
            "has_warranty": None
        }
    def _get_city_id(self, city_name: str) -> int | None:
        """
            query to city table to find city_id by city_name
            if city_name is not found return None
        """
        try:
            result = self.db.query(
                "SELECT id FROM cities WHERE name = ? LIMIT 1",
                (city_name,)
            )
            if result:
                return result[0]["id"]
            return None
        except Exception as e:
            print(f"Error in _get_city_id: {e}")
            return None

    def _find_mean_price(self, product_random_key, city_id, has_warranty=None):
        """
            query to member table to find mean price of product in specific city or all cities
            if city_id is existed you join with shop table to filter by city_id
            if has_warranty is specified, filter by warranty status
        """
        try:
            if city_id and has_warranty is not None:
                # Query with city and warranty filter
                result = self.db.query(
                    "SELECT AVG(m.price) as mean_price FROM members m "
                    "JOIN shops s ON m.shop_id = s.id "
                    "WHERE m.base_random_key = ? AND s.city_id = ? AND s.has_warranty = ?",
                    (product_random_key, city_id, 1 if has_warranty else 0)
                )
            elif city_id:
                # Query with city filter only
                result = self.db.query(
                    "SELECT AVG(m.price) as mean_price FROM members m "
                    "JOIN shops s ON m.shop_id = s.id "
                    "WHERE m.base_random_key = ? AND s.city_id = ?",
                    (product_random_key, city_id)
                )
            elif has_warranty is not None:
                # Query with warranty filter only
                result = self.db.query(
                    "SELECT AVG(m.price) as mean_price FROM members m "
                    "JOIN shops s ON m.shop_id = s.id "
                    "WHERE m.base_random_key = ? AND s.has_warranty = ?",
                    (product_random_key, 1 if has_warranty else 0)
                )
            else:
                # Query without any filter - all cities and all warranty statuses
                result = self.db.query(
                    "SELECT AVG(price) as mean_price FROM members "
                    "WHERE base_random_key = ?",
                    (product_random_key,)
                )
            
            if result and result[0]["mean_price"] is not None:
                return round(result[0]["mean_price"], 2)
            return None
        except Exception as e:
            print(f"Error in _find_mean_price: {e}")
            return None

    def _find_max_price(self, product_random_key, city_id, has_warranty=None):
        """
            query to member table to find max price of product in specific city or all cities
            if city_id is existed you join with shop table to filter by city_id
            if has_warranty is specified, filter by warranty status
        """
        try:
            if city_id and has_warranty is not None:
                # Query with city and warranty filter
                result = self.db.query(
                    "SELECT MAX(m.price) as max_price FROM members m "
                    "JOIN shops s ON m.shop_id = s.id "
                    "WHERE m.base_random_key = ? AND s.city_id = ? AND s.has_warranty = ?",
                    (product_random_key, city_id, 1 if has_warranty else 0)
                )
            elif city_id:
                # Query with city filter only
                result = self.db.query(
                    "SELECT MAX(m.price) as max_price FROM members m "
                    "JOIN shops s ON m.shop_id = s.id "
                    "WHERE m.base_random_key = ? AND s.city_id = ?",
                    (product_random_key, city_id)
                )
            elif has_warranty is not None:
                # Query with warranty filter only
                result = self.db.query(
                    "SELECT MAX(m.price) as max_price FROM members m "
                    "JOIN shops s ON m.shop_id = s.id "
                    "WHERE m.base_random_key = ? AND s.has_warranty = ?",
                    (product_random_key, 1 if has_warranty else 0)
                )
            else:
                # Query without any filter - all cities and all warranty statuses
                result = self.db.query(
                    "SELECT MAX(price) as max_price FROM members "
                    "WHERE base_random_key = ?",
                    (product_random_key,)
                )
            
            if result and result[0]["max_price"] is not None:
                return result[0]["max_price"]
            return None
        except Exception as e:
            print(f"Error in _find_max_price: {e}")
            return None

    def _find_min_price(self, product_random_key, city_id, has_warranty=None):
        """
            query to member table to find min price of product in specific city or all cities
            if city_id is existed you join with shop table to filter by city_id
            if has_warranty is specified, filter by warranty status
        """
        try:
            if city_id and has_warranty is not None:
                # Query with city and warranty filter
                result = self.db.query(
                    "SELECT MIN(m.price) as min_price FROM members m "
                    "JOIN shops s ON m.shop_id = s.id "
                    "WHERE m.base_random_key = ? AND s.city_id = ? AND s.has_warranty = ?",
                    (product_random_key, city_id, 1 if has_warranty else 0)
                )
            elif city_id:
                # Query with city filter only
                result = self.db.query(
                    "SELECT MIN(m.price) as min_price FROM members m "
                    "JOIN shops s ON m.shop_id = s.id "
                    "WHERE m.base_random_key = ? AND s.city_id = ?",
                    (product_random_key, city_id)
                )
            elif has_warranty is not None:
                # Query with warranty filter only
                result = self.db.query(
                    "SELECT MIN(m.price) as min_price FROM members m "
                    "JOIN shops s ON m.shop_id = s.id "
                    "WHERE m.base_random_key = ? AND s.has_warranty = ?",
                    (product_random_key, 1 if has_warranty else 0)
                )
            else:
                # Query without any filter - all cities and all warranty statuses
                result = self.db.query(
                    "SELECT MIN(price) as min_price FROM members "
                    "WHERE base_random_key = ?",
                    (product_random_key,)
                )
            
            if result and result[0]["min_price"] is not None:
                return result[0]["min_price"]
            return None
        except Exception as e:
            print(f"Error in _find_min_price: {e}")
            return None

    def _find_shop_count(self, product_random_key, city_id, has_warranty=None):
        """
            query to member table to find count of shops that have the product in specific city or all cities
            if city_id is existed you join with shop table to filter by city_id
            if has_warranty is specified, filter by warranty status
        """
        try:
            if city_id and has_warranty is not None:
                # Query with city and warranty filter
                result = self.db.query(
                    "SELECT COUNT(DISTINCT m.shop_id) as shop_count FROM members m "
                    "JOIN shops s ON m.shop_id = s.id "
                    "WHERE m.base_random_key = ? AND s.city_id = ? AND s.has_warranty = ?",
                    (product_random_key, city_id, 1 if has_warranty else 0)
                )
            elif city_id:
                # Query with city filter only
                result = self.db.query(
                    "SELECT COUNT(DISTINCT m.shop_id) as shop_count FROM members m "
                    "JOIN shops s ON m.shop_id = s.id "
                    "WHERE m.base_random_key = ? AND s.city_id = ?",
                    (product_random_key, city_id)
                )
            elif has_warranty is not None:
                # Query with warranty filter only
                result = self.db.query(
                    "SELECT COUNT(DISTINCT m.shop_id) as shop_count FROM members m "
                    "JOIN shops s ON m.shop_id = s.id "
                    "WHERE m.base_random_key = ? AND s.has_warranty = ?",
                    (product_random_key, 1 if has_warranty else 0)
                )
            else:
                # Query without any filter - all cities and all warranty statuses
                result = self.db.query(
                    "SELECT COUNT(DISTINCT shop_id) as shop_count FROM members "
                    "WHERE base_random_key = ?",
                    (product_random_key,)
                )
            
            if result and result[0]["shop_count"] is not None:
                return result[0]["shop_count"]
            return 0
        except Exception as e:
            print(f"Error in _find_shop_count: {e}")
            return 0

    async def process_query(self, query: str) -> Response:
        extarct_prompt_data = await self._route_shop_agent_task(query)
        task_type, product_name, shop_name, location, has_warranty = extarct_prompt_data['task_type'], extarct_prompt_data['product_name'], extarct_prompt_data['shop_name'], extarct_prompt_data['location'], extarct_prompt_data["has_warranty"]
        product_result = await self.search_product(product_name)
        if product_result:
            product_random_key = product_result['random_key'] if product_result else None
            if location:
                city_id = self._get_city_id(location)
            else:
                city_id = None
            if task_type == "mean_price":
                answer = self._find_mean_price(product_random_key, city_id, has_warranty)
                if answer is not None:
                    message = f"{answer:.2f}"
                else:
                    message = "0.00"
            elif task_type == "max_price":
                answer = self._find_max_price(product_random_key,  city_id, has_warranty)
                if answer is not None:
                    message = f"{answer:.2f}"
                else:
                    message = "0.00"
            elif task_type == "min_price":
                answer = self._find_min_price(product_random_key, city_id, has_warranty)
                if answer is not None:
                    message = f"{answer:.2f}"
                else:
                    message = "0.00"
            elif task_type == "shop_count":
                answer = self._find_shop_count(product_random_key, city_id, has_warranty)
                if answer is not None:
                    message = str(answer)
                else:
                    message = "0"
            else:
                message = "0.00"
        else:
            message = "0.00"
        
        return Response(message=message, base_random_keys=[], member_random_keys=[])

import time
async def main():
    prompt_template = PromptTemplate(
        input_variables=["query"],
        template="از متن زیر نام محصول و ویژگی‌های خواسته‌شده را استخراج کن و فقط خروجی را به صورت JSON زیر بده:\n{\"product_name\": ..., \"features\": [...]}\nمتن: {{ query }}",
        template_format="jinja2"
    )

    agent = ShoppingAgent(prompt_template)

    test_queries = [
        "گوشت کوب برقی مولینکس مدل DD65J827 ظرفیت ۳ لیتر چند کاره: چند فروشگاه با ضمانت این محصول را عرضه می‌کنند؟",
        "در محصول تابلو معرق سنگ طبیعی سایز ۱.۶ متر طرح ۹، چند فروشگاه آن را با گارانتی عرضه می‌کنند؟"
    ]

    for query in test_queries:
        start = time.time()
        response = await agent.process_query(query)
        print(f"Query: {query}\nResponse: {response}\n")
        end = time.time()
        print(f"Processing time: {end - start:.2f} seconds\n{'-'*40}")

if __name__ == "__main__":
    asyncio.run(main())
