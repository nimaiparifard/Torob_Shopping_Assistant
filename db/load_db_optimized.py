"""
Memory-Optimized Database Loader - Torob AI Assistant

This module loads parquet files into SQLite database with minimal memory usage.
It processes data in chunks and loads one table at a time to reduce RAM consumption.

Key optimizations:
- Chunked data processing
- One table at a time loading
- Memory cleanup after each table
- Streaming data processing for large tables

Usage:
    python -m db.load_db_optimized
    python -m db.load_db_optimized --table cities
    python -m db.load_db_optimized --chunk-size 10000

Author: Torob AI Team
"""

import sqlite3
import pandas as pd
import os
import gc
import argparse
from pathlib import Path
from db.config import get_data_path, get_db_path, get_backup_path, ensure_data_directory

# Global dictionaries to store string-to-integer ID mappings
id_mappings = {
    'searches': {},  # string_id -> integer_id
    'base_views': {},  # string_id -> integer_id  
    'final_clicks': {}  # string_id -> integer_id
}

def create_id_mapping_chunked(df_chunk: pd.DataFrame, id_column: str, table_name: str) -> pd.DataFrame:
    """Create integer ID mapping for string IDs in a chunk."""
    df_copy = df_chunk.copy()
    
    # Get unique IDs in this chunk
    unique_ids = df_copy[id_column].unique()
    
    # Check if we need to add new mappings
    if table_name not in id_mappings:
        id_mappings[table_name] = {}
    
    # Find the next available ID
    next_id = max(id_mappings[table_name].values()) + 1 if id_mappings[table_name] else 1
    
    # Create mappings for new IDs
    for str_id in unique_ids:
        if str_id not in id_mappings[table_name]:
            id_mappings[table_name][str_id] = next_id
            next_id += 1
    
    # Replace string IDs with integer IDs
    df_copy[id_column] = df_copy[id_column].map(id_mappings[table_name])
    
    return df_copy

def map_foreign_key_chunked(df_chunk: pd.DataFrame, fk_column: str, target_table: str) -> pd.DataFrame:
    """Map foreign key string IDs to integer IDs using existing mapping."""
    df_copy = df_chunk.copy()
    
    if target_table in id_mappings:
        # Map foreign key values, handling missing keys with None
        df_copy[fk_column] = df_copy[fk_column].map(id_mappings[target_table])
        
        # Remove rows where foreign key mapping failed (referential integrity)
        before_count = len(df_copy)
        df_copy = df_copy.dropna(subset=[fk_column])
        after_count = len(df_copy)
        
        if before_count != after_count:
            print(f"  [WARNING] Removed {before_count - after_count} rows with invalid foreign keys")
        
        # Convert to integer
        df_copy[fk_column] = df_copy[fk_column].astype(int)
    
    return df_copy

def load_table_in_chunks(con: sqlite3.Connection, backup_path: str, table_name: str, 
                        chunk_size: int = 10000, **kwargs):
    """Load a table in chunks to reduce memory usage."""
    parquet_path = os.path.join(backup_path, f'{table_name}.parquet')
    
    if not os.path.exists(parquet_path):
        print(f"  [WARNING] Parquet file not found: {parquet_path}")
        return
    
    print(f"Loading {table_name} in chunks of {chunk_size:,} rows...")
    
    # Get total rows for progress tracking
    total_rows = 0
    try:
        # Get total rows by reading the parquet file metadata
        parquet_file = pd.read_parquet(parquet_path)
        total_rows = len(parquet_file)
        del parquet_file  # Free memory
        gc.collect()
    except Exception as e:
        print(f"  [ERROR] Could not determine total rows: {e}")
        return
    
    print(f"  Total rows to process: {total_rows:,}")
    
    # Process in chunks
    processed_rows = 0
    chunk_num = 0
    
    try:
        # Read parquet file in chunks manually
        df = pd.read_parquet(parquet_path)
        
        # Process in chunks
        for start_idx in range(0, total_rows, chunk_size):
            chunk_num += 1
            end_idx = min(start_idx + chunk_size, total_rows)
            chunk = df.iloc[start_idx:end_idx].copy()
            chunk_rows = len(chunk)
            
            print(f"  Processing chunk {chunk_num}: {chunk_rows:,} rows")
            
            # Apply any transformations
            if 'transform_func' in kwargs:
                chunk = kwargs['transform_func'](chunk)
            
            # Load chunk to database
            if chunk_num == 1:
                # First chunk - replace table
                chunk.to_sql(table_name, con, if_exists='replace', index=False)
            else:
                # Subsequent chunks - append
                chunk.to_sql(table_name, con, if_exists='append', index=False)
            
            processed_rows += chunk_rows
            print(f"  [OK] Chunk {chunk_num} loaded ({processed_rows:,}/{total_rows:,} rows)")
            
            # Force garbage collection
            del chunk
            gc.collect()
        
        # Clean up the main dataframe
        del df
        gc.collect()
        
        print(f"  [SUCCESS] Loaded {processed_rows:,} rows into {table_name}")
        
    except Exception as e:
        print(f"  [ERROR] Failed to load {table_name}: {e}")
        raise

