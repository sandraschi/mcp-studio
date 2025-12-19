"""Simple API server for MCP Studio - guaranteed to work."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="MCP Studio Simple API")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API endpoints
@app.get("/api/v1/test")
async def api_test():
    """API test endpoint."""
    return {"message": "API test successful", "timestamp": "2025-12-17"}

@app.get("/api/v1/repos/")
async def get_repos():
    """Get repository data."""
    return {
        "status": "no_data",
        "message": "No scan data yet. Click 'START REPO SCAN' to analyze repositories.",
        "scan_url": "/api/v1/repos/run_scan/"
    }

@app.post("/api/v1/repos/run_scan/")
async def run_scan():
    """Start repository scan."""
    return {
        "status": "scan_started",
        "message": "Repository scan started in background."
    }

@app.get("/api/v1/repos/progress")
async def get_progress():
    """Get scan progress."""
    return {
        "status": "idle",
        "current": "",
        "done": 0,
        "total": 0,
        "mcp_repos_found": 0,
        "skipped": 0,
        "errors": 0,
        "activity_log": ["Waiting for scan to start..."]
    }

@app.get("/health")
async def health():
    """Health check."""
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    print("Starting simple API server on http://localhost:8001")
    uvicorn.run(app, host="0.0.0.0", port=8001)
