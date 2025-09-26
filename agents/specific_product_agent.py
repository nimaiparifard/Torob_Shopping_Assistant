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
from system_prompts.extract_name_system_prompt import extracting_name_system_prompt, extracting_name_samples
from system_prompts.find_important_part_system_prompt import find_important_part_system_prompt, \
    find_important_part_samples

dotenv.load_dotenv()


class SpecificProductAgent:
    def __init__(self, db_path: str | None = None, embedding_similarity=None):
        self.db_path = db_path or os.getenv("PRODUCTS_DB_PATH") or "products.db"
        self._conn = None
        self.client = AsyncOpenAI(
            api_key=os.getenv("OPENAI_API_KEY"),
            base_url=os.getenv("OPENAI_URL"),
        )
        self.embedding_similarity = embedding_similarity or EmbeddingSimilarity(
            embedding_service if 'embedding_service' in globals() else EmbeddingService({
                'OPENAI_API_KEY': os.getenv("OPENAI_API_KEY"),
                'OPENAI_URL': os.getenv("OPENAI_URL")
            })
        )
        from db.base import DatabaseBaseLoader
        self.db = DatabaseBaseLoader()

    async def _extract_product_name(self, query: str) -> str:
        """
        Use LLM with strong system prompt and few-shot learning. Returns ONLY product name or 'نامشخص'.
        """
        if not query or not query.strip():
            return "نامشخص"

        try:
            # استفاده از نمونه‌ها برای few-shot learning
            few_shot_examples = "\n".join([
                f"ورودی: {sample['input']}\nخروجی: {sample['extracted_name']}"
                for sample in extracting_name_samples[:5]  # استفاده از 5 نمونه اول
            ])

            user_content = f"{few_shot_examples}\n\nورودی: {query}\nخروجی:"

            model_name = os.getenv("OPENAI_MODEL") or os.getenv("CHAT_MODEL") or "gpt-4o-mini"

            resp = await self.client.chat.completions.create(
                model=model_name,
                messages=[
                    {"role": "system", "content": extracting_name_system_prompt},
                    {"role": "user", "content": user_content}
                ],
                temperature=0
            )

            extracted = (resp.choices[0].message.content or "").strip()

            # اگر خروجی خالی است یا فقط فاصله، نامشخص برگردان
            if not extracted or extracted.isspace():
                return "نامشخص"

            # حذف کاراکترهای اضافی احتمالی
            extracted = extracted.strip('"\'`')

            return extracted if extracted else "نامشخص"

        except Exception as e:
            print(f"Error in _extract_product_name: {e}")
            return "نامشخص"

    async def _extract_most_important_part(self, product_name: str) -> List[str]:
        """Return list of important parts (phrases) of product name using LLM."""
        if not product_name or product_name == "نامشخص":
            return []

        try:
            # استفاده از نمونه‌ها برای few-shot learning
            few_shot_examples = "\n".join([
                f"ورودی: {sample['input']}\nخروجی:\n" + "\n".join(sample['important_parts'])
                for sample in find_important_part_samples[:3]  # استفاده از 3 نمونه اول
            ])

            user_content = f"{few_shot_examples}\n\nورودی: {product_name}\nخروجی:"

            model_name = os.getenv("OPENAI_MODEL") or os.getenv("CHAT_MODEL") or "gpt-4o-mini"

            resp = await self.client.chat.completions.create(
                model=model_name,
                messages=[
                    {"role": "system", "content": find_important_part_system_prompt},
                    {"role": "user", "content": user_content}
                ],
                temperature=0
            )

            raw = (resp.choices[0].message.content or "").strip()
            if not raw or raw == "نامشخص":
                return []

            # Normalize lines, drop header variants
            lines = [l.strip() for l in raw.splitlines() if l.strip()]
            cleaned = []
            for l in lines:
                if l.startswith("بخش") or l.startswith("نام محصول") or l.startswith("ورودی") or l.startswith("خروجی"):
                    continue
                cleaned.append(l)

            # Deduplicate preserving order
            seen = set()
            parts = []
            for c in cleaned:
                if c not in seen:
                    seen.add(c)
                    parts.append(c)
            return parts

        except Exception as e:
            print(f"Error in _extract_most_important_part: {e}")
            return []

    async def search_product(self, product_name: str) -> Dict[str, Any]:
        """
        Exact match -> progressive LIKE (truncate from end) -> embedding similarity ranking.
        """
        if not product_name or product_name == "نامشخص":
            return {}

        # Exact match
        try:
            result = self.db.query(
                "SELECT random_key, persian_name FROM base_products WHERE persian_name = ? LIMIT 1",
                (product_name,)
            )
            if result:
                return {
                    "random_key": result[0]["random_key"],
                    "persian_name": result[0]["persian_name"],
                    "similarity": 1.0,
                    "match_type": "exact",
                }
        except Exception:
            pass

        # IMPORTANT PARTS BASED LIKE SEARCH (before progressive token truncation)
        important_parts = await self._extract_most_important_part(product_name)
        part_candidates = []
        total_parts = len([p for p in important_parts if len(p) > 1])
        if total_parts:
            start = time.time()
            import itertools
            # Use unique parts (order preserved) and keep only length > 1
            unique_parts = [p for p in dict.fromkeys(important_parts) if len(p) > 1]
            seen_keys = set()
            max_combos = 200  # safety cap to avoid explosion
            for idx, (part, part2, part3) in enumerate(itertools.combinations(unique_parts, 3)):
                if idx >= max_combos:
                    break
                like_pattern = f"%{part}%"
                like_pattern_2 = f"%{part2}%"
                like_pattern_3 = f"%{part3}%"
                try:
                    rows = self.db.query(
                        "SELECT random_key, persian_name FROM base_products "
                        "WHERE persian_name LIKE ? AND persian_name LIKE ? AND persian_name LIKE ?",
                        (like_pattern, like_pattern_2, like_pattern_3)
                    )
                except Exception:
                    rows = []

                if len(rows) == 1:
                    chosen = rows[0]
                    return {
                        "random_key": chosen["random_key"],
                        "persian_name": chosen["persian_name"],
                        "similarity": 1,
                        "match_type": "fuzzy"
                    }
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
                if part_candidates and len(part_candidates) > len(temp_part_candidates) and temp_part_candidates:
                    part_candidates = temp_part_candidates

            if len(part_candidates) >= 40:
                print(" i am here")
                for idx, (part, part2, part3, part4) in enumerate(itertools.combinations(unique_parts, 4)):
                    if idx >= max_combos:
                        break
                    like_pattern = f"%{part}%"
                    like_pattern_2 = f"%{part2}%"
                    like_pattern_3 = f"%{part3}%"
                    like_pattern_4 = f"%{part4}%"
                    try:
                        rows = self.db.query(
                            "SELECT random_key, persian_name FROM base_products "
                            "WHERE persian_name LIKE ? AND persian_name LIKE ? AND persian_name LIKE ? AND persian_name LIKE ?",
                            (like_pattern, like_pattern_2, like_pattern_3, like_pattern_4)
                        )
                    except Exception:
                        rows = []

                    if len(rows) == 1:
                        chosen = rows[0]
                        return {
                            "random_key": chosen["random_key"],
                            "persian_name": chosen["persian_name"],
                            "similarity": 1,
                            "match_type": "fuzzy"
                        }
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
                    if part_candidates and len(part_candidates) > len(temp_part_candidates) and temp_part_candidates:
                        part_candidates = temp_part_candidates

            if len(part_candidates) == 1:
                chosen = part_candidates[0]
                return {
                    "random_key": chosen["random_key"],
                    "persian_name": chosen["persian_name"],
                    "similarity": 1,
                    "match_type": "fuzzy"
                }

            if part_candidates:
                q_emb = await self.embedding_similarity.get_embedding(product_name)
                cand_names = [c["persian_name"] for c in part_candidates]
                cand_embs = await self.embedding_similarity.get_embeddings_batch(cand_names)
                best = self.embedding_similarity.find_most_similar(q_emb, cand_embs)
                if best["index"] >= 0:
                    chosen = part_candidates[best["index"]]
                    return {
                        "random_key": chosen["random_key"],
                        "persian_name": chosen["persian_name"],
                        "similarity": float(best["similarity"]),
                        "match_type": "fuzzy"
                    }

            if part_candidates:
                embedder = EmbeddingServiceWrapper()
                # q_emb = await self.embedding_similarity.get_embedding(product_name)
                cand_names = [c["persian_name"] for c in part_candidates]
                p = [product_name, ]
                c = await build_hnsw_from_texts(cand_names, embedder, metric='cosine', m=32, ef_construction=300,
                                                ef_search=128)
                hits = await semantic_search(c, p, embedder, top_k=1)
                if hits[0][0]['score'] > 0.7:
                    chosen = part_candidates[hits[0][0]['id']]
                    return {
                        "random_key": chosen["random_key"],
                        "persian_name": chosen["persian_name"],
                        "similarity": float(hits[0][0]['score']),
                        "match_type": "fuzzy"
                    }

            if len(part_candidates) == 0:  # Avoid too many candidates
                for idx, (part, part2) in enumerate(itertools.combinations(unique_parts, 2)):
                    if idx >= max_combos:
                        break
                    like_pattern = f"%{part}%"
                    like_pattern_2 = f"%{part2}%"
                    try:
                        rows = self.db.query(
                            "SELECT random_key, persian_name FROM base_products "
                            "WHERE persian_name LIKE ? AND persian_name LIKE ? AND persian_name LIKE ?",
                            (like_pattern, like_pattern_2)
                        )
                    except Exception:
                        rows = []
                    if len(rows) == 1:
                        chosen = rows[0]
                        return {
                            "random_key": chosen["random_key"],
                            "persian_name": chosen["persian_name"],
                            "similarity": 1,
                            "match_type": "fuzzy"
                        }
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
                    if part_candidates and len(part_candidates) > len(temp_part_candidates) and temp_part_candidates:
                        part_candidates = temp_part_candidates

            if part_candidates:
                q_emb = await self.embedding_similarity.get_embedding(product_name)
                cand_names = [c["persian_name"] for c in part_candidates]
                cand_embs = await self.embedding_similarity.get_embeddings_batch(cand_names)
                best = self.embedding_similarity.find_most_similar(q_emb, cand_embs)
                if best["index"] >= 0:
                    chosen = part_candidates[best["index"]]
                    return {
                        "random_key": chosen["random_key"],
                        "persian_name": chosen["persian_name"],
                        "similarity": float(best["similarity"]),
                        "match_type": "fuzzy"
                    }


            if len(part_candidates) == 0:  # Avoid too many candidates
                for idx, (part,) in enumerate(itertools.combinations(unique_parts, 1)):
                    if idx >= max_combos:
                        break
                    like_pattern = f"%{part}%"
                    try:
                        rows = self.db.query(
                            "SELECT random_key, persian_name FROM base_products "
                            "WHERE persian_name LIKE ? LIMIT 100",
                            (like_pattern,)
                        )
                    except Exception:
                        rows = []
                    for r in rows:
                        rk = r["random_key"]
                        if rk in seen_keys:
                            continue
                        seen_keys.add(rk)
                        part_candidates.append({
                            "random_key": rk,
                            "persian_name": r["persian_name"],
                        })

            if part_candidates:
                embedder = EmbeddingServiceWrapper()
                # q_emb = await self.embedding_similarity.get_embedding(product_name)
                cand_names = [c["persian_name"] for c in part_candidates]
                p = [product_name, ]
                c = await build_hnsw_from_texts(cand_names, embedder, metric='cosine', m=32,
                                                ef_construction=300,
                                                ef_search=128)
                hits = await semantic_search(c, p, embedder, top_k=1)
                if hits[0][0]['score'] > 0.7:
                    chosen = part_candidates[hits[0][0]['id']]
                    return {
                        "random_key": chosen["random_key"],
                        "persian_name": chosen["persian_name"],
                        "similarity": float(hits[0][0]['score']),
                        "match_type": "fuzzy"
                    }

                    # Compute best scored candidate without sorting dicts
            end = time.time()
            print(
                f"Important parts DB search time: {end - start:.2f} seconds, found {len(part_candidates)} candidates from {total_parts} parts")
            # print(part_candidates)
            if part_candidates:
                embedder = EmbeddingServiceWrapper()
                # q_emb = await self.embedding_similarity.get_embedding(product_name)
                cand_names = [c["persian_name"] for c in part_candidates]
                p = [product_name, ]
                c = await build_hnsw_from_texts(cand_names, embedder, metric='cosine', m=32, ef_construction=300,
                                                ef_search=128)
                hits = await semantic_search(c, p, embedder, top_k=1)
                if hits[0][0]['score'] > 0.7:
                    chosen = part_candidates[hits[0][0]['id']]
                    return {
                        "random_key": chosen["random_key"],
                        "persian_name": chosen["persian_name"],
                        "similarity": float(hits[0][0]['score']),
                        "match_type": "fuzzy"
                    }

        # Progressive LIKE fallback
        tokens = product_name.split()
        tokens = self.trim_trailing_stopwords(tokens)
        candidates = []
        while tokens:
            prefix = " ".join(tokens)
            like_pattern = f"{prefix}%"
            try:
                result = self.db.query(
                    "SELECT random_key, persian_name FROM base_products WHERE persian_name LIKE ? LIMIT 100",
                    (like_pattern,)
                )
                if result:
                    print(len(result))
                    for r in result:
                        candidates.append({"random_key": r["random_key"], "persian_name": r["persian_name"]})
                    break
            except Exception:
                pass
            tokens.pop()

        if not candidates:
            return {}

        # Embedding similarity (if embedding service configured)
        try:
            q_emb = await self.embedding_similarity.get_embedding(product_name)
            cand_names = [c["persian_name"] for c in candidates]
            cand_embs = await self.embedding_similarity.get_embeddings_batch(cand_names)
            best = self.embedding_similarity.find_most_similar(q_emb, cand_embs)
            if best["index"] >= 0:
                chosen = candidates[best["index"]]
                return {
                    "random_key": chosen["random_key"],
                    "persian_name": chosen["persian_name"],
                    "similarity": float(best["similarity"]),
                    "match_type": "fuzzy"
                }
        except Exception:
            # Fallback: pick  name overlap
            chosen = max(candidates, key=lambda c: len(c["persian_name"]))
            return {
                "random_key": chosen["random_key"],
                "persian_name": chosen["persian_name"],
                "similarity": 0.0,
                "match_type": "fallback"
            }
        return {}

    def norm(self, token: str) -> str:
        """Normalize token by removing punctuation and standardizing characters"""
        PUNCTUATION_PATTERN = re.compile(r'[^\w\u0600-\u06FF]+')
        t = token.strip()
        t = t.replace('ي', 'ی').replace('ك', 'ک')
        t = PUNCTUATION_PATTERN.sub('', t)
        return t

    def trim_trailing_stopwords(self, tokens):
        """Remove ALL stopwords from anywhere in the token list"""
        # Expanded list of common Persian stopwords
        STOPWORDS = {
            'و', 'با', 'که', 'برای', 'از', 'تا', 'در', 'به', 'یک', 'را', 'است', 'هست',
        }

        # Create a copy to avoid modifying the original list
        tokens = tokens.copy()

        # Filter out stopwords from anywhere in the list
        filtered_tokens = []
        for token in tokens:
            normalized_token = self.norm(token)

            # Check if the normalized token is a stopword
            if normalized_token not in STOPWORDS and token not in STOPWORDS:
                filtered_tokens.append(token)

        return filtered_tokens

    async def process_query(self, query: str) -> Response:
        """
        Orchestrate extraction + search.
        """
        product_name = await self._extract_product_name(query)
        result = await self.search_product(product_name)
        base_keys = [result["random_key"]] if result else []
        if result:
            msg = "null"
        else:
            msg = "محصولی یافت نشد"
        # Optionally could log important_parts
        return Response(message=msg, base_random_keys=base_keys, member_random_keys=[])


