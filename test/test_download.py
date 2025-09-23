#!/usr/bin/env python3
"""
Test script to verify the download process works correctly
"""

import os
import sys
from export_utils import download_and_extract

def test_download():
    """Test the download and extract process."""
    print("🧪 Testing download and extract process...")
    
    # Configuration
    FILE_ID = "1W4mSI33IbeKkWztK3XmE05F7m4tNYDYu"
    TAR_GZ_FILENAME = "../torob-turbo-stage2.tar.gz"
    BACKUP_FOLDER = "backup"
    
    # Remove existing files to test fresh download
    if os.path.exists(TAR_GZ_FILENAME):
        os.remove(TAR_GZ_FILENAME)
        print(f"🗑️ Removed existing {TAR_GZ_FILENAME}")
    
    if os.path.exists(BACKUP_FOLDER):
        import shutil
        shutil.rmtree(BACKUP_FOLDER)
        print(f"🗑️ Removed existing {BACKUP_FOLDER} folder")
    
    # Test the download process
    print(f"\n📥 Testing download from Google Drive...")
    tar_path, backup_path = download_and_extract(FILE_ID, TAR_GZ_FILENAME, BACKUP_FOLDER)
    
    if tar_path and backup_path:
        print(f"\n✅ SUCCESS! Download and extract worked correctly!")
        print(f"📦 Tar file: {tar_path}")
        print(f"📁 Backup folder: {backup_path}")
        
        # Check if backup files exist
        backup_files = os.listdir(backup_path)
        print(f"📊 Found {len(backup_files)} files in backup folder:")
        for file in sorted(backup_files):
            print(f"  - {file}")
        
        return True
    else:
        print(f"\n❌ FAILED! Download process failed!")
        return False

if __name__ == "__main__":
    success = test_download()
    sys.exit(0 if success else 1)
