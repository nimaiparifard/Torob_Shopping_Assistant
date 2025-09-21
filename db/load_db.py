import sqlite3
import pandas as pd
import os
from pathlib import Path
from db.path import get_data_path

# Global dictionaries to store string-to-integer ID mappings
id_mappings = {
    'searches': {},  # string_id -> integer_id
    'base_views': {},  # string_id -> integer_id  
    'final_clicks': {}  # string_id -> integer_id
}

def create_id_mapping(df: pd.DataFrame, id_column: str, table_name: str) -> pd.DataFrame:
    """Create integer ID mapping for string IDs and update the dataframe."""
    df_copy = df.copy()
    
    # Create mapping from string IDs to sequential integers
    unique_ids = df_copy[id_column].unique()
    string_to_int = {str_id: idx + 1 for idx, str_id in enumerate(unique_ids)}
    
    # Store the mapping globally for reference by other tables
    id_mappings[table_name] = string_to_int
    
    # Replace string IDs with integer IDs
    df_copy[id_column] = df_copy[id_column].map(string_to_int)
    
    return df_copy

def map_foreign_key(df: pd.DataFrame, fk_column: str, target_table: str) -> pd.DataFrame:
    """Map foreign key string IDs to integer IDs using existing mapping."""
    df_copy = df.copy()
    
    if target_table in id_mappings:
        # Map foreign key values, handling missing keys with None
        df_copy[fk_column] = df_copy[fk_column].map(id_mappings[target_table])
        
        # Remove rows where foreign key mapping failed (referential integrity)
        before_count = len(df_copy)
        df_copy = df_copy.dropna(subset=[fk_column])
        after_count = len(df_copy)
        
        if before_count != after_count:
            print(f"  ⚠️ Removed {before_count - after_count} rows with invalid foreign keys")
        
        # Convert to integer
        df_copy[fk_column] = df_copy[fk_column].astype(int)
    
    return df_copy

def get_backup_path() -> str:
    """Return absolute path to the project's backup directory."""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    repo_root = os.path.abspath(os.path.join(current_dir, os.pardir))
    return os.path.join(repo_root, 'backup')

def get_db_path() -> str:
    """Return the path to the SQLite database file."""
    from db.create_db import DB_PATH
    return DB_PATH

def load_cities(con: sqlite3.Connection, backup_path: str):
    """Load cities data (no dependencies)."""
    print("Loading cities...")
    df = pd.read_parquet(os.path.join(backup_path, 'cities.parquet'))
    df.to_sql('cities', con, if_exists='append', index=False)
    print(f"  ✓ Loaded {len(df)} cities")

def load_brands(con: sqlite3.Connection, backup_path: str):
    """Load brands data (no dependencies)."""
    print("Loading brands...")
    df = pd.read_parquet(os.path.join(backup_path, 'brands.parquet'))
    df.to_sql('brands', con, if_exists='append', index=False)
    print(f"  ✓ Loaded {len(df)} brands")

def load_categories(con: sqlite3.Connection, backup_path: str):
    """Load categories data (no FK dependencies, but has self-reference)."""
    print("Loading categories...")
    df = pd.read_parquet(os.path.join(backup_path, 'categories.parquet'))
    
    # Sort by parent_id to load parent categories first (if any have parent_id != -1)
    # This ensures parent categories exist before children are inserted
    df = df.sort_values('parent_id', na_position='first')
    
    df.to_sql('categories', con, if_exists='append', index=False)
    print(f"  ✓ Loaded {len(df)} categories")

def load_shops(con: sqlite3.Connection, backup_path: str):
    """Load shops data (depends on cities)."""
    print("Loading shops...")
    df = pd.read_parquet(os.path.join(backup_path, 'shops.parquet'))
    df.to_sql('shops', con, if_exists='append', index=False)
    print(f"  ✓ Loaded {len(df)} shops")

def load_base_products(con: sqlite3.Connection, backup_path: str):
    """Load base_products data (depends on categories and brands)."""
    print("Loading base_products...")
    df = pd.read_parquet(os.path.join(backup_path, 'base_products.parquet'))
    df.to_sql('base_products', con, if_exists='append', index=False)
    print(f"  ✓ Loaded {len(df)} base products")

def load_members(con: sqlite3.Connection, backup_path: str):
    """Load members data (depends on base_products and shops)."""
    print("Loading members...")
    df = pd.read_parquet(os.path.join(backup_path, 'members.parquet'))
    df.to_sql('members', con, if_exists='append', index=False)
    print(f"  ✓ Loaded {len(df)} members")

def load_searches(con: sqlite3.Connection, backup_path: str):
    """Load searches data with string-to-integer ID conversion."""
    print("Loading searches...")
    df = pd.read_parquet(os.path.join(backup_path, 'searches.parquet'))
    
    # Convert timestamp to string format for SQLite
    df['timestamp'] = df['timestamp'].dt.strftime('%Y-%m-%d %H:%M:%S.%f+00:00')
    
    # Create integer ID mapping for the 'id' column
    df = create_id_mapping(df, 'id', 'searches')
    
    # Create integer mapping for uid column (it's just a regular INTEGER column, not FK)
    unique_uids = df['uid'].unique()
    uid_to_int = {str_uid: idx + 1 for idx, str_uid in enumerate(unique_uids)}
    df['uid'] = df['uid'].map(uid_to_int)
    
    # Sort by page to ensure consistent loading order
    df = df.sort_values(['uid', 'page'], na_position='first')
    
    df.to_sql('searches', con, if_exists='append', index=False)
    print(f"  ✓ Loaded {len(df)} searches")

