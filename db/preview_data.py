import pandas as pd
import os
from pathlib import Path

def get_backup_path() -> str:
    """Return absolute path to the project's backup directory."""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    repo_root = os.path.abspath(os.path.join(current_dir, os.pardir))
    return os.path.join(repo_root, 'backup')

def preview_parquet_files():
    """Load and preview all parquet files with beautiful formatting."""
    backup_path = get_backup_path()
    
    # Get all parquet files
    parquet_files = [f for f in os.listdir(backup_path) if f.endswith('.parquet')]
    parquet_files.sort()  # Sort alphabetically
    
    print("🎯 TOROB AI ASSISTANT - DATA PREVIEW")
    print("=" * 80)
    print(f"📁 Loading data from: {backup_path}")
    print(f"📊 Found {len(parquet_files)} parquet files")
    print("=" * 80)
    
    for i, file in enumerate(parquet_files, 1):
        file_path = os.path.join(backup_path, file)
        table_name = file.replace('.parquet', '')
        
        print(f"\n🔹 [{i}/{len(parquet_files)}] TABLE: {table_name.upper()}")
        print("-" * 60)
        
        try:
            # Load the parquet file
            df = pd.read_parquet(file_path)
            
            # Basic info
            print(f"📈 Rows: {len(df):,} | Columns: {len(df.columns)}")
            print(f"📋 Columns: {', '.join(df.columns)}")
            
            # Show data types
            print(f"🔧 Data Types:")
            for col, dtype in df.dtypes.items():
                print(f"   • {col}: {dtype}")
            
            print(f"\n📝 SAMPLE DATA (First 3 rows):")
            print("-" * 40)
            
            # Configure pandas display options for better formatting
            pd.set_option('display.max_columns', None)
            pd.set_option('display.width', None)
            pd.set_option('display.max_colwidth', 50)
            pd.set_option('display.expand_frame_repr', False)
            
            # Show first 3 rows
            sample_data = df.head(3)
            
            # Format the display
            if len(sample_data) > 0:
                for idx, row in sample_data.iterrows():
                    print(f"\n   Row {idx + 1}:")
                    for col, value in row.items():
                        # Truncate long values
                        if isinstance(value, str) and len(value) > 50:
                            display_value = value[:47] + "..."
                        else:
                            display_value = value
                        print(f"     {col}: {display_value}")
            else:
                print("   ⚠️ No data available")
                
        except Exception as e:
            print(f"   ❌ Error loading {file}: {e}")
        
        print("-" * 60)
    
    print(f"\n✅ Preview completed for all {len(parquet_files)} files!")
    print("=" * 80)

def preview_specific_table(table_name: str):
    """Preview a specific table with more detailed information."""
    backup_path = get_backup_path()
    file_path = os.path.join(backup_path, f"{table_name}.parquet")
    
    if not os.path.exists(file_path):
        print(f"❌ File not found: {table_name}.parquet")
        return
    
    print(f"🔍 DETAILED PREVIEW: {table_name.upper()}")
    print("=" * 60)
    
    try:
        df = pd.read_parquet(file_path)
        
        # Comprehensive info
        print(f"📊 Shape: {df.shape[0]:,} rows × {df.shape[1]} columns")
        print(f"💾 Memory usage: {df.memory_usage(deep=True).sum() / 1024 / 1024:.2f} MB")
        
        print(f"\n📋 Column Details:")
        for i, (col, dtype) in enumerate(df.dtypes.items(), 1):
            null_count = df[col].isnull().sum()
            null_pct = (null_count / len(df)) * 100
            unique_count = df[col].nunique()
            
            print(f"   {i:2d}. {col}")
            print(f"       Type: {dtype}")
            print(f"       Nulls: {null_count:,} ({null_pct:.1f}%)")
            print(f"       Unique: {unique_count:,}")
            
            # Show sample values
            if df[col].dtype == 'object':
                sample_values = df[col].dropna().head(3).tolist()
                print(f"       Sample: {sample_values}")
            else:
                print(f"       Range: {df[col].min()} to {df[col].max()}")
            print()
        
        print(f"📝 SAMPLE ROWS:")
        print("-" * 40)
        
        # Configure display
        pd.set_option('display.max_columns', None)
        pd.set_option('display.width', None)
        pd.set_option('display.max_colwidth', 60)
        
        print(df.head(3).to_string())
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        # Preview specific table
        table_name = sys.argv[1]
        preview_specific_table(table_name)
    else:
        # Preview all tables
        preview_parquet_files()

