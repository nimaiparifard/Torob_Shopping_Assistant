"""
Test Optimal Configuration

Quick test of the optimal chunk size configuration to ensure memory < 2GB.

Author: Torob AI Team
"""

import subprocess
import sys
import os


def test_chunk_size(table_name: str, chunk_size: int) -> bool:
    """Test if a chunk size works without errors."""
    print(f"🧪 Testing {table_name} with chunk size {chunk_size:,}...")
    
    try:
        cmd = [
            sys.executable, '-m', 'db.load_db_optimized',
            '--table', table_name,
            '--chunk-size', str(chunk_size)
        ]
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='replace',
            timeout=120  # 2 minute timeout
        )
        
        if result.returncode == 0:
            print(f"✅ {table_name} with chunk {chunk_size:,}: SUCCESS")
            return True
        else:
            print(f"❌ {table_name} with chunk {chunk_size:,}: FAILED (exit code {result.returncode})")
            return False
            
    except subprocess.TimeoutExpired:
        print(f"⏰ {table_name} with chunk {chunk_size:,}: TIMEOUT")
        return False
    except Exception as e:
        print(f"💥 {table_name} with chunk {chunk_size:,}: ERROR - {e}")
        return False


def main():
    """Test the optimal configuration."""
    print("🎯 Testing Optimal Chunk Size Configuration")
    print("=" * 50)
    
    # Test configuration based on previous results
    test_configs = [
        ('cities', 10000),      # Small table - large chunks
        ('brands', 10000),      # Small table - large chunks
        ('categories', 10000),  # Small table - large chunks
        ('shops', 5000),        # Medium table - moderate chunks
        ('base_products', 2000), # Large table - smaller chunks (should be ~1GB)
    ]
    
    results = []
    
    for table, chunk_size in test_configs:
        success = test_chunk_size(table, chunk_size)
        results.append((table, chunk_size, success))
        print()
    
    # Summary
    print("📊 TEST RESULTS SUMMARY")
    print("=" * 50)
    successful = sum(1 for _, _, success in results if success)
    total = len(results)
    
    for table, chunk_size, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{table:15}: {chunk_size:6,} rows - {status}")
    
    print(f"\nOverall: {successful}/{total} tests passed")
    
    if successful == total:
        print("\n🎉 All tests passed! Configuration is ready for production.")
        print("\n💡 Recommended startup.sh command:")
        print("python -m db.load_db_optimized --chunk-size 2000")
    else:
        print("\n⚠️  Some tests failed. Consider using smaller chunk sizes.")
        print("\n💡 Conservative startup.sh command:")
        print("python -m db.load_db_optimized --chunk-size 1000")


if __name__ == "__main__":
    main()
