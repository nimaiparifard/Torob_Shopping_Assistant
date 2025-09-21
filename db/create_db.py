"""
Torob AI Assistant - Database Schema Creation Module

This module creates the complete SQLite database schema for the Torob e-commerce
analytics system. It defines 10 interconnected tables that track the complete
user journey from search to purchase.

Database Structure:
- Core entities: Cities, Brands, Categories, Shops, Products
- User activity: Searches, Views, Clicks
- Relationships: Search Results, Product Members

Usage:
    # Create new database
    python -m db.create_db
    
    # Or programmatically
    from db.create_db import init_db
    init_db()

Author: Torob AI Team
"""

import sqlite3
from pathlib import Path
import os
from datetime import datetime
from db.config import get_data_path, get_db_path, ensure_data_directory

# Global database path - used throughout the application
DB_PATH = get_db_path()

ddl = """
-- ================================================================
-- TOROB AI ASSISTANT - DATABASE SCHEMA
-- ================================================================
-- This schema defines a complete e-commerce analytics database
-- that tracks user behavior from search to purchase conversion.
-- 
-- Key Features:
-- - Full referential integrity with foreign keys
-- - Hierarchical categories with unlimited nesting
-- - Flexible JSON attributes for products
-- - Complete user journey tracking
-- - Performance-optimized indexes
-- ================================================================

PRAGMA foreign_keys = ON;

-- =========================
-- CITIES TABLE (مرجع shops)
-- =========================
-- Stores geographic locations where shops operate
-- Referenced by: shops table
CREATE TABLE IF NOT EXISTS cities (
    id          INTEGER PRIMARY KEY,
    name        TEXT NOT NULL
);

-- =========================
-- BRANDS TABLE (مرجع base_products)
-- =========================
-- Master catalog of product brands
-- Referenced by: base_products table
-- Example data: {id: 1, title: "سامسونگ"}, {id: 2, title: "اپل"}
CREATE TABLE IF NOT EXISTS brands (
    id          INTEGER PRIMARY KEY,
    title       TEXT NOT NULL
);

-- =========================
-- CATEGORIES TABLE (دسته‌بندی‌ها)
-- =========================
-- Hierarchical product categorization system
-- Features:
-- - Self-referential hierarchy (parent_id = -1 for root categories)
-- - Unlimited nesting levels supported
-- - CHECK constraint ensures data integrity
-- 
-- Example hierarchy:
-- {id: 1, title: "الکترونیک", parent_id: -1}        (root)
-- {id: 2, title: "موبایل", parent_id: 1}             (child)
-- {id: 3, title: "گوشی هوشمند", parent_id: 2}        (grandchild)
-- =========================
CREATE TABLE IF NOT EXISTS categories (
    id          INTEGER PRIMARY KEY,
    title       TEXT NOT NULL,
    parent_id   INTEGER NOT NULL DEFAULT -1,
    CHECK (parent_id = -1 OR parent_id >= 0)
    -- گزینهٔ جایگزینِ سخت‌گیرانه:
    -- ,FOREIGN KEY (parent_id) REFERENCES categories(id) ON UPDATE CASCADE ON DELETE SET NULL
);

-- =========================
-- SHOPS TABLE (فروشگاه‌ها)
-- =========================
-- E-commerce stores with location and quality metrics
-- Foreign Keys: shops.city_id -> cities.id
-- 
-- Features:
-- - Location-based (city_id references cities)
-- - Quality scoring (0.0 to 5.0 scale)
-- - Warranty indication (0=no, 1=yes)
-- 
-- Example data:
-- {id: 1, city_id: 1, score: 4.5, has_warranty: 1}
-- {id: 2, city_id: 2, score: 3.8, has_warranty: 0}
-- =========================
CREATE TABLE IF NOT EXISTS shops (
    id              INTEGER PRIMARY KEY,
    city_id         INTEGER NOT NULL,
    score           REAL NOT NULL DEFAULT 0.0,   -- 0..5
    has_warranty    INTEGER NOT NULL DEFAULT 0,  -- 0/1
    FOREIGN KEY (city_id) REFERENCES cities(id) ON UPDATE CASCADE ON DELETE RESTRICT
);

CREATE INDEX IF NOT EXISTS idx_shops_city_id ON shops(city_id);

-- =========================
-- جدول محصولات پایه (Base Products)
-- FK: base_products.category_id -> categories.id
-- FK: base_products.brand_id    -> brands.id
-- members: لیست RK اعضا؛ به‌صورت TEXT/JSON ذخیره می‌شود و FK ندارد (denormalized)
-- =========================
CREATE TABLE IF NOT EXISTS base_products (
    random_key      TEXT PRIMARY KEY,
    persian_name    TEXT,
    english_name    TEXT,
    category_id     INTEGER,  -- بهتر است NULL وقتی دسته ندارد
    brand_id        INTEGER,
    extra_features  TEXT,     -- JSON
    image_url       TEXT,
    members         TEXT,     -- JSON array از member RK ها (اختیاری/غیرنرمال)
    FOREIGN KEY (category_id) REFERENCES categories(id) ON UPDATE CASCADE ON DELETE SET NULL,
    FOREIGN KEY (brand_id)    REFERENCES brands(id)    ON UPDATE CASCADE ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_base_products_category ON base_products(category_id);
CREATE INDEX IF NOT EXISTS idx_base_products_brand    ON base_products(brand_id);

-- =========================
-- جدول محصولات فروشگاه‌ها (Members)
-- FK: members.base_random_key -> base_products.random_key
-- FK: members.shop_id         -> shops.id
-- =========================
CREATE TABLE IF NOT EXISTS members (
    random_key      TEXT PRIMARY KEY,
    base_random_key TEXT NOT NULL,
    shop_id         INTEGER NOT NULL,
    price           INTEGER NOT NULL,
    FOREIGN KEY (base_random_key) REFERENCES base_products(random_key) ON UPDATE CASCADE ON DELETE CASCADE,
    FOREIGN KEY (shop_id)        REFERENCES shops(id)                ON UPDATE CASCADE ON DELETE RESTRICT
);

CREATE INDEX IF NOT EXISTS idx_members_base ON members(base_random_key);
CREATE INDEX IF NOT EXISTS idx_members_shop ON members(shop_id);
CREATE INDEX IF NOT EXISTS idx_members_price ON members(price);

-- =========================
-- جدول جستجوها (Searches)
-- FK ها:
--   searches.uid -> searches.id (خودارجاع؛ uid=شناسه صفحه صفر همان جستجو)
--   توجه: category_id = 0 به معنی "بدون دسته" است؛ به‌خاطر این قاعده FK گذاشته نشده
--   و به‌جایش CHECK داریم. اگر NULL را بپذیرید، می‌توان FK گذاشت.
-- =========================
CREATE TABLE IF NOT EXISTS searches (
    id                          TEXT PRIMARY KEY,
    uid                         TEXT,      -- خودارجاع به id صفحه صفر
    query                       TEXT NOT NULL,
    page                        INTEGER NOT NULL CHECK (page >= 0),
    timestamp                   TEXT NOT NULL,          -- UTC ISO8601
    session_id                  TEXT,
    result_base_product_rks     TEXT,                   -- JSON array از RK ها
    category_id                 INTEGER NOT NULL DEFAULT 0,
    category_brand_boosts       TEXT,                   -- JSON: {categories:[], brands:[]}
    CHECK (category_id = 0 OR category_id > 0)
    -- اگر خواستید FK بگذارید:
    -- ,FOREIGN KEY (category_id) REFERENCES categories(id)
);

CREATE INDEX IF NOT EXISTS idx_searches_uid ON searches(uid);
CREATE INDEX IF NOT EXISTS idx_searches_timestamp ON searches(timestamp);
CREATE INDEX IF NOT EXISTS idx_searches_session ON searches(session_id);
CREATE INDEX IF NOT EXISTS idx_searches_category ON searches(category_id);

-- =========================
-- جدول نتایج جستجو (Search Results) - رابطه یک به چند
-- FK: search_results.search_id -> searches.id
-- FK: search_results.base_product_rk -> base_products.random_key
-- position: موقعیت محصول در نتایج جستجو (1, 2, 3, ...)
-- =========================
CREATE TABLE IF NOT EXISTS search_results (
    id                  INTEGER PRIMARY KEY,
    search_id           TEXT NOT NULL,
    base_product_rk     TEXT NOT NULL,
    position            INTEGER NOT NULL,
    FOREIGN KEY (search_id) REFERENCES searches(id) ON UPDATE CASCADE ON DELETE CASCADE,
    FOREIGN KEY (base_product_rk) REFERENCES base_products(random_key) ON UPDATE CASCADE ON DELETE RESTRICT
);

CREATE INDEX IF NOT EXISTS idx_search_results_search_id ON search_results(search_id);
CREATE INDEX IF NOT EXISTS idx_search_results_product_rk ON search_results(base_product_rk);
CREATE INDEX IF NOT EXISTS idx_search_results_position ON search_results(position);

-- =========================
-- جدول مشاهده بیس (Base Views)
-- FK: base_views.search_id      -> searches.id
-- FK: base_views.base_product_rk-> base_products.random_key
-- =========================
CREATE TABLE IF NOT EXISTS base_views (
    id               TEXT PRIMARY KEY,
    search_id        TEXT NOT NULL,
    base_product_rk  TEXT NOT NULL,
    timestamp        TEXT NOT NULL,    -- UTC ISO8601
    FOREIGN KEY (search_id)       REFERENCES searches(id)         ON UPDATE CASCADE ON DELETE CASCADE,
    FOREIGN KEY (base_product_rk) REFERENCES base_products(random_key) ON UPDATE CASCADE ON DELETE RESTRICT
);

CREATE INDEX IF NOT EXISTS idx_base_views_search ON base_views(search_id);
CREATE INDEX IF NOT EXISTS idx_base_views_base   ON base_views(base_product_rk);
CREATE INDEX IF NOT EXISTS idx_base_views_ts     ON base_views(timestamp);

-- =========================
-- جدول کلیک نهایی (Final Click)
-- FK: final_clicks.base_view_id -> base_views.id
-- FK: final_clicks.shop_id      -> shops.id
-- =========================
CREATE TABLE IF NOT EXISTS final_clicks (
    id            TEXT PRIMARY KEY,
    base_view_id  TEXT NOT NULL,
    shop_id       INTEGER NOT NULL,
    timestamp     TEXT NOT NULL,   -- UTC ISO8601
    FOREIGN KEY (base_view_id) REFERENCES base_views(id) ON UPDATE CASCADE ON DELETE CASCADE,
    FOREIGN KEY (shop_id)      REFERENCES shops(id)      ON UPDATE CASCADE ON DELETE RESTRICT
);

CREATE INDEX IF NOT EXISTS idx_final_clicks_base_view ON final_clicks(base_view_id);
CREATE INDEX IF NOT EXISTS idx_final_clicks_shop      ON final_clicks(shop_id);
CREATE INDEX IF NOT EXISTS idx_final_clicks_ts        ON final_clicks(timestamp);
"""

