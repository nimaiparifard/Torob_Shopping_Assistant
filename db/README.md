# Torob AI Assistant - Database Module

This module handles the complete database management system for the Torob AI Assistant project, including database creation, data loading, verification, and preview functionality.

## 📁 Module Structure

```
db/
├── __init__.py          # Package initialization
├── create_db.py         # Database schema creation
├── load_db.py          # Data loading from parquet files
├── verify_data.py      # Database integrity verification
├── preview_data.py     # Data preview and exploration
├── path.py             # Path utilities
└── README.md           # This documentation
```

## 🗄️ Database Schema Overview

The Torob database is designed to handle e-commerce data with the following main entities:

### Core Tables

1. **Cities** - Geographic locations for shops
2. **Brands** - Product brands
3. **Categories** - Hierarchical product categories
4. **Shops** - E-commerce stores with ratings and locations
5. **Base Products** - Master product catalog
6. **Members** - Shop-specific product listings with prices

### Activity Tables

7. **Searches** - User search queries and metadata
8. **Search Results** - Products returned for each search
9. **Base Views** - Product detail page views
10. **Final Clicks** - User clicks on specific shop offers

## 📊 Detailed Database Structure

### 1. Cities Table
```sql
CREATE TABLE cities (
    id          INTEGER PRIMARY KEY,
    name        TEXT NOT NULL
);
```
**Purpose**: Reference table for shop locations
**Example Data**: 
- `{id: 1, name: "تهران"}`
- `{id: 2, name: "اصفهان"}`

### 2. Brands Table
```sql
CREATE TABLE brands (
    id          INTEGER PRIMARY KEY,
    title       TEXT NOT NULL
);
```
**Purpose**: Product brand catalog
**Example Data**: 
- `{id: 1, title: "سامسونگ"}`
- `{id: 2, title: "اپل"}`

### 3. Categories Table
```sql
CREATE TABLE categories (
    id          INTEGER PRIMARY KEY,
    title       TEXT NOT NULL,
    parent_id   INTEGER NOT NULL DEFAULT -1,
    CHECK (parent_id = -1 OR parent_id >= 0)
);
```
**Purpose**: Hierarchical product categorization
**Features**: 
- Self-referential hierarchy (parent_id = -1 for root categories)
- Unlimited nesting levels
**Example Data**:
- `{id: 1, title: "الکترونیک", parent_id: -1}`
- `{id: 2, title: "موبایل", parent_id: 1}`

### 4. Shops Table
```sql
CREATE TABLE shops (
    id              INTEGER PRIMARY KEY,
    city_id         INTEGER NOT NULL,
    score           REAL NOT NULL DEFAULT 0.0,   -- 0-5 rating
    has_warranty    INTEGER NOT NULL DEFAULT 0,  -- 0/1 boolean
    FOREIGN KEY (city_id) REFERENCES cities(id)
);
```
**Purpose**: E-commerce store information
**Features**:
- Location-based (linked to cities)
- Quality scoring (0-5 scale)
- Warranty indication
**Example Data**:
- `{id: 1, city_id: 1, score: 4.5, has_warranty: 1}`

### 5. Base Products Table
```sql
CREATE TABLE base_products (
    random_key      TEXT PRIMARY KEY,           -- Unique product identifier
    persian_name    TEXT,                       -- Persian product name
    english_name    TEXT,                       -- English product name
    category_id     INTEGER,                    -- Category reference
    brand_id        INTEGER,                    -- Brand reference
    extra_features  TEXT,                       -- JSON: additional attributes
    image_url       TEXT,                       -- Product image URL
    members         TEXT,                       -- JSON: list of member RKs
    FOREIGN KEY (category_id) REFERENCES categories(id),
    FOREIGN KEY (brand_id) REFERENCES brands(id)
);
```
**Purpose**: Master product catalog
**Features**:
- Bilingual naming (Persian/English)
- JSON-based flexible attributes
- Category and brand classification
**Example Data**:
```json
{
    "random_key": "prod_12345_xyz",
    "persian_name": "گوشی سامسونگ گلکسی S24",
    "english_name": "Samsung Galaxy S24",
    "category_id": 2,
    "brand_id": 1,
    "extra_features": "{\"storage\": \"256GB\", \"color\": \"black\"}",
    "image_url": "https://example.com/image.jpg"
}
```

### 6. Members Table
```sql
CREATE TABLE members (
    random_key      TEXT PRIMARY KEY,           -- Unique member identifier
    base_random_key TEXT NOT NULL,              -- Reference to base product
    shop_id         INTEGER NOT NULL,           -- Shop offering this product
    price           INTEGER NOT NULL,           -- Price in smallest currency unit
    FOREIGN KEY (base_random_key) REFERENCES base_products(random_key),
    FOREIGN KEY (shop_id) REFERENCES shops(id)
);
```
**Purpose**: Shop-specific product offerings and pricing
**Features**:
- Links products to specific shops
- Price tracking per shop
**Example Data**:
```json
{
    "random_key": "member_shop1_prod12345",
    "base_random_key": "prod_12345_xyz",
    "shop_id": 1,
    "price": 15000000
}
```

