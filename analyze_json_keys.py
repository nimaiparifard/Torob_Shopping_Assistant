"""
Analyze JSON Keys in extra_features Field - Torob AI Assistant

This script queries the base_products table to extract and analyze
unique keys from the extra_features JSON field.

Usage:
    python analyze_json_keys.py

Author: Torob AI Team
"""

import json
import sqlite3
from collections import Counter
from db.base import DatabaseBaseLoader
from db.create_db import DB_PATH

def analyze_json_keys():
    """Analyze unique keys in extra_features JSON field."""
    
    print("🔍 ANALYZING JSON KEYS IN extra_features FIELD")
    print("=" * 60)
    
    # Connect to database
    db = DatabaseBaseLoader()
    
    try:
        # Query all extra_features data
        print("📊 Querying base_products table...")
        results = db.query("""
            SELECT random_key, extra_features 
            FROM base_products 
            WHERE extra_features IS NOT NULL 
            AND extra_features != '' 
            AND extra_features != 'null'
        """)
        
        print(f"✅ Found {len(results)} products with extra_features data")
        
        # Collect all JSON keys
        all_keys = []
        valid_json_count = 0
        invalid_json_count = 0
        
        print("\n🔍 Processing JSON data...")
        
        for i, row in enumerate(results):
            random_key = row['random_key']
            extra_features = row['extra_features']
            
            try:
                # Parse JSON
                if extra_features and extra_features.strip():
                    json_data = json.loads(extra_features)
                    
                    if isinstance(json_data, dict):
                        # Extract keys from this JSON object
                        keys = list(json_data.keys())
                        all_keys.extend(keys)
                        valid_json_count += 1
                        
                        # Show progress every 1000 records
                        if (i + 1) % 1000 == 0:
                            print(f"   Processed {i + 1:,} records...")
                    else:
                        invalid_json_count += 1
                        
            except (json.JSONDecodeError, TypeError) as e:
                invalid_json_count += 1
                if invalid_json_count <= 5:  # Show first 5 errors
                    print(f"   ⚠️ Invalid JSON in {random_key}: {e}")
        
        print(f"\n📈 PROCESSING SUMMARY:")
        print(f"   Valid JSON records: {valid_json_count:,}")
        print(f"   Invalid JSON records: {invalid_json_count:,}")
        print(f"   Total keys found: {len(all_keys):,}")
        
        # Count unique keys
        key_counts = Counter(all_keys)
        unique_keys = list(key_counts.keys())
        
        print(f"\n🎯 UNIQUE JSON KEYS FOUND: {len(unique_keys)}")
        print("=" * 60)
        
        # Sort keys by frequency (most common first)
        sorted_keys = sorted(key_counts.items(), key=lambda x: x[1], reverse=True)
        
        print(f"\n📊 KEY FREQUENCY ANALYSIS:")
        print("-" * 40)
        for i, (key, count) in enumerate(sorted_keys, 1):
            percentage = (count / len(all_keys)) * 100
            print(f"{i:2d}. {key:<30} | {count:>6,} times ({percentage:5.1f}%)")
        
        # Show sample JSON structures
        print(f"\n🔍 SAMPLE JSON STRUCTURES:")
        print("-" * 40)
        
        sample_count = 0
        for row in results[:10]:  # Show first 10 samples
            try:
                extra_features = row['extra_features']
                if extra_features and extra_features.strip():
                    json_data = json.loads(extra_features)
                    if isinstance(json_data, dict) and json_data:
                        sample_count += 1
                        print(f"\nSample {sample_count} (RK: {row['random_key'][:10]}...):")
                        for key, value in json_data.items():
                            # Truncate long values
                            if isinstance(value, str) and len(value) > 50:
                                display_value = value[:47] + "..."
                            else:
                                display_value = value
                            print(f"  {key}: {display_value}")
            except:
                continue
        
        # Save results to file
        output_file = "json_keys_analysis.txt"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("JSON KEYS ANALYSIS - extra_features FIELD\n")
            f.write("=" * 50 + "\n\n")
            f.write(f"Total products analyzed: {len(results):,}\n")
            f.write(f"Valid JSON records: {valid_json_count:,}\n")
            f.write(f"Invalid JSON records: {invalid_json_count:,}\n")
            f.write(f"Total keys found: {len(all_keys):,}\n")
            f.write(f"Unique keys: {len(unique_keys)}\n\n")
            
            f.write("KEY FREQUENCY ANALYSIS:\n")
            f.write("-" * 30 + "\n")
            for i, (key, count) in enumerate(sorted_keys, 1):
                percentage = (count / len(all_keys)) * 100
                f.write(f"{i:2d}. {key:<30} | {count:>6,} times ({percentage:5.1f}%)\n")
        
        print(f"\n💾 Results saved to: {output_file}")
        print(f"✅ Analysis completed successfully!")
        
    except Exception as e:
        print(f"❌ Error during analysis: {e}")
        
    finally:
        db.close()

def query_specific_keys(key_pattern=None):
    """Query products containing specific JSON keys."""
    
    if not key_pattern:
        print("🔍 Please provide a key pattern to search for.")
        return
    
    print(f"🔍 SEARCHING FOR KEY PATTERN: '{key_pattern}'")
    print("=" * 60)
    
    db = DatabaseBaseLoader()
    
    try:
        # Query products with specific key in extra_features
        results = db.query("""
            SELECT random_key, persian_name, extra_features 
            FROM base_products 
            WHERE extra_features LIKE ?
            LIMIT 20
        """, (f'%"{key_pattern}"%',))
        
        print(f"✅ Found {len(results)} products containing key '{key_pattern}'")
        
        for i, row in enumerate(results, 1):
            print(f"\n{i:2d}. {row['persian_name']}")
            print(f"    RK: {row['random_key']}")
            
            try:
                extra_features = json.loads(row['extra_features'])
                if key_pattern in extra_features:
                    print(f"    {key_pattern}: {extra_features[key_pattern]}")
            except:
                print(f"    Raw extra_features: {row['extra_features'][:100]}...")
                
    except Exception as e:
        print(f"❌ Error: {e}")
        
    finally:
        db.close()

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        # Search for specific key
        key_pattern = sys.argv[1]
        query_specific_keys(key_pattern)
    else:
        # Full analysis
        analyze_json_keys()