def load_cities_optimized(con: sqlite3.Connection, backup_path: str, chunk_size: int = 10000):
    """Load cities data in chunks (no dependencies)."""
    load_table_in_chunks(con, backup_path, 'cities', chunk_size)

def load_brands_optimized(con: sqlite3.Connection, backup_path: str, chunk_size: int = 10000):
    """Load brands data in chunks (no dependencies)."""
    load_table_in_chunks(con, backup_path, 'brands', chunk_size)

def load_categories_optimized(con: sqlite3.Connection, backup_path: str, chunk_size: int = 10000):
    """Load categories data in chunks (no FK dependencies, but has self-reference)."""
    def transform_categories(df):
        # Sort by parent_id to load parent categories first
        return df.sort_values('parent_id', na_position='first')
    
    load_table_in_chunks(con, backup_path, 'categories', chunk_size, 
                        transform_func=transform_categories)

def load_shops_optimized(con: sqlite3.Connection, backup_path: str, chunk_size: int = 10000):
    """Load shops data in chunks (depends on cities)."""
    load_table_in_chunks(con, backup_path, 'shops', chunk_size)

def load_base_products_optimized(con: sqlite3.Connection, backup_path: str, chunk_size: int = 5000):
    """Load base_products data in chunks (depends on categories and brands)."""
    # Smaller chunk size for base_products due to large size
    load_table_in_chunks(con, backup_path, 'base_products', chunk_size)

def load_members_optimized(con: sqlite3.Connection, backup_path: str, chunk_size: int = 10000):
    """Load members data in chunks (depends on base_products and shops)."""
    load_table_in_chunks(con, backup_path, 'members', chunk_size)

