"""
Memory Monitor for Optimized load_db.py

This script monitors memory usage when running the optimized database loader
and compares it with the original version.

Usage:
    python monitor_optimized_load.py
    python monitor_optimized_load.py --chunk-size 5000
    python monitor_optimized_load.py --table base_products

Author: Torob AI Team
"""

import psutil
import time
import subprocess
import sys
import threading
import os
import argparse


class OptimizedMemoryMonitor:
    """Memory monitor for optimized database loading."""
    
    def __init__(self, interval: float = 0.5):
        """
        Initialize memory monitor.
        
        Args:
            interval: Monitoring interval in seconds
        """
        self.interval = interval
        self.monitoring = False
        self.memory_samples: list = []
        self.peak_memory = 0.0
        self.start_time = None
        self.end_time = None
        
    def start_monitoring(self, process_id: int):
        """Start monitoring memory usage for a specific process."""
        self.process_id = process_id
        self.monitoring = True
        self.start_time = time.time()
        
        def monitor_loop():
            while self.monitoring:
                try:
                    process = psutil.Process(self.process_id)
                    memory_info = process.memory_info()
                    
                    # Get memory usage in MB
                    memory_mb = memory_info.rss / (1024 * 1024)
                    self.memory_samples.append(memory_mb)
                    
                    # Update peak memory
                    if memory_mb > self.peak_memory:
                        self.peak_memory = memory_mb
                    
                    # Print real-time memory usage every 10 seconds
                    if len(self.memory_samples) % 20 == 0:  # Every 10 seconds (20 * 0.5s)
                        print(f"📊 Current RAM: {memory_mb:.1f} MB | Peak: {self.peak_memory:.1f} MB")
                    
                    time.sleep(self.interval)
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    # Process ended or access denied
                    break
                except Exception as e:
                    print(f"⚠️ Monitoring error: {e}")
                    break
        
        # Start monitoring in a separate thread
        self.monitor_thread = threading.Thread(target=monitor_loop, daemon=True)
        self.monitor_thread.start()
    
    def stop_monitoring(self):
        """Stop monitoring and calculate statistics."""
        self.monitoring = False
        self.end_time = time.time()
        
        if hasattr(self, 'monitor_thread') and self.monitor_thread.is_alive():
            self.monitor_thread.join(timeout=1.0)
    
    def get_statistics(self) -> dict:
        """Get comprehensive memory usage statistics."""
        if not self.memory_samples:
            return {
                'peak_memory_mb': 0,
                'average_memory_mb': 0,
                'min_memory_mb': 0,
                'duration_seconds': 0,
                'sample_count': 0,
                'memory_growth_mb': 0
            }
        
        # Calculate memory growth (end - start)
        memory_growth = 0
        if len(self.memory_samples) > 1:
            memory_growth = self.memory_samples[-1] - self.memory_samples[0]
        
        return {
            'peak_memory_mb': round(self.peak_memory, 2),
            'average_memory_mb': round(sum(self.memory_samples) / len(self.memory_samples), 2),
            'min_memory_mb': round(min(self.memory_samples), 2),
            'duration_seconds': round(self.end_time - self.start_time, 2) if self.end_time and self.start_time else 0,
            'sample_count': len(self.memory_samples),
            'memory_growth_mb': round(memory_growth, 2)
        }


def run_optimized_load_with_monitoring(chunk_size: int = 10000, table_name: str = None):
    """Run optimized load_db.py with memory monitoring."""
    print("🔍 Memory Monitor for Optimized load_db.py")
    print("=" * 60)
    print("📊 This will monitor RAM usage during optimized database loading")
    print(f"⏱️  Monitoring interval: 0.5 seconds")
    print(f"📦 Chunk size: {chunk_size:,} rows")
    if table_name:
        print(f"🎯 Loading only table: {table_name}")
    print()
    
    # Check if we're in production mode
    production_mode = os.getenv('PRODUCTION', 'false').lower() == 'true'
    if production_mode:
        print("🏭 Running in PRODUCTION mode (database: /database/torob.db)")
    else:
        print("🛠️  Running in DEVELOPMENT mode (database: ./data/torob.db)")
    
    print()
    
    try:
        # Build command
        cmd = [sys.executable, '-m', 'db.load_db_optimized', '--chunk-size', str(chunk_size)]
        if table_name:
            cmd.extend(['--table', table_name])
        
        print(f"🚀 Starting: {' '.join(cmd)}")
        print()
        
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            universal_newlines=True
        )
        
        # Start memory monitoring
        monitor = OptimizedMemoryMonitor(interval=0.5)
        monitor.start_monitoring(process.pid)
        
        print("📝 Script Output:")
        print("-" * 40)
        
        # Stream output in real-time
        while True:
            output = process.stdout.readline()
            if output == '' and process.poll() is not None:
                break
            if output:
                print(output.strip())
        
        # Wait for process to complete
        return_code = process.wait()
        
        # Stop monitoring
        monitor.stop_monitoring()
        
        # Get final statistics
        stats = monitor.get_statistics()
        
        return return_code, stats
        
    except Exception as e:
        print(f"❌ Error running optimized load_db.py: {e}")
        return 1, {}


