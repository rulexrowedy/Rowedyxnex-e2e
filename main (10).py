"""
FB Multi-Session Manager - Main Entry Point

This file is used to start both the keep-alive server and the Streamlit app.
For Replit deployment, use this as the entry point.
"""

import os
import subprocess
import threading
import time

def start_keep_alive():
    """Start the keep-alive Flask server"""
    from keep_alive import keep_alive
    keep_alive()

def start_streamlit():
    """Start the Streamlit application"""
    port = os.environ.get('STREAMLIT_PORT', '5000')
    subprocess.run([
        'streamlit', 'run', 'streamlit_app.py',
        '--server.port', port,
        '--server.address', '0.0.0.0',
        '--server.headless', 'true',
        '--browser.gatherUsageStats', 'false'
    ])

if __name__ == "__main__":
    print("=" * 50)
    print("FB Multi-Session Manager")
    print("=" * 50)
    print()
    
    print("[1/2] Starting keep-alive server...")
    start_keep_alive()
    time.sleep(1)
    
    print("[2/2] Starting Streamlit application...")
    print()
    print("Access the app at: http://localhost:5000")
    print()
    
    start_streamlit()