def load_searches_optimized(con: sqlite3.Connection, backup_path: str, chunk_size: int = 5000):
    """Load searches data in chunks with string-to-integer ID conversion."""
    print("Loading searches in chunks...")
    
    parquet_path = os.path.join(backup_path, 'searches.parquet')
    if not os.path.exists(parquet_path):
        print(f"  [WARNING] Parquet file not found: {parquet_path}")
        return
    
    # Get total rows
    try:
        parquet_file = pd.read_parquet(parquet_path)
        total_rows = len(parquet_file)
        del parquet_file
        gc.collect()
    except Exception as e:
        print(f"  [ERROR] Could not determine total rows: {e}")
        return
    
    print(f"  Total rows to process: {total_rows:,}")
    
    processed_rows = 0
    chunk_num = 0
    
    try:
        # Read parquet file and process in chunks
        df = pd.read_parquet(parquet_path)
        
        for start_idx in range(0, total_rows, chunk_size):
            chunk_num += 1
            end_idx = min(start_idx + chunk_size, total_rows)
            chunk = df.iloc[start_idx:end_idx].copy()
            chunk_rows = len(chunk)
            
            print(f"  Processing chunk {chunk_num}: {chunk_rows:,} rows")
            
            # Convert timestamp to string format for SQLite
            chunk['timestamp'] = chunk['timestamp'].dt.strftime('%Y-%m-%d %H:%M:%S.%f+00:00')
            
            # Create integer ID mapping for the 'id' column
            chunk = create_id_mapping_chunked(chunk, 'id', 'searches')
            
            # Create integer mapping for uid column
            unique_uids = chunk['uid'].unique()
            uid_to_int = {str_uid: idx + 1 for idx, str_uid in enumerate(unique_uids)}
            chunk['uid'] = chunk['uid'].map(uid_to_int)
            
            # Sort by page to ensure consistent loading order
            chunk = chunk.sort_values(['uid', 'page'], na_position='first')
            
            # Load chunk to database
            if chunk_num == 1:
                chunk.to_sql('searches', con, if_exists='replace', index=False)
            else:
                chunk.to_sql('searches', con, if_exists='append', index=False)
            
            processed_rows += chunk_rows
            print(f"  [OK] Chunk {chunk_num} loaded ({processed_rows:,}/{total_rows:,} rows)")
            
            # Force garbage collection
            del chunk
            gc.collect()
        
        # Clean up the main dataframe
        del df
        gc.collect()
        
        print(f"  [SUCCESS] Loaded {processed_rows:,} rows into searches")
        
    except Exception as e:
        print(f"  [ERROR] Failed to load searches: {e}")
        raise

def load_search_results_optimized(con: sqlite3.Connection, backup_path: str, chunk_size: int = 5000):
    """Load search results data in chunks by normalizing JSON arrays."""
    print("Loading search_results in chunks...")
    
    parquet_path = os.path.join(backup_path, 'searches.parquet')
    if not os.path.exists(parquet_path):
        print(f"  [WARNING] Parquet file not found: {parquet_path}")
        return
    
    # Get total rows
    try:
        parquet_file = pd.read_parquet(parquet_path)
        total_rows = len(parquet_file)
        del parquet_file
        gc.collect()
    except Exception as e:
        print(f"  [ERROR] Could not determine total rows: {e}")
        return
    
    print(f"  Total rows to process: {total_rows:,}")
    
    processed_rows = 0
    chunk_num = 0
    all_search_results = []
    
    try:
        # Read parquet file and process in chunks
        df = pd.read_parquet(parquet_path)
        
        for start_idx in range(0, total_rows, chunk_size):
            chunk_num += 1
            end_idx = min(start_idx + chunk_size, total_rows)
            chunk = df.iloc[start_idx:end_idx].copy()
            chunk_rows = len(chunk)
            
            print(f"  Processing chunk {chunk_num}: {chunk_rows:,} rows")
            
            search_results_data = []
            
            # Process each search record in this chunk
            for _, row in chunk.iterrows():
                search_id = row['id']
                result_rks = row['result_base_product_rks']
                
                # Parse the JSON array of product random keys
                if isinstance(result_rks, str):
                    try:
                        import json
                        product_rks = json.loads(result_rks.replace("'", '"'))
                    except:
                        try:
                            product_rks = eval(result_rks)
                        except:
                            continue
                elif hasattr(result_rks, '__iter__'):
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
            
            all_search_results.extend(search_results_data)
            processed_rows += chunk_rows
            print(f"  [OK] Chunk {chunk_num} processed ({processed_rows:,}/{total_rows:,} rows)")
            
            # Force garbage collection
            del chunk
            gc.collect()
        
        # Clean up the main dataframe
        del df
        gc.collect()
        
        # Load all search results to database
        if all_search_results:
            print(f"  Loading {len(all_search_results):,} search results to database...")
            results_df = pd.DataFrame(all_search_results)
            results_df.to_sql('search_results', con, if_exists='replace', index=False)
            print(f"  [SUCCESS] Loaded {len(all_search_results):,} search results")
        else:
            print("  [WARNING] No search results data found")
        
    except Exception as e:
        print(f"  [ERROR] Failed to load search_results: {e}")
        raise

