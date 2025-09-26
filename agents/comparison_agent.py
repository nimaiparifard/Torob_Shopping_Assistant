import asyncio
import json
import os
from typing import Dict, Any, final
from langchain.prompts import PromptTemplate
from response_format import Response
import dotenv
from embedding.faiss_embedding import EmbeddingServiceWrapper, build_hnsw_from_texts, semantic_search
from agents.specific_product_agent import SpecificProductAgent
from agents.feature_product_agents import FeatureProductAgent
from system_prompts.product_features_system_prompts import system_msg_extracting_product_features, samples_extracting_product_features
from features_list import features_dict
from system_prompts.comparison_system_prompt import *
from system_prompts.comparison_feature_system_prompt import *
from system_prompts.comparison_shop_system_prompt import *
from system_prompts.comparison_final_decide_system_prompt import comparison_final_decide_system_prompt, compare_final_decide_samples
from system_prompts.comparison_find_feature_general import find_main_feature_of_general_comapre_system_prompt, find_main_feature_of_general_comapre_samples
dotenv.load_dotenv()

class ComparisonAgent(FeatureProductAgent):
    def __init__(self, prompt_template: PromptTemplate, db_path: str | None = None):
        # Properly initialize parent so we have self.prompt_template, self.client, etc.
        super().__init__(prompt_template, db_path)

    async def _route_task_type(self, query: str) -> Dict[str, Any]:
        try:
            # Create few-shot examples string
            examples_str = ""
            for sample in route_task_comparison_samples:
                examples_str += f"ورودی: {sample['input']}\n"
                examples_str += f"خروجی: {json.dumps({k: v for k, v in sample.items() if k != 'input'}, ensure_ascii=False)}\n\n"
            
            # Create the full prompt
            full_prompt = f"{route_task_comparison_system_prompt}\n\nمثال‌ها:\n{examples_str}\nورودی: {query}\nخروجی:"
            
            # Call the LLM
            response = await self.client.chat.completions.create(
                model=os.getenv("OPENAI_MODEL") or os.getenv("CHAT_MODEL") or "gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "تو یک مسیریاب هوشمند برای تشخیص نوع مقایسه محصولات هستی."},
                    {"role": "user", "content": full_prompt}
                ]
            )
            
            # Parse the JSON response
            result = json.loads(response.choices[0].message.content)
            
            return result
            
        except json.JSONDecodeError as e:
            # If JSON parsing fails, return a default structure
            return {
                "comparison_type": "general",
                "product_name_1": "نامشخص",
                "product_random_key_1": None,
                "product_name_2": "نامشخص", 
                "product_random_key_2": None
            }
        except Exception as e:
            # Handle any other errors
            return {
                "comparison_type": "general",
                "product_name_1": "نامشخص",
                "product_random_key_1": None,
                "product_name_2": "نامشخص",
                "product_random_key_2": None
            }

    async def _search_compare_feature(self, query, product_random_key_1, product_name_1, product_random_key_2, product_name_2):
        try:
            # Create few-shot examples string
            examples_str = ""
            for sample in comparison_feature_samples:
                examples_str += f"ورودی: {sample['input']}\n"
                examples_str += f"خروجی: {json.dumps({'compare_feature': sample['compare_feature']}, ensure_ascii=False)}\n\n"
            
            # Create the full prompt
            full_prompt = f"{comparison_feature_system_prompt}\n\nمثال‌ها:\n{examples_str}\nورودی: {query}\nخروجی:"
            
            # Call the LLM
            response = await self.client.chat.completions.create(
                model=os.getenv("OPENAI_MODEL") or os.getenv("CHAT_MODEL") or "gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "تو یک استخراج‌کننده ویژگی مقایسه هستی."},
                    {"role": "user", "content": full_prompt}
                ]
            )
            
            # Parse the JSON response
            result = json.loads(response.choices[0].message.content)
            compare_feature_fa = result.get("compare_feature", "نامشخص")

            extra_features_product_result = self.db.query(
                "SELECT extra_features FROM base_products WHERE random_key = ? LIMIT 1",
                (product_random_key_1,)
            )
            extra_features_product = dict(extra_features_product_result[0])
            extra_features_product_str = extra_features_product['extra_features']
            extra_features_product_dict = json.loads(extra_features_product_str)

            # Find English name of the feature using exact match first
            find_compare_feature_en = None
            for eng_key, persian_value in features_dict.items():
                if persian_value == compare_feature_fa or compare_feature_fa in persian_value or persian_value in compare_feature_fa:
                    find_compare_feature_en = eng_key
                    break
            
            # If exact match not found, use semantic search
            if not find_compare_feature_en:
                try:
                    # Get all Persian feature names from features_dict
                    persian_feature_names = list(extra_features_product_dict.values())
                    
                    # Use faiss_embedding.py for embedding similarity search
                    embedder = EmbeddingServiceWrapper()
                    
                    # Build HNSW index from Persian feature names
                    c = await build_hnsw_from_texts(persian_feature_names, embedder, metric='cosine', m=32, ef_construction=300, ef_search=128)
                    
                    # Search for similarity
                    hits = await semantic_search(c, [compare_feature_fa], embedder, top_k=1)
                    
                    # If similarity is more than 0.75, use the match
                    if hits[0][0]['score'] > 0.75:
                        best_match_index = hits[0][0]['id']
                        best_match = persian_feature_names[best_match_index]
                        
                        # Find the English key for this Persian feature name
                        for eng_key, persian_value in features_dict.items():
                            if persian_value == best_match:
                                find_compare_feature_en = eng_key
                                compare_feature_fa = persian_value
                                break
                                
                except Exception as e:
                    print(f"Error in embedding similarity search: {e}")
            if not find_compare_feature_en:
                p = [compare_feature_fa]
                find_compare_feature_en = await self._find_features_with_llm(product_random_key_1, p, extra_features_product_dict, product_name_1)
            return find_compare_feature_en, compare_feature_fa
            
        except json.JSONDecodeError as e:
            print(f"Error parsing JSON response: {e}")
            return None, "نامشخص"
        except Exception as e:
            print(f"Error in feature extraction: {e}")
            return None, "نامشخص"

    def _get_feature_value(self, product_random_key, find_compare_feature_en):
        """Get feature value for a specific product using its random key and feature name"""
        if not product_random_key or not find_compare_feature_en:
            return None
            
        try:
            result = self.db.query(
                "SELECT extra_features FROM base_products WHERE random_key = ? LIMIT 1",
                (product_random_key,)
            )
            if result:
                product_data = dict(result[0])
                extra_features_str = product_data['extra_features']
                extra_features_dict = json.loads(extra_features_str)
                
                # Return the feature value if it exists
                if find_compare_feature_en in extra_features_dict:
                    return extra_features_dict[find_compare_feature_en]
                else:
                    return None
            return None
        except Exception as e:
            print(f"Error getting feature value: {e}")
            return None

    async def _get_final_comparison_answer_feature_level(self, query, data):
        """Generate final comparison answer using LLM"""
        try:
            # استفاده از نمونه‌ها برای few-shot learning
            few_shot_examples = "\n".join([
                f"ورودی: {sample['final_explanation']}\nخروجی: {json.dumps(sample, ensure_ascii=False, separators=(',', ':'))}"
                for sample in compare_final_decide_samples  # استفاده از 3 نمونه اول
            ])
            
            user_content = f"""
            پرسش کاربر: {query}
            
            داده‌های مقایسه:
            {json.dumps(data, ensure_ascii=False, indent=2)}
            
            {few_shot_examples}
            
            لطفاً بر اساس داده‌های بالا، مقایسه نهایی را انجام داده و برنده را مشخص کن.
            """
            
            response = await self.client.chat.completions.create(
                model=os.getenv("OPENAI_MODEL") or os.getenv("CHAT_MODEL") or "gpt-4o-mini",
                messages=[
                    {"role": "system", "content": comparison_final_decide_system_prompt},
                    {"role": "user", "content": user_content}
                ],
                temperature=0
            )
            response_text = (response.choices[0].message.content or "").strip()
            
            # Clean the response text to remove markdown code blocks if present
            if response_text.startswith('```json'):
                response_text = response_text[7:]  # Remove ```json
            if response_text.startswith('```'):
                response_text = response_text[3:]   # Remove ```
            if response_text.endswith('```'):
                response_text = response_text[:-3]  # Remove trailing ```
            
            response_text = response_text.strip()
            response_json = json.loads(response_text)
            if response_json["winner_random_key"] == "مساوی":
                response_json["winner_random_key"] = None
            if response_json:
                return response_json["final_explanation"], response_json["winner_random_key"]
            else:
                return None, None
            
        except Exception as e:
            print(f"Error generating final answer: {e}")
            return "متأسفم، نتوانستم پاسخ مناسبی برای مقایسه این محصولات ارائه دهم."

    async def _feature_level_comparison(self, query, product_random_key_1, product_name_1, product_random_key_2, product_name_2):
        find_compare_feature_en, find_compare_feature_fa = await self._search_compare_feature(query,product_random_key_1, product_name_1, product_random_key_2, product_name_2)
        value_compare_feature_product_1 = self._get_feature_value(product_random_key_1, find_compare_feature_en)
        value_compare_feature_product_2 = self._get_feature_value(product_random_key_2, find_compare_feature_en)
        data =  {
            "نام محصول ۱": product_name_1,
            "random_key محصول ۱": product_random_key_1,
            "نام محصول ۲": product_name_2,
            "random_key محصول ۲": product_random_key_2,
            find_compare_feature_fa + " محصول ۱": value_compare_feature_product_1,
            find_compare_feature_fa + " محصول ۲": value_compare_feature_product_2
        }
        final_answer, winner_random_key = await self._get_final_comparison_answer_feature_level(query, data)
        return final_answer, winner_random_key

    async def _detect_shop_comparison_task(self, query):
        """Detect the type of shop comparison task from user query"""
        try:
            # Create few-shot examples string
            examples_str = ""
            for sample in comparison_shop_samples:
                examples_str += f"ورودی: {sample['input']}\n"
                examples_str += f"خروجی: {json.dumps({'shop_task': sample['comparison_type']}, ensure_ascii=False)}\n\n"
            
            # Create the full prompt
            full_prompt = f"{comparison_shop_system_prompt}\n\nمثال‌ها:\n{examples_str}\nورودی: {query}\nخروجی:"
            
            # Call the LLM
            response = await self.client.chat.completions.create(
                model=os.getenv("OPENAI_MODEL") or os.getenv("CHAT_MODEL") or "gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "تو یک مسیریاب هوشمند برای تشخیص نوع مقایسه فروشگاهی هستی."},
                    {"role": "user", "content": full_prompt}
                ]
            )
            
            # Parse the JSON response
            result = json.loads(response.choices[0].message.content)
            shop_task = result.get("shop_task", "unknown")
            
            return shop_task
            
        except json.JSONDecodeError as e:
            print(f"Error parsing JSON response: {e}")
            return "unknown"
        except Exception as e:
            print(f"Error in shop task detection: {e}")
            return "unknown"

    def _get_count_of_shops(self, random_key):
        """Get count of shops that have this product"""
        if not random_key:
            return 0
            
        try:
            query = """
            SELECT COUNT(DISTINCT m.shop_id) as shop_count
            FROM members m
            WHERE m.base_random_key = ?
            """
            result = self.db.query(query, (random_key,))
            if result:
                return result[0]['shop_count']
            return 0
        except Exception as e:
            print(f"Error getting shop count: {e}")
            return 0

    def _get_mean_price_of_product(self, random_key):
        """Get mean price of product across all shops"""
        if not random_key:
            return 0
            
        try:
            query = """
            SELECT AVG(m.price) as mean_price
            FROM members m
            WHERE m.base_random_key = ?
            """
            result = self.db.query(query, (random_key,))
            if result and result[0]['mean_price'] is not None:
                return round(result[0]['mean_price'], 2)
            return 0
        except Exception as e:
            print(f"Error getting mean price: {e}")
            return 0

    def _get_least_price_of_product(self, random_key):
        """Get least price of product across all shops"""
        if not random_key:
            return 0
            
        try:
            query = """
            SELECT MIN(m.price) as least_price
            FROM members m
            WHERE m.base_random_key = ?
            """
            result = self.db.query(query, (random_key,))
            if result and result[0]['least_price'] is not None:
                return result[0]['least_price']
            return 0
        except Exception as e:
            print(f"Error getting least price: {e}")
            return 0

    def _get_most_price_of_product(self, random_key):
        """Get most price of product across all shops"""
        if not random_key:
            return 0
            
        try:
            query = """
            SELECT MAX(m.price) as most_price
            FROM members m
            WHERE m.base_random_key = ?
            """
            result = self.db.query(query, (random_key,))
            if result and result[0]['most_price'] is not None:
                return result[0]['most_price']
            return 0
        except Exception as e:
            print(f"Error getting most price: {e}")
            return 0

    async def _shop_level_comparison(self, query,product_random_key_1, product_name_1, product_random_key_2, product_name_2):
        """
        here for now we have some task:
            compare_count_of_shops
            compare_mean_price
            compare_least_price
            compare_most_price
        """
        compare_shop_task = await self._detect_shop_comparison_task(query)
        final_answer = "متأسفم، نتوانستم پاسخ مناسبی برای مقایسه این محصولات ارائه دهم."
        winner_random_key = None
        if compare_shop_task == "compare_count_of_shops":
            count_shops_product_1 = self._get_count_of_shops(product_random_key_1)
            count_shops_product_2 = self._get_count_of_shops(product_random_key_2)
            data = {
                "نام محصول ۱": product_name_1,
                "random_key محصول ۱": product_random_key_1,
                "نام محصول ۲": product_name_2,
                "random_key محصول ۲": product_random_key_2,
                "تعداد فروشگاه‌های محصول ۱": count_shops_product_1,
                "تعداد فروشگاه‌های محصول ۲": count_shops_product_2
            }
            final_answer, winner_random_key = await self._get_final_comparison_answer_feature_level(query, data)
        if compare_shop_task == "compare_mean_price":
            mean_price_product_1 = self._get_mean_price_of_product(product_random_key_1)
            mean_price_product_2 = self._get_mean_price_of_product(product_random_key_2)
            data = {
                "نام محصول ۱": product_name_1,
                "random_key محصول ۱": product_random_key_1,
                "نام محصول ۲": product_name_2,
                "random_key محصول ۲": product_random_key_2,
                "میانگین قیمت محصول ۱": mean_price_product_1,
                "میانگین قیمت محصول ۲": mean_price_product_2
            }
            final_answer, winner_random_key = await self._get_final_comparison_answer_feature_level(query, data)
        if compare_shop_task == "compare_least_price":
            least_price_product_1 = self._get_least_price_of_product(product_random_key_1)
            least_price_product_2 = self._get_least_price_of_product(product_random_key_2)
            data = {
                "نام محصول ۱": product_name_1,
                "random_key محصول ۱": product_random_key_1,
                "نام محصول ۲": product_name_2,
                "random_key محصول ۲": product_random_key_2,
                "کمترین قیمت محصول ۱": least_price_product_1,
                "کمترین قیمت محصول ۲": least_price_product_2
            }
            final_answer, winner_random_key = await self._get_final_comparison_answer_feature_level(query, data)
        if compare_shop_task == "compare_most_price":
            most_price_product_1 = self._get_most_price_of_product(product_random_key_1)
            most_price_product_2 = self._get_most_price_of_product(product_random_key_2)
            data = {
                "نام محصول ۱": product_name_1,
                "random_key محصول ۱": product_random_key_1,
                "نام محصول ۲": product_name_2,
                "random_key محصول ۲": product_random_key_2,
                "بیشترین قیمت محصول ۱": most_price_product_1,
                "بیشترین قیمت محصول ۲": most_price_product_2
            }
            final_answer, winner_random_key = await self._get_final_comparison_answer_feature_level(query, data)
        return final_answer, winner_random_key

    def _get_warranty_count(self, random_key):
        """Get count of shops that have this product with warranty"""
        if not random_key:
            return 0
            
        try:
            query = """
            SELECT COUNT(DISTINCT m.shop_id) as warranty_shop_count
            FROM members m
            JOIN shops s ON m.shop_id = s.id
            WHERE m.base_random_key = ? AND s.has_warranty = 1
            """
            result = self.db.query(query, (random_key,))
            if result:
                return result[0]['warranty_shop_count']
            return 0
        except Exception as e:
            print(f"Error getting warranty count: {e}")
            return 0

    async def _warranty_level_comparison(self, query,product_random_key_1, product_name_1, product_random_key_2, product_name_2):
        number_of_warranty_product_1 = self._get_warranty_count(product_random_key_1)
        number_of_warranty_product_2 = self._get_warranty_count(product_random_key_2)
        data = {
            "نام محصول ۱": product_name_1,
            "random_key محصول ۱": product_random_key_1,
            "نام محصول ۲": product_name_2,
            "random_key محصول ۲": product_random_key_2,
            "تعداد فروشگاههای دارای محصول ۱ همراه با گارانتی": number_of_warranty_product_1,
            "تعداد فروشگاههای دارای محصول ۲ همراه با گارانتی": number_of_warranty_product_2
        }
        final_answer, winner_random_key = await self._get_final_comparison_answer_feature_level(query, data)
        return final_answer, winner_random_key

    def _get_number_of_cities_has_product(self, random_key):
        """Get count of cities that have this product"""
        if not random_key:
            return 0
            
        try:
            query = """
            SELECT COUNT(DISTINCT c.id) as city_count
            FROM members m
            JOIN shops s ON m.shop_id = s.id
            JOIN cities c ON s.city_id = c.id
            WHERE m.base_random_key = ?
            """
            result = self.db.query(query, (random_key,))
            if result:
                return result[0]['city_count']
            return 0
        except Exception as e:
            print(f"Error getting city count: {e}")
            return 0

    async def _city_level_comparison(self, query, product_random_key_1, product_name_1, product_random_key_2, product_name_2):
        numver_of_cities_has_product_1 = self._get_number_of_cities_has_product(product_random_key_1)
        numver_of_cities_has_product_2 = self._get_number_of_cities_has_product(product_random_key_2)
        data = {
            "نام محصول ۱": product_name_1,
            "random_key محصول ۱": product_random_key_1,
            "نام محصول ۲": product_name_2,
            "random_key محصول ۲": product_random_key_2,
            "تعداد شهرهای دارای محصول ۱": numver_of_cities_has_product_1,
            "تعداد شهرهای دارای محصول ۲": numver_of_cities_has_product_2
        }
        final_answer, winner_random_key = await self._get_final_comparison_answer_feature_level(query, data)
        return final_answer, winner_random_key

    def check_random_key_is_valid(self, random_key):
        if random_key is None:
            return False
        else:
            # Query the database to check if the random key exists
            try:
                query = "SELECT random_key FROM base_products WHERE random_key = ?"
                result = self.db.query(query, (random_key,))
                return len(result) > 0
            except Exception as e:
                print(f"Error checking random key validity: {e}")
                return False

    async def _find_feature_for_compare_in_general(self, query: str) -> str:
        """
        در این تابع LLM ویژگی مقایسه‌ای را از سوالات مبهم تشخیص می‌دهد:
        وظیفه: تشخیص ویژگی اصلی که باید مقایسه شود از سوالات غیرمستقیم
        """
        if not query or not query.strip():
            return "عمومی"

        try:
            # استفاده از نمونه‌ها برای few-shot learning
            few_shot_examples = "\n".join([
                f"ورودی: {sample['input']}\nخروجی: {json.dumps(sample, ensure_ascii=False, separators=(',', ':'))}"
                for sample in find_main_feature_of_general_comapre_samples  # استفاده از 5 نمونه اول
            ])
            
            user_content = f"{few_shot_examples}\n\nورودی: {query}\nخروجی:"
            
            model_name = os.getenv("OPENAI_MODEL") or os.getenv("CHAT_MODEL") or "gpt-4o-mini"
            
            resp = await self.client.chat.completions.create(
                model=model_name,
                messages=[
                    {"role": "system", "content": find_main_feature_of_general_comapre_system_prompt},
                    {"role": "user", "content": user_content}
                ],
                temperature=0
            )
            
            response_text = (resp.choices[0].message.content or "").strip()
            
            # تلاش برای پارس کردن JSON
            try:
                result = json.loads(response_text)
                if "comparison_feature" in result:
                    return result["comparison_feature"]
            except json.JSONDecodeError:
                pass
            
            # در صورت خطا در پارس، تلاش برای استخراج JSON از متن
            import re
            json_match = re.search(r'\{[^}]*\}', response_text)
            if json_match:
                try:
                    result = json.loads(json_match.group())
                    if "comparison_feature" in result:
                        return result["comparison_feature"]
                except json.JSONDecodeError:
                    pass
            
            # در صورت عدم موفقیت، تلاش برای استخراج مستقیم از متن
            if "comparison_feature" in response_text:
                import re
                feature_match = re.search(r'"comparison_feature":\s*"([^"]+)"', response_text)
                if feature_match:
                    return feature_match.group(1)
            
        except Exception as e:
            print(f"Error in _find_feature_for_compare_in_general: {e}")
        
        # در صورت خطا، بازگشت به حالت پیش‌فرض
        return None
    
    async def _feature_level_comparison_genral(self, query, product_random_key_1, product_name_1, product_random_key_2, product_name_2, find_feature_to_compare):
        """
        مقایسه در سطح ویژگی برای سوالات عمومی
        در این تابع ویژگی مقایسه‌ای از قبل استخراج شده و نیازی به استخراج مجدد نیست
        """
        try:
            # تبدیل نام فارسی ویژگی به انگلیسی
            find_compare_feature_en = None
            for eng_key, persian_value in features_dict.items():
                if persian_value == find_feature_to_compare or find_feature_to_compare in persian_value or persian_value in find_feature_to_compare:
                    find_compare_feature_en = eng_key
                    break
            
            # اگر تطبیق دقیق پیدا نشد، از جستجوی معنایی استفاده کن
            if not find_compare_feature_en:
                try:
                    # دریافت ویژگی‌های اضافی محصول اول
                    extra_features_product_result = self.db.query(
                        "SELECT extra_features FROM base_products WHERE random_key = ? LIMIT 1",
                        (product_random_key_1,)
                    )
                    if extra_features_product_result:
                        extra_features_product = dict(extra_features_product_result[0])
                        extra_features_product_str = extra_features_product['extra_features']
                        extra_features_product_dict = json.loads(extra_features_product_str)
                        
                        # دریافت نام‌های فارسی ویژگی‌ها
                        persian_feature_names = list(extra_features_product_dict.values())
                        
                        # استفاده از جستجوی معنایی
                        embedder = EmbeddingServiceWrapper()
                        c = await build_hnsw_from_texts(persian_feature_names, embedder, metric='cosine', m=32, ef_construction=300, ef_search=128)
                        hits = await semantic_search(c, [find_feature_to_compare], embedder, top_k=1)
                        
                        # اگر شباهت بیش از 0.75 باشد، از تطبیق استفاده کن
                        if hits[0][0]['score'] > 0.75:
                            best_match_index = hits[0][0]['id']
                            best_match = persian_feature_names[best_match_index]
                            
                            # پیدا کردن کلید انگلیسی برای این نام فارسی
                            for eng_key, persian_value in features_dict.items():
                                if persian_value == best_match:
                                    find_compare_feature_en = eng_key
                                    find_feature_to_compare = persian_value
                                    break
                                    
                except Exception as e:
                    print(f"Error in embedding similarity search: {e}")
            
            # اگر هنوز کلید انگلیسی پیدا نشد، از LLM استفاده کن
            if not find_compare_feature_en:
                extra_features_product_result = self.db.query(
                    "SELECT extra_features FROM base_products WHERE random_key = ? LIMIT 1",
                    (product_random_key_1,)
                )
                if extra_features_product_result:
                    extra_features_product = dict(extra_features_product_result[0])
                    extra_features_product_str = extra_features_product['extra_features']
                    extra_features_product_dict = json.loads(extra_features_product_str)
                    p = [find_feature_to_compare]
                    find_compare_feature_en = await self._find_features_with_llm(product_random_key_1, p, extra_features_product_dict, product_name_1)
            
            # اگر کلید انگلیسی پیدا نشد، از نام فارسی استفاده کن
            if not find_compare_feature_en:
                find_compare_feature_en = find_feature_to_compare
            
            # دریافت مقادیر ویژگی برای هر دو محصول
            value_compare_feature_product_1 = self._get_feature_value(product_random_key_1, find_compare_feature_en)
            value_compare_feature_product_2 = self._get_feature_value(product_random_key_2, find_compare_feature_en)
            
            # آماده‌سازی داده‌ها برای مقایسه نهایی
            data = {
                "نام محصول ۱": product_name_1,
                "random_key محصول ۱": product_random_key_1,
                "نام محصول ۲": product_name_2,
                "random_key محصول ۲": product_random_key_2,
                find_feature_to_compare + " محصول ۱": value_compare_feature_product_1,
                find_feature_to_compare + " محصول ۲": value_compare_feature_product_2
            }
            
            # دریافت پاسخ نهایی مقایسه
            final_answer, winner_random_key = await self._get_final_comparison_answer_feature_level(query, data)
            return final_answer, winner_random_key
            
        except Exception as e:
            print(f"Error in _feature_level_comparison_genral: {e}")
            return "خطا در مقایسه ویژگی‌ها", None

    async def process_query(self, query: str) -> Response:
        extract_prompt_data = await self._route_task_type(query)
        comparison_type, product_name_1, product_random_key_1, product_name_2, product_random_key_2 = (
            extract_prompt_data.get("comparison_type", "general"),
            extract_prompt_data.get("product_name_1", "نامشخص"),
            extract_prompt_data.get("product_random_key_1"),
            extract_prompt_data.get("product_name_2", "نامشخص"),
            extract_prompt_data.get("product_random_key_2")
        )
        print(f"Comparison type: {comparison_type}, Product 1: {product_name_1} ({product_random_key_1}), Product 2: {product_name_2} ({product_random_key_2})")
        check_random_key_1_is_valid = self.check_random_key_is_valid(product_random_key_1)
        if product_random_key_1 is None or not check_random_key_1_is_valid:
            product_result = await self.search_product(product_name_1)
            product_random_key_1 = product_result['random_key'] if product_result else None
        check_random_key_2_is_valid = self.check_random_key_is_valid(product_random_key_2)
        if product_random_key_2 is None or not check_random_key_2_is_valid:
            product_result = await self.search_product(product_name_2)
            product_random_key_2 = product_result['random_key'] if product_result else None
        final_answer = "متأسفم، نتوانستم محصولات را برای مقایسه پیدا کنم."
        winner_random_key = None
        if comparison_type == "feature_level":
            final_answer, winner_random_key = await self._feature_level_comparison(query, product_random_key_1, product_name_1, product_random_key_2, product_name_2)
        elif comparison_type == "shop_level":
            final_answer, winner_random_key =  await self._shop_level_comparison(query,product_random_key_1, product_name_1, product_random_key_2, product_name_2)
        elif comparison_type == "warranty_level":
            final_answer, winner_random_key =  await self._warranty_level_comparison(query,product_random_key_1, product_name_1, product_random_key_2, product_name_2)
        elif comparison_type == "city_level":
            final_answer, winner_random_key =  await self._city_level_comparison(query,product_random_key_1, product_name_1, product_random_key_2, product_name_2)
        elif comparison_type == "general":
            find_feature_to_compare = await self._find_feature_for_compare_in_general(query)
            if not find_feature_to_compare or find_feature_to_compare.lower() == "عمومی":
                final_answer = "متأسفم، نتوانستم ویژگی خاصی برای مقایسه این محصولات تشخیص دهم."
                winner_random_key = None
                return Response(message=final_answer, base_random_keys=[], member_random_keys=[])
            else:
                final_answer, winner_random_key = await self._feature_level_comparison_genral(query, product_random_key_1, product_name_1, product_random_key_2, product_name_2, find_feature_to_compare)
        if winner_random_key:
            return Response(message=final_answer, base_random_keys=[winner_random_key], member_random_keys=[])
        else:
            return Response(message=final_answer, base_random_keys=[], member_random_keys=[])


