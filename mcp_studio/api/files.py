"""
Files API Endpoints for MCP Studio

This module provides API endpoints for file system operations.
"""
import os
import shutil
import tempfile
from pathlib import Path
from typing import List, Optional, Dict, Any, BinaryIO
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse
from pydantic import BaseModel, Field, HttpUrl, DirectoryPath

from ..tools.files import (
    list_directory,
    read_file,
    write_file,
    create_temp_file,
    copy_file,
    FileInfo
)
from .auth import get_current_active_user

router = APIRouter()

# Pydantic models
class FileInfoModel(BaseModel):
    """File information model."""
    name: str
    path: str
    size: int
    is_dir: bool
    modified_time: float
    created_time: float
    permissions: str

class DirectoryListing(BaseModel):
    """Directory listing model."""
    path: str
    files: List[FileInfoModel]

class FileOperationResponse(BaseModel):
    """File operation response model."""
    success: bool
    message: str
    path: Optional[str] = None
    error: Optional[str] = None

class FileUploadResponse(BaseModel):
    """File upload response model."""
    success: bool
    filename: str
    size: int
    saved_path: str
    message: Optional[str] = None

# Helper functions
def to_file_info_model(file_info: FileInfo) -> FileInfoModel:
    """Convert FileInfo to FileInfoModel."""
    return FileInfoModel(
        name=file_info.name,
        path=str(file_info.path),
        size=file_info.size,
        is_dir=file_info.is_dir,
        modified_time=file_info.modified_time,
        created_time=file_info.created_time,
        permissions=file_info.permissions
    )

# API Endpoints
@router.get("/list/{path:path}", response_model=DirectoryListing)
async def list_directory_endpoint(
    path: str = "",
    current_user: Any = Depends(get_current_active_user)
):
    """
    List contents of a directory.
    
    Args:
        path: Directory path (relative to base directory)
        
    Returns:
        Directory listing
    """
    try:
        # Ensure the path is safe and within allowed directories
        base_dir = Path(".").resolve()  # Or your configured base directory
        target_path = (base_dir / path).resolve()
        
        # Security check to prevent directory traversal
        if not str(target_path).startswith(str(base_dir)):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access to this path is not allowed"
            )
        
        if not target_path.exists():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Path not found: {path}"
            )
            
        if not target_path.is_dir():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Not a directory: {path}"
            )
        
        # List directory contents
        files = list_directory(str(target_path))
        return DirectoryListing(
            path=str(target_path.relative_to(base_dir)),
            files=[to_file_info_model(f) for f in files]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list directory: {str(e)}"
        )

@router.get("/download/{path:path}")
async def download_file(
    path: str,
    current_user: Any = Depends(get_current_active_user)
):
    """
    Download a file.
    
    Args:
        path: File path (relative to base directory)
        
    Returns:
        File download response
    """
    try:
        # Security check
        base_dir = Path(".").resolve()
        file_path = (base_dir / path).resolve()
        
        if not str(file_path).startswith(str(base_dir)):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access to this file is not allowed"
            )
        
        if not file_path.exists() or not file_path.is_file():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"File not found: {path}"
            )
        
        return FileResponse(
            path=file_path,
            filename=file_path.name,
            media_type="application/octet-stream"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to download file: {str(e)}"
        )

@router.post("/upload/{path:path}", response_model=FileUploadResponse)
async def upload_file(
    path: str,
    file: UploadFile = File(...),
    current_user: Any = Depends(get_current_active_user)
):
    """
    Upload a file.
    
    Args:
        path: Target directory path (relative to base directory)
        file: File to upload
        
    Returns:
        Upload result
    """
    try:
        # Security check
        base_dir = Path(".").resolve()
        target_dir = (base_dir / path).resolve()
        
        if not str(target_dir).startswith(str(base_dir)):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Upload to this location is not allowed"
            )
        
        if not target_dir.exists() or not target_dir.is_dir():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Target directory does not exist: {path}"
            )
        
        # Save the uploaded file
        file_path = target_dir / file.filename
        
        # Ensure we don't overwrite existing files (or handle as needed)
        if file_path.exists():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File already exists: {file.filename}"
            )
        
        # Write the file
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Get file info
        file_info = file_path.stat()
        
        return FileUploadResponse(
            success=True,
            filename=file.filename,
            size=file_info.st_size,
            saved_path=str(file_path.relative_to(base_dir)),
            message="File uploaded successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload file: {str(e)}"
        )

@router.post("/create-directory/{path:path}", response_model=FileOperationResponse)
async def create_directory(
    path: str,
    current_user: Any = Depends(get_current_active_user)
):
    """
    Create a directory.
    
    Args:
        path: Directory path to create (relative to base directory)
        
    Returns:
        Operation result
    """
    try:
        # Security check
        base_dir = Path(".").resolve()
        target_dir = (base_dir / path).resolve()
        
        if not str(target_dir).startswith(str(base_dir)):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cannot create directory at this location"
            )
        
        if target_dir.exists():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Path already exists: {path}"
            )
        
        # Create the directory
        target_dir.mkdir(parents=True, exist_ok=True)
        
        return FileOperationResponse(
            success=True,
            message=f"Directory created: {path}",
            path=str(target_dir.relative_to(base_dir))
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create directory: {str(e)}"
        )

@router.delete("/delete/{path:path}", response_model=FileOperationResponse)
async def delete_path(
    path: str,
    recursive: bool = False,
    current_user: Any = Depends(get_current_active_user)
):
    """
    Delete a file or directory.
    
    Args:
        path: Path to delete (relative to base directory)
        recursive: Whether to delete directories recursively
        
    Returns:
        Operation result
    """
    try:
        # Security check
        base_dir = Path(".").resolve()
        target_path = (base_dir / path).resolve()
        
        if not str(target_path).startswith(str(base_dir)):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cannot delete this path"
            )
        
        if not target_path.exists():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Path not found: {path}"
            )
        
        # Delete the file or directory
        if target_path.is_file() or target_path.is_symlink():
            target_path.unlink()
        elif target_path.is_dir():
            if recursive:
                shutil.rmtree(target_path)
            else:
                target_path.rmdir()
        
        return FileOperationResponse(
            success=True,
            message=f"Deleted: {path}",
            path=str(target_path.relative_to(base_dir))
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete path: {str(e)}"
        )