def load_base_views_optimized(con: sqlite3.Connection, backup_path: str, chunk_size: int = 5000):
    """Load base_views data in chunks (depends on searches and base_products)."""
    print("Loading base_views in chunks...")
    
    parquet_path = os.path.join(backup_path, 'base_views.parquet')
    if not os.path.exists(parquet_path):
        print(f"  [WARNING] Parquet file not found: {parquet_path}")
        return
    
    # Get total rows
    try:
        parquet_file = pd.read_parquet(parquet_path)
        total_rows = len(parquet_file)
        del parquet_file
        gc.collect()
    except Exception as e:
        print(f"  [ERROR] Could not determine total rows: {e}")
        return
    
    print(f"  Total rows to process: {total_rows:,}")
    
    processed_rows = 0
    chunk_num = 0
    
    try:
        # Read parquet file and process in chunks
        df = pd.read_parquet(parquet_path)
        
        for start_idx in range(0, total_rows, chunk_size):
            chunk_num += 1
            end_idx = min(start_idx + chunk_size, total_rows)
            chunk = df.iloc[start_idx:end_idx].copy()
            chunk_rows = len(chunk)
            
            print(f"  Processing chunk {chunk_num}: {chunk_rows:,} rows")
            
            # Convert timestamp to string format for SQLite
            chunk['timestamp'] = chunk['timestamp'].dt.strftime('%Y-%m-%d %H:%M:%S.%f+00:00')
            
            # Create integer ID mapping for the 'id' column
            chunk = create_id_mapping_chunked(chunk, 'id', 'base_views')
            
            # Map the search_id foreign key to integer IDs
            chunk = map_foreign_key_chunked(chunk, 'search_id', 'searches')
            
            # Load chunk to database
            if chunk_num == 1:
                chunk.to_sql('base_views', con, if_exists='replace', index=False)
            else:
                chunk.to_sql('base_views', con, if_exists='append', index=False)
            
            processed_rows += chunk_rows
            print(f"  [OK] Chunk {chunk_num} loaded ({processed_rows:,}/{total_rows:,} rows)")
            
            # Force garbage collection
            del chunk
            gc.collect()
        
        # Clean up the main dataframe
        del df
        gc.collect()
        
        print(f"  [SUCCESS] Loaded {processed_rows:,} rows into base_views")
        
    except Exception as e:
        print(f"  [ERROR] Failed to load base_views: {e}")
        raise

def load_final_clicks_optimized(con: sqlite3.Connection, backup_path: str, chunk_size: int = 5000):
    """Load final_clicks data in chunks (depends on base_views and shops)."""
    print("Loading final_clicks in chunks...")
    
    parquet_path = os.path.join(backup_path, 'final_clicks.parquet')
    if not os.path.exists(parquet_path):
        print(f"  [WARNING] Parquet file not found: {parquet_path}")
        return
    
    # Get total rows
    try:
        parquet_file = pd.read_parquet(parquet_path)
        total_rows = len(parquet_file)
        del parquet_file
        gc.collect()
    except Exception as e:
        print(f"  [ERROR] Could not determine total rows: {e}")
        return
    
    print(f"  Total rows to process: {total_rows:,}")
    
    processed_rows = 0
    chunk_num = 0
    
    try:
        # Read parquet file and process in chunks
        df = pd.read_parquet(parquet_path)
        
        for start_idx in range(0, total_rows, chunk_size):
            chunk_num += 1
            end_idx = min(start_idx + chunk_size, total_rows)
            chunk = df.iloc[start_idx:end_idx].copy()
            chunk_rows = len(chunk)
            
            print(f"  Processing chunk {chunk_num}: {chunk_rows:,} rows")
            
            # Convert timestamp to string format for SQLite
            chunk['timestamp'] = chunk['timestamp'].dt.strftime('%Y-%m-%d %H:%M:%S.%f+00:00')
            
            # Create integer ID mapping for the 'id' column
            chunk = create_id_mapping_chunked(chunk, 'id', 'final_clicks')
            
            # Map the base_view_id foreign key to integer IDs
            chunk = map_foreign_key_chunked(chunk, 'base_view_id', 'base_views')
            
            # Load chunk to database
            if chunk_num == 1:
                chunk.to_sql('final_clicks', con, if_exists='replace', index=False)
            else:
                chunk.to_sql('final_clicks', con, if_exists='append', index=False)
            
            processed_rows += chunk_rows
            print(f"  [OK] Chunk {chunk_num} loaded ({processed_rows:,}/{total_rows:,} rows)")
            
            # Force garbage collection
            del chunk
            gc.collect()
        
        # Clean up the main dataframe
        del df
        gc.collect()
        
        print(f"  [SUCCESS] Loaded {processed_rows:,} rows into final_clicks")
        
    except Exception as e:
        print(f"  [ERROR] Failed to load final_clicks: {e}")
        raise