def format_optimized_stats(stats: dict) -> str:
    """Format detailed memory statistics for display."""
    if not stats:
        return "No memory data available"
    
    peak_mb = stats.get('peak_memory_mb', 0)
    avg_mb = stats.get('average_memory_mb', 0)
    min_mb = stats.get('min_memory_mb', 0)
    duration = stats.get('duration_seconds', 0)
    growth = stats.get('memory_growth_mb', 0)
    
    # Convert to GB for large values
    peak_gb = peak_mb / 1024
    avg_gb = avg_mb / 1024
    
    return f"""
📊 OPTIMIZED LOADER MEMORY STATISTICS
{'=' * 60}
🔝 Peak Memory Usage:    {peak_mb:8.2f} MB ({peak_gb:.3f} GB)
📈 Average Memory Usage: {avg_mb:8.2f} MB ({avg_gb:.3f} GB)
📉 Minimum Memory Usage: {min_mb:8.2f} MB
📊 Memory Growth:        {growth:8.2f} MB
⏱️  Duration:             {duration:8.2f} seconds
📊 Sample Count:         {stats.get('sample_count', 0):8d} samples
{'=' * 60}
💡 PEAK RAM REQUIRED: {peak_mb:.2f} MB ({peak_gb:.3f} GB)
"""


def get_optimization_recommendations(peak_mb: float, chunk_size: int) -> str:
    """Get optimization recommendations based on peak usage."""
    recommendations = []
    
    if peak_mb > 1024:  # More than 1GB
        recommendations.append("⚠️  HIGH MEMORY USAGE: Consider reducing chunk size")
        recommendations.append(f"💡 Try: --chunk-size {chunk_size // 2}")
        recommendations.append("💡 Or process tables individually: --table <table_name>")
    elif peak_mb > 512:  # More than 512MB
        recommendations.append("⚠️  MODERATE-HIGH MEMORY USAGE")
        recommendations.append("💡 Current chunk size is reasonable")
        recommendations.append("💡 Monitor memory usage in production")
    elif peak_mb > 256:  # More than 256MB
        recommendations.append("✅ MODERATE MEMORY USAGE")
        recommendations.append("💡 Good memory efficiency")
        recommendations.append("💡 You could try increasing chunk size for speed")
    else:
        recommendations.append("✅ EXCELLENT MEMORY EFFICIENCY")
        recommendations.append("💡 Very low memory usage")
        recommendations.append("💡 Consider increasing chunk size for better performance")
    
    # Chunk size recommendations
    recommendations.append("")
    recommendations.append("🔧 CHUNK SIZE RECOMMENDATIONS:")
    if peak_mb > 1024:
        recommended_chunk = max(chunk_size // 2, 1000)
        recommendations.append(f"💡 Reduce chunk size: --chunk-size {recommended_chunk}")
    elif peak_mb < 256:
        recommended_chunk = min(chunk_size * 2, 50000)
        recommendations.append(f"💡 Increase chunk size for speed: --chunk-size {recommended_chunk}")
    else:
        recommendations.append(f"💡 Current chunk size ({chunk_size:,}) is optimal")
    
    # Docker recommendations
    recommendations.append("")
    recommendations.append("🐳 DOCKER RECOMMENDATIONS:")
    recommended_ram = max(int(peak_mb * 1.5), 512)
    recommendations.append(f"💡 Set --memory={recommended_ram}m in docker run")
    recommendations.append(f"💡 Or memory: {recommended_ram}m in docker-compose.yml")
    
    return "\n".join(recommendations)


def main():
    """Main function to run optimized load_db.py with memory monitoring."""
    parser = argparse.ArgumentParser(
        description="Memory monitor for optimized database loader",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python monitor_optimized_load.py
  python monitor_optimized_load.py --chunk-size 5000
  python monitor_optimized_load.py --table base_products
  python monitor_optimized_load.py --table cities --chunk-size 20000
        """
    )
    
    parser.add_argument(
        '--chunk-size',
        type=int,
        default=10000,
        help='Number of rows to process in each chunk (default: 10000)'
    )
    
    parser.add_argument(
        '--table',
        help='Load only specific table (e.g., cities, base_products)'
    )
    
    args = parser.parse_args()
    
    print("🔍 Optimized Load Database Memory Monitor")
    print("=" * 60)
    
    # Check if psutil is available
    try:
        import psutil
    except ImportError:
        print("❌ Error: psutil is required for memory monitoring")
        print("📦 Install it with: pip install psutil")
        sys.exit(1)
    
    # Run optimized load_db.py with monitoring
    return_code, stats = run_optimized_load_with_monitoring(
        chunk_size=args.chunk_size,
        table_name=args.table
    )
    
    # Display results
    print("\n" + "=" * 60)
    print("✅ Optimized database loading completed")
    print(f"🚪 Exit code: {return_code}")
    
    if stats:
        print(format_optimized_stats(stats))
        
        # Get recommendations
        peak_mb = stats.get('peak_memory_mb', 0)
        print(get_optimization_recommendations(peak_mb, args.chunk_size))
        
        # Save results to file
        with open('../optimized_memory_report.txt', 'w', encoding='utf-8') as f:
            f.write("Optimized Load Database Memory Usage Report\n")
            f.write("=" * 50 + "\n\n")
            f.write(format_optimized_stats(stats))
            f.write("\n" + get_optimization_recommendations(peak_mb, args.chunk_size))
        
        print(f"\n📄 Detailed report saved to: optimized_memory_report.txt")
    else:
        print("❌ No memory statistics available")
    
    return return_code


if __name__ == "__main__":
    sys.exit(main())
