#!/usr/bin/env python3
"""
Single Table Creation Script - Torob AI Assistant

This script creates a single table from the Torob database schema.
It supports creating any of the 11 tables defined in the schema with
proper foreign key constraints and indexes.

Usage:
    python create_table.py <table_name>
    
    # Examples:
    python create_table.py base_products
    python create_table.py searches
    python create_table.py exploration

Supported Tables:
- cities, brands, categories, shops
- base_products, members, exploration
- searches, search_results, base_views, final_clicks

Features:
- Validates table name against schema
- Shows table definition before creating
- Handles foreign key constraints properly
- Creates necessary indexes
- Checks if table already exists

Author: Torob AI Team
"""

import sys
import sqlite3
from db.config import get_db_path, ensure_data_directory
from db.base import DatabaseBaseLoader


# Table definitions from create_db.py schema
TABLE_DEFINITIONS = {
    'cities': {
        'description': 'Geographic locations for shops',
        'ddl': """
CREATE TABLE IF NOT EXISTS cities (
    id          INTEGER PRIMARY KEY,
    name        TEXT NOT NULL
);""",
        'indexes': []
    },
    
    'brands': {
        'description': 'Product brand catalog',
        'ddl': """
CREATE TABLE IF NOT EXISTS brands (
    id          INTEGER PRIMARY KEY,
    title       TEXT NOT NULL
);""",
        'indexes': []
    },
    
    'categories': {
        'description': 'Hierarchical product categories',
        'ddl': """
CREATE TABLE IF NOT EXISTS categories (
    id          INTEGER PRIMARY KEY,
    title       TEXT NOT NULL,
    parent_id   INTEGER NOT NULL DEFAULT -1,
    CHECK (parent_id = -1 OR parent_id >= 0)
);""",
        'indexes': []
    },
    
    'shops': {
        'description': 'E-commerce stores with ratings',
        'ddl': """
CREATE TABLE IF NOT EXISTS shops (
    id              INTEGER PRIMARY KEY,
    city_id         INTEGER NOT NULL,
    score           REAL NOT NULL DEFAULT 0.0,   -- 0..5
    has_warranty    INTEGER NOT NULL DEFAULT 0,  -- 0/1
    FOREIGN KEY (city_id) REFERENCES cities(id) ON UPDATE CASCADE ON DELETE RESTRICT
);""",
        'indexes': [
            "CREATE INDEX IF NOT EXISTS idx_shops_city_id ON shops(city_id);"
        ]
    },
    
    'base_products': {
        'description': 'Master product catalog',
        'ddl': """
CREATE TABLE IF NOT EXISTS base_products (
    random_key      TEXT PRIMARY KEY,
    persian_name    TEXT,
    english_name    TEXT,
    category_id     INTEGER,
    brand_id        INTEGER,
    extra_features  TEXT,     -- JSON
    image_url       TEXT,
    members         TEXT,     -- JSON array of member RK values
    FOREIGN KEY (category_id) REFERENCES categories(id) ON UPDATE CASCADE ON DELETE SET NULL,
    FOREIGN KEY (brand_id)    REFERENCES brands(id)    ON UPDATE CASCADE ON DELETE SET NULL
);""",
        'indexes': [
            "CREATE INDEX IF NOT EXISTS idx_base_products_category ON base_products(category_id);",
            "CREATE INDEX IF NOT EXISTS idx_base_products_brand    ON base_products(brand_id);"
        ]
    },
    
    'members': {
        'description': 'Shop-specific product offerings',
        'ddl': """
CREATE TABLE IF NOT EXISTS members (
    random_key      TEXT PRIMARY KEY,
    base_random_key TEXT NOT NULL,
    shop_id         INTEGER NOT NULL,
    price           INTEGER NOT NULL,
    FOREIGN KEY (base_random_key) REFERENCES base_products(random_key) ON UPDATE CASCADE ON DELETE CASCADE,
    FOREIGN KEY (shop_id)        REFERENCES shops(id)                ON UPDATE CASCADE ON DELETE RESTRICT
);""",
        'indexes': [
            "CREATE INDEX IF NOT EXISTS idx_members_base ON members(base_random_key);",
            "CREATE INDEX IF NOT EXISTS idx_members_shop ON members(shop_id);",
            "CREATE INDEX IF NOT EXISTS idx_members_price ON members(price);"
        ]
    },
    
    'exploration': {
        'description': 'Exploration sessions with filters',
        'ddl': """
CREATE TABLE exploration (
    chat_id        TEXT PRIMARY KEY,
    base_random_key  TEXT,
    product_name    TEXT,
    shop_id         INTEGER,
    brand_name        TEXT,
    city_id        INTEGER,
    category_name    TEXT,
    lower_price     INTEGER,
    upper_price     INTEGER,
    counts          INTEGER,
    score           REAL NOT NULL DEFAULT 0.0,
    has_warranty    INTEGER NOT NULL DEFAULT 0
);""",
        'indexes': [
            "CREATE INDEX IF NOT EXISTS idx_exploration_base ON exploration(base_random_key);",
            "CREATE INDEX IF NOT EXISTS idx_exploration_shop ON exploration(shop_id);",
            "CREATE INDEX IF NOT EXISTS idx_exploration_city ON exploration(city_id);"
        ]
    },
    
    'searches': {
        'description': 'User search queries and metadata',
        'ddl': """
CREATE TABLE IF NOT EXISTS searches (
    id                          TEXT PRIMARY KEY,
    uid                         TEXT,      -- self-reference to id of page 0
    query                       TEXT NOT NULL,
    page                        INTEGER NOT NULL CHECK (page >= 0),
    timestamp                   TEXT NOT NULL,          -- UTC ISO8601
    session_id                  TEXT,
    result_base_product_rks     TEXT,                   -- JSON array of RK values
    category_id                 INTEGER NOT NULL DEFAULT 0,
    category_brand_boosts       TEXT,                   -- JSON: {categories:[], brands:[]}
    CHECK (category_id = 0 OR category_id > 0)
);""",
        'indexes': [
            "CREATE INDEX IF NOT EXISTS idx_searches_uid ON searches(uid);",
            "CREATE INDEX IF NOT EXISTS idx_searches_timestamp ON searches(timestamp);",
            "CREATE INDEX IF NOT EXISTS idx_searches_session ON searches(session_id);",
            "CREATE INDEX IF NOT EXISTS idx_searches_category ON searches(category_id);"
        ]
    },
    
    'search_results': {
        'description': 'Normalized search results with ranking',
        'ddl': """
CREATE TABLE IF NOT EXISTS search_results (
    id                  INTEGER PRIMARY KEY,
    search_id           TEXT NOT NULL,
    base_product_rk     TEXT NOT NULL,
    position            INTEGER NOT NULL,
    FOREIGN KEY (search_id) REFERENCES searches(id) ON UPDATE CASCADE ON DELETE CASCADE,
    FOREIGN KEY (base_product_rk) REFERENCES base_products(random_key) ON UPDATE CASCADE ON DELETE RESTRICT
);""",
        'indexes': [
            "CREATE INDEX IF NOT EXISTS idx_search_results_search_id ON search_results(search_id);",
            "CREATE INDEX IF NOT EXISTS idx_search_results_product_rk ON search_results(base_product_rk);",
            "CREATE INDEX IF NOT EXISTS idx_search_results_position ON search_results(position);"
        ]
    },
    
    'base_views': {
        'description': 'Product detail page views',
        'ddl': """
CREATE TABLE IF NOT EXISTS base_views (
    id               TEXT PRIMARY KEY,
    search_id        TEXT NOT NULL,
    base_product_rk  TEXT NOT NULL,
    timestamp        TEXT NOT NULL,    -- UTC ISO8601
    FOREIGN KEY (search_id)       REFERENCES searches(id)         ON UPDATE CASCADE ON DELETE CASCADE,
    FOREIGN KEY (base_product_rk) REFERENCES base_products(random_key) ON UPDATE CASCADE ON DELETE RESTRICT
);""",
        'indexes': [
            "CREATE INDEX IF NOT EXISTS idx_base_views_search ON base_views(search_id);",
            "CREATE INDEX IF NOT EXISTS idx_base_views_base   ON base_views(base_product_rk);",
            "CREATE INDEX IF NOT EXISTS idx_base_views_ts     ON base_views(timestamp);"
        ]
    },
    
    'final_clicks': {
        'description': 'User clicks on shop offers',
        'ddl': """
CREATE TABLE IF NOT EXISTS final_clicks (
    id            TEXT PRIMARY KEY,
    base_view_id  TEXT NOT NULL,
    shop_id       INTEGER NOT NULL,
    timestamp     TEXT NOT NULL,   -- UTC ISO8601
    FOREIGN KEY (base_view_id) REFERENCES base_views(id) ON UPDATE CASCADE ON DELETE CASCADE,
    FOREIGN KEY (shop_id)      REFERENCES shops(id)      ON UPDATE CASCADE ON DELETE RESTRICT
);""",
        'indexes': [
            "CREATE INDEX IF NOT EXISTS idx_final_clicks_base_view ON final_clicks(base_view_id);",
            "CREATE INDEX IF NOT EXISTS idx_final_clicks_shop      ON final_clicks(shop_id);",
            "CREATE INDEX IF NOT EXISTS idx_final_clicks_ts        ON final_clicks(timestamp);"
        ]
    }
}


