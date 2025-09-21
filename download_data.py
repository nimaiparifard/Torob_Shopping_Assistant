# Install: pip install gdown

import gdown

# For a file with a direct Google Drive link
url = "https://drive.google.com/file/d/FILE_ID/view?usp=sharing"
file_id = "1W4mSI33IbeKkWztK3XmE05F7m4tNYDYu"  # Extract from the URL
gdown.download(f"https://drive.google.com/uc?id={file_id}", "torob-turbo-stage2.tar.gz")

# # Or directly with the sharing URL
# gdown.download(url, "output_filename.ext", quiet=False)