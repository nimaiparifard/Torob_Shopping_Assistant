#!/usr/bin/env python3
"""
Combined download and extract script for Torob AI Assistant
Downloads tar.gz file if it doesn't exist, then extracts to backup folder
"""

import os
from export_utils import download_and_extract

def ensure_data_directories():
    """Ensure required directories exist."""
    directories = ['data', 'backup', 'logs']
    
    for directory in directories:
        if not os.path.exists(directory):
            os.makedirs(directory, exist_ok=True)
            print(f"📁 Created directory: {directory}")
        else:
            print(f"✅ Directory exists: {directory}")

if __name__ == "__main__":
    # Ensure required directories exist
    print("🔧 Setting up directories...")
    ensure_data_directories()
    
    # Configuration
    FILE_ID = "1W4mSI33IbeKkWztK3XmE05F7m4tNYDYu"
    TAR_GZ_FILENAME = "torob-turbo-stage2.tar.gz"
    BACKUP_FOLDER = "backup"
    
    print(f"\n📥 Downloading and extracting data...")
    # Run the combined process
    tar_path, backup_path = download_and_extract(FILE_ID, TAR_GZ_FILENAME, BACKUP_FOLDER)
    
    if tar_path and backup_path:
        print(f"\n✅ Success! Files extracted to: {backup_path}")
    else:
        print("\n❌ Process failed!")
