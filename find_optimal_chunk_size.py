"""
Find Optimal Chunk Size for Memory Usage < 2GB

This script tests different chunk sizes to find the optimal one that keeps
memory usage under 2GB while maintaining good performance.

Author: Torob AI Team
"""

import subprocess
import sys
import time
import os
import re


def test_chunk_size(table_name: str, chunk_size: int) -> dict:
    """Test a specific chunk size and return memory statistics."""
    print(f"\n🧪 Testing {table_name} with chunk size: {chunk_size:,}")
    print("-" * 50)
    
    try:
        # Run the optimized loader with monitoring
        cmd = [
            sys.executable, 'monitor_optimized_load.py',
            '--table', table_name,
            '--chunk-size', str(chunk_size)
        ]
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='replace',
            timeout=300  # 5 minute timeout
        )
        
        # Parse memory statistics from output
        output = result.stdout + result.stderr
        
        # Extract peak memory usage
        peak_match = re.search(r'Peak Memory Usage:\s+(\d+\.?\d*)\s+MB', output)
        avg_match = re.search(r'Average Memory Usage:\s+(\d+\.?\d*)\s+MB', output)
        duration_match = re.search(r'Duration:\s+(\d+\.?\d*)\s+seconds', output)
        
        if peak_match and avg_match and duration_match:
            peak_mb = float(peak_match.group(1))
            avg_mb = float(avg_match.group(1))
            duration = float(duration_match.group(1))
            
            return {
                'chunk_size': chunk_size,
                'peak_memory_mb': peak_mb,
                'average_memory_mb': avg_mb,
                'duration_seconds': duration,
                'success': True,
                'exit_code': result.returncode
            }
        else:
            return {
                'chunk_size': chunk_size,
                'peak_memory_mb': 0,
                'average_memory_mb': 0,
                'duration_seconds': 0,
                'success': False,
                'exit_code': result.returncode,
                'error': 'Could not parse memory statistics'
            }
            
    except subprocess.TimeoutExpired:
        return {
            'chunk_size': chunk_size,
            'peak_memory_mb': 0,
            'average_memory_mb': 0,
            'duration_seconds': 0,
            'success': False,
            'exit_code': -1,
            'error': 'Timeout after 5 minutes'
        }
    except Exception as e:
        return {
            'chunk_size': chunk_size,
            'peak_memory_mb': 0,
            'average_memory_mb': 0,
            'duration_seconds': 0,
            'success': False,
            'exit_code': -1,
            'error': str(e)
        }


def find_optimal_chunk_size(table_name: str, max_memory_mb: int = 2000) -> dict:
    """Find the optimal chunk size for a given table."""
    print(f"🔍 Finding optimal chunk size for {table_name}")
    print(f"🎯 Target: Peak memory < {max_memory_mb:,} MB")
    print("=" * 60)
    
    # Test different chunk sizes
    chunk_sizes = [500, 1000, 1500, 2000, 2500, 3000, 4000, 5000]
    results = []
    
    for chunk_size in chunk_sizes:
        result = test_chunk_size(table_name, chunk_size)
        results.append(result)
        
        if result['success']:
            peak_gb = result['peak_memory_mb'] / 1024
            print(f"✅ Chunk {chunk_size:,}: Peak {result['peak_memory_mb']:.1f} MB ({peak_gb:.2f} GB), Duration {result['duration_seconds']:.1f}s")
            
            # If we're under the memory limit, this is a good candidate
            if result['peak_memory_mb'] < max_memory_mb:
                print(f"   🎯 Under memory limit! Good candidate.")
        else:
            print(f"❌ Chunk {chunk_size:,}: Failed - {result.get('error', 'Unknown error')}")
        
        # Small delay between tests
        time.sleep(1)
    
    # Find the best result
    successful_results = [r for r in results if r['success'] and r['peak_memory_mb'] < max_memory_mb]
    
    if not successful_results:
        print(f"\n❌ No chunk size found that keeps memory under {max_memory_mb:,} MB")
        # Return the result with lowest memory usage
        successful_results = [r for r in results if r['success']]
        if not successful_results:
            return {'optimal_chunk_size': 1000, 'reason': 'No successful tests'}
    
    # Sort by peak memory usage (ascending) then by duration (ascending)
    best_result = min(successful_results, key=lambda x: (x['peak_memory_mb'], x['duration_seconds']))
    
    print(f"\n🏆 OPTIMAL CHUNK SIZE FOUND!")
    print(f"   Chunk Size: {best_result['chunk_size']:,} rows")
    print(f"   Peak Memory: {best_result['peak_memory_mb']:.1f} MB ({best_result['peak_memory_mb']/1024:.2f} GB)")
    print(f"   Average Memory: {best_result['average_memory_mb']:.1f} MB")
    print(f"   Duration: {best_result['duration_seconds']:.1f} seconds")
    
    return {
        'optimal_chunk_size': best_result['chunk_size'],
        'peak_memory_mb': best_result['peak_memory_mb'],
        'average_memory_mb': best_result['average_memory_mb'],
        'duration_seconds': best_result['duration_seconds'],
        'all_results': results
    }


