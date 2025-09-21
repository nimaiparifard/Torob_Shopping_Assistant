"""
Test script for router configuration with environment variables
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from router.config import get_router_config_from_env, validate_config, print_config_summary


async def test_router_config():
    """Test router configuration loading"""
    print("🧪 تست پیکربندی Router با متغیرهای محیطی\n")
    
    # Validate environment variables
    if not validate_config():
        print("❌ پیکربندی نامعتبر!")
        return
    
    # Load configuration
    config = get_router_config_from_env()
    print_config_summary()
    
    print(f"\n📋 جزئیات پیکربندی:")
    print(f"  - API Key: {'✅ تنظیم شده' if config.openai_api_key else '❌ تنظیم نشده'}")
    print(f"  - Base URL: {config.openai_base_url}")
    print(f"  - Embedding Model: {config.embedding_model}")
    print(f"  - LLM Model: {config.llm_model}")
    print(f"  - آستانه پایین: {config.similarity_threshold_low}")
    print(f"  - آستانه بالا: {config.similarity_threshold_high}")
    print(f"  - حداکثر دور: {config.max_turns}")
    print(f"  - دور اجبار نتیجه: {config.force_conclusion_turn}")
    print(f"  - Top-K exemplars: {config.top_k_exemplars}")
    print(f"  - استفاده از Qdrant: {config.use_qdrant}")
    
    if config.use_qdrant and config.qdrant_url:
        print(f"  - Qdrant URL: {config.qdrant_url}")
        print(f"  - Qdrant Collection: {config.qdrant_collection}")
    
    print("\n✅ تست پیکربندی با موفقیت انجام شد!")


if __name__ == "__main__":
    asyncio.run(test_router_config())