def load_search_results(con: sqlite3.Connection, backup_path: str):
    """Load search results data by normalizing the result_base_product_rks JSON arrays."""
    print("Loading search_results...")
    df = pd.read_parquet(os.path.join(backup_path, 'searches.parquet'))
    
    search_results_data = []
    
    # Process each search record
    for _, row in df.iterrows():
        search_id = row['id']
        result_rks = row['result_base_product_rks']
        
        # Parse the JSON array of product random keys
        if isinstance(result_rks, str):
            try:
                import json
                product_rks = json.loads(result_rks.replace("'", '"'))
            except:
                # If JSON parsing fails, try to parse as Python array
                try:
                    product_rks = eval(result_rks)
                except:
                    continue
        elif hasattr(result_rks, '__iter__'):
            # If it's already an array/list
            product_rks = result_rks
        else:
            continue
        
        # Create a record for each product in the search results
        for position, product_rk in enumerate(product_rks, 1):
            search_results_data.append({
                'search_id': search_id,
                'base_product_rk': product_rk,
                'position': position
            })
    
    # Convert to DataFrame and load to database
    if search_results_data:
        results_df = pd.DataFrame(search_results_data)
        results_df.to_sql('search_results', con, if_exists='append', index=False)
        print(f"  ✓ Loaded {len(results_df)} search results")
    else:
        print("  ⚠️ No search results data found")

def load_base_views(con: sqlite3.Connection, backup_path: str):
    """Load base_views data (depends on searches and base_products)."""
    print("Loading base_views...")
    df = pd.read_parquet(os.path.join(backup_path, 'base_views.parquet'))
    
    # Convert timestamp to string format for SQLite
    df['timestamp'] = df['timestamp'].dt.strftime('%Y-%m-%d %H:%M:%S.%f+00:00')
    
    # Create integer ID mapping for the 'id' column
    df = create_id_mapping(df, 'id', 'base_views')
    
    # Map the search_id foreign key to integer IDs (references searches.id)
    df = map_foreign_key(df, 'search_id', 'searches')
    
    # base_product_rk stays as string (references base_products.random_key which is TEXT)
    
    df.to_sql('base_views', con, if_exists='append', index=False)
    print(f"  ✓ Loaded {len(df)} base views")

def load_final_clicks(con: sqlite3.Connection, backup_path: str):
    """Load final_clicks data (depends on base_views and shops)."""
    print("Loading final_clicks...")
    df = pd.read_parquet(os.path.join(backup_path, 'final_clicks.parquet'))
    
    # Convert timestamp to string format for SQLite
    df['timestamp'] = df['timestamp'].dt.strftime('%Y-%m-%d %H:%M:%S.%f+00:00')
    
    # Create integer ID mapping for the 'id' column
    df = create_id_mapping(df, 'id', 'final_clicks')
    
    # Map the base_view_id foreign key to integer IDs (references base_views.id)
    df = map_foreign_key(df, 'base_view_id', 'base_views')
    
    # shop_id is already integer and references shops.id
    
    df.to_sql('final_clicks', con, if_exists='append', index=False)
    print(f"  ✓ Loaded {len(df)} final clicks")

def load_all_data():
    """Load all parquet files into SQLite database in the correct order based on FK dependencies."""
    backup_path = get_backup_path()
    db_path = get_db_path()
    
    # Ensure data directory exists
    data_dir = os.path.dirname(db_path)
    if not os.path.exists(data_dir):
        os.makedirs(data_dir, exist_ok=True)
    
    print(f"Loading data from: {backup_path}")
    print(f"Into database: {db_path}")
    print("=" * 50)
    
    con = None
    try:
        con = sqlite3.connect(db_path)
        
        # Loading order based on foreign key dependencies:
        # 1. Independent tables (no FK dependencies)
        load_cities(con, backup_path)
        load_brands(con, backup_path)
        load_categories(con, backup_path)
        
        # 2. Tables with single-level dependencies
        load_shops(con, backup_path)  # depends on cities
        load_base_products(con, backup_path)  # depends on categories, brands
        
        # 3. Tables with multi-level dependencies
        load_members(con, backup_path)  # depends on base_products, shops
        load_searches(con, backup_path)  # self-referential
        load_search_results(con, backup_path)  # depends on searches, base_products
        
        # 4. Tables with complex dependencies
        load_base_views(con, backup_path)  # depends on searches, base_products
        load_final_clicks(con, backup_path)  # depends on base_views, shops
        
        con.commit()
        print("=" * 50)
        print("✅ All data loaded successfully!")
        
        # Display summary statistics
        print("\n📊 Database Summary:")
        tables = ['cities', 'brands', 'categories', 'shops', 'base_products', 
                 'members', 'searches', 'search_results', 'base_views', 'final_clicks']
        
        for table in tables:
            cursor = con.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            print(f"  {table}: {count:,} rows")
            
    except Exception as e:
        print(f"❌ Error loading data: {e}")
        if con:
            con.rollback()
        raise
    finally:
        if con:
            con.close()

if __name__ == "__main__":
    load_all_data()
