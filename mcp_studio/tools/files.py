"""File System Tools for MCP Studio"""
import logging
import os
import shutil
import tempfile
from pathlib import Path
from typing import List, Optional, Union

import aiofiles
import aiofiles.os
from pydantic import BaseModel, Field

from . import tool, structured_log, retry_on_failure

logger = logging.getLogger("mcp.tools.files")

class FileInfo(BaseModel):
    """File information model."""
    path: str = Field(..., description="File path")
    size: int = Field(..., description="File size in bytes")
    modified: float = Field(..., description="Last modified timestamp")
    is_dir: bool = Field(False, description="Whether the path is a directory")

@tool(
    name="list_directory",
    description="List directory contents",
    tags=["filesystem", "directory"]
)
@structured_log()
async def list_directory(path: str) -> List[FileInfo]:
    """List contents of a directory."""
    path = Path(path).resolve()
    if not await aiofiles.os.path.exists(path):
        raise FileNotFoundError(f"Directory not found: {path}")
    
    results = []
    with os.scandir(path) as entries:
        for entry in entries:
            stat = entry.stat()
            results.append(FileInfo(
                path=entry.path,
                size=stat.st_size,
                modified=stat.st_mtime,
                is_dir=entry.is_dir()
            ))
    return results

@tool(
    name="read_file",
    description="Read file contents",
    tags=["filesystem", "file"]
)
@structured_log()
async def read_file(path: str) -> str:
    """Read file contents as text."""
    path = Path(path).resolve()
    if not await aiofiles.os.path.exists(path):
        raise FileNotFoundError(f"File not found: {path}")
    
    async with aiofiles.open(path, 'r', encoding='utf-8') as f:
        return await f.read()

@tool(
    name="write_file",
    description="Write data to a file",
    tags=["filesystem", "file"]
)
@structured_log()
async def write_file(path: str, content: str) -> FileInfo:
    """Write text content to a file."""
    path = Path(path).resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    
    async with aiofiles.open(path, 'w', encoding='utf-8') as f:
        await f.write(content)
    
    stat = await aiofiles.os.stat(path)
    return FileInfo(
        path=str(path),
        size=stat.st_size,
        modified=stat.st_mtime,
        is_dir=False
    )

@tool(
    name="create_temp_file",
    description="Create a temporary file",
    tags=["filesystem", "temporary"]
)
async def create_temp_file() -> str:
    """Create a temporary file and return its path."""
    fd, path = tempfile.mkstemp(prefix='mcp_')
    os.close(fd)
    return path

@tool(
    name="copy_file",
    description="Copy a file",
    tags=["filesystem", "file", "copy"]
)
@retry_on_failure(max_retries=3)
async def copy_file(source: str, destination: str) -> FileInfo:
    """Copy a file from source to destination."""
    source = Path(source).resolve()
    destination = Path(destination).resolve()
    
    if not await aiofiles.os.path.exists(source):
        raise FileNotFoundError(f"Source file not found: {source}")
    
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, destination)
    
    stat = await aiofiles.os.stat(destination)
    return FileInfo(
        path=str(destination),
        size=stat.st_size,
        modified=stat.st_mtime,
        is_dir=False
    )
