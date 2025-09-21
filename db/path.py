
import os
def get_data_path() -> str:
    """Return absolute path to the project's `data` directory.

    Works relative to this file to avoid relying on CWD or environment.
    """
    current_dir = os.path.dirname(os.path.abspath(__file__))
    repo_root = os.path.abspath(os.path.join(current_dir, os.pardir))
    return os.path.join(repo_root, 'data')