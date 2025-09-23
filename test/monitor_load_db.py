"""
Memory Monitor for load_db.py - Track Peak RAM Usage

This script specifically monitors memory usage when running load_db.py
and provides detailed statistics about RAM consumption.

Usage:
    python monitor_load_db.py

Author: Torob AI Team
"""

import psutil
import time
import subprocess
import sys
import threading
from typing import List, Tuple
import os


class LoadDBMemoryMonitor:
    """Memory monitor specifically for load_db.py execution."""
    
    def __init__(self, interval: float = 0.1):
        """
        Initialize memory monitor.
        
        Args:
            interval: Monitoring interval in seconds
        """
        self.interval = interval
        self.monitoring = False
        self.memory_samples: List[float] = []
        self.peak_memory = 0.0
        self.start_time = None
        self.end_time = None
        self.process = None
        
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
                    
                    # Print real-time memory usage every 5 seconds
                    if len(self.memory_samples) % 50 == 0:  # Every 5 seconds (50 * 0.1s)
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


def run_load_db_with_monitoring():
    """Run load_db.py with memory monitoring."""
    print("🔍 Memory Monitor for load_db.py")
    print("=" * 60)
    print("📊 This will monitor RAM usage during database loading")
    print("⏱️  Monitoring interval: 0.1 seconds")
    print()
    
    # Check if we're in production mode
    production_mode = os.getenv('PRODUCTION', 'false').lower() == 'true'
    if production_mode:
        print("🏭 Running in PRODUCTION mode (database: /database/torob.db)")
    else:
        print("🛠️  Running in DEVELOPMENT mode (database: ./data/torob.db)")
    
    print()
    
    try:
        # Start the load_db process
        cmd = [sys.executable, '-m', 'db.load_db']
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
        monitor = LoadDBMemoryMonitor(interval=0.1)
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
        print(f"❌ Error running load_db.py: {e}")
        return 1, {}


def format_detailed_stats(stats: dict) -> str:
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
📊 DETAILED MEMORY USAGE STATISTICS
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


def get_memory_recommendations(peak_mb: float) -> str:
    """Get memory recommendations based on peak usage."""
    recommendations = []
    
    if peak_mb > 2048:  # More than 2GB
        recommendations.append("⚠️  HIGH MEMORY USAGE: Consider optimizing data loading")
        recommendations.append("💡 Suggestion: Process data in smaller chunks")
        recommendations.append("💡 Suggestion: Use streaming data processing")
    elif peak_mb > 1024:  # More than 1GB
        recommendations.append("⚠️  MODERATE-HIGH MEMORY USAGE")
        recommendations.append("💡 Monitor memory usage in production")
        recommendations.append("💡 Consider increasing available RAM")
    elif peak_mb > 512:  # More than 512MB
        recommendations.append("✅ MODERATE MEMORY USAGE")
        recommendations.append("💡 Memory usage is reasonable for most systems")
    else:
        recommendations.append("✅ LOW MEMORY USAGE")
        recommendations.append("💡 Excellent memory efficiency")
    
    # Docker/Production recommendations
    recommendations.append("")
    recommendations.append("🐳 DOCKER RECOMMENDATIONS:")
    recommended_ram = max(peak_mb * 1.5, 1024)  # 1.5x peak + minimum 1GB
    recommendations.append(f"💡 Set --memory={int(recommended_ram)}m in docker run")
    recommendations.append(f"💡 Or memory: {int(recommended_ram)}m in docker-compose.yml")
    
    return "\n".join(recommendations)


def main():
    """Main function to run load_db.py with memory monitoring."""
    print("🔍 Load Database Memory Monitor")
    print("=" * 60)
    
    # Check if psutil is available
    try:
        import psutil
    except ImportError:
        print("❌ Error: psutil is required for memory monitoring")
        print("📦 Install it with: pip install psutil")
        sys.exit(1)
    
    # Run load_db.py with monitoring
    return_code, stats = run_load_db_with_monitoring()
    
    # Display results
    print("\n" + "=" * 60)
    print("✅ Database loading completed")
    print(f"🚪 Exit code: {return_code}")
    
    if stats:
        print(format_detailed_stats(stats))
        
        # Get recommendations
        peak_mb = stats.get('peak_memory_mb', 0)
        print(get_memory_recommendations(peak_mb))
        
        # Save results to file
        with open('../memory_usage_report.txt', 'w', encoding='utf-8') as f:
            f.write("Load Database Memory Usage Report\n")
            f.write("=" * 40 + "\n\n")
            f.write(format_detailed_stats(stats))
            f.write("\n" + get_memory_recommendations(peak_mb))
        
        print(f"\n📄 Detailed report saved to: memory_usage_report.txt")
    else:
        print("❌ No memory statistics available")
    
    return return_code


if __name__ == "__main__":
    sys.exit(main())
