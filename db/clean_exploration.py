"""
Clean Exploration Table - Torob AI Assistant

This module provides functionality to clean the exploration table from entries
that represent "no data found" scenarios. It can remove entries with:
- All NULL values (except chat_id and counts)
- Partial NULL values based on specific criteria
- Entries with specific patterns indicating no data found

Usage:
    # Clean ALL entries from exploration table (no constraints)
    python -m db.clean_exploration --clean-everything
    
    # Clean all entries with no data
    python -m db.clean_exploration --clean-all
    
    # Clean entries with all NULL values
    python -m db.clean_exploration --clean-null
    
    # Clean entries older than 7 days
    python -m db.clean_exploration --clean-old --days 7
    
    # Show statistics only
    python -m db.clean_exploration --stats
    
    # Backup before cleaning
    python -m db.clean_exploration --backup --clean-everything

Author: Torob AI Team
"""

import sqlite3
import os
import argparse
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any, Tuple
from db.config import get_db_path
from db.base import DatabaseBaseLoader


class ExplorationCleaner:
    """
    Cleaner class for the exploration table.
    Provides various cleaning strategies for removing "no data found" entries.
    """
    
    def __init__(self, db_path: str = None):
        """
        Initialize the exploration cleaner.
        
        Args:
            db_path (str, optional): Path to database file. Defaults to get_db_path().
        """
        self.db_path = db_path or get_db_path()
        self.db = DatabaseBaseLoader(self.db_path)
        self.backup_dir = Path("backup")
        self.backup_dir.mkdir(exist_ok=True)
    
    def get_exploration_stats(self) -> Dict[str, Any]:
        """
        Get comprehensive statistics about the exploration table.
        
        Returns:
            Dict containing various statistics about the exploration table.
        """
        try:
            stats = {}
            
            # Total entries
            total_result = self.db.query("SELECT COUNT(*) as total FROM exploration")
            stats['total_entries'] = total_result[0]['total'] if total_result else 0
            
            # Entries with all NULL values (except chat_id and counts)
            null_all_result = self.db.query("""
                SELECT COUNT(*) as count FROM exploration 
                WHERE base_random_key IS NULL 
                AND shop_id IS NULL 
                AND brand_id IS NULL 
                AND category_id IS NULL 
                AND lower_price IS NULL 
                AND upper_price IS NULL
            """)
            stats['all_null_entries'] = null_all_result[0]['count'] if null_all_result else 0
            
            # Entries with partial NULL values
            partial_null_result = self.db.query("""
                SELECT COUNT(*) as count FROM exploration 
                WHERE (base_random_key IS NULL 
                OR shop_id IS NULL 
                OR brand_id IS NULL 
                OR category_id IS NULL 
                OR lower_price IS NULL 
                OR upper_price IS NULL)
                AND NOT (base_random_key IS NULL 
                AND shop_id IS NULL 
                AND brand_id IS NULL 
                AND category_id IS NULL 
                AND lower_price IS NULL 
                AND upper_price IS NULL)
            """)
            stats['partial_null_entries'] = partial_null_result[0]['count'] if partial_null_result else 0
            
            # Entries with valid data (no NULL values in key fields)
            valid_result = self.db.query("""
                SELECT COUNT(*) as count FROM exploration 
                WHERE base_random_key IS NOT NULL 
                AND shop_id IS NOT NULL 
                AND brand_id IS NOT NULL 
                AND category_id IS NOT NULL
            """)
            stats['valid_entries'] = valid_result[0]['count'] if valid_result else 0
            
            # Entries with only counts (typical "no data found" pattern)
            counts_only_result = self.db.query("""
                SELECT COUNT(*) as count FROM exploration 
                WHERE counts > 0 
                AND base_random_key IS NULL 
                AND shop_id IS NULL 
                AND brand_id IS NULL 
                AND category_id IS NULL 
                AND lower_price IS NULL 
                AND upper_price IS NULL
            """)
            stats['counts_only_entries'] = counts_only_result[0]['count'] if counts_only_result else 0
            
            # Count distribution
            count_dist_result = self.db.query("""
                SELECT counts, COUNT(*) as frequency 
                FROM exploration 
                GROUP BY counts 
                ORDER BY counts
            """)
            stats['count_distribution'] = {row['counts']: row['frequency'] for row in count_dist_result}
            
            # Entries with high counts (might be stuck in exploration loop)
            high_count_result = self.db.query("""
                SELECT COUNT(*) as count FROM exploration 
                WHERE counts > 10
            """)
            stats['high_count_entries'] = high_count_result[0]['count'] if high_count_result else 0
            
            return stats
            
        except Exception as e:
            print(f"Error getting exploration stats: {e}")
            return {}
    
    def clean_all_null_entries(self) -> int:
        """
        Remove entries where all data fields are NULL (except chat_id and counts).
        These represent "no data found" scenarios.
        
        Returns:
            int: Number of entries removed.
        """
        try:
            # Count entries to be removed
            count_result = self.db.query("""
                SELECT COUNT(*) as count FROM exploration 
                WHERE base_random_key IS NULL 
                AND shop_id IS NULL 
                AND brand_id IS NULL 
                AND category_id IS NULL 
                AND lower_price IS NULL 
                AND upper_price IS NULL
            """)
            entries_to_remove = count_result[0]['count'] if count_result else 0
            
            if entries_to_remove == 0:
                print("No all-NULL entries found to clean.")
                return 0
            
            # Remove the entries
            self.db.execute("""
                DELETE FROM exploration 
                WHERE base_random_key IS NULL 
                AND shop_id IS NULL 
                AND brand_id IS NULL 
                AND category_id IS NULL 
                AND lower_price IS NULL 
                AND upper_price IS NULL
            """)
            
            print(f"✅ Removed {entries_to_remove} entries with all NULL values.")
            return entries_to_remove
            
        except Exception as e:
            print(f"❌ Error cleaning all-NULL entries: {e}")
            return 0
    
    def clean_counts_only_entries(self) -> int:
        """
        Remove entries that only have counts but no other data.
        These are typical "no data found" patterns.
        
        Returns:
            int: Number of entries removed.
        """
        try:
            # Count entries to be removed
            count_result = self.db.query("""
                SELECT COUNT(*) as count FROM exploration 
                WHERE counts > 0 
                AND base_random_key IS NULL 
                AND shop_id IS NULL 
                AND brand_id IS NULL 
                AND category_id IS NULL 
                AND lower_price IS NULL 
                AND upper_price IS NULL
            """)
            entries_to_remove = count_result[0]['count'] if count_result else 0
            
            if entries_to_remove == 0:
                print("No counts-only entries found to clean.")
                return 0
            
            # Remove the entries
            self.db.execute("""
                DELETE FROM exploration 
                WHERE counts > 0 
                AND base_random_key IS NULL 
                AND shop_id IS NULL 
                AND brand_id IS NULL 
                AND category_id IS NULL 
                AND lower_price IS NULL 
                AND upper_price IS NULL
            """)
            
            print(f"✅ Removed {entries_to_remove} counts-only entries.")
            return entries_to_remove
            
        except Exception as e:
            print(f"❌ Error cleaning counts-only entries: {e}")
            return 0
    
    def clean_high_count_entries(self, max_count: int = 10) -> int:
        """
        Remove entries with very high counts that might be stuck in exploration loops.
        
        Args:
            max_count (int): Maximum allowed count. Entries with higher counts will be removed.
            
        Returns:
            int: Number of entries removed.
        """
        try:
            # Count entries to be removed
            count_result = self.db.query("""
                SELECT COUNT(*) as count FROM exploration 
                WHERE counts > ?
            """, (max_count,))
            entries_to_remove = count_result[0]['count'] if count_result else 0
            
            if entries_to_remove == 0:
                print(f"No entries with count > {max_count} found to clean.")
                return 0
            
            # Remove the entries
            self.db.execute("""
                DELETE FROM exploration 
                WHERE counts > ?
            """, (max_count,))
            
            print(f"✅ Removed {entries_to_remove} entries with count > {max_count}.")
            return entries_to_remove
            
        except Exception as e:
            print(f"❌ Error cleaning high-count entries: {e}")
            return 0
    
    def clean_old_entries(self, days: int = 7) -> int:
        """
        Remove entries older than specified days.
        Note: This requires a timestamp column which might not exist in exploration table.
        
        Args:
            days (int): Number of days. Entries older than this will be removed.
            
        Returns:
            int: Number of entries removed.
        """
        try:
            # Check if we have a timestamp column
            columns_result = self.db.query("PRAGMA table_info(exploration)")
            columns = [row['name'] for row in columns_result]
            
            if 'timestamp' not in columns:
                print("⚠️ No timestamp column found in exploration table. Cannot clean old entries.")
                return 0
            
            # Calculate cutoff date
            cutoff_date = datetime.now() - timedelta(days=days)
            cutoff_str = cutoff_date.strftime('%Y-%m-%d %H:%M:%S')
            
            # Count entries to be removed
            count_result = self.db.query("""
                SELECT COUNT(*) as count FROM exploration 
                WHERE timestamp < ?
            """, (cutoff_str,))
            entries_to_remove = count_result[0]['count'] if count_result else 0
            
            if entries_to_remove == 0:
                print(f"No entries older than {days} days found to clean.")
                return 0
            
            # Remove the entries
            self.db.execute("""
                DELETE FROM exploration 
                WHERE timestamp < ?
            """, (cutoff_str,))
            
            print(f"✅ Removed {entries_to_remove} entries older than {days} days.")
            return entries_to_remove
            
        except Exception as e:
            print(f"❌ Error cleaning old entries: {e}")
            return 0
    
    def clean_partial_null_entries(self) -> int:
        """
        Remove entries with partial NULL values that represent incomplete/no data found scenarios.
        These are entries that have some data but are missing critical fields.
        
        Returns:
            int: Number of entries removed.
        """
        try:
            # Count entries to be removed - entries missing critical identification fields
            # These are entries that have base_random_key but are missing shop, brand, or category
            count_result = self.db.query("""
                SELECT COUNT(*) as count FROM exploration 
                WHERE base_random_key IS NOT NULL 
                AND (shop_id IS NULL OR brand_id IS NULL OR category_id IS NULL)
            """)
            entries_to_remove = count_result[0]['count'] if count_result else 0
            
            if entries_to_remove == 0:
                print("No partial-NULL entries found to clean.")
                return 0
            
            # Remove the entries
            self.db.execute("""
                DELETE FROM exploration 
                WHERE base_random_key IS NOT NULL 
                AND (shop_id IS NULL OR brand_id IS NULL OR category_id IS NULL)
            """)
            
            print(f"✅ Removed {entries_to_remove} partial-NULL entries.")
            return entries_to_remove
            
        except Exception as e:
            print(f"❌ Error cleaning partial-NULL entries: {e}")
            return 0

    def clean_all_entries(self) -> int:
        """
        Remove ALL entries from the exploration table without any constraints.
        This will completely empty the table.
        
        Returns:
            int: Total number of entries removed.
        """
        try:
            # Count total entries
            count_result = self.db.query("SELECT COUNT(*) as count FROM exploration")
            total_entries = count_result[0]['count'] if count_result else 0
            
            if total_entries == 0:
                print("No entries found to clean.")
                return 0
            
            # Remove ALL entries
            self.db.execute("DELETE FROM exploration")
            
            print(f"✅ Removed ALL {total_entries} entries from exploration table.")
            return total_entries
            
        except Exception as e:
            print(f"❌ Error cleaning all entries: {e}")
            return 0

    def clean_all_no_data_entries(self) -> int:
        """
        Comprehensive cleaning of all "no data found" entries.
        This includes all-NULL entries, counts-only entries, partial-NULL entries, and high-count entries.
        
        Returns:
            int: Total number of entries removed.
        """
        total_removed = 0
        
        print("🧹 Starting comprehensive cleaning of exploration table...")
        
        # Clean all-NULL entries
        removed = self.clean_all_null_entries()
        total_removed += removed
        
        # Clean counts-only entries
        removed = self.clean_counts_only_entries()
        total_removed += removed
        
        # Clean partial-NULL entries (incomplete data)
        removed = self.clean_partial_null_entries()
        total_removed += removed
        
        # Clean high-count entries (stuck in loops)
        removed = self.clean_high_count_entries(max_count=10)
        total_removed += removed
        
        print(f"🎉 Total entries removed: {total_removed}")
        return total_removed
    
    def backup_exploration_table(self) -> str:
        """
        Create a backup of the exploration table before cleaning.
        
        Returns:
            str: Path to the backup file.
        """
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_file = self.backup_dir / f"exploration_backup_{timestamp}.json"
            
            # Get all exploration data
            data = self.db.query("SELECT * FROM exploration")
            
            # Convert to JSON-serializable format
            backup_data = []
            for row in data:
                backup_data.append({
                    'chat_id': row['chat_id'],
                    'base_random_key': row['base_random_key'],
                    'shop_id': row['shop_id'],
                    'brand_id': row['brand_id'],
                    'category_id': row['category_id'],
                    'lower_price': row['lower_price'],
                    'upper_price': row['upper_price'],
                    'counts': row['counts'],
                    'score': row['score'],
                    'has_warranty': row['has_warranty']
                })
            
            # Write backup file
            with open(backup_file, 'w', encoding='utf-8') as f:
                json.dump(backup_data, f, ensure_ascii=False, indent=2)
            
            print(f"💾 Backup created: {backup_file}")
            return str(backup_file)
            
        except Exception as e:
            print(f"❌ Error creating backup: {e}")
            return ""
    
    def restore_exploration_table(self, backup_file: str) -> bool:
        """
        Restore exploration table from backup file.
        
        Args:
            backup_file (str): Path to the backup file.
            
        Returns:
            bool: True if restore was successful, False otherwise.
        """
        try:
            if not os.path.exists(backup_file):
                print(f"❌ Backup file not found: {backup_file}")
                return False
            
            # Clear current exploration table
            self.db.execute("DELETE FROM exploration")
            
            # Load backup data
            with open(backup_file, 'r', encoding='utf-8') as f:
                backup_data = json.load(f)
            
            # Restore data
            for row in backup_data:
                self.db.execute("""
                    INSERT INTO exploration 
                    (chat_id, base_random_key, shop_id, brand_id, category_id, 
                     lower_price, upper_price, counts, score, has_warranty)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    row['chat_id'],
                    row['base_random_key'],
                    row['shop_id'],
                    row['brand_id'],
                    row['category_id'],
                    row['lower_price'],
                    row['upper_price'],
                    row['counts'],
                    row['score'],
                    row['has_warranty']
                ))
            
            print(f"✅ Restored {len(backup_data)} entries from backup.")
            return True
            
        except Exception as e:
            print(f"❌ Error restoring from backup: {e}")
            return False
    
    def print_stats(self):
        """Print comprehensive statistics about the exploration table."""
        stats = self.get_exploration_stats()
        
        print("\n📊 EXPLORATION TABLE STATISTICS")
        print("=" * 50)
        print(f"Total entries: {stats.get('total_entries', 0):,}")
        print(f"All-NULL entries: {stats.get('all_null_entries', 0):,}")
        print(f"Partial-NULL entries: {stats.get('partial_null_entries', 0):,}")
        print(f"Valid entries: {stats.get('valid_entries', 0):,}")
        print(f"Counts-only entries: {stats.get('counts_only_entries', 0):,}")
        print(f"High-count entries (>10): {stats.get('high_count_entries', 0):,}")
        
        print(f"\n📈 Count Distribution:")
        for count, frequency in stats.get('count_distribution', {}).items():
            print(f"  Count {count}: {frequency:,} entries")
        
        print("\n💡 Cleaning Recommendations:")
        if stats.get('all_null_entries', 0) > 0:
            print(f"  - Remove {stats.get('all_null_entries', 0):,} all-NULL entries")
        if stats.get('counts_only_entries', 0) > 0:
            print(f"  - Remove {stats.get('counts_only_entries', 0):,} counts-only entries")
        if stats.get('high_count_entries', 0) > 0:
            print(f"  - Remove {stats.get('high_count_entries', 0):,} high-count entries")
        if stats.get('total_entries', 0) == 0:
            print("  - No entries to clean")
    
    def close(self):
        """Close the database connection."""
        if self.db:
            self.db.close()


def main():
    """Main function for command-line interface."""
    parser = argparse.ArgumentParser(description="Clean exploration table from no data found entries")
    
    # Cleaning options
    parser.add_argument('--clean-all', action='store_true', 
                       help='Clean all no-data-found entries (comprehensive cleaning)')
    parser.add_argument('--clean-everything', action='store_true', 
                       help='Clean ALL entries from exploration table (no constraints)')
    parser.add_argument('--clean-null', action='store_true', 
                       help='Clean entries with all NULL values')
    parser.add_argument('--clean-counts', action='store_true', 
                       help='Clean counts-only entries')
    parser.add_argument('--clean-partial', action='store_true', 
                       help='Clean entries with partial NULL values')
    parser.add_argument('--clean-high-count', type=int, metavar='MAX_COUNT',
                       help='Clean entries with count higher than MAX_COUNT')
    parser.add_argument('--clean-old', type=int, metavar='DAYS',
                       help='Clean entries older than DAYS (requires timestamp column)')
    
    # Utility options
    parser.add_argument('--stats', action='store_true', 
                       help='Show statistics only (no cleaning)')
    parser.add_argument('--backup', action='store_true', 
                       help='Create backup before cleaning')
    parser.add_argument('--restore', type=str, metavar='BACKUP_FILE',
                       help='Restore from backup file')
    parser.add_argument('--db-path', type=str, 
                       help='Path to database file')
    
    args = parser.parse_args()
    
    # Initialize cleaner
    cleaner = ExplorationCleaner(args.db_path)
    
    try:
        # Handle restore
        if args.restore:
            success = cleaner.restore_exploration_table(args.restore)
            if success:
                print("✅ Restore completed successfully")
            else:
                print("❌ Restore failed")
            return
        
        # Show stats
        if args.stats or not any([args.clean_all, args.clean_everything, args.clean_null, args.clean_counts, 
                                 args.clean_partial, args.clean_high_count, args.clean_old]):
            cleaner.print_stats()
            return
        
        # Create backup if requested
        backup_file = ""
        if args.backup:
            backup_file = cleaner.backup_exploration_table()
            if not backup_file:
                print("❌ Backup failed. Aborting cleaning.")
                return
        
        # Perform cleaning operations
        total_removed = 0
        
        if args.clean_everything:
            total_removed += cleaner.clean_all_entries()
        elif args.clean_all:
            total_removed += cleaner.clean_all_no_data_entries()
        else:
            if args.clean_null:
                total_removed += cleaner.clean_all_null_entries()
            if args.clean_counts:
                total_removed += cleaner.clean_counts_only_entries()
            if args.clean_partial:
                total_removed += cleaner.clean_partial_null_entries()
            if args.clean_high_count:
                total_removed += cleaner.clean_high_count_entries(args.clean_high_count)
            if args.clean_old:
                total_removed += cleaner.clean_old_entries(args.clean_old)
        
        # Show final stats
        print(f"\n📊 CLEANING COMPLETED")
        print(f"Total entries removed: {total_removed:,}")
        if backup_file:
            print(f"Backup available at: {backup_file}")
        
        # Show updated stats
        cleaner.print_stats()
        
    finally:
        cleaner.close()


if __name__ == "__main__":
    main()
