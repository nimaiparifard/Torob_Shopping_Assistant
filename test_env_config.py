"""
Test Environment Configuration

Test that the environment variables are being loaded correctly.

Author: Torob AI Team
"""

import os
import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Load environment variables
try:
    import dotenv
    dotenv.load_dotenv()
    print("✅ dotenv loaded successfully")
except ImportError:
    print("❌ dotenv not available")

print("\n🔍 Environment Variables:")
print(f"PRODUCTION = '{os.getenv('PRODUCTION', 'NOT_SET')}'")
print(f"API_HOST = '{os.getenv('API_HOST', 'NOT_SET')}'")
print(f"API_PORT = '{os.getenv('API_PORT', 'NOT_SET')}'")

print("\n🔍 Testing config functions:")
try:
    from db.config import is_production, get_data_path, get_db_path, ensure_data_directory
    
    print(f"is_production() = {is_production()}")
    print(f"get_data_path() = {get_data_path()}")
    print(f"get_db_path() = {get_db_path()}")
    
    print("\n🔍 Testing directory creation:")
    ensure_data_directory()
    
    # Check if directories exist
    data_path = get_data_path()
    db_path = get_db_path()
    
    print(f"Data directory exists: {os.path.exists(data_path)}")
    print(f"Database file exists: {os.path.exists(db_path)}")
    
    if os.path.exists(data_path):
        print(f"Data directory contents: {os.listdir(data_path)}")
    
except Exception as e:
    print(f"❌ Error testing config: {e}")
    import traceback
    traceback.print_exc()
