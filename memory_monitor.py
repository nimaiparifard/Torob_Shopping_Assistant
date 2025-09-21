"""
Memory Monitor - Track Peak RAM Usage for Python Scripts

This script monitors memory usage during execution and reports peak RAM consumption.
It can be used to profile any Python script to understand memory requirements.

Usage:
    python memory_monitor.py db/load_db.py
    python memory_monitor.py -m db.load_db
    python memory_monitor.py --script "python db/load_db.py"

Author: Torob AI Team
"""

import psutil
import time
import sys
import subprocess
import threading
import argparse
from typing import Optional, List, Tuple
import os


class MemoryMonitor:
    """Monitor memory usage of a running process."""
    
    def __init__(self, process_id: int, interval: float = 0.1):
        """
        Initialize memory monitor.
        
        Args:
            process_id: Process ID to monitor
            interval: Monitoring interval in seconds
        """
        self.process_id = process_id
        self.interval = interval
        self.monitoring = False
        self.memory_samples: List[float] = []
        self.peak_memory = 0.0
        self.start_time = None
        self.end_time = None
        
    def start_monitoring(self):
        """Start monitoring memory usage."""
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
        
        if self.monitor_thread.is_alive():
            self.monitor_thread.join(timeout=1.0)
    
    def get_statistics(self) -> dict:
        """Get memory usage statistics."""
        if not self.memory_samples:
            return {
                'peak_memory_mb': 0,
                'average_memory_mb': 0,
                'min_memory_mb': 0,
                'duration_seconds': 0,
                'sample_count': 0
            }
        
        return {
            'peak_memory_mb': round(self.peak_memory, 2),
            'average_memory_mb': round(sum(self.memory_samples) / len(self.memory_samples), 2),
            'min_memory_mb': round(min(self.memory_samples), 2),
            'duration_seconds': round(self.end_time - self.start_time, 2) if self.end_time and self.start_time else 0,
            'sample_count': len(self.memory_samples)
        }


def run_with_memory_monitoring(script_path: str, args: List[str] = None) -> Tuple[int, dict]:
    """
    Run a Python script and monitor its memory usage.
    
    Args:
        script_path: Path to Python script or module
        args: Additional arguments to pass to the script
        
    Returns:
        Tuple of (exit_code, memory_statistics)
    """
    if args is None:
        args = []
    
    print(f"🚀 Starting memory monitoring for: {script_path}")
    print(f"📊 Monitoring interval: 0.1 seconds")
    print("=" * 60)
    
    # Start the process
    try:
        if script_path.startswith('-m'):
            # Module execution
            cmd = [sys.executable, script_path] + args
        else:
            # Script execution
            cmd = [sys.executable, script_path] + args
        
        print(f"🔧 Command: {' '.join(cmd)}")
        print()
        
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
            universal_newlines=True
        )
        
        # Start memory monitoring
        monitor = MemoryMonitor(process.pid, interval=0.1)
        monitor.start_monitoring()
        
        # Stream output in real-time
        print("📝 Script Output:")
        print("-" * 40)
        
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
        print(f"❌ Error running script: {e}")
        return 1, {}


def format_memory_stats(stats: dict) -> str:
    """Format memory statistics for display."""
    if not stats:
        return "No memory data available"
    
    return f"""
📊 MEMORY USAGE STATISTICS
{'=' * 50}
🔝 Peak Memory Usage:    {stats.get('peak_memory_mb', 0):.2f} MB
📈 Average Memory Usage: {stats.get('average_memory_mb', 0):.2f} MB
📉 Minimum Memory Usage: {stats.get('min_memory_mb', 0):.2f} MB
⏱️  Duration:             {stats.get('duration_seconds', 0):.2f} seconds
📊 Sample Count:         {stats.get('sample_count', 0)} samples
{'=' * 50}
💡 Peak RAM Required: {stats.get('peak_memory_mb', 0):.2f} MB
"""


def main():
    """Main function to run memory monitoring."""
    parser = argparse.ArgumentParser(
        description="Monitor memory usage of Python scripts",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python memory_monitor.py db/load_db.py
  python memory_monitor.py -m db.load_db
  python memory_monitor.py --script "python db/load_db.py"
        """
    )
    
    parser.add_argument(
        'script',
        help='Python script path or module name (use -m for modules)'
    )
    
    parser.add_argument(
        'args',
        nargs='*',
        help='Additional arguments to pass to the script'
    )
    
    parser.add_argument(
        '--script',
        dest='script_command',
        help='Full command to execute (overrides script argument)'
    )
    
    args = parser.parse_args()
    
    # Check if psutil is available
    try:
        import psutil
    except ImportError:
        print("❌ Error: psutil is required for memory monitoring")
        print("📦 Install it with: pip install psutil")
        sys.exit(1)
    
    print("🔍 Memory Monitor - Python Script Profiler")
    print("=" * 60)
    
    # Run the script with monitoring
    if args.script_command:
        # Execute the full command
        print(f"🔧 Executing: {args.script_command}")
        return_code, stats = run_with_memory_monitoring(
            args.script_command.split()[0],
            args.script_command.split()[1:]
        )
    else:
        # Execute script or module
        return_code, stats = run_with_memory_monitoring(args.script, args.args)
    
    # Display results
    print("\n" + "=" * 60)
    print("✅ Script execution completed")
    print(f"🚪 Exit code: {return_code}")
    
    if stats:
        print(format_memory_stats(stats))
        
        # Additional recommendations
        peak_mb = stats.get('peak_memory_mb', 0)
        if peak_mb > 1000:  # More than 1GB
            print("⚠️  WARNING: High memory usage detected!")
            print("💡 Consider optimizing the script or increasing available RAM")
        elif peak_mb > 500:  # More than 500MB
            print("💡 Moderate memory usage - monitor for production deployment")
        else:
            print("✅ Memory usage is within reasonable limits")
    else:
        print("❌ No memory statistics available")
    
    return return_code


if __name__ == "__main__":
    sys.exit(main())