### 7. Searches Table
```sql
CREATE TABLE searches (
    id                          TEXT PRIMARY KEY,    -- Unique search identifier
    uid                         TEXT,                 -- User/session grouping
    query                       TEXT NOT NULL,       -- Search query text
    page                        INTEGER NOT NULL,    -- Pagination (0-based)
    timestamp                   TEXT NOT NULL,       -- ISO8601 UTC timestamp
    session_id                  TEXT,                -- Session identifier
    result_base_product_rks     TEXT,                -- JSON: array of product RKs
    category_id                 INTEGER DEFAULT 0,   -- Category filter
    category_brand_boosts       TEXT                 -- JSON: search boosts
);
```
**Purpose**: User search activity tracking
**Features**:
- Full-text search queries
- Pagination support
- Category filtering
- Search result caching
**Example Data**:
```json
{
    "id": "search_20241201_123456",
    "uid": "user_session_001",
    "query": "گوشی سامسونگ",
    "page": 0,
    "timestamp": "2024-12-01T10:30:00.000000+00:00",
    "result_base_product_rks": "[\"prod_12345_xyz\", \"prod_67890_abc\"]",
    "category_id": 2
}
```

### 8. Search Results Table
```sql
CREATE TABLE search_results (
    id                  INTEGER PRIMARY KEY,
    search_id           TEXT NOT NULL,           -- Reference to search
    base_product_rk     TEXT NOT NULL,          -- Product in results
    position            INTEGER NOT NULL,       -- Ranking position (1,2,3...)
    FOREIGN KEY (search_id) REFERENCES searches(id),
    FOREIGN KEY (base_product_rk) REFERENCES base_products(random_key)
);
```
**Purpose**: Normalized search results with ranking
**Features**:
- Explicit result ordering
- Many-to-many relationship between searches and products
**Example Data**:
```json
{
    "id": 1,
    "search_id": "search_20241201_123456",
    "base_product_rk": "prod_12345_xyz",
    "position": 1
}
```

### 9. Base Views Table
```sql
CREATE TABLE base_views (
    id               TEXT PRIMARY KEY,           -- Unique view identifier
    search_id        TEXT NOT NULL,              -- Originating search
    base_product_rk  TEXT NOT NULL,             -- Viewed product
    timestamp        TEXT NOT NULL,              -- View timestamp
    FOREIGN KEY (search_id) REFERENCES searches(id),
    FOREIGN KEY (base_product_rk) REFERENCES base_products(random_key)
);
```
**Purpose**: Product detail page view tracking
**Features**:
- Links views to originating searches
- Time-based analytics capability
**Example Data**:
```json
{
    "id": "view_20241201_123500",
    "search_id": "search_20241201_123456",
    "base_product_rk": "prod_12345_xyz",
    "timestamp": "2024-12-01T10:35:00.000000+00:00"
}
```

### 10. Final Clicks Table
```sql
CREATE TABLE final_clicks (
    id            TEXT PRIMARY KEY,              -- Unique click identifier
    base_view_id  TEXT NOT NULL,                -- Reference to product view
    shop_id       INTEGER NOT NULL,             -- Selected shop
    timestamp     TEXT NOT NULL,                -- Click timestamp
    FOREIGN KEY (base_view_id) REFERENCES base_views(id),
    FOREIGN KEY (shop_id) REFERENCES shops(id)
);
```
**Purpose**: Conversion tracking - user clicks on shop offers
**Features**:
- Complete funnel tracking (search → view → click)
- Shop performance analytics
**Example Data**:
```json
{
    "id": "click_20241201_123600",
    "base_view_id": "view_20241201_123500",
    "shop_id": 1,
    "timestamp": "2024-12-01T10:36:00.000000+00:00"
}
```

## 🔄 Database Creation and Loading Pipeline

### Step 1: Create Database Schema
```bash
# Create the SQLite database with all tables and constraints
python -m db.create_db
```
**What it does**:
- Creates `data/torob.db` SQLite database
- Executes DDL to create all tables
- Sets up foreign key constraints
- Creates performance indexes

### Step 2: Preview Source Data (Optional)
```bash
# Preview all parquet files
python -m db.preview_data

# Preview specific table
python -m db.preview_data base_products
```
**What it does**:
- Shows data structure and sample records
- Validates data types and formats
- Identifies potential data quality issues

### Step 3: Load Data
```bash
# Load all data from backup/ directory
python -m db.load_db
```
**What it does**:
- Loads data in dependency order:
  1. **Independent tables**: cities, brands, categories
  2. **Single-level dependencies**: shops, base_products
  3. **Multi-level dependencies**: members, searches
  4. **Complex dependencies**: search_results, base_views, final_clicks
- Handles string-to-integer ID mapping for searches, base_views, final_clicks
- Maintains referential integrity
- Provides loading progress and statistics

### Step 4: Verify Database Integrity
```bash
# Comprehensive database verification
python -m db.verify_data
```
**What it does**:
- Checks table existence and row counts
- Validates foreign key relationships
- Runs data quality checks
- Shows sample data and analytics
- Identifies orphaned records or integrity issues

