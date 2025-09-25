#!/usr/bin/env python3
"""
Clear corrupted embedding cache files

This script removes corrupted pickle cache files that might be causing
EOFError: Ran out of input errors.
"""

import os
import glob

def clear_cache_files():
    """Clear all embedding cache files"""
    cache_files = [
        "embeddings_cache.pkl",
        "agents/embeddings_cache.pkl",
        "**/embeddings_cache.pkl"
    ]
    
    cleared_files = []
    
    for pattern in cache_files:
        files = glob.glob(pattern, recursive=True)
        for file_path in files:
            try:
                if os.path.exists(file_path):
                    os.remove(file_path)
                    cleared_files.append(file_path)
                    print(f"✅ Cleared: {file_path}")
            except Exception as e:
                print(f"❌ Error clearing {file_path}: {e}")
    
    if cleared_files:
        print(f"\n🎉 Successfully cleared {len(cleared_files)} cache file(s)")
    else:
        print("\n📝 No cache files found to clear")

if __name__ == "__main__":
    print("🧹 Clearing corrupted embedding cache files...")
    clear_cache_files()
    print("\n✨ Done! You can now run your application again.")
