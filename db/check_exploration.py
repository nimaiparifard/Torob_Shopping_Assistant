"""
Check Exploration Table - Torob AI Assistant

This script queries and displays all entries in the exploration table
for debugging and inspection purposes.

Usage:
    python db/check_exploration.py
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db.base import DatabaseBaseLoader

def main():
    """Query and display all exploration table entries."""
    try:
        # Initialize database connection
        db = DatabaseBaseLoader()
        
        # Query all entries from exploration table
        result = db.query("SELECT * FROM exploration ORDER BY chat_id")
        
        print("🔍 EXPLORATION TABLE CONTENTS")
        print("=" * 80)
        
        if not result:
            print("No entries found in exploration table.")
            return
        
        print(f"Total entries: {len(result)}")
        print()
        
        # Display each entry
        for i, row in enumerate(result, 1):
            print(f"Entry #{i}:")
            print(f"  Chat ID: {row['chat_id']}")
            print(f"  Count: {row['counts']}")
            print(f"  Base Random Key: {row['base_random_key']}")
            print(f"  Shop ID: {row['shop_id']}")
            print(f"  Brand ID: {row['brand_id']}")
            print(f"  Category ID: {row['city_id']}")
            print(f"  Category ID: {row['category_id']}")
            print(f"  Lower Price: {row['lower_price']}")
            print(f"  Upper Price: {row['upper_price']}")
            print(f"  Has Warranty: {row['has_warranty']}")
            print(f"  Score: {row['score']}")
            print("-" * 40)
        
        # Summary statistics
        print("\n📊 SUMMARY STATISTICS")
        print("=" * 40)
        
        # Count entries with different patterns
        all_null = sum(1 for row in result if all([
            row['base_random_key'] is None,
            row['shop_id'] is None,
            row['brand_id'] is None,
            row['category_id'] is None,
            row['lower_price'] is None,
            row['upper_price'] is None
        ]))
        
        partial_null = sum(1 for row in result if any([
            row['base_random_key'] is None,
            row['shop_id'] is None,
            row['brand_id'] is None,
            row['category_id'] is None,
            row['lower_price'] is None,
            row['upper_price'] is None
        ]) and not all([
            row['base_random_key'] is None,
            row['shop_id'] is None,
            row['brand_id'] is None,
            row['category_id'] is None,
            row['lower_price'] is None,
            row['upper_price'] is None
        ]))
        
        valid_entries = sum(1 for row in result if all([
            row['base_random_key'] is not None,
            row['shop_id'] is not None,
            row['brand_id'] is not None,
            row['category_id'] is not None
        ]))
        
        print(f"Total entries: {len(result)}")
        print(f"All-NULL entries: {all_null}")
        print(f"Partial-NULL entries: {partial_null}")
        print(f"Valid entries: {valid_entries}")
        
        # Count distribution
        count_dist = {}
        for row in result:
            count = row['counts']
            count_dist[count] = count_dist.get(count, 0) + 1
        
        print(f"\nCount distribution:")
        for count in sorted(count_dist.keys()):
            print(f"  Count {count}: {count_dist[count]} entries")
        
        # Close database connection
        db.close()
        
    except Exception as e:
        print(f"❌ Error querying exploration table: {e}")

if __name__ == "__main__":
    main()
