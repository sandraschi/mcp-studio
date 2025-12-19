#!/usr/bin/env python3
"""Minimal MCP Studio server to isolate hanging issue."""

import sys
sys.path.insert(0, 'src')

# Test importing MCP Studio components step by step
print("Testing imports...")

try:
    from fastapi import FastAPI
    from fastapi.middleware.cors import CORSMiddleware
    print("[OK] FastAPI imports OK")
except Exception as e:
    print(f"[FAIL] FastAPI import failed: {e}")
    sys.exit(1)

try:
    from mcp_studio.app.core.config import settings
    print("[OK] Settings import OK")
except Exception as e:
    print(f"[FAIL] Settings import failed: {e}")
    sys.exit(1)

try:
    from mcp_studio.app.core.logging_utils import get_logger, configure_uvicorn_logging
    print("[OK] Logging imports OK")
except Exception as e:
    print(f"[FAIL] Logging imports failed: {e}")
    sys.exit(1)

try:
    from mcp_studio.app.api import router as api_router
    print("[OK] API router import OK")
except Exception as e:
    print(f"[FAIL] API router import failed: {e}")
    sys.exit(1)

app = FastAPI(title="MCP Studio Test")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API router
try:
    app.include_router(api_router, prefix="/api")
    print("[OK] API router included OK")
except Exception as e:
    print(f"[FAIL] API router include failed: {e}")
    sys.exit(1)

@app.get("/api/v1/test")
async def test():
    return {"message": "MCP Studio test server working", "timestamp": "2025-12-16"}

if __name__ == "__main__":
    import uvicorn
    print("Starting MCP Studio test server on http://localhost:8331")
    uvicorn.run(app, host="127.0.0.1", port=8331)
