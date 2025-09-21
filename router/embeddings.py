"""
Embedding service for semantic similarity
Uses OpenAI embeddings or alternative models
"""

import numpy as np
from typing import List, Dict, Optional, Union
from openai import AsyncOpenAI
import asyncio
from functools import lru_cache
import hashlib
from .base import RouterConfig


class EmbeddingService:
    """Service for generating and caching embeddings"""
    
    def __init__(self, config: RouterConfig):
        self.config = config
        self.client = AsyncOpenAI(
            api_key=config.openai_api_key,
            base_url=config.openai_base_url
        )
        self.model = config.embedding_model
        self._embedding_cache: Dict[str, np.ndarray] = {}
    
    def _get_cache_key(self, text: str) -> str:
        """Generate cache key for text"""
        return hashlib.md5(f"{self.model}:{text}".encode()).hexdigest()
    
    async def get_embedding(self, text: str) -> np.ndarray:
        """Get embedding for a single text"""
        # Check cache first
        cache_key = self._get_cache_key(text)
        if cache_key in self._embedding_cache:
            return self._embedding_cache[cache_key]
        
        # Clean and prepare text
        text = text.strip()
        if not text:
            return np.zeros(1536)  # Default dimension for text-embedding-3-small
        
        try:
            response = await self.client.embeddings.create(
                model=self.model,
                input=text,
                encoding_format="float"
            )
            embedding = np.array(response.data[0].embedding)
            
            # Cache the result
            self._embedding_cache[cache_key] = embedding
            
            return embedding
            
        except Exception as e:
            print(f"خطا در دریافت embedding: {e}")
            # Return zero vector on error
            return np.zeros(1536)
    
    async def get_embeddings_batch(self, texts: List[str]) -> List[np.ndarray]:
        """Get embeddings for multiple texts efficiently"""
        # Separate cached and uncached texts
        results = [None] * len(texts)
        uncached_texts = []
        uncached_indices = []
        
        for i, text in enumerate(texts):
            cache_key = self._get_cache_key(text)
            if cache_key in self._embedding_cache:
                results[i] = self._embedding_cache[cache_key]
            else:
                uncached_texts.append(text)
                uncached_indices.append(i)
        
        # Get embeddings for uncached texts
        if uncached_texts:
            try:
                # OpenAI supports batch processing
                response = await self.client.embeddings.create(
                    model=self.model,
                    input=uncached_texts,
                    encoding_format="float"
                )
                
                # Process and cache results
                for idx, embedding_data in enumerate(response.data):
                    embedding = np.array(embedding_data.embedding)
                    original_idx = uncached_indices[idx]
                    results[original_idx] = embedding
                    
                    # Cache the result
                    cache_key = self._get_cache_key(uncached_texts[idx])
                    self._embedding_cache[cache_key] = embedding
                    
            except Exception as e:
                print(f"خطا در دریافت دسته ای embeddings: {e}")
                # Fill with zero vectors on error
                for idx in uncached_indices:
                    results[idx] = np.zeros(1536)
        
        return results
    
    @staticmethod
    def cosine_similarity(vec1: np.ndarray, vec2: np.ndarray) -> float:
        """Calculate cosine similarity between two vectors"""
        # Handle zero vectors
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return float(np.dot(vec1, vec2) / (norm1 * norm2))
    
    async def find_most_similar(
        self,
        query_embedding: np.ndarray,
        candidate_embeddings: List[np.ndarray],
        top_k: int = 3
    ) -> List[tuple[int, float]]:
        """
        Find top-k most similar embeddings
        Returns list of (index, similarity_score) tuples
        """
        similarities = []
        
        for idx, candidate in enumerate(candidate_embeddings):
            sim = self.cosine_similarity(query_embedding, candidate)
            similarities.append((idx, sim))
        
        # Sort by similarity (descending)
        similarities.sort(key=lambda x: x[1], reverse=True)
        
        return similarities[:top_k]
    
    def clear_cache(self):
        """Clear the embedding cache"""
        self._embedding_cache.clear()
    
    def get_cache_size(self) -> int:
        """Get number of cached embeddings"""
        return len(self._embedding_cache)
