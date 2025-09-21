"""
Quick Memory Test for load_db.py

A simplified memory monitoring script that runs load_db.py and reports peak RAM usage.

Usage:
    python quick_memory_test.py

Author: Torob AI Team
"""

import psutil
import time
import subprocess
import sys
import threading
import os


def monitor_memory(process_id, duration=30):
    """Monitor memory usage for a specific duration."""
    peak_memory = 0
    samples = []
    
    start_time = time.time()
    
    while time.time() - start_time < duration:
        try:
            process = psutil.Process(process_id)
            memory_mb = process.memory_info().rss / (1024 * 1024)
            samples.append(memory_mb)
            
            if memory_mb > peak_memory:
                peak_memory = memory_mb
            
            time.sleep(0.5)  # Check every 0.5 seconds
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            break
        except Exception:
            break
    
    return peak_memory, samples


def run_quick_test():
    """Run a quick memory test on load_db.py."""
    print("🔍 Quick Memory Test for load_db.py")
    print("=" * 50)
    
    # Check environment
    production_mode = os.getenv('PRODUCTION', 'false').lower() == 'true'
    print(f"Environment: {'PRODUCTION' if production_mode else 'DEVELOPMENT'}")
    print(f"Database: {'/database/torob.db' if production_mode else './data/torob.db'}")
    print()
    
    try:
        # Start load_db process
        cmd = [sys.executable, '-m', 'db.load_db']
        print(f"Starting: {' '.join(cmd)}")
        print()
        
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True
        )
        
        # Monitor memory for up to 60 seconds
        print("Monitoring memory usage...")
        peak_memory, samples = monitor_memory(process.pid, duration=60)
        
        # Wait for process to complete
        stdout, stderr = process.communicate()
        return_code = process.returncode
        
        # Calculate statistics
        if samples:
            avg_memory = sum(samples) / len(samples)
            min_memory = min(samples)
        else:
            avg_memory = min_memory = 0
        
        # Display results
        print("\n" + "=" * 50)
        print("📊 MEMORY USAGE RESULTS")
        print("=" * 50)
        print(f"Peak RAM Usage:    {peak_memory:.2f} MB ({peak_memory/1024:.3f} GB)")
        print(f"Average RAM Usage: {avg_memory:.2f} MB ({avg_memory/1024:.3f} GB)")
        print(f"Minimum RAM Usage: {min_memory:.2f} MB ({min_memory/1024:.3f} GB)")
        print(f"Sample Count:      {len(samples)}")
        print(f"Process Exit Code: {return_code}")
        print("=" * 50)
        
        # Recommendations
        print("\n💡 RECOMMENDATIONS:")
        if peak_memory > 2048:  # > 2GB
            print("⚠️  HIGH MEMORY: Consider optimizing data loading")
            print("💡 Recommended Docker memory: 4GB+")
        elif peak_memory > 1024:  # > 1GB
            print("⚠️  MODERATE-HIGH: Monitor in production")
            print("💡 Recommended Docker memory: 2GB+")
        elif peak_memory > 512:  # > 512MB
            print("✅ MODERATE: Reasonable memory usage")
            print("💡 Recommended Docker memory: 1GB+")
        else:
            print("✅ LOW: Excellent memory efficiency")
            print("💡 Recommended Docker memory: 512MB+")
        
        print(f"\n🐳 Docker Command:")
        recommended_memory = max(int(peak_memory * 1.5), 1024)
        print(f"docker run --memory={recommended_memory}m your-image")
        
        print(f"\n🐳 Docker Compose:")
        print(f"services:")
        print(f"  your-service:")
        print(f"    memory: {recommended_memory}m")
        
        return return_code, peak_memory
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return 1, 0


if __name__ == "__main__":
    print("🚀 Starting Quick Memory Test...")
    print()
    
    exit_code, peak_ram = run_quick_test()
    
    print(f"\n🎯 SUMMARY:")
    print(f"Peak RAM Required: {peak_ram:.2f} MB ({peak_ram/1024:.3f} GB)")
    print(f"Test {'PASSED' if exit_code == 0 else 'FAILED'}")
    
    sys.exit(exit_code)
