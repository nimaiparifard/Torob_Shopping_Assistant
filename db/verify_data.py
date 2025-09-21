import sqlite3
import os
from db.create_db import DB_PATH

def connect_to_db():
    """Connect to the SQLite database."""
    if not os.path.exists(DB_PATH):
        print(f"❌ Database not found at: {DB_PATH}")
        print("Please run 'python -m db.create_db' first to create the database.")
        return None
    
    try:
        conn = sqlite3.connect(DB_PATH)
        print(f"✅ Connected to database: {DB_PATH}")
        return conn
    except Exception as e:
        print(f"❌ Failed to connect to database: {e}")
        return None

def check_table_exists(conn, table_name):
    """Check if a table exists in the database."""
    cursor = conn.execute("""
        SELECT name FROM sqlite_master 
        WHERE type='table' AND name=?
    """, (table_name,))
    return cursor.fetchone() is not None

def get_table_info(conn, table_name):
    """Get detailed information about a table."""
    try:
        # Get table schema
        cursor = conn.execute(f"PRAGMA table_info({table_name})")
        columns = cursor.fetchall()
        
        # Get row count
        cursor = conn.execute(f"SELECT COUNT(*) FROM {table_name}")
        row_count = cursor.fetchone()[0]
        
        return {
            'columns': columns,
            'row_count': row_count
        }
    except Exception as e:
        return {'error': str(e)}

def check_foreign_keys(conn):
    """Check foreign key constraints."""
    print("\n🔗 CHECKING FOREIGN KEY CONSTRAINTS:")
    print("-" * 50)
    
    # Enable foreign keys
    conn.execute("PRAGMA foreign_keys = ON")
    
    fk_tests = [
        {
            'name': 'Shops → Cities',
            'query': '''
                SELECT COUNT(*) FROM shops s
                LEFT JOIN cities c ON s.city_id = c.id
                WHERE c.id IS NULL
            '''
        },
        {
            'name': 'Base Products → Categories',
            'query': '''
                SELECT COUNT(*) FROM base_products bp
                LEFT JOIN categories cat ON bp.category_id = cat.id
                WHERE cat.id IS NULL AND bp.category_id IS NOT NULL
            '''
        },
        {
            'name': 'Base Products → Brands',
            'query': '''
                SELECT COUNT(*) FROM base_products bp
                LEFT JOIN brands b ON bp.brand_id = b.id
                WHERE b.id IS NULL AND bp.brand_id != -1
            '''
        },
        {
            'name': 'Members → Base Products',
            'query': '''
                SELECT COUNT(*) FROM members m
                LEFT JOIN base_products bp ON m.base_random_key = bp.random_key
                WHERE bp.random_key IS NULL
            '''
        },
        {
            'name': 'Members → Shops',
            'query': '''
                SELECT COUNT(*) FROM members m
                LEFT JOIN shops s ON m.shop_id = s.id
                WHERE s.id IS NULL
            '''
        },
        {
            'name': 'Search Results → Searches',
            'query': '''
                SELECT COUNT(*) FROM search_results sr
                LEFT JOIN searches s ON sr.search_id = s.id
                WHERE s.id IS NULL
            '''
        },
        {
            'name': 'Search Results → Base Products',
            'query': '''
                SELECT COUNT(*) FROM search_results sr
                LEFT JOIN base_products bp ON sr.base_product_rk = bp.random_key
                WHERE bp.random_key IS NULL
            '''
        },
        {
            'name': 'Base Views → Searches',
            'query': '''
                SELECT COUNT(*) FROM base_views bv
                LEFT JOIN searches s ON bv.search_id = s.id
                WHERE s.id IS NULL
            '''
        },
        {
            'name': 'Base Views → Base Products',
            'query': '''
                SELECT COUNT(*) FROM base_views bv
                LEFT JOIN base_products bp ON bv.base_product_rk = bp.random_key
                WHERE bp.random_key IS NULL
            '''
        },
        {
            'name': 'Final Clicks → Base Views',
            'query': '''
                SELECT COUNT(*) FROM final_clicks fc
                LEFT JOIN base_views bv ON fc.base_view_id = bv.id
                WHERE bv.id IS NULL
            '''
        },
        {
            'name': 'Final Clicks → Shops',
            'query': '''
                SELECT COUNT(*) FROM final_clicks fc
                LEFT JOIN shops s ON fc.shop_id = s.id
                WHERE s.id IS NULL
            '''
        }
    ]
    
    for test in fk_tests:
        try:
            cursor = conn.execute(test['query'])
            orphaned_count = cursor.fetchone()[0]
            
            if orphaned_count == 0:
                print(f"✅ {test['name']}: All references valid")
            else:
                print(f"⚠️ {test['name']}: {orphaned_count} orphaned records")
        except Exception as e:
            print(f"❌ {test['name']}: Error - {e}")

