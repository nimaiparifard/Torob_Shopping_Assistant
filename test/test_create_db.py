#!/usr/bin/env python3
"""
Test script to demonstrate the updated create_db.py behavior
"""

import os
import sys
from pathlib import Path

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from db.create_db import init_db, show_schema_info
from db.config import get_db_path

def test_database_creation():
    """Test the database creation with different scenarios"""
    
    print("🧪 Testing Database Creation Behavior")
    print("=" * 50)
    
    db_path = get_db_path()
    
    # Test 1: Create database when it doesn't exist
    print("\n1️⃣ Testing: Create database when it doesn't exist")
    if os.path.exists(db_path):
        os.remove(db_path)
        print(f"   Removed existing database: {db_path}")
    
    success = init_db()
    print(f"   Result: {'✅ Success' if success else '❌ Failed'}")
    
    # Test 2: Try to create again (should skip)
    print("\n2️⃣ Testing: Try to create again (should skip)")
    success = init_db()
    print(f"   Result: {'✅ Success (skipped)' if success else '❌ Failed'}")
    
    # Test 3: Force recreate
    print("\n3️⃣ Testing: Force recreate")
    success = init_db(force_recreate=True)
    print(f"   Result: {'✅ Success (recreated)' if success else '❌ Failed'}")
    
    # Test 4: Try to create again after force recreate (should skip)
    print("\n4️⃣ Testing: Try to create again after force recreate (should skip)")
    success = init_db()
    print(f"   Result: {'✅ Success (skipped)' if success else '❌ Failed'}")
    
    print("\n" + "=" * 50)
    print("✅ All tests completed!")
    
    # Show database info
    if os.path.exists(db_path):
        size = os.path.getsize(db_path)
        print(f"\n📊 Database Info:")
        print(f"   Path: {db_path}")
        print(f"   Size: {size:,} bytes")
        print(f"   Exists: {'Yes' if os.path.exists(db_path) else 'No'}")

def show_usage_examples():
    """Show usage examples for the updated create_db.py"""
    
    print("\n📚 Usage Examples:")
    print("=" * 30)
    
    print("\n🔹 Create database only if it doesn't exist (default):")
    print("   python -m db.create_db")
    
    print("\n🔹 Force recreate database:")
    print("   python -m db.create_db --force")
    
    print("\n🔹 Show schema information:")
    print("   python -m db.create_db --info")
    
    print("\n🔹 Programmatic usage:")
    print("   from db.create_db import init_db")
    print("   init_db()  # Skip if exists")
    print("   init_db(force_recreate=True)  # Force recreate")

if __name__ == "__main__":
    print("🗄️ Torob Database Creation Test")
    print("=" * 50)
    
    # Run tests
    test_database_creation()
    
    # Show usage examples
    show_usage_examples()
    
    print(f"\n💡 The database creation now:")
    print(f"   ✅ Skips creation if dataset already exists")
    print(f"   ✅ Only creates empty database if needed")
    print(f"   ✅ Provides clear feedback about what's happening")
    print(f"   ✅ Supports force recreation when needed")
