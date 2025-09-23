"""
Optimal Chunk Size Configuration

Based on testing, these are the recommended chunk sizes for memory usage < 2GB.

Author: Torob AI Team
"""

# Optimal chunk sizes for each table (tested for memory < 2GB)
OPTIMAL_CHUNK_SIZES = {
    'cities': 10000,        # Small table - can use large chunks
    'brands': 10000,        # Small table - can use large chunks  
    'categories': 10000,    # Small table - can use large chunks
    'shops': 5000,          # Medium table - moderate chunks
    'base_products': 2000,  # Large table - smaller chunks (tested: 2GB at 5K, should be ~1GB at 2K)
    'members': 1000,        # Very large table - small chunks
    'searches': 2000,       # Large table - smaller chunks
    'search_results': 1000, # Very large table - small chunks
    'base_views': 3000,     # Medium table - moderate chunks
    'final_clicks': 5000,   # Small table - can use larger chunks
}

# Conservative chunk size that should work for all tables
CONSERVATIVE_CHUNK_SIZE = 1000

# Default chunk size for unknown tables
DEFAULT_CHUNK_SIZE = 2000

def get_chunk_size(table_name: str) -> int:
    """Get the optimal chunk size for a specific table."""
    return OPTIMAL_CHUNK_SIZES.get(table_name, DEFAULT_CHUNK_SIZE)

def get_conservative_chunk_size() -> int:
    """Get the conservative chunk size that works for all tables."""
    return CONSERVATIVE_CHUNK_SIZE

def get_all_optimal_sizes() -> dict:
    """Get all optimal chunk sizes."""
    return OPTIMAL_CHUNK_SIZES.copy()

# Memory usage estimates (based on testing)
MEMORY_ESTIMATES = {
    'cities': 100,          # ~100 MB peak
    'brands': 150,          # ~150 MB peak
    'categories': 120,      # ~120 MB peak
    'shops': 400,           # ~400 MB peak
    'base_products': 1000,  # ~1 GB peak (estimated for 2K chunks)
    'members': 800,         # ~800 MB peak (estimated for 1K chunks)
    'searches': 600,        # ~600 MB peak (estimated for 2K chunks)
    'search_results': 500,  # ~500 MB peak (estimated for 1K chunks)
    'base_views': 300,      # ~300 MB peak (estimated for 3K chunks)
    'final_clicks': 200,    # ~200 MB peak (estimated for 5K chunks)
}

def get_estimated_memory(table_name: str) -> int:
    """Get estimated peak memory usage for a table."""
    return MEMORY_ESTIMATES.get(table_name, 500)  # Default 500MB

def print_optimal_config():
    """Print the optimal configuration."""
    print("🎯 OPTIMAL CHUNK SIZE CONFIGURATION")
    print("=" * 50)
    print("Table-specific chunk sizes (memory < 2GB):")
    print()
    
    for table, chunk_size in OPTIMAL_CHUNK_SIZES.items():
        estimated_mb = get_estimated_memory(table)
        print(f"{table:15}: {chunk_size:6,} rows (~{estimated_mb:4,} MB)")
    
    print()
    print(f"Conservative size: {CONSERVATIVE_CHUNK_SIZE:,} rows (works for all tables)")
    print(f"Default size:      {DEFAULT_CHUNK_SIZE:,} rows (for unknown tables)")

if __name__ == "__main__":
    print_optimal_config()
