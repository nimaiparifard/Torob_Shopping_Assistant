#!/usr/bin/env python3
"""
Table Cleaner Script - Torob AI Assistant

This script takes a table name as input and deletes all records from that table
without any conditions. It's useful for cleaning up data during development
or testing.

Usage:
    python clean_table.py <table_name>
    
    # Examples:
    python clean_table.py base_products
    python clean_table.py searches
    python clean_table.py exploration

Safety Features:
- Lists all available tables before cleaning
- Confirms the operation before executing
- Shows count of records before and after deletion
- Validates table name exists

Author: Torob AI Team
"""

import sys
import sqlite3
from db.config import get_db_path
from db.base import DatabaseBaseLoader


def get_all_tables():
    """Get list of all tables in the database."""
    db = DatabaseBaseLoader()
    try:
        tables = db.query("""
            SELECT name 
            FROM sqlite_master 
            WHERE type='table' 
            AND name NOT LIKE 'sqlite_%'
            ORDER BY name
        """)
        return [table['name'] for table in tables]
    finally:
        db.close()


def get_table_count(table_name):
    """Get the number of records in a table."""
    db = DatabaseBaseLoader()
    try:
        result = db.query(f"SELECT COUNT(*) as count FROM {table_name}")
        return result[0]['count'] if result else 0
    except sqlite3.OperationalError as e:
        if "no such table" in str(e).lower():
            return None
        raise
    finally:
        db.close()


def clean_table(table_name):
    """Delete all records from the specified table."""
    db = DatabaseBaseLoader()
    try:
        # Get count before deletion
        count_before = get_table_count(table_name)
        if count_before is None:
            print(f"❌ Error: Table '{table_name}' does not exist!")
            return False
        
        print(f"📊 Records in '{table_name}' before deletion: {count_before:,}")
        
        if count_before == 0:
            print(f"ℹ️  Table '{table_name}' is already empty.")
            return True
        
        # Execute DELETE statement
        affected_rows = db.execute(f"DELETE FROM {table_name}")
        
        # Get count after deletion
        count_after = get_table_count(table_name)
        
        print(f"✅ Successfully deleted {affected_rows:,} records from '{table_name}'")
        print(f"📊 Records in '{table_name}' after deletion: {count_after:,}")
        
        return True
        
    except sqlite3.OperationalError as e:
        print(f"❌ Error executing DELETE on table '{table_name}': {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False
    finally:
        db.close()


def main():
    """Main function to handle command line arguments and execute table cleaning."""
    if len(sys.argv) != 2:
        print("Usage: python clean_table.py <table_name>")
        print("\nAvailable tables:")
        tables = get_all_tables()
        for i, table in enumerate(tables, 1):
            count = get_table_count(table)
            if count is not None:
                print(f"  {i:2d}. {table:<20} ({count:,} records)")
            else:
                print(f"  {i:2d}. {table:<20} (error reading)")
        sys.exit(1)
    
    table_name = sys.argv[1]
    
    # Validate table exists
    tables = get_all_tables()
    if table_name not in tables:
        print(f"❌ Error: Table '{table_name}' does not exist!")
        print(f"\nAvailable tables: {', '.join(tables)}")
        sys.exit(1)
    
    # Get current count
    count = get_table_count(table_name)
    if count is None:
        print(f"❌ Error: Cannot access table '{table_name}'")
        sys.exit(1)
    
    if count == 0:
        print(f"ℹ️  Table '{table_name}' is already empty.")
        sys.exit(0)
    
    # Confirm deletion
    print(f"\n⚠️  WARNING: You are about to delete ALL {count:,} records from table '{table_name}'")
    print("This action cannot be undone!")
    
    while True:
        response = input("\nDo you want to continue? (yes/no): ").lower().strip()
        if response in ['yes', 'y']:
            break
        elif response in ['no', 'n']:
            print("❌ Operation cancelled.")
            sys.exit(0)
        else:
            print("Please enter 'yes' or 'no'")
    
    # Execute cleaning
    print(f"\n🧹 Cleaning table '{table_name}'...")
    success = clean_table(table_name)
    
    if success:
        print(f"\n✅ Table '{table_name}' has been successfully cleaned!")
    else:
        print(f"\n❌ Failed to clean table '{table_name}'")
        sys.exit(1)


if __name__ == "__main__":
    main()
