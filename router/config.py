"""
Configuration management using environment variables
"""

import os
from typing import Optional
from dotenv import load_dotenv
from .base import RouterConfig

# Load environment variables from .env file
load_dotenv()


def get_router_config_from_env() -> RouterConfig:
    """Create RouterConfig from environment variables"""
    return RouterConfig(
        # OpenAI settings
        openai_api_key=os.getenv("OPENAI_API_KEY", ""),
        openai_base_url=os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1"),
        embedding_model=os.getenv("EMBEDDING_MODEL", "text-embedding-3-small"),
        llm_model=os.getenv("LLM_MODEL", "gpt-4o-mini"),
        
        # Similarity thresholds
        similarity_threshold_low=float(os.getenv("SIMILARITY_THRESHOLD_LOW", "0.3")),
        similarity_threshold_high=float(os.getenv("SIMILARITY_THRESHOLD_HIGH", "0.7")),
        
        # K-NN settings
        top_k_exemplars=int(os.getenv("TOP_K_EXEMPLARS", "3")),
        
        # Turn budget
        max_turns=int(os.getenv("MAX_TURNS", "5")),
        force_conclusion_turn=int(os.getenv("FORCE_CONCLUSION_TURN", "4")),
        
        # Vector store settings
        use_qdrant=os.getenv("USE_QDRANT", "false").lower() == "true",
        qdrant_url=os.getenv("QDRANT_URL"),
        qdrant_collection=os.getenv("QDRANT_COLLECTION", "router_exemplars")
    )


def get_database_path() -> str:
    """Get database path from environment"""
    return os.getenv("DATABASE_PATH", "data/torob.db")


def get_session_cleanup_hours() -> int:
    """Get session cleanup hours from environment"""
    return int(os.getenv("SESSION_CLEANUP_HOURS", "24"))


def validate_config() -> bool:
    """Validate that required environment variables are set"""
    required_vars = [
        "OPENAI_API_KEY"
    ]
    
    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print(f"❌ متغیرهای محیطی زیر تنظیم نشده‌اند: {', '.join(missing_vars)}")
        print("لطفا فایل .env را بررسی کنید.")
        return False
    
    print("✅ تمام متغیرهای محیطی مورد نیاز تنظیم شده‌اند.")
    return True


def print_config_summary():
    """Print configuration summary"""
    config = get_router_config_from_env()
    
    print("🔧 تنظیمات Router:")
    print(f"  - مدل Embedding: {config.embedding_model}")
    print(f"  - مدل LLM: {config.llm_model}")
    print(f"  - آستانه پایین: {config.similarity_threshold_low}")
    print(f"  - آستانه بالا: {config.similarity_threshold_high}")
    print(f"  - حداکثر دور: {config.max_turns}")
    print(f"  - استفاده از Qdrant: {config.use_qdrant}")
    
    if config.openai_base_url != "https://api.openai.com/v1":
        print(f"  - Base URL سفارشی: {config.openai_base_url}")
    
    db_path = get_database_path()
    print(f"  - مسیر دیتابیس: {db_path}")
    
    cleanup_hours = get_session_cleanup_hours()
    print(f"  - پاکسازی جلسات: هر {cleanup_hours} ساعت")