def get_all_tables():
    """Get list of all existing tables in the database."""
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


def table_exists(table_name):
    """Check if a table already exists."""
    existing_tables = get_all_tables()
    return table_name in existing_tables


def show_table_definition(table_name):
    """Display the table definition and dependencies."""
    if table_name not in TABLE_DEFINITIONS:
        print(f"❌ Error: Table '{table_name}' is not defined in the schema!")
        return False
    
    definition = TABLE_DEFINITIONS[table_name]
    
    print(f"📋 Table Definition: {table_name.upper()}")
    print(f"   Description: {definition['description']}")
    print(f"\n📝 DDL Statement:")
    print(definition['ddl'])
    
    if definition['indexes']:
        print(f"\n🔍 Indexes to be created:")
        for i, index_sql in enumerate(definition['indexes'], 1):
            print(f"   {i}. {index_sql}")
    
    return True


def create_table(table_name, force=False):
    """Create the specified table."""
    if table_name not in TABLE_DEFINITIONS:
        print(f"❌ Error: Table '{table_name}' is not defined in the schema!")
        return False
    
    # Check if table already exists
    if table_exists(table_name):
        if not force:
            print(f"⚠️  Table '{table_name}' already exists!")
            print(f"Use --force to recreate it.")
            return False
        else:
            print(f"🔄 Force mode enabled. Recreating table '{table_name}'...")
    
    db = DatabaseBaseLoader()
    try:
        definition = TABLE_DEFINITIONS[table_name]
        
        # Enable foreign keys
        db.execute("PRAGMA foreign_keys = ON")
        
        # Create the table
        print(f"🏗️  Creating table '{table_name}'...")
        db.execute(definition['ddl'])
        
        # Create indexes
        if definition['indexes']:
            print(f"🔍 Creating {len(definition['indexes'])} index(es)...")
            for index_sql in definition['indexes']:
                db.execute(index_sql)
        
        # Verify table was created
        if table_exists(table_name):
            print(f"✅ Table '{table_name}' created successfully!")
            
            # Show table info
            schema_result = db.query(f"PRAGMA table_info({table_name})")
            columns = [col['name'] for col in schema_result]
            print(f"   Columns: {len(columns)} ({', '.join(columns)})")
            
            return True
        else:
            print(f"❌ Failed to create table '{table_name}'")
            return False
        
    except sqlite3.OperationalError as e:
        print(f"❌ Error creating table '{table_name}': {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False
    finally:
        db.close()


def show_available_tables():
    """Display all available tables in the schema."""
    print("📋 Available Tables in Schema:")
    print("=" * 50)
    
    for table_name, definition in TABLE_DEFINITIONS.items():
        exists = "✅" if table_exists(table_name) else "❌"
        print(f"  {exists} {table_name:<20} - {definition['description']}")
    
    print("=" * 50)


def main():
    """Main function to handle command line arguments."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Create a single table from Torob database schema",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python create_table.py base_products
  python create_table.py searches --force
  python create_table.py --list
  python create_table.py --info base_products
        """
    )
    
    parser.add_argument('table_name', nargs='?', help='Name of table to create')
    parser.add_argument('--force', action='store_true', help='Recreate table if it already exists')
    parser.add_argument('--list', action='store_true', help='List all available tables')
    parser.add_argument('--info', help='Show detailed information about a table')
    
    args = parser.parse_args()
    
    # Ensure data directory exists
    ensure_data_directory()
    
    # Handle different modes
    if args.list:
        show_available_tables()
        return
    
    if args.info:
        if args.info not in TABLE_DEFINITIONS:
            print(f"❌ Error: Table '{args.info}' is not defined in the schema!")
            print(f"Available tables: {', '.join(TABLE_DEFINITIONS.keys())}")
            sys.exit(1)
        show_table_definition(args.info)
        return
    
    if not args.table_name:
        print("Usage: python create_table.py <table_name>")
        print("\nUse --list to see available tables")
        print("Use --info <table_name> to see table definition")
        sys.exit(1)
    
    # Validate table name
    if args.table_name not in TABLE_DEFINITIONS:
        print(f"❌ Error: Table '{args.table_name}' is not defined in the schema!")
        print(f"Available tables: {', '.join(TABLE_DEFINITIONS.keys())}")
        sys.exit(1)
    
    # Show table definition
    if not show_table_definition(args.table_name):
        sys.exit(1)
    
    # Confirm creation
    if not args.force and table_exists(args.table_name):
        print(f"\n⚠️  Table '{args.table_name}' already exists!")
        print(f"Use --force to recreate it.")
        sys.exit(1)
    
    if not args.force:
        print(f"\n⚠️  This will create table '{args.table_name}'")
        while True:
            response = input("Continue? (yes/no): ").lower().strip()
            if response in ['yes', 'y']:
                break
            elif response in ['no', 'n']:
                print("❌ Operation cancelled.")
                sys.exit(0)
            else:
                print("Please enter 'yes' or 'no'")
    
    # Create the table
    success = create_table(args.table_name, force=args.force)
    
    if success:
        print(f"\n🎉 Table '{args.table_name}' has been successfully created!")
    else:
        print(f"\n❌ Failed to create table '{args.table_name}'")
        sys.exit(1)


if __name__ == "__main__":
    main()
