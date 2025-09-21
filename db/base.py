"""
Database Base Class - Torob AI Assistant

Simple base class for database operations with connection management.

Usage:
    from db.base import DatabaseBase
    
    db = DatabaseBase()
    results = db.query("SELECT * FROM cities LIMIT 5")
    db.close()

Author: Torob AI Team
"""

import sqlite3
import os
from db.config import get_db_path

class DatabaseBaseLoader:
    """
    Simple base class for database operations.
    Handles connection, queries, and proper cleanup.
    """
    
    def __init__(self, db_path=None):
        """
        Initialize database connection.
        
        Args:
            db_path (str, optional): Path to database file. Defaults to get_db_path().
        """
        self.db_path = db_path or get_db_path()
        self.conn = None
        self.connect()
    
    def connect(self):
        """Connect to the database."""
        if not os.path.exists(self.db_path):
            raise FileNotFoundError(f"Database not found at {self.db_path}")
        
        self.conn = sqlite3.connect(self.db_path)
        self.conn.execute("PRAGMA foreign_keys = ON")
        self.conn.row_factory = sqlite3.Row
    
    def query(self, sql, params=None):
        """
        Execute a SELECT query and return results.
        
        Args:
            sql (str): SQL query string
            params (tuple, optional): Query parameters
            
        Returns:
            list: Query results
        """
        if not self.conn:
            raise RuntimeError("No database connection")
        
        cursor = self.conn.execute(sql, params or ())
        return cursor.fetchall()
    
    def execute(self, sql, params=None):
        """
        Execute an INSERT/UPDATE/DELETE query.
        
        Args:
            sql (str): SQL query string
            params (tuple, optional): Query parameters
            
        Returns:
            int: Number of affected rows
        """
        if not self.conn:
            raise RuntimeError("No database connection")
        
        cursor = self.conn.execute(sql, params or ())
        self.conn.commit()
        return cursor.rowcount
    
    def close(self):
        """Close the database connection."""
        if self.conn:
            self.conn.close()
            self.conn = None


db = DatabaseBaseLoader()

# Exact match - get random_key for specific persian name
persian_name = "کمد چهار درب ونوس طوسی"
results = db.query("SELECT random_key, extra_features FROM base_products WHERE persian_name = ?", (persian_name,))
if results:
    random_key = results[0]['random_key']
    extra_features = results[0]['extra_features']
    print(f"Random key: {random_key}, extra features: {extra_features}")
else:
    print("Product not found")

# Partial match - search for products containing a term
search_term = "کمد چهار"
results = db.query("SELECT random_key, persian_name FROM base_products WHERE persian_name LIKE ?", (f'%{search_term}%',))
for product in results:
    print(f"{product['persian_name']} -> {product['random_key']}")

db.close()
