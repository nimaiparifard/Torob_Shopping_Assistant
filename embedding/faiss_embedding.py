import os
import asyncio
from typing import List, Dict, Any, Optional, Tuple
import numpy as np
import faiss
import dotenv
import aiohttp
from aiohttp import ClientSession, TCPConnector
import pickle
import hashlib
from functools import lru_cache

# Try to reuse existing embedding service if available
try:
    from embedding import EmbeddingService as _EmbeddingService
except Exception:  # pragma: no cover - fallback
    _EmbeddingService = None

dotenv.load_dotenv()


# ---------------- Embedding Wrapper (async) ---------------- #
class EmbeddingServiceWrapper:
    """
    Thin wrapper that uses existing EmbeddingService if OPENAI creds are set.
    Falls back to random vectors when credentials or model are missing so that
    FAISS pipeline can still be demonstrated / tested offline.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None, dim_fallback: int = 1536,
                 cache_file: str = "embeddings_cache.pkl"):
        self.dim_fallback = dim_fallback
        self.enabled = bool(
            os.getenv("OPENAI_API_KEY") and os.getenv("EMBEDDING_MODEL")) and _EmbeddingService is not None
        self.svc = None
        self.session = None
        self.semaphore = asyncio.Semaphore(10)  # Limit concurrent requests
        self.cache_file = cache_file
        self.cache = self._load_cache()

        if self.enabled:
            self.svc = _EmbeddingService({
                'OPENAI_API_KEY': os.getenv("OPENAI_API_KEY")
            })

    def _load_cache(self) -> Dict[str, List[float]]:
        """Load embeddings cache from disk"""
        try:
            with open(self.cache_file, 'rb') as f:
                return pickle.load(f)
        except FileNotFoundError:
            return {}

    def _save_cache(self):
        """Save embeddings cache to disk"""
        with open(self.cache_file, 'wb') as f:
            pickle.dump(self.cache, f)

    def _get_cache_key(self, text: str) -> str:
        """Generate cache key for text"""
        return hashlib.md5(text.encode()).hexdigest()

    async def __aenter__(self):
        """Async context manager entry"""
        if self.enabled:
            connector = TCPConnector(limit=100, limit_per_host=30)
            self.session = ClientSession(connector=connector)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()
        # Save cache on exit
        self._save_cache()

    async def embed_one(self, text: str) -> List[float]:
        # Check cache first
        cache_key = self._get_cache_key(text)
        if cache_key in self.cache:
            return self.cache[cache_key]

        if self.enabled:
            resp = await self.svc.run(text)
            result = resp.data[0].embedding  # type: ignore[attr-defined]
        else:
            # fallback deterministic random-ish (hash based seed for stability)
            rng = np.random.default_rng(abs(hash(text)) % (2 ** 32))
            result = rng.standard_normal(self.dim_fallback).astype(np.float32).tolist()

        # Cache the result
        self.cache[cache_key] = result
        return result

    async def embed_batch(self, texts: List[str]) -> np.ndarray:
        if not texts:
            return np.zeros((0, self.dim_fallback), dtype=np.float32)

        # Check cache first
        cached_results = {}
        uncached_texts = []
        uncached_indices = []

        for i, text in enumerate(texts):
            cache_key = self._get_cache_key(text)
            if cache_key in self.cache:
                cached_results[i] = self.cache[cache_key]
            else:
                uncached_texts.append(text)
                uncached_indices.append(i)

        # Get embeddings for uncached texts
        if uncached_texts:
            if self.enabled:
                # Process in smaller chunks to avoid memory issues and improve concurrency
                chunk_size = 100  # Adjust based on your API limits
                uncached_embeddings = []

                for i in range(0, len(uncached_texts), chunk_size):
                    chunk = uncached_texts[i:i + chunk_size]
                    # Use asyncio.gather with semaphore to limit concurrent requests
                    async with self.semaphore:
                        tasks = [self.svc.run(t) for t in chunk]
                        responses = await asyncio.gather(*tasks, return_exceptions=True)

                        # Handle errors gracefully
                        for j, resp in enumerate(responses):
                            if isinstance(resp, Exception):
                                # Fallback to random embedding for failed requests
                                rng = np.random.default_rng(abs(hash(chunk[j])) % (2 ** 32))
                                embedding = rng.standard_normal(self.dim_fallback).astype(np.float32).tolist()
                            else:
                                embedding = resp.data[0].embedding
                            uncached_embeddings.append(embedding)
            else:
                # fallback
                uncached_embeddings = [await self.embed_one(t) for t in uncached_texts]

            # Cache the results
            for idx, embedding in zip(uncached_indices, uncached_embeddings):
                cache_key = self._get_cache_key(texts[idx])
                self.cache[cache_key] = embedding

        # Combine results
        results = [None] * len(texts)
        for i, text in enumerate(texts):
            cache_key = self._get_cache_key(text)
            if cache_key in self.cache:
                results[i] = self.cache[cache_key]

        # Save cache periodically
        if len(self.cache) % 1000 == 0:
            self._save_cache()

        return np.array(results, dtype=np.float32)


# ---------------- FAISS HNSW Index ---------------- #
class FaissHNSWIndex:
    """
    HNSW Approximate Nearest Neighbor index supporting cosine or L2.

    For cosine similarity we L2-normalize vectors and use inner product metric.
    """

    def __init__(self, dim: int, metric: str = 'cosine', m: int = 32,
                 ef_construction: int = 200, ef_search: int = 64, use_id_map: bool = True):
        self.dim = dim
        metric_lower = metric.lower()
        if metric_lower not in ("cosine", "l2", "ip"):
            raise ValueError("metric must be one of: cosine, l2, ip")
        self.metric_mode = metric_lower
        # Choose FAISS metric
        if metric_lower == 'l2':
            faiss_metric = faiss.METRIC_L2
            self.normalize = False
        elif metric_lower == 'ip':  # user explicitly wants raw inner product
            faiss_metric = faiss.METRIC_INNER_PRODUCT
            self.normalize = False
        else:  # cosine
            faiss_metric = faiss.METRIC_INNER_PRODUCT
            self.normalize = True
        base_index = faiss.IndexHNSWFlat(dim, m, faiss_metric)
        # tune HNSW parameters
        hnsw_params = base_index.hnsw
        hnsw_params.efConstruction = ef_construction
        hnsw_params.efSearch = ef_search
        self._ef_search = ef_search
        # Wrap with ID map if we want custom ids
        if use_id_map:
            self.index = faiss.IndexIDMap(base_index)
            self.uses_id_map = True
        else:
            self.index = base_index
            self.uses_id_map = False

        # Pre-allocate arrays for better performance
        self._query_buffer = np.zeros((1, dim), dtype=np.float32)
        self._score_buffer = np.zeros((1, 1), dtype=np.float32)
        self._idx_buffer = np.zeros((1, 1), dtype=np.int64)

    def set_ef_search(self, ef: int):
        self.index.hnsw.efSearch = ef  # type: ignore[attr-defined]
        self._ef_search = ef

    @staticmethod
    def _l2_normalize(mat: np.ndarray) -> np.ndarray:
        norms = np.linalg.norm(mat, axis=1, keepdims=True) + 1e-12
        return mat / norms

    def add(self, vectors: np.ndarray, ids: Optional[List[int]] = None):
        if vectors.dtype != np.float32:
            vectors = vectors.astype(np.float32)
        if self.normalize:
            vectors = self._l2_normalize(vectors)
        if self.uses_id_map:
            if ids is None:
                raise ValueError("ids must be provided when use_id_map=True")
            id_array = np.array(ids, dtype=np.int64)
            if id_array.shape[0] != vectors.shape[0]:
                raise ValueError("ids length mismatch")
            self.index.add_with_ids(vectors, id_array)
        else:
            self.index.add(vectors)

    def search(self, queries: np.ndarray, k: int = 5) -> Tuple[np.ndarray, np.ndarray]:
        if queries.dtype != np.float32:
            queries = queries.astype(np.float32)
        if self.normalize:
            queries = self._l2_normalize(queries)
        scores, idx = self.index.search(queries, k)
        # If cosine, scores are cosine similarity. If L2, they are -L2^2 distances internally? For METRIC_L2 in HNSW, FAISS returns squared L2 distances.
        return scores, idx

    def save(self, path: str):
        faiss.write_index(self.index, path)

    @classmethod
    def load(cls, path: str):  # type: ignore[override]
        index = faiss.read_index(path)
        # Attempt to infer settings (best effort)
        obj = cls(dim=index.d, metric='ip')  # placeholder metric
        obj.index = index
        # Try to detect normalization need by metric type
        # Not always possible; default to no normalization
        obj.normalize = False
        return obj


# ---------------- High-level Builders ---------------- #
async def build_hnsw_from_texts(texts: List[str], embedder: EmbeddingServiceWrapper,
                                metric: str = 'cosine', m: int = 32, ef_construction: int = 200,
                                ef_search: int = 64, ids: Optional[List[int]] = None,
                                batch_size: int = 1000) -> FaissHNSWIndex:
    """Memory-efficient index building with batching"""
    if not texts:
        raise ValueError("No texts provided")

    # Process in batches to avoid memory issues
    all_vectors = []
    all_ids = []

    for i in range(0, len(texts), batch_size):
        batch_texts = texts[i:i + batch_size]
        batch_ids = list(range(i, min(i + batch_size, len(texts)))) if ids is None else ids[i:i + batch_size]

        # Get embeddings for this batch
        batch_vectors = await embedder.embed_batch(batch_texts)
        all_vectors.append(batch_vectors)
        all_ids.extend(batch_ids)

        # Clear memory
        del batch_vectors

    # Concatenate all vectors
    vecs = np.vstack(all_vectors)
    dim = vecs.shape[1]

    if ids is None:
        ids = list(range(len(texts)))
    index = FaissHNSWIndex(dim, metric=metric, m=m, ef_construction=ef_construction, ef_search=ef_search,
                           use_id_map=True)

    # Add vectors in chunks to avoid memory spikes
    chunk_size = 10000
    for i in range(0, len(vecs), chunk_size):
        chunk_vecs = vecs[i:i + chunk_size]
        chunk_ids = all_ids[i:i + chunk_size]
        index.add(chunk_vecs, ids=chunk_ids)

    return index


async def semantic_search(index: FaissHNSWIndex, query_texts: List[str], embedder: EmbeddingServiceWrapper,
                          top_k: int = 5) -> List[List[Dict[str, Any]]]:
    if not query_texts:
        return []

    # Batch embed queries
    q_vecs = await embedder.embed_batch(query_texts)

    # Batch search
    scores, idx = index.search(q_vecs, k=top_k)

    results: List[List[Dict[str, Any]]] = []
    for qi in range(scores.shape[0]):
        row = []
        for j in range(top_k):
            row.append({
                'rank': j + 1,
                'id': int(idx[qi, j]),
                'score': float(scores[qi, j])
            })
        results.append(row)
    return results


# ---------------- Example main ---------------- #
example_texts = [
    "فرش اتاق کودک و نوجوان کد 8153 مخمل تُرک قابل شستشو در ماشین لباسشویی",
    "فرش اتاق کودک و نوجوان طرح 3 بعدی کد 8101",
    "فرش کودک دخترانه نخ اکرلیک طرح عروسکی طوسی",
    "فرش اتاق کودک و نوجوان طرح چشم زخم کد 8147",
    "فرش اتاق کودک و نوجوان کد H505 مخمل تُرک استُپ دار",
    "فرش اتاق کودک و نوجوان طرح مرد عنکبوتی WA-3168",
]


async def _demo():
    query = ["فرش اتاق برای کودک طرح سه بعدی 8101"]

    # Use async context manager for proper resource management
    async with EmbeddingServiceWrapper() as embedder:
        # Build index with optimized parameters
        index = await build_hnsw_from_texts(
            example_texts,
            embedder,
            metric='cosine',
            m=64,  # Higher connectivity for better recall
            ef_construction=400,  # Higher for better quality
            ef_search=128,  # Higher for better search quality
            batch_size=500  # Process in smaller batches
        )

        # Optimized search
        hits = await semantic_search(index, query, embedder, top_k=3)

        print("Query:", query[0])
        print("Results:")
        for h in hits[0]:
            print(f"  rank={h['rank']} id={h['id']} score={h['score']:.4f} text={example_texts[h['id']]}")


if __name__ == "__main__":
    asyncio.run(_demo())