import asyncio

embedding_service = EmbeddingService({
    'OPENAI_API_KEY': os.getenv("OPENAI_API_KEY"),
    'OPENAI_URL': os.getenv("OPENAI_URL")
})


async def main():
    prompt_template = PromptTemplate(
        input_variables=["query"],
        template="از متن زیر فقط نام محصول را استخراج کن: {{ query }}",
        template_format="jinja2"
    )
    agent = SpecificProductAgent(prompt_template)

    test_queries = [
        "من دنبال فرشینه مخمل با ترمزگیر و عرض ۱ متر، طرح آشپزخانه با کد ۰۴ هستم.",
        # "پرده با طرح چتر و برج ایفل و کد W4838 را می‌خواستم.",
        # "من دنبال فرشینه مخمل با ترمزگیر و عرض ۱ متر، طرح آشپزخانه با کد ۰۴ هستم.",
        # "شمع تزیینی شمعدونی پیچی سبز با ارتفاع ۲۵ سانتی‌متر که ۱ عددی است را می‌خواهم.",
    ]

    for query in test_queries:
        start = time.time()
        response = await agent.process_query(query)
        print(f"Query: {query}\nResponse: {response}\n")
        end = time.time()
        print(f"Processing time: {end - start:.2f} seconds\n{'-' * 40}")


if __name__ == "__main__":
    asyncio.run(main())