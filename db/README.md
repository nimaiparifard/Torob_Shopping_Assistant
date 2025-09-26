# Database Module

The database module provides comprehensive database management for the Torob AI Assistant, including schema definition, data loading, connection management, and optimization utilities.

## 📁 Structure

```
db/
├── base.py              # Database base class and connection management
├── config.py            # Database configuration and path management
├── create_db.py         # Database schema definition and initialization
├── load_db.py           # Data loading from parquet files
├── load_db_optimized.py # Optimized data loading with performance improvements
├── preview_data.py      # Data preview and exploration utilities
├── verify_data.py       # Data integrity verification
├── check_exploration.py # Exploration data validation
├── clean_exploration.py # Exploration data cleanup
└── backup/              # Database backup utilities
```

## 🗄️ Database Schema

### Core Tables

#### Cities (`cities`)
```sql
CREATE TABLE cities (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL UNIQUE
);
```
Stores city information for location-based queries.

#### Brands (`brands`)
```sql
CREATE TABLE brands (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL UNIQUE
);
```
Product brand information.

#### Categories (`categories`)
```sql
CREATE TABLE categories (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL UNIQUE
);
```
Product category classification.

#### Shops (`shops`)
```sql
CREATE TABLE shops (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    city_id INTEGER,
    score REAL,
    FOREIGN KEY (city_id) REFERENCES cities(id)
);
```
Shop information including location and ratings.

#### Base Products (`base_products`)
```sql
CREATE TABLE base_products (
    id INTEGER PRIMARY KEY,
    random_key TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    brand_id INTEGER,
    category_id INTEGER,
    extra_features TEXT, -- JSON format
    FOREIGN KEY (brand_id) REFERENCES brands(id),
    FOREIGN KEY (category_id) REFERENCES categories(id)
);
```
Main product information with features stored as JSON.

#### Members (`members`)
```sql
CREATE TABLE members (
    id INTEGER PRIMARY KEY,
    random_key TEXT UNIQUE NOT NULL,
    shop_id INTEGER,
    base_product_id INTEGER,
    price REAL,
    has_warranty BOOLEAN,
    FOREIGN KEY (shop_id) REFERENCES shops(id),
    FOREIGN KEY (base_product_id) REFERENCES base_products(id)
);
```
Shop member products with pricing and warranty information.

### Analytics Tables

#### Exploration (`exploration`)
```sql
CREATE TABLE exploration (
    id INTEGER PRIMARY KEY,
    chat_id TEXT NOT NULL,
    product_name TEXT,
    brand_name TEXT,
    category_name TEXT,
    city_name TEXT,
    features TEXT, -- JSON format
    lowest_price REAL,
    highest_price REAL,
    has_warranty BOOLEAN,
    shop_name TEXT,
    score REAL,
    counts INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```
User exploration sessions and filtering criteria.

#### Searches (`searches`)
```sql
CREATE TABLE searches (
    id INTEGER PRIMARY KEY,
    search_id TEXT UNIQUE NOT NULL,
    query TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```
Search query history.

#### Search Results (`search_results`)
```sql
CREATE TABLE search_results (
    id INTEGER PRIMARY KEY,
    search_id TEXT,
    result_base_product_rks TEXT, -- JSON array
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (search_id) REFERENCES searches(search_id)
);
```
Search result tracking.

#### Base Views (`base_views`)
```sql
CREATE TABLE base_views (
    id INTEGER PRIMARY KEY,
    view_id TEXT UNIQUE NOT NULL,
    base_product_rk TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```
Product view tracking.

#### Final Clicks (`final_clicks`)
```sql
CREATE TABLE final_clicks (
    id INTEGER PRIMARY KEY,
    click_id TEXT UNIQUE NOT NULL,
    base_product_rk TEXT,
    member_rk TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```
Click tracking for analytics.

## 🔧 Core Components

### DatabaseBaseLoader (`base.py`)

Base class for database operations with connection management.

**Key Features:**
- SQLite connection management
- Foreign key constraint enforcement
- Row factory for dictionary-like access
- Automatic connection cleanup
- Query and execution methods

**Usage Example:**
```python
db = DatabaseBaseLoader()
results = db.query("SELECT * FROM base_products WHERE brand_id = ?", [1])
db.execute("INSERT INTO cities (name) VALUES (?)", ["Tehran"])
db.close()
```

**Methods:**
- `connect()`: Establishes database connection
- `query(sql, params)`: Executes SELECT queries
- `execute(sql, params)`: Executes INSERT/UPDATE/DELETE queries
- `close()`: Closes database connection

### Configuration (`config.py`)

Database configuration and path management.

**Environment Support:**
- Development: `./data/torob.db`
- Production: `/database/torob.db`
- Automatic directory creation
- Backup path management

