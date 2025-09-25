"""
Combined download and extract utility for Torob AI Assistant
Downloads tar.gz file if it doesn't exist, then extracts to backup folder
"""

import os
import tarfile
import gdown
from pathlib import Path


def ensure_gdown_cache():
    """Ensure gdown cache directory exists and is writable."""
    cache_dir = Path.home() / '.cache' / 'gdown'
    cache_dir.mkdir(parents=True, exist_ok=True)
    print(f"📁 Ensured gdown cache directory: {cache_dir}")


def download_tar_gz(file_id, filename):
    """
    Download tar.gz file from Google Drive if it doesn't exist
    
    Args:
        file_id (str): Google Drive file ID
        filename (str): Local filename to save as
        
    Returns:
        str: Path to the downloaded file
    """
    if os.path.exists(filename):
        print(f"✅ File already exists: {filename}")
        return filename
    
    # Ensure gdown cache directory exists
    ensure_gdown_cache()
    
    print(f"📥 Downloading {filename} from Google Drive...")
    try:
        gdown.download(f"https://drive.google.com/uc?id={file_id}", filename, quiet=False)
        print(f"✅ Downloaded: {filename}")
        return filename
    except Exception as e:
        print(f"❌ Download failed: {e}")
        return None


def extract_tar_gz(tar_gz_file, folder_name):
    """
    Extract a tar.gz file to a folder
    
    Args:
        tar_gz_file (str): Path to the tar.gz file
        folder_name (str): Name of the folder to create and extract to
        
    Returns:
        str: Path to the created folder
    """
    # Get current directory (project root)
    project_root = os.getcwd()
    
    # Create extraction folder
    extract_dir = os.path.join(project_root, folder_name)
    os.makedirs(extract_dir, exist_ok=True)
    print(f"📁 Created folder: {extract_dir}")
    
    # Extract tar.gz file
    try:
        with tarfile.open(tar_gz_file, "r:gz") as tar:
            tar.extractall(extract_dir)
            print(f"📦 Extracted {tar_gz_file} to {extract_dir}")
        return extract_dir
    except Exception as e:
        print(f"❌ Extraction failed: {e}")
        return None


def download_and_extract(file_id, tar_gz_filename, backup_folder):
    """
    Combined function: Download tar.gz if not exists, then extract to backup folder
    
    Args:
        file_id (str): Google Drive file ID
        tar_gz_filename (str): Local tar.gz filename
        backup_folder (str): Backup folder name
        
    Returns:
        tuple: (tar_gz_path, backup_folder_path)
    """
    print("🚀 Starting download and extract process...")
    print("=" * 50)
    
    # Step 1: Download tar.gz file if it doesn't exist
    tar_gz_path = download_tar_gz(file_id, tar_gz_filename)
    if not tar_gz_path:
        return None, None
    
    # Step 2: Extract to backup folder
    backup_path = extract_tar_gz(tar_gz_path, backup_folder)
    if not backup_path:
        return tar_gz_path, None
    
    print("=" * 50)
    print("🎉 Process completed successfully!")
    print(f"📦 Tar.gz file: {tar_gz_path}")
    print(f"📁 Backup folder: {backup_path}")
    
    return tar_gz_path, backup_path


if __name__ == "__main__":
    # Configuration
    FILE_ID = "1W4mSI33IbeKkWztK3XmE05F7m4tNYDYu"
    TAR_GZ_FILENAME = "torob-turbo-stage2.tar.gz"
    BACKUP_FOLDER = "backup_2"
    
    # Run the combined process
    tar_path, backup_path = download_and_extract(FILE_ID, TAR_GZ_FILENAME, BACKUP_FOLDER)
    
    if tar_path and backup_path:
        print(f"\n✅ Success! Files extracted to: {backup_path}")
    else:
        print("\n❌ Process failed!")
