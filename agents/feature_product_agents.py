import asyncio
import json
import os
from typing import Dict, Any
from langchain.prompts import PromptTemplate
from response_format import Response
import dotenv
from embedding.faiss_embedding import EmbeddingServiceWrapper, build_hnsw_from_texts, semantic_search
from agents.specific_product_agent import SpecificProductAgent
from system_prompts.product_features_system_prompts import system_msg_extracting_product_features, samples_extracting_product_features
from features_list import features_dict
dotenv.load_dotenv()



class FeatureProductAgent(SpecificProductAgent):
    def __init__(self, prompt_template: PromptTemplate, db_path: str | None = None):
        # Properly initialize parent so we have self.prompt_template, self.client, etc.
        super().__init__(prompt_template, db_path)

    async def _extract_product_name_and_features(self, query: str) -> Dict[str, Any]:
        """
        Extract product name and requested features from a Persian user query.
        Returns: {"product_name": str, "features": List[str]}
        """
        if not query or not query.strip():
            return {"product_name": "نامشخص", "features": ["ویژگی نامشخص"]}

        system_msg = system_msg_extracting_product_features
        samples = samples_extracting_product_features

        few_shot_parts = []
        for s in samples:
            few_shot_parts.append(
                f"مثال:\nپرسش: {s['input']}\nخروجی JSON:\n" +
                json.dumps({
                    "product_name": s["نام محصول"],
                    "features": s["ویژگی‌ها"]
                }, ensure_ascii=False)
            )
        few_shot_block = "\n\n".join(few_shot_parts)

        try:
            rendered = self.prompt_template.format(query=query)
            user_content = (
                f"{few_shot_block}\n\nپرسش کاربر جدید:\n{rendered}\n\n"
                "فقط JSON نهایی را بده."
            )
        except Exception:
            user_content = (
                f"{few_shot_block}\n\nپرسش کاربر جدید:\n{query}\n\n"
                "فقط JSON نهایی را بده."
            )

        try:
            # Call the LLM API
            response = await self.client.chat.completions.create(
                model="gpt-4.1-mini",
                messages=[
                    {"role": "system", "content": system_msg},
                    {"role": "user", "content": user_content}
                ],
            )
            
            # Extract the JSON response
            llm_response = response.choices[0].message.content.strip()
            
            # Parse JSON response
            try:
                result = json.loads(llm_response)
                # Validate the response structure
                if "product_name" not in result or "features" not in result:
                    return {"product_name": "نامشخص", "features": ["ویژگی نامشخص"]}
                
                # Ensure features is a list
                if not isinstance(result["features"], list):
                    result["features"] = ["ویژگی نامشخص"]
                
                # Ensure product_name is not empty
                if not result["product_name"] or not result["product_name"].strip():
                    result["product_name"] = "نامشخص"
                
                return result
                
            except json.JSONDecodeError:
                # If JSON parsing fails, return default values
                return {"product_name": "نامشخص", "features": ["ویژگی نامشخص"]}
                
        except Exception as e:
            print(f"Error calling LLM API: {e}")
            return {"product_name": "نامشخص", "features": ["ویژگی نامشخص"]}

    async def _search_features(self, product_result_random_key, product_features, product_name=None):
        try:
            result = self.db.query(
                "SELECT extra_features FROM base_products WHERE random_key = ? LIMIT 1",
                (product_result_random_key,)
            )
            if result:
                product_data = dict(result[0])
                extra_features_str = product_data['extra_features']
                extra_features_dict = json.loads(extra_features_str)
                for feature in product_features:
                    for eng_feature in extra_features_dict.keys():
                        # Extract search in features_dict to see persian name of feature is here report it not all them are do embedding search
                        if eng_feature in features_dict:
                            persian_feature_name = features_dict[eng_feature]
                            # Check if this Persian feature name matches any of the requested features
                            for requested_feature in product_features:
                                if persian_feature_name in requested_feature or requested_feature in persian_feature_name:
                                    feature_value = extra_features_dict[eng_feature]
                                    print(f"Found exact match: {persian_feature_name} = {feature_value}")
                                    return feature_value
                        
                        # If feature not found, do embedding search similarity with features and persian name in feature dict
                        try:
                            # Get all Persian feature names from features_dict
                            persian_feature_names = list(features_dict.values())
                            
                            # Use faiss_embedding.py for embedding similarity search
                            embedder = EmbeddingServiceWrapper()
                            requested_features_text = " ".join(product_features)
                            
                            # Build HNSW index from Persian feature names
                            c = await build_hnsw_from_texts(persian_feature_names, embedder, metric='cosine', m=32, ef_construction=300, ef_search=128)
                            
                            # Search for similarity
                            hits = await semantic_search(c, [requested_features_text], embedder, top_k=1)
                            
                            # If similarity is more than 0.75, report the value of the feature
                            if hits[0][0]['score'] > 0.75:
                                best_match_index = hits[0][0]['id']
                                best_match = persian_feature_names[best_match_index]
                                
                                # Find the English key for this Persian feature name
                                eng_key = None
                                for eng_key, persian_value in features_dict.items():
                                    if persian_value == best_match:
                                        eng_key = eng_key
                                        break
                                
                                if eng_key and eng_key in extra_features_dict:
                                    feature_value = extra_features_dict[eng_key]
                                    print(f"Found similar match: {best_match} (similarity: {hits[0][0]['score']:.3f}) = {feature_value}")
                                    return feature_value
                        except Exception as e:
                            print(f"Error in embedding similarity search: {e}")
                            continue
                        
                        # If nothing found, continue to next feature
                feature_value_name = await self._find_features_with_llm(product_result_random_key,
                                                                   product_features,
                                                                   extra_features_dict, product_name)
                if feature_value_name and feature_value_name in extra_features_dict:
                    feature_value = extra_features_dict[feature_value_name]
                    return feature_value
                else:
                    return None


        except Exception as e:
            print(f"Error in feature extraction: {e}")
            return None


    async def translation_features_to_english(self, product_features, product_name=None):
        """ ask the llm to translate the persian feature name to english based on category type of product use the feature_dict as a sample"""
            
        try:
            # Create feature dictionary samples for context
            feature_samples = []
            for eng_key, persian_value in list(features_dict.items())[:10]:  # Use first 10 as samples
                feature_samples.append(f"{eng_key}: {persian_value}")
            feature_samples_str = "\n".join(feature_samples)
            
            system_msg = f"""کلمه گقته شده را به انگلیسی بیان کن: این کلمه یک ویژگی محصول است.

            محصول مورد نظر: {product_name if product_name else 'نامشخص'}
            
            در بخش زیر نمونه هایی اورده شده است:
            {feature_samples_str}
            
            قوانین ترجمه:
            ۱.  ویژگی فارسی را به انگلیسی ترجمه کن
            ۲. از اصطلاحات فنی استاندارد استفاده کن
            ۳. برای ترکیبات، از underscore استفاده کن (مثل: energy_consumption)
            ۴. فقط نام انگلیسی ویژگی را برگردان
            ۵. هر ویژگی را در یک خط جداگانه بنویس
            ۶. اگر ترجمه دقیق نمی‌دانی، بهترین حدس خود را بزن
            ۷. از کلمات ساده و قابل فهم استفاده کن"""
            
            user_content = f"""کلمه ای که قرار است ترجمه کنی.
            {', '.join(product_features)}
            
             
             لطفاً این ویژگی‌ را به انگلیسی ترجمه کن:
            بسیار مهم: خر.جی حتما باید به صورت یک کلمه انگلیسی که ترجمه کلمه گفته شده می باشد.
            """
            
            response = await self.client.chat.completions.create(
                model=os.getenv("OPENAI_MODEL") or os.getenv("CHAT_MODEL") or "gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_msg},
                    {"role": "user", "content": user_content}
                ]
            )
            
            # Parse the response and split by lines
            translated_features = response.choices[0].message.content.strip().split('\n')
            # Clean up each feature
            translated_features = [feature.strip() for feature in translated_features if feature.strip()]
            
            return translated_features
            
        except Exception as e:
            print(f"Error translating features: {e}")
            return product_features  # Return original if translation fails

    async def find_feature_name(self, product_features_english_translation, features_dict, product_name=None):
        """ ask the llm to based on feature dict find the most similar feature name in the feature dict and return it if not found return None the outout must bne just """
        # if not product_features_english_translation or not features_dict:
        #     return None
            
        try:
            # Create feature dictionary samples for context
            feature_samples = []
            for eng_key, persian_value in list(features_dict.items())[:15]:  # Use first 15 as samples
                feature_samples.append(f"{eng_key}: {persian_value}")
            feature_samples_str = "\n\n".join(feature_samples)
            
            system_msg = f"""تو یک متخصص تطبیق ویژگی‌های محصولات هستی.

            محصول مورد نظر: {product_name if product_name else 'نامشخص'}
            
            ویژگی‌های موجود در دیکشنری:
            {feature_samples_str}
            
            قوانین تطبیق:
            ۱. ویژگی‌های ترجمه شده را با ویژگی‌های موجود در دیکشنری مقایسه کن
            ۲. بهترین تطبیق را پیدا کن (حتی اگر ۷۰٪ مشابه باشد)
            ۳. فقط نام انگلیسی ویژگی از دیکشنری را برگردان
            ۴. اگر تطبیق مناسبی پیدا نکردی، نزدیک‌ترین مورد را انتخاب کن
            ۵. هیچ توضیح اضافی نده
            ۶. حتماً یک پاسخ بده، حتی اگر مطمئن نیستی
            
            مثال:
            اگر ویژگی "resolution" ترجمه شده و در دیکشنری "display_resolution" وجود دارد، "display_resolution" را برگردان"""
            
            user_content = f"""ویژگی‌های ترجمه شده برای تطبیق:
            {', '.join(product_features_english_translation)}
            
            لطفاً بهترین تطبیق را از دیکشنری پیدا کن:"""
            
            response = await self.client.chat.completions.create(
                model=os.getenv("OPENAI_MODEL") or os.getenv("CHAT_MODEL") or "gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_msg},
                    {"role": "user", "content": user_content}
                ]
            )
            
            # Parse the response
            result = response.choices[0].message.content.strip()
            
            # Check if result is in the features_dict
            if result in features_dict:
                return result
            elif result.lower() == "none" or result.lower() == "null":
                return None
            else:
                # Try to find partial match with better logic
                best_match = None
                best_score = 0
                
                for eng_key in features_dict.keys():
                    # Check for exact substring match
                    if result.lower() in eng_key.lower():
                        if len(result) / len(eng_key) > best_score:
                            best_match = eng_key
                            best_score = len(result) / len(eng_key)
                    elif eng_key.lower() in result.lower():
                        if len(eng_key) / len(result) > best_score:
                            best_match = eng_key
                            best_score = len(eng_key) / len(result)
                    # Check for word-level matching
                    elif any(word in eng_key.lower() for word in result.lower().split('_')):
                        if 0.5 > best_score:  # Lower threshold for word matching
                            best_match = eng_key
                            best_score = 0.5
                
                return best_match if best_score > 0.3 else None
            
        except Exception as e:
            print(f"Error finding feature name: {e}")
            return None

    async def _find_features_with_llm(self, random_key, product_features, extra_features_dict, product_name=None):
        product_features_english_translation =  await self.translation_features_to_english(product_features, product_name)
        feature_name = await self.find_feature_name(product_features_english_translation, extra_features_dict)
        return feature_name

    async def process_query(self, query: str) -> Response:
        result = await self._extract_product_name_and_features(query)
        product_name, product_features = result["product_name"], result["features"]
        product_result = await self.search_product(product_name)
        product_result_random_key = product_result['random_key'] if product_result else None
        result_requested_features_list = await self._search_features(product_result_random_key, product_features, product_name) if product_result_random_key else []
        
        # Create response message
        if result_requested_features_list:
            # Convert list to string format
            if isinstance(result_requested_features_list, list):
                msg = str(result_requested_features_list[0]) if len(result_requested_features_list) == 1 else (',').join(result_requested_features_list)
            else:
                msg = str(result_requested_features_list)
        else:
            msg = f"هیچ ویژگی‌ای برای محصول '{product_name}' یافت نشد."
        
        return Response(message=msg, base_random_keys=[], member_random_keys=[])

import time

async def main():
    prompt_template = PromptTemplate(
        input_variables=["query"],
        template="از متن زیر نام محصول و ویژگی‌های خواسته‌شده را استخراج کن و فقط خروجی را به صورت JSON زیر بده:\n{\"product_name\": ..., \"features\": [...]}\nمتن: {{ query }}",
        template_format="jinja2"
    )

    agent = FeatureProductAgent(prompt_template)

    test_queries = [
        "آیا محصول باکس 60لیتری سایز همه مدل سایز - نارنجی / ۱۰اینچ به صورت نو موجود است یا دست دوم؟"
    ]

    for query in test_queries:
        start = time.time()
        response = await agent.process_query(query)
        print(f"Query: {query}\nResponse: {response}\n")
        end = time.time()
        print(f"Processing time: {end - start:.2f} seconds\n{'-'*40}")

if __name__ == "__main__":
    asyncio.run(main())
