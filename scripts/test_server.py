#!/usr/bin/env python3
"""Minimal test FastAPI server to check if routing works."""

from fastapi import FastAPI

app = FastAPI()

@app.get("/api/v1/test")
async def test():
    return {"message": "Test successful", "timestamp": "2025-12-16"}

@app.get("/api/v1/repos")
async def repos():
    return {"status": "no_data", "message": "No scan data yet"}

if __name__ == "__main__":
    import uvicorn
    print("Starting minimal test server on http://localhost:8332")
    uvicorn.run(app, host="127.0.0.1", port=8332)