## 🛠️ Usage Examples

### Basic Database Operations
```python
from db.create_db import init_db, DB_PATH
from db.load_db import load_all_data
from db.verify_data import verify_database
import sqlite3

# 1. Create fresh database
init_db()

# 2. Load all data
load_all_data()

# 3. Connect and query
conn = sqlite3.connect(DB_PATH)
cursor = conn.execute("SELECT COUNT(*) FROM base_products")
print(f"Total products: {cursor.fetchone()[0]}")
conn.close()

# 4. Verify integrity
verify_database()
```

### Advanced Queries
```python
import sqlite3
from db.create_db import DB_PATH

conn = sqlite3.connect(DB_PATH)

# Find popular search queries
popular_searches = conn.execute("""
    SELECT query, COUNT(*) as search_count
    FROM searches 
    GROUP BY query 
    ORDER BY search_count DESC 
    LIMIT 10
""").fetchall()

# Get conversion funnel data
funnel_data = conn.execute("""
    SELECT 
        COUNT(DISTINCT s.id) as searches,
        COUNT(DISTINCT bv.id) as views,
        COUNT(DISTINCT fc.id) as clicks
    FROM searches s
    LEFT JOIN base_views bv ON s.id = bv.search_id
    LEFT JOIN final_clicks fc ON bv.id = fc.base_view_id
""").fetchone()

# Top performing shops by click-through rate
shop_performance = conn.execute("""
    SELECT 
        s.id,
        c.name as city,
        s.score,
        COUNT(DISTINCT fc.id) as total_clicks,
        AVG(m.price) as avg_price
    FROM shops s
    JOIN cities c ON s.city_id = c.id
    LEFT JOIN members m ON s.id = m.shop_id
    LEFT JOIN final_clicks fc ON s.id = fc.shop_id
    GROUP BY s.id, c.name, s.score
    HAVING total_clicks > 0
    ORDER BY total_clicks DESC
""").fetchall()

conn.close()
```

## 📈 Performance Considerations

### Indexes
The schema includes strategic indexes for common query patterns:
- `idx_shops_city_id` - Shop location queries
- `idx_members_price` - Price range filtering
- `idx_searches_timestamp` - Time-based analytics
- `idx_search_results_position` - Result ranking queries

### Query Optimization Tips
1. **Use EXPLAIN QUERY PLAN** to analyze query performance
2. **Filter early** - Apply WHERE clauses on indexed columns first
3. **Limit result sets** - Use LIMIT for paginated results
4. **Join efficiently** - Start with smaller tables in JOINs

### Data Loading Best Practices
1. **Disable foreign keys** during bulk loading (handled automatically)
2. **Load in dependency order** (implemented in load_db.py)
3. **Use transactions** for data consistency
4. **Monitor memory usage** for large datasets

## 🔧 Maintenance and Monitoring

### Regular Checks
```bash
# Weekly database health check
python -m db.verify_data

# Monitor database size
ls -lh data/torob.db

# Check table sizes
sqlite3 data/torob.db "SELECT name, COUNT(*) FROM sqlite_master WHERE type='table' GROUP BY name;"
```

### Backup Strategy
```bash
# Create database backup
cp data/torob.db backup/torob_backup_$(date +%Y%m%d).db

# Export to SQL
sqlite3 data/torob.db .dump > backup/torob_schema_$(date +%Y%m%d).sql
```

### Troubleshooting

**Common Issues**:

1. **Foreign Key Violations**
   - Run `python -m db.verify_data` to identify orphaned records
   - Check data loading order in `load_db.py`

2. **Performance Issues**
   - Analyze slow queries with `EXPLAIN QUERY PLAN`
   - Consider additional indexes for frequent query patterns
   - Use `VACUUM` to optimize database file

3. **Data Quality Issues**
   - Use `preview_data.py` to inspect source data
   - Check for null values in required fields
   - Validate JSON format in extra_features columns

## 📚 API Reference

### Core Functions

#### `create_db.py`
- `init_db(db_path=DB_PATH)` - Initialize database with schema
- `get_data_path()` - Get absolute path to data directory

#### `load_db.py`
- `load_all_data()` - Load all parquet files in correct order
- `create_id_mapping(df, id_column, table_name)` - Map string IDs to integers
- `map_foreign_key(df, fk_column, target_table)` - Map foreign key references

#### `verify_data.py`
- `verify_database()` - Complete database integrity check
- `check_foreign_keys(conn)` - Validate referential integrity
- `check_data_quality(conn)` - Run data quality checks

#### `preview_data.py`
- `preview_parquet_files()` - Preview all source files
- `preview_specific_table(table_name)` - Detailed table preview

## 🤝 Contributing

When modifying the database schema:

1. Update the DDL in `create_db.py`
2. Modify loading logic in `load_db.py` if needed
3. Add verification checks in `verify_data.py`
4. Update this documentation
5. Test the complete pipeline:
   ```bash
   python -m db.create_db
   python -m db.load_db
   python -m db.verify_data
   ```

## 📄 License

This database module is part of the Torob AI Assistant project. See the main project license for details.
