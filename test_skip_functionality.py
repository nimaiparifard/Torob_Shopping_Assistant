"""
Test Skip Functionality

Test that the optimized loader correctly skips existing tables.

Author: Torob AI Team
"""

import subprocess
import sys
import os


def test_skip_functionality():
    """Test that tables are skipped when they already exist."""
    print("🧪 Testing Skip Functionality")
    print("=" * 50)
    
    # Test loading cities table twice
    print("\n1. Loading cities table (first time)...")
    result1 = subprocess.run([
        sys.executable, '-m', 'db.load_db_optimized',
        '--table', 'cities',
        '--chunk-size', '5000'
    ], capture_output=True, text=True, encoding='utf-8', errors='replace')
    
    print("Exit code:", result1.returncode)
    if "Loading cities" in result1.stdout:
        print("✅ First load: Table loaded successfully")
    else:
        print("❌ First load: Failed to load table")
    
    print("\n2. Loading cities table (second time - should skip)...")
    result2 = subprocess.run([
        sys.executable, '-m', 'db.load_db_optimized',
        '--table', 'cities',
        '--chunk-size', '5000'
    ], capture_output=True, text=True, encoding='utf-8', errors='replace')
    
    print("Exit code:", result2.returncode)
    if "[SKIP]" in result2.stdout:
        print("✅ Second load: Table correctly skipped")
    else:
        print("❌ Second load: Table was not skipped")
        print("Output:", result2.stdout)
    
    print("\n3. Force reloading cities table...")
    result3 = subprocess.run([
        sys.executable, '-m', 'db.load_db_optimized',
        '--table', 'cities',
        '--chunk-size', '5000',
        '--force-reload'
    ], capture_output=True, text=True, encoding='utf-8', errors='replace')
    
    print("Exit code:", result3.returncode)
    if "Loading cities" in result3.stdout and "[SKIP]" not in result3.stdout:
        print("✅ Force reload: Table loaded despite existing data")
    else:
        print("❌ Force reload: Failed to force reload")
    
    print("\n📊 Test Summary:")
    print(f"First load: {'✅ PASS' if result1.returncode == 0 else '❌ FAIL'}")
    print(f"Skip check: {'✅ PASS' if '[SKIP]' in result2.stdout else '❌ FAIL'}")
    print(f"Force reload: {'✅ PASS' if result3.returncode == 0 and 'Loading cities' in result3.stdout else '❌ FAIL'}")


if __name__ == "__main__":
    test_skip_functionality()
