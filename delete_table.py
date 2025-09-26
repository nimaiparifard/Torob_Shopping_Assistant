#!/usr/bin/env python3
"""
Single Table Deletion Script - Torob AI Assistant

This script deletes a single table from the database with safety features.
It validates the table exists, shows record count, and asks for confirmation.

Usage:
    python delete_table.py <table_name>
    
    # Examples:
    python delete_table.py base_products
    python delete_table.py searches
    python delete_table.py exploration

Safety Features:
- Validates table exists before deletion
- Shows record count before deletion
- Confirms operation before executing
- Handles foreign key constraints properly
- Shows available tables if invalid name provided

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


def get_table_info(table_name):
    """Get detailed information about a table."""
    db = DatabaseBaseLoader()
    try:
        # Get record count
        count_result = db.query(f"SELECT COUNT(*) as count FROM {table_name}")
        count = count_result[0]['count'] if count_result else 0
        
        # Get table schema info
        schema_result = db.query(f"PRAGMA table_info({table_name})")
        columns = [col['name'] for col in schema_result]
        
        # Get foreign key constraints
        fk_result = db.query(f"PRAGMA foreign_key_list({table_name})")
        foreign_keys = []
        for fk in fk_result:
            foreign_keys.append({
                'column': fk['from'],
                'references': f"{fk['table']}.{fk['to']}"
            })
        
        return {
            'name': table_name,
            'count': count,
            'columns': columns,
            'column_count': len(columns),
            'foreign_keys': foreign_keys
        }
    except sqlite3.OperationalError as e:
        if "no such table" in str(e).lower():
            return None
        raise
    finally:
        db.close()


def get_referenced_tables(table_name):
    """Get tables that reference this table."""
    db = DatabaseBaseLoader()
    try:
        # Get all tables
        all_tables = get_all_tables()
        referenced_by = []
        
        for other_table in all_tables:
            if other_table == table_name:
                continue
                
            # Check foreign keys in this table
            fk_result = db.query(f"PRAGMA foreign_key_list({other_table})")
            for fk in fk_result:
                if fk['table'] == table_name:
                    referenced_by.append({
                        'table': other_table,
                        'column': fk['from'],
                        'references': f"{table_name}.{fk['to']}"
                    })
        
        return referenced_by
    finally:
        db.close()


def delete_table(table_name):
    """Delete the specified table."""
    db = DatabaseBaseLoader()
    try:
        # Get table info
        table_info = get_table_info(table_name)
        if table_info is None:
            print(f"❌ Error: Table '{table_name}' does not exist!")
            return False
        
        # Get referencing tables
        referenced_by = get_referenced_tables(table_name)
        
        print(f"📊 Table Information:")
        print(f"   Name: {table_info['name']}")
        print(f"   Columns: {table_info['column_count']} ({', '.join(table_info['columns'][:3])}{'...' if table_info['column_count'] > 3 else ''})")
        print(f"   Records: {table_info['count']:,}")
        
        if table_info['foreign_keys']:
            print(f"   Foreign Keys: {len(table_info['foreign_keys'])}")
            for fk in table_info['foreign_keys']:
                print(f"     - {fk['column']} → {fk['references']}")
        
        if referenced_by:
            print(f"   Referenced by: {len(referenced_by)} table(s)")
            for ref in referenced_by:
                print(f"     - {ref['table']}.{ref['column']} → {ref['references']}")
        
        if table_info['count'] == 0:
            print(f"\nℹ️  Table '{table_name}' is already empty.")
        else:
            print(f"\n⚠️  This will delete {table_info['count']:,} records!")
        
        if referenced_by:
            print(f"\n⚠️  WARNING: This table is referenced by other tables!")
            print(f"   Deleting this table may cause foreign key constraint violations.")
            print(f"   Consider deleting referencing tables first or handling dependencies.")
        
        # Confirm deletion
        print(f"\n⚠️  CONFIRMATION REQUIRED")
        print(f"You are about to DELETE the entire table '{table_name}'!")
        print(f"This action CANNOT be undone!")
        
        while True:
            response = input(f"\nAre you sure you want to delete table '{table_name}'? (yes/no): ").lower().strip()
            if response in ['yes', 'y']:
                break
            elif response in ['no', 'n']:
                print("❌ Operation cancelled.")
                return False
            else:
                print("Please enter 'yes' or 'no'")
        
        # Execute DROP TABLE
        print(f"\n🗑️  Deleting table '{table_name}'...")
        
        try:
            # Disable foreign key checks temporarily
            db.execute("PRAGMA foreign_keys = OFF")
            
            # Drop the table
            db.execute(f"DROP TABLE IF EXISTS {table_name}")
            
            # Re-enable foreign key checks
            db.execute("PRAGMA foreign_keys = ON")
            
            print(f"✅ Table '{table_name}' deleted successfully!")
            return True
            
        except sqlite3.OperationalError as e:
            print(f"❌ Error deleting table '{table_name}': {e}")
            return False
        
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False
    finally:
        db.close()


def main():
    """Main function to handle command line arguments."""
    if len(sys.argv) != 2:
        print("Usage: python delete_table.py <table_name>")
        print("\nAvailable tables:")
        tables = get_all_tables()
        if tables:
            for i, table in enumerate(tables, 1):
                info = get_table_info(table)
                if info:
                    print(f"  {i:2d}. {table:<20} ({info['count']:,} records)")
                else:
                    print(f"  {i:2d}. {table:<20} (error reading)")
        else:
            print("  No tables found in database.")
        sys.exit(1)
    
    table_name = sys.argv[1]
    
    # Validate table exists
    tables = get_all_tables()
    if table_name not in tables:
        print(f"❌ Error: Table '{table_name}' does not exist!")
        print(f"\nAvailable tables: {', '.join(tables)}")
        sys.exit(1)
    
    # Execute deletion
    success = delete_table(table_name)
    
    if success:
        print(f"\n🎉 Table '{table_name}' has been successfully deleted!")
    else:
        print(f"\n❌ Failed to delete table '{table_name}'")
        sys.exit(1)


if __name__ == "__main__":
    main()
