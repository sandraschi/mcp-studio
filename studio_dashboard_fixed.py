"""
MCP Studio Dashboard
===================
A unified dashboard for managing MCP servers and tools.
"""

import os
import sys
import json
import logging
import asyncio
import uvicorn
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
from fastapi import FastAPI, Request, HTTPException, Depends, status
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field
import aiohttp
import re
import subprocess
import time
from datetime import datetime
import random
import socket
import psutil
import platform
from urllib.parse import urlparse
import tomli

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('mcp_studio.log')
    ]
)
logger = logging.getLogger(__name__)

# Constants
VERSION = "1.0.0"
PORT = 8000
LOG_FILE = "mcp_studio.log"

# Initialize FastAPI app
app = FastAPI(
    title="MCP Studio",
    description="A unified dashboard for managing MCP servers and tools",
    version=VERSION,
    docs_url="/docs",
    redoc_url=None
)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory="templates")

# Global state
connected_servers = {}
scan_progress = {
    "current": 0,
    "total": 0,
    "status": "idle",
    "current_repo": ""
}

# MCP client configurations
MCP_CLIENT_CONFIGS = {
    "cursor": [
        Path.home() / ".cursor" / "mcp.json",
        Path.home() / ".cursor" / "config.json"
    ],
    "vscode": [
        Path.home() / ".vscode" / "mcp.json",
        Path.home() / ".vscode" / "settings.json"
    ]
}

# Helper functions
def log(message: str):
    """Log a message with timestamp."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {message}")
    logger.info(message)

def is_port_available(port: int) -> bool:
    """Check if a port is available for binding."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind(('0.0.0.0', port))
            return True
        except OSError:
            return False

def find_available_port(start_port: int, max_attempts: int = 10) -> int:
    """Find an available port starting from the given port."""
    port = start_port
    attempts = 0
    while attempts < max_attempts:
        if is_port_available(port):
            return port
        port += 1
        attempts += 1
    raise RuntimeError(f"Could not find an available port after {max_attempts} attempts")

# API Endpoints
@app.get("/", response_class=HTMLResponse)
async def get_dashboard(request: Request):
    """Serve the main dashboard."""
    return templates.TemplateResponse("dashboard.html", {"request": request, "version": VERSION})

@app.get("/api/servers")
async def get_servers():
    """Get list of available MCP servers."""
    return {"servers": list(connected_servers.keys())}

@app.get("/api/scan")
async def scan_repositories():
    """Trigger a repository scan."""
    global scan_progress
    
    # Simulate scanning
    repos = ["repo1", "repo2", "repo3"]  # Replace with actual repo detection
    scan_progress = {
        "current": 0,
        "total": len(repos),
        "status": "scanning",
        "current_repo": ""
    }
    
    # Simulate progress
    for i, repo in enumerate(repos):
        scan_progress["current"] = i + 1
        scan_progress["current_repo"] = repo
        log(f"Scanning {repo}...")
        await asyncio.sleep(1)  # Simulate work
    
    scan_progress["status"] = "completed"
    return {"status": "completed", "scanned": len(repos)}

@app.get("/api/scan/progress")
async def get_scan_progress():
    """Get current scan progress."""
    return scan_progress

# Main function
def main():
    """Main entry point for the application."""
    try:
        # Check if the default port is available
        port = PORT
        if not is_port_available(port):
            log(f"Port {port} is already in use. Trying to find an available port...")
            port = find_available_port(port)
            log(f"Using alternative port: {port}")
        
        # Display startup banner
        banner = f"""
╔══════════════════════════════════════════════════════════════════╗
║  🦁 MCP Studio v{VERSION}                                        ║
║  Mission Control for the MCP Zoo 🐘🦒🐿️                         ║
╠══════════════════════════════════════════════════════════════════╣
║  Dashboard: http://localhost:{port}                              ║
║  API Docs:  http://localhost:{port}/docs                         ║
║  Log File:  {LOG_FILE}                                          ║
╚══════════════════════════════════════════════════════════════════╝
"""
        print(banner)
        
        # Start the server
        log(f"Starting MCP Studio on port {port}...")
        uvicorn.run(
            "studio_dashboard_fixed:app",
            host="0.0.0.0",
            port=port,
            reload=True,
            log_level="info"
        )
        
    except Exception as e:
        log(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
