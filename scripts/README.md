# Scripts Module

The scripts module contains utility scripts for data management, project export, and system maintenance in the Torob AI Assistant project.

## 📁 Structure

```
scripts/
├── download_data.py        # Data download from Google Drive
├── download_and_extract.py # Combined download and extraction
├── export_project.py       # Project export utilities
└── export_utils.py         # Export utility functions
```

## 🚀 Core Scripts

### 1. Data Download (`download_data.py`)

Downloads data files from Google Drive using the `gdown` library.

**Features:**
- Google Drive file download
- Direct file ID support
- URL-based download
- Progress tracking
- Error handling

**Usage Example:**
```python
import gdown

# Download using file ID
file_id = "1W4mSI33IbeKkWztK3XmE05F7m4tNYDYu"
gdown.download(f"https://drive.google.com/uc?id={file_id}", "torob-turbo-stage2.tar.gz")

# Download using sharing URL
url = "https://drive.google.com/file/d/FILE_ID/view?usp=sharing"
gdown.download(url, "output_filename.ext", quiet=False)
```

**Configuration:**
- **File ID**: `1W4mSI33IbeKkWztK3XmE05F7m4tNYDYu`
- **Output File**: `torob-turbo-stage2.tar.gz`
- **Quiet Mode**: Configurable output verbosity

### 2. Download and Extract (`download_and_extract.py`)

Combined script that downloads and extracts data files in one operation.

**Features:**
- Automatic directory creation
- Download and extraction in one step
- Progress tracking
- Error handling and recovery
- Directory structure validation

**Key Functions:**
```python
def ensure_data_directories():
    """Ensure required directories exist"""
    directories = ['data', 'backup', 'logs']
    for directory in directories:
        if not os.path.exists(directory):
            os.makedirs(directory, exist_ok=True)

def main():
    """Main execution function"""
    # Setup directories
    ensure_data_directories()
    
    # Download and extract
    tar_path, backup_path = download_and_extract(
        FILE_ID, TAR_GZ_FILENAME, BACKUP_FOLDER
    )
```

**Directory Structure:**
- `data/`: Database files
- `backup/`: Backup data files
- `logs/`: Application logs

### 3. Project Export (`export_project.py`)

Exports the project with all necessary files and dependencies.

**Features:**
- Complete project export
- Dependency inclusion
- Configuration preservation
- Data file handling
- Documentation inclusion

**Export Process:**
1. **Source Code**: All Python files and modules
2. **Dependencies**: Requirements and package files
3. **Configuration**: Environment and config files
4. **Data**: Database and backup files
5. **Documentation**: README and documentation files
6. **Scripts**: Utility and maintenance scripts

**Usage Example:**
```python
from export_utils import export_project

# Export complete project
export_project(
    source_dir=".",
    output_dir="exported_project",
    include_data=True,
    include_logs=False
)
```

### 4. Export Utilities (`export_utils.py`)

Utility functions for project export and data management.

**Key Functions:**

#### Download and Extract
```python
def download_and_extract(file_id: str, filename: str, 
                        backup_folder: str) -> Tuple[str, str]:
    """Download and extract data files"""
    # Download file from Google Drive
    # Extract to backup folder
    # Return paths to tar file and extracted folder
```

**Features:**
- Google Drive integration
- Tar.gz extraction
- Progress tracking
- Error handling
- Path validation

#### Project Export
```python
def export_project(source_dir: str, output_dir: str, 
                  include_data: bool = True, 
                  include_logs: bool = False) -> bool:
    """Export complete project"""
    # Copy source code
    # Include dependencies
    # Handle data files
    # Preserve configuration
```

**Export Options:**
- **Include Data**: Database and backup files
- **Include Logs**: Application log files
- **Include Cache**: Embedding and cache files
- **Include Temp**: Temporary files

## 🔧 Utility Functions

### Directory Management
```python
def ensure_directory(path: str) -> bool:
    """Ensure directory exists"""
    
def clean_directory(path: str) -> bool:
    """Clean directory contents"""
    
def copy_directory(src: str, dst: str) -> bool:
    """Copy directory recursively"""
```

### File Operations
```python
def download_file(url: str, filename: str) -> bool:
    """Download file from URL"""
    
def extract_archive(archive_path: str, extract_path: str) -> bool:
    """Extract archive file"""
    
def copy_file(src: str, dst: str) -> bool:
    """Copy file with error handling"""
```