def load_all_data_optimized(chunk_size: int = 10000, table_name: str = None):
    """Load all parquet files into SQLite database with memory optimization."""
    backup_path = get_backup_path()
    db_path = get_db_path()
    
    # Ensure data directory exists
    ensure_data_directory()
    
    print(f"Memory-Optimized Database Loading")
    print(f"Loading data from: {backup_path}")
    print(f"Into database: {db_path}")
    print(f"Chunk size: {chunk_size:,} rows")
    print("=" * 60)
    
    # Define loading order and functions
    loading_order = [
        ('cities', load_cities_optimized),
        ('brands', load_brands_optimized),
        ('categories', load_categories_optimized),
        ('shops', load_shops_optimized),
        ('base_products', load_base_products_optimized),
        ('members', load_members_optimized),
        ('searches', load_searches_optimized),
        ('search_results', load_search_results_optimized),
        ('base_views', load_base_views_optimized),
        ('final_clicks', load_final_clicks_optimized),
    ]
    
    # Filter to specific table if requested
    if table_name:
        loading_order = [(name, func) for name, func in loading_order if name == table_name]
        if not loading_order:
            print(f"[ERROR] Table '{table_name}' not found in loading order")
            return
    
    con = None
    try:
        con = sqlite3.connect(db_path)
        
        for table_name, load_func in loading_order:
            print(f"\n{'='*20} Loading {table_name.upper()} {'='*20}")
            
            # Load the table
            load_func(con, backup_path, chunk_size)
            
            # Commit after each table
            con.commit()
            print(f"[SUCCESS] {table_name} loaded and committed")
            
            # Force garbage collection
            gc.collect()
        
        print("\n" + "=" * 60)
        print("[SUCCESS] All data loaded successfully!")
        
        # Display summary statistics
        print("\nDatabase Summary:")
        tables = ['cities', 'brands', 'categories', 'shops', 'base_products', 
                 'members', 'searches', 'search_results', 'base_views', 'final_clicks']
        
        for table in tables:
            cursor = con.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            print(f"  {table}: {count:,} rows")
            
    except Exception as e:
        print(f"[ERROR] Error loading data: {e}")
        if con:
            con.rollback()
        raise
    finally:
        if con:
            con.close()

def main():
    """Main function with command line arguments."""
    parser = argparse.ArgumentParser(
        description="Memory-optimized database loader",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m db.load_db_optimized
  python -m db.load_db_optimized --table cities
  python -m db.load_db_optimized --chunk-size 5000
  python -m db.load_db_optimized --table base_products --chunk-size 2000
        """
    )
    
    parser.add_argument(
        '--table',
        help='Load only specific table (e.g., cities, base_products)'
    )
    
    parser.add_argument(
        '--chunk-size',
        type=int,
        default=10000,
        help='Number of rows to process in each chunk (default: 10000)'
    )
    
    args = parser.parse_args()
    
    # Load data
    load_all_data_optimized(
        chunk_size=args.chunk_size,
        table_name=args.table
    )

if __name__ == "__main__":
    main()