def check_data_quality(conn):
    """Check data quality and consistency."""
    print("\n📊 DATA QUALITY CHECKS:")
    print("-" * 50)
    
    quality_checks = [
        {
            'name': 'Null IDs in Primary Keys',
            'query': '''
                SELECT 
                    'cities' as table_name, COUNT(*) as null_count FROM cities WHERE id IS NULL
                UNION ALL
                SELECT 'brands', COUNT(*) FROM brands WHERE id IS NULL
                UNION ALL
                SELECT 'categories', COUNT(*) FROM categories WHERE id IS NULL
                UNION ALL
                SELECT 'shops', COUNT(*) FROM shops WHERE id IS NULL
                UNION ALL
                SELECT 'base_products', COUNT(*) FROM base_products WHERE random_key IS NULL
                UNION ALL
                SELECT 'members', COUNT(*) FROM members WHERE random_key IS NULL
                UNION ALL
                SELECT 'searches', COUNT(*) FROM searches WHERE id IS NULL
                UNION ALL
                SELECT 'search_results', COUNT(*) FROM search_results WHERE id IS NULL
                UNION ALL
                SELECT 'base_views', COUNT(*) FROM base_views WHERE id IS NULL
                UNION ALL
                SELECT 'final_clicks', COUNT(*) FROM final_clicks WHERE id IS NULL
            '''
        },
        {
            'name': 'Empty Product Names',
            'query': '''
                SELECT COUNT(*) FROM base_products 
                WHERE (persian_name IS NULL OR persian_name = '') 
                AND (english_name IS NULL OR english_name = '')
            '''
        },
        {
            'name': 'Invalid Prices',
            'query': '''
                SELECT COUNT(*) FROM members WHERE price <= 0
            '''
        },
        {
            'name': 'Invalid Shop Scores',
            'query': '''
                SELECT COUNT(*) FROM shops WHERE score < 0 OR score > 5
            '''
        },
        {
            'name': 'Search Results Position Issues',
            'query': '''
                SELECT COUNT(*) FROM search_results WHERE position <= 0
            '''
        }
    ]
    
    for check in quality_checks:
        try:
            cursor = conn.execute(check['query'])
            
            if check['name'] == 'Null IDs in Primary Keys':
                results = cursor.fetchall()
                total_nulls = sum(row[1] for row in results)
                if total_nulls == 0:
                    print(f"✅ {check['name']}: No null primary keys found")
                else:
                    print(f"⚠️ {check['name']}: {total_nulls} null primary keys found")
                    for table, count in results:
                        if count > 0:
                            print(f"   - {table}: {count} null IDs")
            else:
                result = cursor.fetchone()[0]
                if result == 0:
                    print(f"✅ {check['name']}: No issues found")
                else:
                    print(f"⚠️ {check['name']}: {result} issues found")
                    
        except Exception as e:
            print(f"❌ {check['name']}: Error - {e}")

def show_sample_data(conn):
    """Show sample data from key tables."""
    print("\n📝 SAMPLE DATA:")
    print("-" * 50)
    
    sample_queries = [
        {
            'name': 'Recent Searches with Results Count',
            'query': '''
                SELECT s.id, s.query, s.page, COUNT(sr.id) as result_count
                FROM searches s
                LEFT JOIN search_results sr ON s.id = sr.search_id
                GROUP BY s.id, s.query, s.page
                ORDER BY s.timestamp DESC
                LIMIT 5
            '''
        },
        {
            'name': 'Top Categories by Product Count',
            'query': '''
                SELECT c.title, COUNT(bp.random_key) as product_count
                FROM categories c
                LEFT JOIN base_products bp ON c.id = bp.category_id
                GROUP BY c.id, c.title
                ORDER BY product_count DESC
                LIMIT 5
            '''
        },
        {
            'name': 'Shop Performance Summary',
            'query': '''
                SELECT s.id, c.name as city, s.score, COUNT(m.random_key) as product_count
                FROM shops s
                JOIN cities c ON s.city_id = c.id
                LEFT JOIN members m ON s.id = m.shop_id
                GROUP BY s.id, c.name, s.score
                ORDER BY product_count DESC
                LIMIT 5
            '''
        },
        {
            'name': 'Search Results Sample',
            'query': '''
                SELECT s.query, bp.persian_name, sr.position
                FROM search_results sr
                JOIN searches s ON sr.search_id = s.id
                JOIN base_products bp ON sr.base_product_rk = bp.random_key
                WHERE sr.position <= 3
                ORDER BY s.id, sr.position
                LIMIT 10
            '''
        }
    ]
    
    for sample in sample_queries:
        print(f"\n🔍 {sample['name']}:")
        print("-" * 30)
        try:
            cursor = conn.execute(sample['query'])
            results = cursor.fetchall()
            
            if results:
                for i, row in enumerate(results, 1):
                    print(f"  {i}. {' | '.join(str(col) for col in row)}")
            else:
                print("  No data found")
                
        except Exception as e:
            print(f"  ❌ Error: {e}")

def verify_database():
    """Main function to verify database integrity."""
    print("🔍 TOROB DATABASE VERIFICATION")
    print("=" * 60)
    
    conn = connect_to_db()
    if not conn:
        return
    
    try:
        # Check all expected tables
        expected_tables = [
            'cities', 'brands', 'categories', 'shops', 'base_products', 
            'members', 'searches', 'search_results', 'base_views', 'final_clicks'
        ]
        
        print("\n📋 TABLE SUMMARY:")
        print("-" * 50)
        
        total_rows = 0
        for table in expected_tables:
            if check_table_exists(conn, table):
                info = get_table_info(conn, table)
                if 'error' in info:
                    print(f"❌ {table}: Error - {info['error']}")
                else:
                    row_count = info['row_count']
                    col_count = len(info['columns'])
                    total_rows += row_count
                    print(f"✅ {table}: {row_count:,} rows, {col_count} columns")
            else:
                print(f"❌ {table}: Table not found")
        
        print(f"\n📊 Total Records: {total_rows:,}")
        
        # Run integrity checks
        check_foreign_keys(conn)
        check_data_quality(conn)
        show_sample_data(conn)
        
        print("\n" + "=" * 60)
        print("✅ Database verification completed!")
        
    except Exception as e:
        print(f"❌ Verification failed: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    verify_database()

