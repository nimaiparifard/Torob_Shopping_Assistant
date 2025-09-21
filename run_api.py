#!/usr/bin/env python3
"""
Run script for Torob AI Assistant API
Starts the FastAPI server with proper configuration
"""

import os
import sys
import subprocess

# Add the app directory to Python path
sys.path.insert(0, '/app')

try:
    import uvicorn
    from api.main import app
except ImportError as e:
    print(f"Import error: {e}")
    print("Installing uvicorn...")
    subprocess.run([sys.executable, "-m", "pip", "install", "uvicorn"], check=True)
    import uvicorn
    from api.main import app

if __name__ == "__main__":
    # Get configuration from environment variables
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))
    reload = os.getenv("RELOAD", "false").lower() == "true"
    log_level = os.getenv("LOG_LEVEL", "info")
    
    print(f"Starting Torob AI Assistant API on {host}:{port}")
    print(f"Reload mode: {reload}")
    print(f"Log level: {log_level}")
    
    # Run the server
    uvicorn.run(
        "api.main:app",
        host=host,
        port=port,
        reload=reload,
        log_level=log_level
    )
