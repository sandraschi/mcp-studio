"""File System Tools for MCP Studio"""

import asyncio
import logging
import os
import shutil
import tempfile
from pathlib import Path

import aiofiles  # type: ignore[import-untyped]
import aiofiles.os  # type: ignore[import-untyped]
from pydantic import BaseModel, Field

from mcp_studio.tools.decorators import retry_on_failure, structured_log, tool

logger = logging.getLogger("mcp.tools.files")


class FileInfo(BaseModel):
    """File information model."""

    path: str = Field(..., description="File path")
    size: int = Field(..., description="File size in bytes")
    modified: float = Field(..., description="Last modified timestamp")
    is_dir: bool = Field(False, description="Whether the path is a directory")


@tool(name="list_directory", description="List directory contents", tags=["filesystem", "directory"])
@structured_log()
async def list_directory(path: str) -> list[FileInfo]:
    """List contents of a directory."""
    resolved = Path(path).resolve()
    if not await aiofiles.os.path.exists(resolved):
        raise FileNotFoundError(f"Directory not found: {resolved}")

    results = []
    with os.scandir(resolved) as entries:
        for entry in entries:
            stat = entry.stat()
            results.append(FileInfo(path=entry.path, size=stat.st_size, modified=stat.st_mtime, is_dir=entry.is_dir()))
    return results


@tool(name="read_file", description="Read file contents", tags=["filesystem", "file"])
@structured_log()
async def read_file(path: str) -> str:
    """Read file contents as text."""
    resolved = Path(path).resolve()
    if not await aiofiles.os.path.exists(resolved):
        raise FileNotFoundError(f"File not found: {resolved}")

    async with aiofiles.open(resolved, encoding="utf-8") as f:
        text: str = await f.read()
        return text


@tool(name="write_file", description="Write data to a file", tags=["filesystem", "file"])
@structured_log()
async def write_file(path: str, content: str) -> FileInfo:
    """Write text content to a file."""
    resolved = Path(path).resolve()
    resolved.parent.mkdir(parents=True, exist_ok=True)

    async with aiofiles.open(resolved, "w", encoding="utf-8") as f:
        await f.write(content)

    stat = await aiofiles.os.stat(resolved)
    return FileInfo(path=str(resolved), size=stat.st_size, modified=stat.st_mtime, is_dir=False)


@tool(name="create_temp_file", description="Create a temporary file", tags=["filesystem", "temporary"])
async def create_temp_file() -> str:
    """Create a temporary file and return its path."""
    fd, path = tempfile.mkstemp(prefix="mcp_")
    os.close(fd)
    return path


@tool(name="copy_file", description="Copy a file", tags=["filesystem", "file", "copy"])
@retry_on_failure(max_retries=3)
async def copy_file(source: str, destination: str) -> FileInfo:
    """Copy a file from source to destination."""
    src = Path(source).resolve()
    dst = Path(destination).resolve()

    if not await aiofiles.os.path.exists(src):
        raise FileNotFoundError(f"Source file not found: {src}")

    dst.parent.mkdir(parents=True, exist_ok=True)
    await asyncio.to_thread(shutil.copy2, src, dst)

    stat = await aiofiles.os.stat(dst)
    return FileInfo(path=str(dst), size=stat.st_size, modified=stat.st_mtime, is_dir=False)
