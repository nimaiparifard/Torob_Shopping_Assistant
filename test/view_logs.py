#!/usr/bin/env python3
"""
Script to view log contents
"""

import os

def view_log_file(filepath, title):
    """View a log file if it exists"""
    print(f"\n{'='*60}")
    print(f"{title}")
    print(f"{'='*60}")
    
    if os.path.exists(filepath):
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read().strip()
            if content:
                print(content)
            else:
                print("(File is empty)")
    else:
        print(f"File not found: {filepath}")

def main():
    """View all log files"""
    print("Torob AI Assistant - Log Viewer")
    print("=" * 60)
    
    # List of log files to check
    log_files = [
        ("logs/api.log", "General Application Logs"),
        ("logs/http_requests.log", "HTTP Request Logs"),
        ("logs/chat_interactions.log", "Chat Interaction Logs"),
        ("logs/errors.log", "Error Logs")
    ]
    
    for filepath, title in log_files:
        view_log_file(filepath, title)
    
    print(f"\n{'='*60}")
    print("End of logs")
    print("=" * 60)

if __name__ == "__main__":
    main()