def test_all_tables_optimal() -> dict:
    """Test optimal chunk sizes for all major tables."""
    print("🔍 Finding optimal chunk sizes for all tables")
    print("🎯 Target: Peak memory < 2,000 MB for each table")
    print("=" * 60)
    
    # Tables to test (in order of size/complexity)
    tables_to_test = [
        'cities',      # Small
        'brands',      # Small
        'categories',  # Small
        'shops',       # Medium
        'base_products', # Large
        'members',     # Very Large
        'searches',    # Large
        'base_views',  # Medium
        'final_clicks' # Small
    ]
    
    optimal_sizes = {}
    
    for table in tables_to_test:
        print(f"\n{'='*20} Testing {table.upper()} {'='*20}")
        result = find_optimal_chunk_size(table, max_memory_mb=2000)
        optimal_sizes[table] = result['optimal_chunk_size']
        
        # Small delay between table tests
        time.sleep(2)
    
    print(f"\n🎯 OPTIMAL CHUNK SIZES SUMMARY")
    print("=" * 60)
    for table, chunk_size in optimal_sizes.items():
        print(f"{table:15}: {chunk_size:6,} rows")
    
    # Find the most conservative (smallest) chunk size that works for all
    conservative_chunk_size = min(optimal_sizes.values())
    print(f"\n💡 CONSERVATIVE CHUNK SIZE: {conservative_chunk_size:,} rows")
    print(f"   This size should work for all tables with memory < 2GB")
    
    return {
        'table_specific': optimal_sizes,
        'conservative': conservative_chunk_size,
        'recommendation': f"Use chunk size {conservative_chunk_size:,} for all tables"
    }


def main():
    """Main function to find optimal chunk sizes."""
    print("🚀 Chunk Size Optimization Tool")
    print("=" * 60)
    
    # Check if we're in production mode
    production_mode = os.getenv('PRODUCTION', 'false').lower() == 'true'
    if production_mode:
        print("🏭 Running in PRODUCTION mode")
    else:
        print("🛠️  Running in DEVELOPMENT mode")
    
    print()
    
    # Test all tables
    results = test_all_tables_optimal()
    
    # Save results to file
    with open('optimal_chunk_sizes.txt', 'w') as f:
        f.write("Optimal Chunk Sizes for Memory < 2GB\n")
        f.write("=" * 40 + "\n\n")
        f.write("Table-specific recommendations:\n")
        for table, chunk_size in results['table_specific'].items():
            f.write(f"{table}: {chunk_size:,} rows\n")
        f.write(f"\nConservative recommendation: {results['conservative']:,} rows\n")
        f.write(f"\nThis conservative size should work for all tables.\n")
    
    print(f"\n📄 Results saved to: optimal_chunk_sizes.txt")
    
    return results


if __name__ == "__main__":
    main()