def init_db(db_path=None, force_recreate=False):
    """Initialize the Torob database with complete schema.
    
    This function creates a fresh SQLite database with all tables, indexes,
    and foreign key constraints. It's designed to be idempotent and safe
    to run multiple times.
    
    Args:
        db_path (str): Path to the SQLite database file. Defaults to DB_PATH.
        force_recreate (bool): If True, removes existing database before creating.
                              If False, only creates if database doesn't exist.
    
    Returns:
        bool: True if database was created successfully, False otherwise.
        
    Example:
        >>> # Create only if doesn't exist (default behavior)
        >>> init_db()
        
        >>> # Force recreate existing database
        >>> init_db(force_recreate=True)
        
        >>> # Create at custom location
        >>> init_db("/path/to/custom/database.db")
        
    Raises:
        sqlite3.Error: If database creation fails
        OSError: If file system operations fail
    """
    try:
        # Use default path if not provided
        if db_path is None:
            db_path = DB_PATH
        
        # Ensure data directory exists
        ensure_data_directory()
        
        # Check if database already exists and has data
        if os.path.exists(db_path):
            if not force_recreate:
                # Check if database has data (not just empty schema)
                try:
                    con = sqlite3.connect(db_path)
                    cursor = con.execute("SELECT COUNT(*) FROM base_products")
                    product_count = cursor.fetchone()[0]
                    con.close()
                    
                    if product_count > 0:
                        print(f"✅ Database already exists with {product_count:,} products: {db_path}")
                        print(f"📊 Dataset is already loaded. Skipping database creation.")
                        return True
                    else:
                        print(f"⚠️ Database exists but is empty. Recreating...")
                        Path(db_path).unlink()
                except Exception as e:
                    print(f"⚠️ Database exists but may be corrupted. Recreating... ({e})")
                    Path(db_path).unlink()
            else:
                print(f"🗑️ Force recreate enabled. Removing existing database: {db_path}")
                Path(db_path).unlink()
        
        print(f"🏗️ Creating database: {db_path}")
        
        # Create database connection
        con = sqlite3.connect(db_path)
        try:
            # Execute the complete DDL script
            con.executescript(ddl)
            con.commit()
            
            # Verify tables were created
            cursor = con.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name NOT LIKE 'sqlite_%'
                ORDER BY name
            """)
            tables = [row[0] for row in cursor.fetchall()]
            
            print(f"✅ Database created successfully!")
            print(f"📊 Created {len(tables)} tables: {', '.join(tables)}")
            
            # Show basic statistics
            print(f"📍 Location: {os.path.abspath(db_path)}")
            print(f"📏 Size: {os.path.getsize(db_path):,} bytes")
            
            return True
            
        finally:
            con.close()
            
    except Exception as e:
        print(f"❌ Failed to create database: {e}")
        return False

def show_schema_info():
    """Display detailed information about the database schema.
    
    This function provides a comprehensive overview of the database structure,
    including table relationships, constraints, and example usage patterns.
    """
    print("🗄️ TOROB DATABASE SCHEMA OVERVIEW")
    print("=" * 60)
    
    schema_info = {
        'cities': {
            'description': 'Geographic locations for shops',
            'columns': ['id (PK)', 'name'],
            'references': [],
            'referenced_by': ['shops.city_id']
        },
        'brands': {
            'description': 'Product brand catalog',
            'columns': ['id (PK)', 'title'],
            'references': [],
            'referenced_by': ['base_products.brand_id']
        },
        'categories': {
            'description': 'Hierarchical product categories',
            'columns': ['id (PK)', 'title', 'parent_id'],
            'references': ['categories.parent_id (self-reference)'],
            'referenced_by': ['base_products.category_id']
        },
        'shops': {
            'description': 'E-commerce stores with ratings',
            'columns': ['id (PK)', 'city_id (FK)', 'score', 'has_warranty'],
            'references': ['cities.id'],
            'referenced_by': ['members.shop_id', 'final_clicks.shop_id']
        },
        'base_products': {
            'description': 'Master product catalog',
            'columns': ['random_key (PK)', 'persian_name', 'english_name', 
                       'category_id (FK)', 'brand_id (FK)', 'extra_features', 
                       'image_url', 'members'],
            'references': ['categories.id', 'brands.id'],
            'referenced_by': ['members.base_random_key', 'search_results.base_product_rk', 
                            'base_views.base_product_rk']
        },
        'members': {
            'description': 'Shop-specific product offerings',
            'columns': ['random_key (PK)', 'base_random_key (FK)', 'shop_id (FK)', 'price'],
            'references': ['base_products.random_key', 'shops.id'],
            'referenced_by': []
        },
        'searches': {
            'description': 'User search queries and metadata',
            'columns': ['id (PK)', 'uid', 'query', 'page', 'timestamp', 
                       'session_id', 'result_base_product_rks', 'category_id', 
                       'category_brand_boosts'],
            'references': [],
            'referenced_by': ['search_results.search_id', 'base_views.search_id']
        },
        'search_results': {
            'description': 'Normalized search results with ranking',
            'columns': ['id (PK)', 'search_id (FK)', 'base_product_rk (FK)', 'position'],
            'references': ['searches.id', 'base_products.random_key'],
            'referenced_by': []
        },
        'base_views': {
            'description': 'Product detail page views',
            'columns': ['id (PK)', 'search_id (FK)', 'base_product_rk (FK)', 'timestamp'],
            'references': ['searches.id', 'base_products.random_key'],
            'referenced_by': ['final_clicks.base_view_id']
        },
        'final_clicks': {
            'description': 'User clicks on shop offers',
            'columns': ['id (PK)', 'base_view_id (FK)', 'shop_id (FK)', 'timestamp'],
            'references': ['base_views.id', 'shops.id'],
            'referenced_by': []
        }
    }
    
    for table_name, info in schema_info.items():
        print(f"\n📋 {table_name.upper()}")
        print(f"   Description: {info['description']}")
        print(f"   Columns: {', '.join(info['columns'])}")
        if info['references']:
            print(f"   References: {', '.join(info['references'])}")
        if info['referenced_by']:
            print(f"   Referenced by: {', '.join(info['referenced_by'])}")
    
    print(f"\n🔄 TYPICAL DATA FLOW:")
    print("   1. User performs search → searches table")
    print("   2. Results returned → search_results table")
    print("   3. User views product → base_views table")
    print("   4. User clicks shop offer → final_clicks table")
    
    print(f"\n💡 USAGE EXAMPLES:")
    print("   # Create database")
    print("   python -m db.create_db")
    print("   ")
    print("   # Load data")
    print("   python -m db.load_db")
    print("   ")
    print("   # Verify integrity")
    print("   python -m db.verify_data")

if __name__ == "__main__":
    import sys
    
    # Check command line arguments
    if len(sys.argv) > 1 and sys.argv[1] == '--info':
        show_schema_info()
    elif len(sys.argv) > 1 and sys.argv[1] == '--force':
        # Force recreate database
        print("🔄 Force recreating database...")
        success = init_db(force_recreate=True)
        if success:
            print(f"\n🚀 Next steps:")
            print(f"   1. Load data: python -m db.load_db")
            print(f"   2. Verify: python -m db.verify_data")
            print(f"   3. Preview: python -m db.preview_data")
        else:
            print(f"❌ Database creation failed!")
            sys.exit(1)
    else:
        # Create the database only if it doesn't exist or is empty
        success = init_db()
        if success:
            print(f"\n🚀 Next steps:")
            print(f"   1. Load data: python -m db.load_db")
            print(f"   2. Verify: python -m db.verify_data")
            print(f"   3. Preview: python -m db.preview_data")
            print(f"\n💡 Options:")
            print(f"   --info: Show schema information")
            print(f"   --force: Force recreate database")
        else:
            print(f"❌ Database creation failed!")
            sys.exit(1)
