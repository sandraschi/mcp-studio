#!/usr/bin/env python3
"""Development runner for MCP Studio - runs outside Docker for fast iteration."""

import os
import sys
import uvicorn

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Set development environment variables
os.environ['PORT'] = '8331'  # Different port from Docker
os.environ['REPOS_DIR'] = 'D:/Dev/repos'  # Point to host repos directory
os.environ['USERPROFILE'] = os.environ.get('USERPROFILE', '/tmp')
os.environ['APPDATA'] = os.environ.get('APPDATA', '/tmp')

# Import and run the app
from mcp_studio.main import app

if __name__ == "__main__":
    print("[START] Starting MCP Studio development server on http://localhost:8331")
    print("[PATH] Repos directory: D:/Dev/repos")
    print("[INFO] Use http://localhost:8331 in your browser")
    print("Press Ctrl+C to stop")

    uvicorn.run(
        "mcp_studio.main:app",
        host="127.0.0.1",
        port=8331,
        reload=True,  # Enable auto-reload on file changes
        reload_dirs=["src", "templates"],
        log_level="info"
    )