**Key Functions:**
- `is_production()`: Checks production environment
- `get_data_path()`: Returns data directory path
- `get_db_path()`: Returns database file path
- `ensure_data_directory()`: Creates data directory
- `get_backup_path()`: Returns backup directory path

### Schema Creation (`create_db.py`)

Database schema definition and initialization.

**Features:**
- Complete DDL script generation
- Foreign key constraint setup
- Index creation for performance
- Table existence checking
- Force recreation option

**Schema Information:**
- 11 main tables
- 15+ foreign key relationships
- 20+ indexes for optimization
- JSON support for flexible data storage

**Usage Example:**
```python
from create_db import init_db

# Initialize database
init_db("data/torob.db", force_recreate=False)

# Show schema information
show_schema_info()
```

### Data Loading (`load_db.py`)

Loads data from parquet files into SQLite database.

**Loading Process:**
1. **Cities**: Load city names
2. **Brands**: Load brand information
3. **Categories**: Load product categories
4. **Shops**: Load shop data with city mapping
5. **Base Products**: Load products with brand/category mapping
6. **Members**: Load shop member products
7. **Searches**: Load search history
8. **Search Results**: Load search results
9. **Base Views**: Load view tracking data
10. **Final Clicks**: Load click tracking data

**ID Mapping System:**
- String-to-integer ID conversion
- Foreign key relationship maintenance
- Data integrity preservation
- Batch processing for large datasets

**Usage Example:**
```python
from load_db import load_all_data

# Load all data from parquet files
load_all_data()
```

### Optimized Loading (`load_db_optimized.py`)

Performance-optimized data loading with improvements.

**Optimizations:**
- Batch processing for large datasets
- Memory-efficient data handling
- Progress tracking
- Error recovery
- Performance monitoring

## 🚀 Performance Features

### Indexing Strategy
- Primary key indexes on all tables
- Foreign key indexes for JOIN operations
- Composite indexes for common query patterns
- Text indexes for search operations

### Query Optimization
- Prepared statements for security
- Batch operations for bulk inserts
- Connection pooling
- Query result caching
- Memory-efficient data structures

### Data Integrity
- Foreign key constraints
- Unique constraints
- Data type validation
- Referential integrity checks
- Transaction management

## 📊 Data Management

### Backup and Recovery
- Automated backup creation
- Data export to parquet format
- Incremental backup support
- Point-in-time recovery
- Data validation after restore

### Data Validation
- Schema validation
- Data type checking
- Referential integrity verification
- Constraint validation
- Data quality metrics

### Monitoring
- Database size tracking
- Query performance monitoring
- Connection pool status
- Index usage statistics
- Data growth analytics

## 🔍 Data Exploration

### Preview Utilities (`preview_data.py`)
- Table structure inspection
- Sample data viewing
- Data type analysis
- Relationship mapping
- Statistics generation

### Verification Tools (`verify_data.py`)
- Data integrity checks
- Constraint validation
- Relationship verification
- Data quality assessment
- Error reporting

## 🧹 Maintenance

### Data Cleanup
- Orphaned record removal
- Duplicate data elimination
- Constraint violation resolution
- Index rebuilding
- Statistics updates

### Performance Tuning
- Query optimization
- Index analysis
- Connection pool tuning
- Memory optimization
- Cache configuration

## 📈 Analytics Support

### Search Analytics
- Query pattern analysis
- Search result tracking
- User behavior insights
- Performance metrics
- Trend analysis

### Product Analytics
- View tracking
- Click analysis
- Popular product identification
- Category performance
- Brand analysis

### Shop Analytics
- Shop performance metrics
- Pricing analysis
- Availability tracking
- Customer behavior
- Market trends

## 🔧 Configuration

### Environment Variables
- `PRODUCTION`: Production mode flag
- `DB_PATH`: Custom database path
- `BACKUP_PATH`: Backup directory
- `LOG_LEVEL`: Logging verbosity

### Database Settings
- Foreign key constraints enabled
- WAL mode for better concurrency
- Memory-mapped I/O
- Optimized page size
- Cache size tuning

## 🧪 Testing

### Test Coverage
- Unit tests for all functions
- Integration tests with database
- Performance benchmarks
- Data integrity tests
- Error handling tests

### Test Data
- Sample datasets for testing
- Mock data generation
- Edge case scenarios
- Performance test data
- Stress testing

## 📚 Dependencies

- **SQLite3**: Database engine
- **Pandas**: Data manipulation
- **PyArrow**: Parquet file support
- **NumPy**: Numerical operations
- **JSON**: Data serialization

## 🔄 Version History

- **v1.0.0**: Initial database implementation
- Complete schema definition
- Data loading from parquet files
- Performance optimizations
- Analytics table support
- Backup and recovery utilities