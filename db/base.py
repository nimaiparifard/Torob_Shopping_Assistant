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

if __name__ == "__main__":
    db = DatabaseBaseLoader()

    # Exact match - get random_key for specific persian name
    persian_name = "فرشینه مخمل دارای ترمزگیر(عرض 1 متر) طرح آشپزخانه کد04"
    results = db.query("SELECT random_key, extra_features FROM base_products WHERE persian_name = ?", (persian_name,))
    if results:
        random_key = results[0]['random_key']
        extra_features = results[0]['extra_features']
        print(f"Random key: {random_key}, extra features: {extra_features}")
    else:
        print("Product not found")

    # Partial match - search for products containing a term
    # search_term = "رخت اویز جاکفشی"
    # a = f"%{search_term}%"
    # print(a)
    # search_term_2 = "تریکو جودون 1/30 لاکرا گردباف نوریس"
    # results = db.query(
    #     "SELECT random_key, persian_name, extra_features FROM base_products"
    #     " WHERE persian_name LIKE ?",
    #     (a,)
    # )
    # for product in results:
    #     print(f"{product['persian_name']} -> {product['random_key']}")

    search_term = "فرش سیزان"
    a = f"%{search_term}%"
    print(a)

    # search_term_2 = "فرش سیزان"
    # results = db.query(
    #     "SELECT random_key, persian_name, extra_features FROM base_products"
    #     " WHERE persian_name LIKE ?",
    #     (a,)
    # )
    # for product in results:
    #     print(f"{product['persian_name']} -> {product['random_key']}")

    # یخچال فریزر کمبی جی‌ پلاس مدل M5320
    search_term = "یخچال فریزر کمبی"
    search_term_2 = "جی‌ پلاس"
    a = f"%{search_term}%"
    b = f"%{search_term_2}%"
    results = db.query(
        "SELECT random_key, persian_name, extra_features FROM base_products"
        " WHERE persian_name LIKE ? AND persian_name LIKE ?",
        (a, b)
    )
    print(len(results))
    for product in results:
        print(f"{product['persian_name']} -> {product['random_key']} extra: {product['extra_features']}")
    print("----")
    #  یخچال فریزر کمبی جی‌ پلاس مدل M5320
    search_term = "جی پلاس"
    search_term_2 = "فریزر"
    search_term_3 = "GRF-P532"
    a = f"%{search_term}%"
    b = f"%{search_term_2}%"
    c = f"%{search_term_3}%"
    results = db.query(
        "SELECT random_key, persian_name, extra_features FROM base_products"
        " WHERE persian_name LIKE ? AND persian_name LIKE ? AND persian_name LIKE ?",
        (a, b , c)
    )
    print(len(results))
    for product in results:
        print(f"{product['persian_name']} -> {product['random_key']}")

    print("----")
    print("check random key is correct in members table")
    random_key = 'matdva'
    results = db.query(
        'SELECT persian_name FROM base_products WHERE random_key = ?', (random_key,)
    )
    print(f"Product name: {results[0]['persian_name']}" if results else "No product found")

    # results = db.query(
    #     """
    #     SELECT DISTINCT m.random_key
    #     FROM members m
    #     JOIN base_products bp ON m.base_random_key = bp.random_key
    #     JOIN shops s ON m.shop_id = s.id
    #     WHERE m.base_random_key = ? AND s.city_id = ? AND s.score >= ?
    #     ORDER BY m.price ASC, m.random_key ASC
    #     LIMIT 1
    #     """,
    #     params=("zxxwse", "248", 1),
    # )
    # print(len(results))
    # print(results[0]['random_key'] if results else "No member found")

    db.close()
