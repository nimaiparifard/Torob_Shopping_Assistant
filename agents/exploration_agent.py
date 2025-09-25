import json
import os
import random
from typing import Dict, Any, final
from langchain.prompts import PromptTemplate
from sqlalchemy.util import await_only
from unicodedata import category

from response_format import Response
import dotenv
from embedding.faiss_embedding import EmbeddingServiceWrapper, build_hnsw_from_texts, semantic_search
from system_prompts.product_features_system_prompts import system_msg_extracting_product_features, samples_extracting_product_features
from features_list import features_dict
from system_prompts.comparison_system_prompt import *
from system_prompts.comparison_feature_system_prompt import *
from system_prompts.comparison_shop_system_prompt import *
from agents.feature_product_agents import FeatureProductAgent
dotenv.load_dotenv()


class ExplorationAgent(FeatureProductAgent):
    def __init__(self, prompt_template: PromptTemplate, db_path: str | None = None):
        # Properly initialize parent so we have self.prompt_template, self.client, etc.
        super().__init__(prompt_template, db_path)

    def _get_chat_history(self, chat_id):
        """ check this chat_id is existed in exploration table if not create new row with chat_id and set count to 1"""
        try:
            # Check if chat_id exists in exploration table
            result = self.db.query(
                "SELECT chat_id, counts, base_random_key,  city_id, brand_id, category_id, lower_price, upper_price, has_warranty, score FROM exploration WHERE chat_id = ?",
                (chat_id,)
            )
            
            if result:
                # Chat exists, return all fields
                row = result[0]
                return (
                    row['chat_id'],
                    row['counts'],
                    row['base_random_key'],
                    row['city_id'],
                    row['brand_id'],
                    row['category_id'],
                    row['lower_price'],
                    row['upper_price'],
                    row['has_warranty'],
                    row['score']
                )
            else:
                # Chat doesn't exist, create new one with count = 1
                self.db.execute(
                    "INSERT INTO exploration (chat_id, counts) VALUES (?, ?)",
                    (chat_id, 1)
                )
                return (chat_id, 1, None, None, None, None, None, None, 0, 0)
                
        except Exception as e:
            print(f"Error in _get_chat_history: {e}")
            return (chat_id, 1, None, None, None, None, None, None, 0, 0)

    async def _extract_info_from_query(self, query: str):
        """
        design system prompt and samples to extract product name, city name, brand name, category name, features, lowest price, highest price, has_warranty from query if exist
        """
        try:
            # Import the system prompt and samples
            from system_prompts.info_extraction_system_prompt import info_extraction_system_prompt, info_extraction_samples
            
            # Create few-shot examples string
            examples_str = ""
            for sample in info_extraction_samples:
                examples_str += f"ورودی: {sample['input']}\n"
                examples_str += f"خروجی: {json.dumps({k: v for k, v in sample.items() if k != 'input'}, ensure_ascii=False)}\n\n"
            
            # Create the full prompt
            full_prompt = f"{info_extraction_system_prompt}\n\nمثال‌ها:\n{examples_str}\nورودی: {query}\nخروجی:"
            
            # Call the LLM
            response = await self.client.chat.completions.create(
                model=os.getenv("OPENAI_MODEL") or os.getenv("CHAT_MODEL") or "gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "تو یک استخراج‌کننده حرفه‌ای اطلاعات محصولات هستی."},
                    {"role": "user", "content": full_prompt}
                ]
            )
            
            # Parse the JSON response
            result = json.loads(response.choices[0].message.content)
            
            # Extract values with proper defaults
            product_name = result.get("product_name")
            city_name = result.get("city_name")
            brand_name = result.get("brand_name")
            category_name = result.get("category_name")
            features = result.get("features")
            lowest_price = result.get("lowest_price")
            highest_price = result.get("highest_price")
            has_warranty = result.get("has_warranty")
            shop_name = result.get("shop_name")
            score = result.get("score")
            
            return (product_name, city_name, brand_name, category_name, features, lowest_price, highest_price, has_warranty, score)
            
        except json.JSONDecodeError as e:
            print(f"Error parsing JSON response: {e}")
            return (None, None, None, None, None, None, None, None, None)
        except Exception as e:
            print(f"Error in info extraction: {e}")
            return (None, None, None, None, None, None, None, None, None)


    async def _get_base_product_id(self, product_name: str):
        """ get base product id from product name using specific product agent"""
        product_result = await self.search_product(product_name)
        product_result_random_key = product_result['random_key'] if product_result else None
        return product_result_random_key

    async def _get_brand_id(self, brand_name: str):
        """ get brand id from brand name using feature product agent if not have with this brand name user like query and used samantic vector similrty for findinf usinng embedding\faiss_embedding.py """
        if not brand_name:
            return None
            
        try:
            # First try exact match in database
            result = self.db.query(
                "SELECT id FROM brands WHERE title = ? LIMIT 1",
                (brand_name,)
            )
            if result:
                return result[0]['id']
            
            # If no exact match, get all brand names for semantic search
            all_brands = self.db.query("SELECT id, title FROM brands")
            if not all_brands:
                return None
                
            brand_names = [brand['title'] for brand in all_brands]
            brand_ids = [brand['id'] for brand in all_brands]
            
            # Use faiss_embedding.py for embedding similarity search
            embedder = EmbeddingServiceWrapper()
            
            # Build HNSW index from brand names
            c = await build_hnsw_from_texts(brand_names, embedder, metric='cosine', m=32, ef_construction=300, ef_search=128)
            
            # Search for similarity
            hits = await semantic_search(c, [brand_name], embedder, top_k=1)
            
            # If similarity is more than 0.75, return the brand id
            if hits[0][0]['score'] > 0.75:
                best_match_index = hits[0][0]['id']
                best_match_brand_id = brand_ids[best_match_index]
                best_match_name = brand_names[best_match_index]
                print(f"Found similar brand: {best_match_name} (similarity: {hits[0][0]['score']:.3f}) = ID: {best_match_brand_id}")
                return best_match_brand_id
            
            return None
            
        except Exception as e:
            print(f"Error in _get_brand_id: {e}")
            return None

    async def _get_category_id(self, category_name: str):
        """ get category id from category name using feature product agent"""
        if not category_name:
            return None
            
        try:
            # First try exact match in database
            result = self.db.query(
                "SELECT id FROM categories WHERE title = ? LIMIT 1",
                (category_name,)
            )
            if result:
                return result[0]['id']
            
            # If no exact match, get all category names for semantic search
            all_categories = self.db.query("SELECT id, title FROM categories")
            if not all_categories:
                return None
                
            category_names = [category['title'] for category in all_categories]
            category_ids = [category['id'] for category in all_categories]
            
            # Use faiss_embedding.py for embedding similarity search
            embedder = EmbeddingServiceWrapper()
            
            # Build HNSW index from category names
            c = await build_hnsw_from_texts(category_names, embedder, metric='cosine', m=32, ef_construction=300, ef_search=128)
            
            # Search for similarity
            hits = await semantic_search(c, [category_name], embedder, top_k=1)
            
            # If similarity is more than 0.75, return the category id
            if hits[0][0]['score'] > 0.75:
                best_match_index = hits[0][0]['id']
                best_match_category_id = category_ids[best_match_index]
                best_match_name = category_names[best_match_index]
                print(f"Found similar category: {best_match_name} (similarity: {hits[0][0]['score']:.3f}) = ID: {best_match_category_id}")
                return best_match_category_id
            
            return None
            
        except Exception as e:
            print(f"Error in _get_category_id: {e}")
            return None

    async def _get_city_id(self, city_name: str):
        """ get city id from city name using feature product agent"""
        if not city_name:
            return None
            
        try:
            # First try exact match in database
            result = self.db.query(
                "SELECT id FROM cities WHERE name = ? LIMIT 1",
                (city_name,)
            )
            if result:
                return result[0]['id']
            
            # If no exact match, get all city names for semantic search
            all_cities = self.db.query("SELECT id, name FROM cities")
            if not all_cities:
                return None
                
            city_names = [city['name'] for city in all_cities]
            city_ids = [city['id'] for city in all_cities]
            
            # Use faiss_embedding.py for embedding similarity search
            embedder = EmbeddingServiceWrapper()
            
            # Build HNSW index from city names
            c = await build_hnsw_from_texts(city_names, embedder, metric='cosine', m=32, ef_construction=300, ef_search=128)
            
            # Search for similarity
            hits = await semantic_search(c, [city_name], embedder, top_k=1)
            
            # If similarity is more than 0.75, return the city id
            if hits[0][0]['score'] > 0.75:
                best_match_index = hits[0][0]['id']
                best_match_city_id = city_ids[best_match_index]
                best_match_name = city_names[best_match_index]
                print(f"Found similar city: {best_match_name} (similarity: {hits[0][0]['score']:.3f}) = ID: {best_match_city_id}")
                return best_match_city_id
            
            return None
            
        except Exception as e:
            print(f"Error in _get_city_id: {e}")
            return None

    # async def _get_features(self, features: list):
    #     """ get features ids from features names using features_dict"""
    #     pass

    def _update_exploration_table(self, chat_id, count, base_product_id, city_id, brand_id, cetegory_id,  lowest_price, highest_price, has_warranty, score):
        """ update exploration table if each value is not None"""
        try:
            # Build the update query dynamically based on which values are not None
            update_fields = []
            update_values = []
            
            # Always update counts
            update_fields.append("counts = ?")
            update_values.append(count)
            
            # Update base_product_id if provided
            if base_product_id is not None:
                update_fields.append("base_random_key = ?")
                update_values.append(base_product_id)
            
            # Update brand_id if provided
            if brand_id is not None:
                update_fields.append("brand_id = ?")
                update_values.append(brand_id)

            if city_id is not None:
                update_fields.append("city_id = ?")
                update_values.append(city_id)

            # Update category_id if provided (note: parameter name has typo but keeping it consistent)
            if cetegory_id is not None:
                update_fields.append("category_id = ?")
                update_values.append(cetegory_id)
            
            # Update extra_features if provided
            # if extra_features is not None:
            #     update_fields.append("extra_features = ?")
            #     update_values.append(extra_features)
            
            # Update lower_price if provided
            if lowest_price is not None:
                update_fields.append("lower_price = ?")
                update_values.append(lowest_price)
            
            # Update upper_price if provided
            if highest_price is not None:
                update_fields.append("upper_price = ?")
                update_values.append(highest_price)
            
            # Update has_warranty if provided
            if has_warranty is not None:
                update_fields.append("has_warranty = ?")
                update_values.append(has_warranty)
            
            # Update score if provided
            if score is not None:
                update_fields.append("score = ?")
                update_values.append(score)
            
            # Add chat_id for WHERE clause
            update_values.append(chat_id)
            
            # Build and execute the update query
            if update_fields:
                query = f"UPDATE exploration SET {', '.join(update_fields)} WHERE chat_id = ?"
                self.db.execute(query, update_values)
                print(f"Updated exploration table for chat_id: {chat_id}")
            else:
                print(f"No fields to update for chat_id: {chat_id}")
                
        except Exception as e:
            print(f"Error updating exploration table: {e}")

    async def _generate_response_text(self, base_product_id, city_id, brand_id, cetegory_id,  lowest_price, highest_price, has_warranty, score):
        prompt = "لطفا موارد خواسته را پاسخ دهید تا من بتوانم کلید تصادفی محصول داخل فروشگاه را پیدا کنم."
        name_prompt= ["برای پاسخگویی متن نام دقیق محصول را وارد کنید.","لطفا نام دقیق محصول را وارد کنید"]
        city_prompt= ["نام شهری که می خواهید از ان محصول را تهیه کنید را وارد کنید.","لطفا نام شهر را وارد کنید"]
        brand_prompt= ["نام برند اگر مد نظر هست حتما وارد کنید.","لطفا نام برند را وارد کنید"]
        category_prompt= ["اگر دسته بندی خواستی مد نظر هست حتما وارد کنید.","لطفا نام دسته بندی را وارد کنید"]
        feature_prompt= ["برای پاسخگویی متن ویژگی های محصول را وارد کنید.","لطفا ویژگی های محصول را وارد کنید"]
        price_prompt= ["اگر بازه قیمتی در نظر دارید حتما به صورت دقیق وارد کنید.","لطفا بازه قیمت را وارد کنید"]
        warranty_prompt= ["لطفا اگر ضمانت کالا برای تان مهم هست اشاره کنید.","لطفا اگر دوست دارید محصول مورد نظر ضمانت داشته باشد اشاره کنید"]
        ## for each prompt select random one from list and join them to main prompt
        prompt = prompt + "." + random.choice(name_prompt)
        if not city_id:
            prompt = prompt + "." + random.choice(city_prompt)
        if not brand_id:
            prompt = prompt + "." + random.choice(brand_prompt)
        if not cetegory_id:
            prompt = prompt + "." + random.choice(category_prompt)
        # if not extra_features:
        #     prompt = prompt + "." + random.choice(feature_prompt)
        if not lowest_price and not highest_price:
            prompt = prompt + "." + random.choice(price_prompt)
        if not has_warranty:
            prompt = prompt + "." + random.choice(warranty_prompt)
        prompt = prompt + ".ممنون بابت اینکه اطلاعات را به کامل ترین شکل ممکن به من دادید"+ "."
        return prompt

    def _get_member_random_keys(self, base_product_id, city_id, brand_id, cetegory_id, extra_features, lowest_price, highest_price, has_warranty, score, count):
        """ get member key query to member table based on that each of them is avaible or not write suatble queries to handle multiple scenarios. 
            do not bring extra_features in the query at this time now may be iadded in the future
        """
        try:
            # Build the query dynamically based on available parameters
            query_parts = []
            query_values = []
            
            # Base query with JOINs to access related tables
            base_query = """
                SELECT DISTINCT m.random_key 
                FROM members m
                JOIN base_products bp ON m.base_random_key = bp.random_key
                JOIN shops s ON m.shop_id = s.id
                WHERE 1=1
            """
            
            # Add base_product_id filter if available
            if base_product_id is not None:
                query_parts.append("m.base_random_key = ?")
                query_values.append(base_product_id)
            
            # Add city_id filter through shops table
            if city_id is not None:
                query_parts.append("s.city_id = ?")
                query_values.append(city_id)
            
            # Add brand_id filter through base_products table
            if brand_id is not None:
                query_parts.append("bp.brand_id = ?")
                query_values.append(brand_id)
            
            # Add category_id filter through base_products table
            if cetegory_id is not None:
                query_parts.append("bp.category_id = ?")
                query_values.append(cetegory_id)
            
            # Add price range filters
            if lowest_price is not None:
                query_parts.append("m.price >= ?")
                query_values.append(lowest_price)
            
            if highest_price is not None:
                query_parts.append("m.price <= ?")
                query_values.append(highest_price)
            
            # Add warranty filter through shops table
            if has_warranty is not None:
                query_parts.append("s.has_warranty = ?")
                query_values.append(has_warranty)
            
            # Add score filter through shops table
            if score is not None:
                query_parts.append("s.score >= ?")
                query_values.append(score)
            
            # Build the complete query
            if query_parts:
                complete_query = base_query + " AND " + " AND ".join(query_parts)
            else:
                complete_query = base_query
            
            # Add ORDER BY for consistent results (by price ascending, then by random_key)
            complete_query += " ORDER BY m.price ASC, m.random_key ASC LIMIT 1"
            
            # Execute the query
            result = self.db.query(complete_query, query_values)
            print("complete_query:", complete_query)
            if count >= 5:
                if result:
                    return result[0]['random_key']
                else:
                    return None
            else:
                if len(result) == 1:
                    return result[0]['random_key']
                else:
                    return None
                
        except Exception as e:
            print(f"Error in _get_member_random_keys: {e}")
            return None


    async def process_query(self, query: str, chat_id) -> Response:
        chat_id, count, base_product_id, city_id, brand_id,  cetegory_id, lowest_price, highest_price, has_warranty, score = self._get_chat_history(chat_id)
        if count <= 5:
            product_name, city_name, brand_name, category_name, features, lowest_price, highest_price, has_warranty, score = await self._extract_info_from_query(query)
            if product_name:
                if len(product_name.strip(" ")) >= 5  and count >= 2:
                    base_product_id = await self._get_base_product_id(product_name)
            if city_name:
                city_id = await self._get_city_id(city_name)
            if brand_name:
                brand_id =  await self._get_brand_id(brand_name)
            if category_name:
                cetegory_id = await self._get_category_id(category_name)
            # if features:
            #     extra_features = await self._get_features(features)
            if lowest_price:
                lowest_price = lowest_price
            if highest_price:
                highest_price = highest_price
            if has_warranty is not None:
                has_warranty = has_warranty
            if score is not None:
                score = score
            extra_features = {}
            if count >= 3:
                result = self._get_member_random_keys(base_product_id, city_id, brand_id, cetegory_id, extra_features, lowest_price,
                                         highest_price, has_warranty, score, count)
                if result:
                # if found member return it
                    return Response(message="null", base_random_keys=[], member_random_keys=[result])
            self._update_exploration_table(chat_id, count+1, base_product_id, city_id, brand_id, cetegory_id,  lowest_price, highest_price, has_warranty, score)
            reponse_text = await self._generate_response_text(base_product_id, city_id, brand_id, cetegory_id,  lowest_price, highest_price, has_warranty, score)
            return Response(message=reponse_text, base_random_keys=[], member_random_keys=[])
        else:
            # after 5 times try to find the member
            extra_features = {}
            member_random_keys = self._get_member_random_keys(base_product_id, city_id, brand_id, cetegory_id, extra_features, lowest_price, highest_price, has_warranty, score, count)
            if member_random_keys:
                return Response(message="", base_random_keys=[], member_random_keys=[member_random_keys])
            else:
                return Response(message="محصولی یافت نشد", base_random_keys=[], member_random_keys=[])
import asyncio
if __name__ == '__main__':
    feature_prompt_template = PromptTemplate(
        input_variables=["query"],
        template="از متن زیر نام محصول و ویژگی‌های خواسته‌شده را استخراج کن و فقط خروجی را به صورت JSON زیر بده:\n{\"product_name\": ..., \"features\": [...]}\nمتن: {{ query }}",
        template_format="jinja2"
    )
    exploration_agent = ExplorationAgent(feature_prompt_template)
    chat_id = 'fgfgdfg'
    query = "سلام! من دنبال یه ظرف مناسب برای نگهداری بنشن و مواد غذایی خشک هستم. می‌خواستم بدونم چه گزینه‌هایی موجوده و چه فروشنده‌هایی این محصولات رو ارائه میدن؟ قیمت و کیفیت برام مهمه. می‌تونید کمکم کنید؟"
    res = asyncio.run(exploration_agent.process_query(query, chat_id))
    print(res)