### Data Management
```python
def backup_database(db_path: str, backup_path: str) -> bool:
    """Backup database file"""
    
def restore_database(backup_path: str, db_path: str) -> bool:
    """Restore database from backup"""
    
def validate_data_integrity(data_path: str) -> bool:
    """Validate data file integrity"""
```

## 📊 Data Management

### Backup Strategy
- **Incremental Backups**: Only changed files
- **Full Backups**: Complete data snapshot
- **Compression**: Space-efficient storage
- **Verification**: Data integrity checks

### Export Strategy
- **Selective Export**: Choose what to include
- **Dependency Resolution**: Include all required packages
- **Configuration Preservation**: Maintain settings
- **Documentation**: Include all documentation

### Cleanup Operations
- **Temporary Files**: Remove temp files
- **Cache Cleanup**: Clear cache directories
- **Log Rotation**: Manage log file sizes
- **Data Archival**: Archive old data

## 🚀 Usage Examples

### Download Data
```bash
# Download data files
python scripts/download_data.py

# Download and extract in one step
python scripts/download_and_extract.py
```

### Export Project
```bash
# Export complete project
python scripts/export_project.py

# Export with specific options
python scripts/export_project.py --include-data --exclude-logs
```

### Data Management
```python
from scripts.export_utils import download_and_extract, export_project

# Download and extract data
tar_path, backup_path = download_and_extract(
    "1W4mSI33IbeKkWztK3XmE05F7m4tNYDYu",
    "torob-turbo-stage2.tar.gz",
    "backup"
)

# Export project
success = export_project(
    source_dir=".",
    output_dir="exported_project",
    include_data=True
)
```

## 🔧 Configuration

### Environment Variables
- `GOOGLE_DRIVE_FILE_ID`: Default file ID for downloads
- `BACKUP_DIRECTORY`: Default backup directory
- `EXPORT_DIRECTORY`: Default export directory
- `INCLUDE_DATA`: Whether to include data files
- `INCLUDE_LOGS`: Whether to include log files

### File Paths
- **Data Files**: `backup/` directory
- **Database**: `data/torob.db`
- **Logs**: `logs/` directory
- **Cache**: `embeddings_cache.pkl`

## 🧪 Testing

### Test Coverage
- **Download Tests**: File download functionality
- **Extraction Tests**: Archive extraction
- **Export Tests**: Project export functionality
- **Utility Tests**: Helper function testing
- **Integration Tests**: End-to-end workflows

### Test Data
- **Sample Files**: Test data for validation
- **Mock Downloads**: Simulated download scenarios
- **Error Cases**: Failure scenario testing
- **Performance Tests**: Speed and memory benchmarks

## 📈 Monitoring and Analytics

### Metrics Tracked
- **Download Speed**: File download performance
- **Extraction Time**: Archive extraction speed
- **Export Size**: Project export size
- **Success Rate**: Operation success rates
- **Error Frequency**: Failure tracking

### Logging
- **Operation Logs**: Script execution tracking
- **Error Logs**: Failure and error reporting
- **Performance Logs**: Speed and resource usage
- **User Actions**: Script usage patterns

## 🔒 Security Features

### Data Protection
- **File Validation**: Verify downloaded files
- **Integrity Checks**: Ensure data integrity
- **Access Control**: Secure file operations
- **Error Handling**: Safe error recovery

### Backup Security
- **Encryption**: Optional file encryption
- **Access Logs**: Track backup access
- **Verification**: Backup integrity checks
- **Recovery**: Secure restore operations

## 📚 Dependencies

- **gdown**: Google Drive file download
- **tarfile**: Archive extraction
- **shutil**: File operations
- **os**: Operating system interface
- **pathlib**: Path manipulation
- **requests**: HTTP operations

## 🔄 Version History

- **v1.0.0**: Initial scripts implementation
- Google Drive integration
- Project export functionality
- Data management utilities
- Error handling and recovery
- Performance optimization
- Security features

## 🎯 Best Practices

### Script Design
- **Modularity**: Reusable utility functions
- **Error Handling**: Comprehensive error management
- **Logging**: Detailed operation logging
- **Documentation**: Clear usage instructions

### Data Management
- **Backup Strategy**: Regular data backups
- **Integrity Checks**: Data validation
- **Cleanup**: Regular maintenance
- **Monitoring**: Performance tracking

### Export Strategy
- **Selective Export**: Choose relevant files
- **Dependency Resolution**: Include all requirements
- **Configuration**: Preserve settings
- **Documentation**: Include all docs
