from openai import AsyncOpenAI
from typing import List, Dict, Any
import dotenv
import os
import asyncio

dotenv.load_dotenv()

class EmbeddingService:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.client = AsyncOpenAI(
            api_key=config['OPENAI_API_KEY'],
            base_url=os.getenv("OPENAI_URL")
        )
        self.model = os.getenv("EMBEDDING_MODEL")

    async def run(self, text: str):
        response = await self.client.embeddings.create(
            model=self.model,
            input=text,
            encoding_format="float"
        )
        return response

class EmbeddingSimilarity:
    def __init__(self, embedding_service: EmbeddingService):
        self.embedding_service = embedding_service

    async def get_embedding(self, text: str) -> List[float]:
        if not text:
            return []
        resp = await self.embedding_service.run(text)
        return resp.data[0].embedding

    async def get_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        if not texts:
            return []
        tasks = [self.embedding_service.run(t) for t in texts]
        responses = await asyncio.gather(*tasks)
        return [r.data[0].embedding for r in responses]

    @staticmethod
    def calculate_cosine_similarity(emb1: List[float], emb2: List[float]) -> float:
        if not emb1 or not emb2 or len(emb1) != len(emb2):
            return 0.0
        dot = sum(a * b for a, b in zip(emb1, emb2))
        norm1 = sum(a * a for a in emb1) ** 0.5
        norm2 = sum(b * b for b in emb2) ** 0.5
        if norm1 == 0 or norm2 == 0:
            return 0.0
        return dot / (norm1 * norm2)

    def find_most_similar(self, embedding: List[float], exemplar_embeddings: List[List[float]]):
        best_idx = -1
        best_score = -1.0
        for idx, emb in enumerate(exemplar_embeddings):
            score = self.calculate_cosine_similarity(embedding, emb)
            if score > best_score:
                best_score = score
                best_idx = idx
        return {"index": best_idx, "similarity": best_score}