import time
async def main():
    prompt_template = PromptTemplate(
        input_variables=["query"],
        template="از متن زیر نام محصول و ویژگی‌های خواسته‌شده را استخراج کن و فقط خروجی را به صورت JSON زیر بده:\n{\"product_name\": ..., \"features\": [...]}\nمتن: {{ query }}",
        template_format="jinja2"
    )

    agent = ComparisonAgent(prompt_template)

    test_queries = [
        "کدام یک از یخچال فریزر کمبی جی‌ پلاس مدل M5320 یا یخچال فریزر جی پلاس مدل GRF-P5325 برای خانواده‌های پرجمعیت مناسب‌تر است؟"
        # "کدامیک از محصولات 'دراور فایل کمدی پلاستیکی طرح کودک' با شناسه \"ebolgl\" و 'دراور هوم کت ۴ طبقه بزرگ طرح دار از پلاستیک' با شناسه \"nihvhq\" در فروشگاه‌های بیشتری موجود است و آسان‌تر می‌توان آن را خرید؟",
        # "برای مقایسه، کدام یک از محصولات \"جا ادویه شیشه ای با درب چوبی و استند نردبانی\" با شناسه \"gouchy\" و \"جا ادویه مک کارتی استند چوبی\" با شناسه \"uhqmhb\" از نظر تعداد تکه‌ها بیشتر است؟",
        # "کدام محصول بین 'گلدون کنار سالنی سه سایزی طرح راش' - شناسه \"dzpdls\" - و 'گلدان شیشه‌ای لب طلایی مدل گلوریا سایز ۷۰ سانتی' در تعداد بیشتری از شهرها موجود است؟",
        # "کدامیک از محصولات 'دراور فایل کمدی پلاستیکی طرح کودک' با شناسه \"ebolgl\" و 'دراور هوم کت ۴ طبقه بزرگ طرح دار از پلاستیک' با شناسه \"nihvhq\" در فروشگاه‌های بیشتری موجود است و آسان‌تر می‌توان آن را خرید؟",
        # "این دو تلویزیون ال جی NANO75 سایز ۵۰ اینچ Ultra HD 4K LED و تلویزیون ال جی مدل UT80006 سایز ۵۰ اینچ Ultra HD 4K LED با شناسه \"dmsmlc\" از لحاظ اصالت محصول چگونه با یکدیگر مقایسه می‌شوند؟ کدام یک اصالت بیشتری دارد؟",
        # "کدام یک از این تلویزیون‌ها برای تماشای محتوای با وضوح بالا مناسب‌تر است؟ تلویزیون جی پلاس مدل PH514N سایز ۵۰ اینچ یا تلویزیون جی پلاس GTV-50RU766S سایز ۵۰ اینچ",
        # "از بین یخچال فریزر هیمالیا مدل FIVE MODE ظرفیت ۲۲ فوت هومباردار با شناسه \"faddzl\" و یخچال فریزر هیمالیا مدل کمبی 530 هوم بار با شناسه \"nkepsf\"، کدام رنگ‌های موجود بیشتری جهت انطباق با سبک‌های مختلف آشپزخانه دارد؟"
    ]

    for query in test_queries:
        # start = time.time()
        response = await agent.process_query(query)
        print(f"Query: {query}\nResponse: {response}\n")
        # end = time.time()
        # print(f"Processing time: {end - start:.2f} seconds\n{'-'*40}")

if __name__ == "__main__":
    asyncio.run(main())


