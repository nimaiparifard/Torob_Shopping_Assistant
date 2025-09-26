import base64
import requests
import os
import logging
from openai import AsyncOpenAI
from typing import Dict, Any
import dotenv
from agents.image_examples import images
from system_prompts.extract_category_from_image_system_prompt import extract_category_from_image_system_prompt
from system_prompts.extract_brand_from_image_system_prompt import extract_brand_from_image_system_prompt
from system_prompts.extract_phrased_name_from_image_system_prompt import extract_phrased_name_from_image_system_prompt
from system_prompts.extract_final_dedicion_product_image_system_prompt import extract_final_dedicion_product_image_system_prompt
from response_format import Response
from db.base import DatabaseBaseLoader
from features_list import features_dict
from agents.specific_product_agent import SpecificProductAgent
import os
import sys
import time
import json
from typing import Dict, Any, List
import re
from openai import AsyncOpenAI
from langchain.prompts import PromptTemplate
import dotenv

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from response_format import Response
from embedding.classic_embedding import EmbeddingService, EmbeddingSimilarity
from embedding.faiss_embedding import EmbeddingServiceWrapper, build_hnsw_from_texts, semantic_search

dotenv.load_dotenv()

logger = logging.getLogger(__name__)


class ProductImageAgent(SpecificProductAgent):
    def __init__(self):
        super().__init__()

    def get_base64_encoded_image(self, image_url: str) -> str:
        """
        Download image from URL and encode it to base64.
        """
        try:
            response = requests.get(image_url)
            response.raise_for_status()
            image_data = response.content
            base64_image = base64.b64encode(image_data).decode("utf-8")
            assert base64.b64decode(base64_image) == image_data
            return base64_image
        except Exception as e:
            print(f"Error downloading image: {e}")
            return None

    async def _map_image_to_category(self, base64_image):
        """Map image to category using vision API and database lookup."""
        try:
            # Call OpenAI Vision API to extract category
            response = await self.client.chat.completions.create(
                model="gpt-40-mini",
                messages=[
                    {
                        "role": "system",
                        "content": extract_category_from_image_system_prompt
                    },
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": "دسته‌بندی این محصول چیست؟"
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{base64_image}"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=200,
                temperature=0.1
            )
            
            # Parse the JSON response
            import json
            import re
            try:
                response_content = response.choices[0].message.content
                logger.info(f"Category extraction response: {response_content}")
                
                # Try to extract JSON from the response if it's wrapped in markdown or has extra text
                json_match = re.search(r'\{.*\}', response_content, re.DOTALL)
                if json_match:
                    json_content = json_match.group(0)
                else:
                    json_content = response_content
                
                category_data = json.loads(json_content)
                category_name = category_data.get("category_name", "نامشخص")
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse category JSON response: {e}")
                logger.error(f"Response content: {response.choices[0].message.content}")
                category_name = "نامشخص"
            
            # Map category_name to database
            if category_name == "نامشخص":
                return None, "نامشخص"
            
            # Query database to find matching category
            db = DatabaseBaseLoader()
            try:
                # Try exact match first
                results = db.query(
                    "SELECT id, title FROM categories WHERE title = ?", 
                    (category_name,)
                )
                
                if results:
                    return results[0]['id'], results[0]['title']
                
                # Try partial match
                results = db.query(
                    "SELECT id, title FROM categories WHERE title LIKE ?", 
                    (f"%{category_name}%",)
                )
                
                if results:
                    return results[0]['id'], results[0]['title']
                
                # If no match found, return unknown
                return None, "نامشخص"
                
            finally:
                db.close()
                
        except Exception as e:
            logger.error(f"Error in _map_image_to_category: {e}")
            return None, "نامشخص"

    async def _map_image_to_brand_id(self, base64_image):
        """Map image to brand using vision API and database lookup."""
        try:
            # Call OpenAI Vision API to extract brand
            response = await self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {
                        "role": "system",
                        "content": extract_brand_from_image_system_prompt
                    },
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": "برند این محصول چیست؟"
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{base64_image}"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=200,
                temperature=0.1
            )
            
            # Parse the JSON response
            import json
            import re
            try:
                response_content = response.choices[0].message.content
                logger.info(f"Brand extraction response: {response_content}")
                
                # Try to extract JSON from the response if it's wrapped in markdown or has extra text
                json_match = re.search(r'\{.*\}', response_content, re.DOTALL)
                if json_match:
                    json_content = json_match.group(0)
                else:
                    json_content = response_content
                
                brand_data = json.loads(json_content)
                brand_name = brand_data.get("brand_name", "نامشخص")
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse brand JSON response: {e}")
                logger.error(f"Response content: {response.choices[0].message.content}")
                brand_name = "نامشخص"
            
            # Map brand_name to database
            if brand_name in ["نامشخص", "بدون برند"]:
                return None, "نامشخص"
            
            # Query database to find matching brand
            db = DatabaseBaseLoader()
            try:
                # Try exact match first
                results = db.query(
                    "SELECT id, title FROM brands WHERE title = ?", 
                    (brand_name,)
                )
                
                if results:
                    return results[0]['id'], results[0]['title']
                
                # Try partial match
                results = db.query(
                    "SELECT id, title FROM brands WHERE title LIKE ?", 
                    (f"%{brand_name}%",)
                )
                
                if results:
                    return results[0]['id'], results[0]['title']
                
                # Try case-insensitive match
                results = db.query(
                    "SELECT id, title FROM brands WHERE LOWER(title) = LOWER(?)", 
                    (brand_name,)
                )
                
                if results:
                    return results[0]['id'], results[0]['title']
                
                # If no match found, return unknown
                return None, "نامشخص"
                
            finally:
                db.close()
                
        except Exception as e:
            logger.error(f"Error in _map_image_to_brand_id: {e}")
            return None, "نامشخص"

    async def _get_phrased_name_of_the_image(self, base64_image, category_name, brand_name):
        """Extract 5 phrased names of the main product in the image."""
        try:
            # Prepare context information for better results
            context_info = ""
            if category_name and category_name != "نامشخص":
                context_info += f"دسته‌بندی محصول: {category_name}\n"
            if brand_name and brand_name != "نامشخص":
                context_info += f"برند محصول: {brand_name}\n"
            
            # Prepare the user message
            user_message = "نام‌های مختلف و عبارات کلیدی محصول اصلی در این تصویر را استخراج کن."
            if context_info:
                user_message += f"\n\nاطلاعات اضافی:\n{context_info}"
            
            # Call OpenAI Vision API to extract phrased names
            response = await self.client.chat.completions.create(
                model="gpt-40-mini",
                messages=[
                    {
                        "role": "system",
                        "content": extract_phrased_name_from_image_system_prompt
                    },
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": user_message
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{base64_image}"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=500,
                temperature=0.1
            )
            
            # Parse the JSON response
            import json
            import re
            
            try:
                response_content = response.choices[0].message.content
                logger.info(f"Raw response content: {response_content}")
                
                # Try to extract JSON from the response if it's wrapped in markdown or has extra text
                json_match = re.search(r'\{.*\}', response_content, re.DOTALL)
                if json_match:
                    json_content = json_match.group(0)
                    logger.info(f"Extracted JSON content: {json_content}")
                else:
                    json_content = response_content
                
                phrased_data = json.loads(json_content)
                phrased_names = phrased_data.get("phrased_names", [])
                confidence = phrased_data.get("confidence", "نامشخص")
                
                logger.info(f"Parsed phrased_names: {phrased_names}")
                logger.info(f"Parsed confidence: {confidence}")
                
                # Validate that we got the expected data
                if not isinstance(phrased_names, list):
                    logger.warning(f"phrased_names is not a list: {type(phrased_names)}")
                    phrased_names = []
                
                return phrased_names
                
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse phrased names JSON response: {e}")
                logger.error(f"Response content that failed to parse: {response_content}")
                
                # Try to extract names manually as a fallback
                try:
                    # Look for quoted strings that might be product names
                    quoted_names = re.findall(r'"([^"]+)"', response_content)
                    if quoted_names:
                        logger.info(f"Extracted names as fallback: {quoted_names}")
                        return quoted_names[:5]  # Return up to 5 names
                except Exception as fallback_error:
                    logger.error(f"Fallback extraction also failed: {fallback_error}")
                
                return []
                
        except Exception as e:
            logger.error(f"Error in _get_phrased_name_of_the_image: {e}")
            return []


    async def _get_candidate_product(self, phrased_name_of_the_image, category_id, brand_id):
        """Find candidate products matching phrased names using exact, fuzzy, and embedding search."""
        if not phrased_name_of_the_image:
            return []
        
        all_candidates = []
        db = DatabaseBaseLoader()
        
        try:
            for phrased_name in phrased_name_of_the_image:
                if not phrased_name:
                    continue
                    
                # Try exact match first
                try:
                    if category_id and brand_id:
                        result = db.query(
                            "SELECT random_key, persian_name FROM base_products WHERE persian_name = ? AND category_id = ? AND brand_id = ? LIMIT 1",
                            (phrased_name, category_id, brand_id)
                        )
                    elif category_id:
                        result = db.query(
                            "SELECT random_key, persian_name FROM base_products WHERE persian_name = ? AND category_id = ? LIMIT 1",
                            (phrased_name, category_id)
                        )
                    elif brand_id:
                        result = db.query(
                            "SELECT random_key, persian_name FROM base_products WHERE persian_name = ? AND brand_id = ? LIMIT 1",
                            (phrased_name, brand_id)
                        )
                    else:
                        result = db.query(
                            "SELECT random_key, persian_name FROM base_products WHERE persian_name = ? LIMIT 1",
                            (phrased_name,)
                        )
                    
                    if result:
                        all_candidates.append({
                            "random_key": result[0]["random_key"],
                            "persian_name": result[0]["persian_name"],
                            "similarity": 1.0,
                            "match_type": "exact"
                        })
                        continue
                except Exception:
                    pass

                # Extract important parts for fuzzy matching
                important_parts = await self._extract_most_important_part(phrased_name)
                part_candidates = []
                total_parts = len([p for p in important_parts if len(p) > 1])
                
                if total_parts:
                    import itertools
                    # Use unique parts (order preserved) and keep only length > 1
                    unique_parts = [p for p in dict.fromkeys(important_parts) if len(p) > 1]
                    seen_keys = set()
                    max_combos = 200  # safety cap to avoid explosion
                    
                    # Try 3-part combinations first
                    for idx, (part, part2, part3) in enumerate(itertools.combinations(unique_parts, 3)):
                        if idx >= max_combos:
                            break
                        like_pattern = f"%{part}%"
                        like_pattern_2 = f"%{part2}%"
                        like_pattern_3 = f"%{part3}%"
                        
                        try:
                            if category_id and brand_id:
                                rows = db.query(
                                    "SELECT random_key, persian_name FROM base_products "
                                    "WHERE persian_name LIKE ? AND persian_name LIKE ? AND persian_name LIKE ? AND category_id = ? AND brand_id = ?",
                                    (like_pattern, like_pattern_2, like_pattern_3, category_id, brand_id)
                                )
                            elif category_id:
                                rows = db.query(
                                    "SELECT random_key, persian_name FROM base_products "
                                    "WHERE persian_name LIKE ? AND persian_name LIKE ? AND persian_name LIKE ? AND category_id = ?",
                                    (like_pattern, like_pattern_2, like_pattern_3, category_id)
                                )
                            elif brand_id:
                                rows = db.query(
                                    "SELECT random_key, persian_name FROM base_products "
                                    "WHERE persian_name LIKE ? AND persian_name LIKE ? AND persian_name LIKE ? AND brand_id = ?",
                                    (like_pattern, like_pattern_2, like_pattern_3, brand_id)
                                )
                            else:
                                rows = db.query(
                                    "SELECT random_key, persian_name FROM base_products "
                                    "WHERE persian_name LIKE ? AND persian_name LIKE ? AND persian_name LIKE ? LIMIT 5",
                                    (like_pattern, like_pattern_2, like_pattern_3)
                                )
                        except Exception:
                            rows = []

                        if len(rows) == 1:
                            chosen = rows[0]
                            all_candidates.append({
                                "random_key": chosen["random_key"],
                                "persian_name": chosen["persian_name"],
                                "similarity": 0.9,
                                "match_type": "fuzzy_3part"
                            })
                            continue

                        temp_part_candidates = []
                        for r in rows:
                            rk = r["random_key"]
                            if rk in seen_keys:
                                continue
                            seen_keys.add(rk)
                            temp_part_candidates.append({
                                "random_key": rk,
                                "persian_name": r["persian_name"],
                            })
                        
                        if len(part_candidates) == 0 and temp_part_candidates:
                            part_candidates = temp_part_candidates
                        elif part_candidates and len(part_candidates) > len(temp_part_candidates) and temp_part_candidates:
                            part_candidates = temp_part_candidates

                    # If we have good candidates, use embedding similarity
                    if len(part_candidates) <= 7 and part_candidates:
                        try:
                            q_emb = await self.embedding_similarity.get_embedding(phrased_name)
                            cand_names = [c["persian_name"] for c in part_candidates]
                            cand_embs = await self.embedding_similarity.get_embeddings_batch(cand_names)
                            best = self.embedding_similarity.find_most_similar(q_emb, cand_embs)
                            if best["index"] >= 0:
                                chosen = part_candidates[best["index"]]
                                all_candidates.append({
                                    "random_key": chosen["random_key"],
                                    "persian_name": chosen["persian_name"],
                                    "similarity": best["similarity"],
                                    "match_type": "embedding_3part"
                                })
                                continue
                        except Exception:
                            pass

                    # Try 2-part combinations
                    for idx, (part, part2) in enumerate(itertools.combinations(unique_parts, 2)):
                        if idx >= max_combos:
                            break
                        like_pattern = f"%{part}%"
                        like_pattern_2 = f"%{part2}%"
                        
                        try:
                            if category_id and brand_id:
                                rows = db.query(
                                    "SELECT random_key, persian_name FROM base_products "
                                    "WHERE persian_name LIKE ? AND persian_name LIKE ? AND category_id = ? AND brand_id = ?",
                                    (like_pattern, like_pattern_2, category_id, brand_id)
                                )
                            elif category_id:
                                rows = db.query(
                                    "SELECT random_key, persian_name FROM base_products "
                                    "WHERE persian_name LIKE ? AND persian_name LIKE ? AND category_id = ?",
                                    (like_pattern, like_pattern_2, category_id)
                                )
                            elif brand_id:
                                rows = db.query(
                                    "SELECT random_key, persian_name FROM base_products "
                                    "WHERE persian_name LIKE ? AND persian_name LIKE ? AND brand_id = ?",
                                    (like_pattern, like_pattern_2, brand_id)
                                )
                            else:
                                rows = db.query(
                                    "SELECT random_key, persian_name FROM base_products "
                                    "WHERE persian_name LIKE ? AND persian_name LIKE ? LIMIT 5",
                                    (like_pattern, like_pattern_2)
                                )
                        except Exception:
                            rows = []
                            
                        if len(rows) == 1:
                            chosen = rows[0]
                            all_candidates.append({
                                "random_key": chosen["random_key"],
                                "persian_name": chosen["persian_name"],
                                "similarity": 0.8,
                                "match_type": "fuzzy_2part"
                            })
                            continue
                            
                        temp_part_candidates = []
                        for r in rows:
                            rk = r["random_key"]
                            if rk in seen_keys:
                                continue
                            seen_keys.add(rk)
                            temp_part_candidates.append({
                                "random_key": rk,
                                "persian_name": r["persian_name"],
                            })
                        
                        if len(part_candidates) == 0 and temp_part_candidates:
                            part_candidates = temp_part_candidates
                        elif part_candidates and len(part_candidates) > len(temp_part_candidates) and temp_part_candidates:
                            part_candidates = temp_part_candidates

                    # Final embedding similarity check
                    if part_candidates:
                        try:
                            q_emb = await self.embedding_similarity.get_embedding(phrased_name)
                            cand_names = [c["persian_name"] for c in part_candidates]
                            cand_embs = await self.embedding_similarity.get_embeddings_batch(cand_names)
                            best = self.embedding_similarity.find_most_similar(q_emb, cand_embs)
                            if best["index"] >= 0:
                                chosen = part_candidates[best["index"]]
                                all_candidates.append({
                                    "random_key": chosen["random_key"],
                                    "persian_name": chosen["persian_name"],
                                    "similarity": best["similarity"],
                                    "match_type": "embedding_2part"
                                })
                        except Exception:
                            pass

            # Remove duplicates and return top candidates (max 2 per phrased name)
            seen_keys = set()
            final_candidates = []
            for candidate in all_candidates:
                if candidate["random_key"] not in seen_keys:
                    seen_keys.add(candidate["random_key"])
                    final_candidates.append(candidate)
                    if len(final_candidates) >= 10:  # Limit total candidates
                        break
            
            return final_candidates
            
        finally:
            db.close()

    async def _get_features_of_candidate_product(self, candidate_products):
        """Get features for candidate products and convert feature names to Persian."""
        if not candidate_products:
            return []
        
        features_list = []
        db = DatabaseBaseLoader()
        
        try:
            for candidate in candidate_products:
                random_key = candidate.get("random_key")
                if not random_key:
                    continue
                
                # Get product features from database
                try:
                    result = db.query(
                        "SELECT extra_features FROM base_products WHERE random_key = ?",
                        (random_key,)
                    )
                    
                    if result and result[0]["extra_features"]:
                        # Parse JSON features
                        import json
                        try:
                            features_json = json.loads(result[0]["extra_features"])
                            
                            # Convert feature names to Persian using features_dict
                            persian_features = {}
                            for key, value in features_json.items():
                                persian_key = features_dict.get(key, key)  # Use original key if not found in dict
                                persian_features[persian_key] = value
                            
                            features_list.append({
                                "random_key": random_key,
                                "persian_name": candidate.get("persian_name", ""),
                                "features": persian_features,
                                "similarity": candidate.get("similarity", 0),
                                "match_type": candidate.get("match_type", "")
                            })
                        except json.JSONDecodeError:
                            # If JSON parsing fails, add empty features
                            features_list.append({
                                "random_key": random_key,
                                "persian_name": candidate.get("persian_name", ""),
                                "features": {},
                                "similarity": candidate.get("similarity", 0),
                                "match_type": candidate.get("match_type", "")
                            })
                    else:
                        # No features found
                        features_list.append({
                            "random_key": random_key,
                            "persian_name": candidate.get("persian_name", ""),
                            "features": {},
                            "similarity": candidate.get("similarity", 0),
                            "match_type": candidate.get("match_type", "")
                        })
                        
                except Exception as e:
                    logger.error(f"Error getting features for {random_key}: {e}")
                    # Add entry with empty features
                    features_list.append({
                        "random_key": random_key,
                        "persian_name": candidate.get("persian_name", ""),
                        "features": {},
                        "similarity": candidate.get("similarity", 0),
                        "match_type": candidate.get("match_type", "")
                    })
            
            return features_list
            
        finally:
            db.close()

    async def _get_final_dicision(self, base64_image, candidate_products, features_candidate_products, category_name, brand_name):
        """Make final decision on best matching product using vision API and candidate comparison."""
        if not candidate_products or not features_candidate_products:
            return None
        
        try:
            # Prepare context information
            context_info = ""
            if category_name and category_name != "نامشخص":
                context_info += f"دسته‌بندی محصول: {category_name}\n"
            if brand_name and brand_name != "نامشخص":
                context_info += f"برند محصول: {brand_name}\n"
            
            # Prepare candidate products information for the prompt
            candidates_info = "محصولات کاندید:\n"
            for i, (candidate, features) in enumerate(zip(candidate_products, features_candidate_products), 1):
                candidates_info += f"\n{i}. نام محصول: {candidate.get('persian_name', 'نامشخص')}\n"
                candidates_info += f"   کلید تصادفی: {candidate.get('random_key', 'نامشخص')}\n"
                candidates_info += f"   امتیاز شباهت: {candidate.get('similarity', 0)}\n"
                candidates_info += f"   نوع تطبیق: {candidate.get('match_type', 'نامشخص')}\n"
                
                if features.get('features'):
                    candidates_info += "   ویژگی‌ها:\n"
                    for feature_name, feature_value in features['features'].items():
                        candidates_info += f"     - {feature_name}: {feature_value}\n"
                else:
                    candidates_info += "   ویژگی‌ها: هیچ ویژگی‌ای یافت نشد\n"
            
            # Prepare the user message
            user_message = f"تصویر را با محصولات کاندید زیر مقایسه کن و بهترین تطبیق را انتخاب کن:\n\n{candidates_info}"
            if context_info:
                user_message += f"\n\nاطلاعات اضافی:\n{context_info}"
            
            # Call OpenAI Vision API to make final decision
            response = await self.client.chat.completions.create(
                model="gpt-40-mini",
                messages=[
                    {
                        "role": "system",
                        "content": extract_final_dedicion_product_image_system_prompt
                    },
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": user_message
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{base64_image}"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=1000,
                temperature=0.1
            )
            
            # Parse the JSON response
            import json
            import re
            try:
                response_content = response.choices[0].message.content
                logger.info(f"Decision response: {response_content}")
                
                # Try to extract JSON from the response if it's wrapped in markdown or has extra text
                json_match = re.search(r'\{.*\}', response_content, re.DOTALL)
                if json_match:
                    json_content = json_match.group(0)
                else:
                    json_content = response_content
                
                decision_data = json.loads(json_content)
                selected_product = decision_data.get("selected_product", {})
                random_key = selected_product.get("random_key")
                
                if random_key and random_key != "null":
                    return random_key
                else:
                    # If no product selected, return the best candidate based on similarity
                    if candidate_products:
                        best_candidate = max(candidate_products, key=lambda x: x.get('similarity', 0))
                        return best_candidate.get('random_key')
                    return None
                    
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse final decision JSON response: {e}")
                logger.error(f"Response content: {response_content}")
                # Fallback to best similarity match
                if candidate_products:
                    best_candidate = max(candidate_products, key=lambda x: x.get('similarity', 0))
                    return best_candidate.get('random_key')
                return None
                
        except Exception as e:
            logger.error(f"Error in _get_final_dicision: {e}")
            # Fallback to best similarity match
            if candidate_products:
                best_candidate = max(candidate_products, key=lambda x: x.get('similarity', 0))
                return best_candidate.get('random_key')
            return None

    async def process_query(self, query: str, image_data: str) -> Response:
        """
        Process user query about an image.

        Args:
            query: User's question about the image
            image_data: Base64 encoded image data, data URL, or URL of the image to analyze

        Returns:
            Answer about the image based on the query
        """
        try:
            # Check if image_data is a data URL, URL, or raw base64
            if image_data.startswith('data:image/'):
                # Extract base64 data from data URL
                try:
                    header, base64_image = image_data.split(',', 1)
                    logger.info(f"Extracted base64 data from data URL: {len(base64_image)} characters")
                except ValueError:
                    return Response(message="فرمت داده تصویر نامعتبر است.", base_random_keys=[], member_random_keys=[])
            elif image_data.startswith(('http://', 'https://')):
                # Download and encode image from URL
                base64_image = self.get_base64_encoded_image(image_data)
                if not base64_image:
                    return Response(message="متأسفم، نتوانستم تصویر را دانلود کنم. لطفاً URL تصویر را بررسی کنید.", base_random_keys=[], member_random_keys=[])
            else:
                # Assume it's already base64 encoded data
                base64_image = image_data

            # Process the image through the product identification pipeline
            category_id, category_name = None, None
            brand_id, brand_name = None, None
            # category_id, category_name = await self._map_image_to_category(base64_image)
            # print(f"Category name: {category_name if category_name else 'پیدا نشد'}")
            # brand_id, brand_name = await self._map_image_to_brand_id(base64_image)
            # print(f"Brand name: {brand_name if  brand_name else "پیدا نشد."}")
            phrased_name_of_the_image = await self._get_phrased_name_of_the_image(base64_image, category_name, brand_name)
            candidate_products = await self._get_candidate_product(phrased_name_of_the_image, category_id, brand_id)
            features_candidate_products = await self._get_features_of_candidate_product(candidate_products)
            random_key = await self._get_final_dicision(base64_image, candidate_products, features_candidate_products, category_name, brand_name)
            return Response(message="null", base_random_keys=[random_key] if random_key else [], member_random_keys=[])

        except Exception as e:
            print(f"Error in process_image_query: {e}")
            return Response(message=f"متأسفم، خطایی در تحلیل تصویر رخ داد: {str(e)}", base_random_keys=[], member_random_keys=[])

    async def identify_main_object(self, image_data: str) -> Response:
        """
        Identify the main object or concept in the image.
        This is a specialized method for the specific query type.
        """
        query = "شیء و مفهوم اصلی در تصویر چیست؟"
        return await self.process_query(query, image_data)

    async def analyze_product_in_image(self, image_data: str) -> Response:
        """
        Analyze if there's a product in the image and provide details.
        """
        query = "آیا در این تصویر محصولی وجود دارد؟ اگر بله، جزئیات آن را شرح بده."
        return await self.process_query(query, image_data)

    async def get_image_description(self, image_data: str) -> Response:
        """
        Get a general description of the image.
        """
        query = "این تصویر را به طور کامل و دقیق توصیف کن."
        return await self.process_query(query, image_data)


# Test function
async def test_image_agent():
    """
    Test the ImageAgent with the provided example.
    """
    agent = ProductImageAgent()

    # Test with the provided example

    # image_url = "https://image.torob.com/base/images/jd/W6/jdW63jxVXQDuO6V6.jpg"
    # query = "شیء و مفهوم اصلی در تصویر چیست؟"
    for p in images:
        query = p['query']
        image =p['image']
        print("🖼️ Testing Image Agent")
        print("=" * 40)
        print(f"Query: {p['query']}")
        print("\nAnalyzing image...")

        try:
            response = await agent.process_query(query, image)
            print(f"\nResponse: {response}")
        except Exception as e:
            print(f"Error: {e}")

        # Test other methods
        print("\n" + "=" * 40)
        print("Testing other analysis methods...")

        try:
            main_object = await agent.identify_main_object(image)
            print(f"\nMain Object: {main_object}")

            product_analysis = await agent.analyze_product_in_image(image)
            print(f"\nProduct Analysis: {product_analysis}")

            description = await agent.get_image_description(image)
            print(f"\nGeneral Description: {description}")

        except Exception as e:
            print(f"Error in additional tests: {e}")


if __name__ == "__main__":
    import asyncio

    asyncio.run(test_image_agent())
