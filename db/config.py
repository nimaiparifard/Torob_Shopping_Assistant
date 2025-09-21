"""
Database Configuration - Torob AI Assistant

Handles database path configuration based on environment (production vs development).

Usage:
    from db.config import get_db_path, get_data_path
    
    db_path = get_db_path()
    data_path = get_data_path()

Author: Torob AI Team
"""

import os
from pathlib import Path
import dotenv
dotenv.load_dotenv()


def is_production() -> bool:
    """
    Check if running in production mode.
    
    Returns:
        bool: True if PRODUCTION environment variable is set to 'true'
    """
    return os.getenv('PRODUCTION', 'false').lower() == 'true'


def get_data_path() -> str:
    """
    Get the data directory path based on environment.
    
    Development: ./data (relative to project root)
    Production: /database (mounted volume in Docker)
    
    Returns:
        str: Absolute path to the data directory
    """
    if is_production():
        # Production: use mounted volume
        return '/database'
    else:
        # Development: use project data folder
        current_dir = os.path.dirname(os.path.abspath(__file__))
        repo_root = os.path.abspath(os.path.join(current_dir, os.pardir))
        return os.path.join(repo_root, 'data')


def get_db_path() -> str:
    """
    Get the database file path based on environment.
    
    Development: ./data/torob.db
    Production: /database/torob.db
    
    Returns:
        str: Absolute path to the database file
    """
    data_path = get_data_path()
    return os.path.join(data_path, 'torob.db')


def ensure_data_directory():
    """
    Ensure the data directory exists.
    Creates the directory if it doesn't exist.
    """
    data_path = get_data_path()
    if not os.path.exists(data_path):
        os.makedirs(data_path, exist_ok=True)
        print(f"📁 Created data directory: {data_path}")


def get_backup_path() -> str:
    """
    Get the backup directory path (always relative to project root).
    
    Returns:
        str: Absolute path to the backup directory
    """
    current_dir = os.path.dirname(os.path.abspath(__file__))
    repo_root = os.path.abspath(os.path.join(current_dir, os.pardir))
    return os.path.join(repo_root, 'backup')


# For backward compatibility, export the main functions
__all__ = ['get_data_path', 'get_db_path', 'ensure_data_directory', 'get_backup_path', 'is_production']
