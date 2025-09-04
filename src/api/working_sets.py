"""
FastAPI endpoints for Working Set management
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import logging
from pathlib import Path

from ..working_sets.manager import WorkingSetManager

logger = logging.getLogger(__name__)

# Initialize working set manager
CLAUDE_CONFIG_PATH = "C:/Users/sandr/AppData/Roaming/Claude/claude_desktop_config.json"
TEMPLATES_DIR = "templates"
BACKUP_DIR = "C:/Users/sandr/AppData/Roaming/Claude/backup"

manager = WorkingSetManager(
    config_path=CLAUDE_CONFIG_PATH,
    backup_dir=BACKUP_DIR, 
    templates_dir=TEMPLATES_DIR
)

router = APIRouter(prefix="/api/working-sets", tags=["working-sets"])

# Pydantic models
class WorkingSetResponse(BaseModel):
    name: str
    id: str
    description: str
    icon: str
    category: str
    servers: List[Dict[str, Any]]
    server_count: int
    is_current: bool

class SwitchRequest(BaseModel):
    working_set_id: str
    create_backup: bool = True

class BackupResponse(BaseModel):
    name: str
    file: str
    created: str
    size: int

class PreviewResponse(BaseModel):
    current_servers: List[str]
    new_servers: List[str] 
    added_servers: List[str]
    removed_servers: List[str]
    config_preview: Dict[str, Any]

class ValidationResponse(BaseModel):
    valid: bool
    missing_servers: List[str]
    available_servers: List[str]
    working_set_servers: List[str]
    error: Optional[str] = None

@router.get("/", response_model=List[WorkingSetResponse])
async def list_working_sets():
    """Get all available working sets with current status."""
    try:
        working_sets = manager.list_working_sets()
        current_working_set = manager.get_current_working_set()
        
        response = []
        for ws in working_sets:
            response.append(WorkingSetResponse(
                name=ws["name"],
                id=ws["id"],
                description=ws["description"], 
                icon=ws["icon"],
                category=ws["category"],
                servers=ws["servers"],
                server_count=len(ws["servers"]),
                is_current=(ws["id"] == current_working_set)
            ))
        
        return response
    except Exception as e:
        logger.error(f"Failed to list working sets: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/current")
async def get_current_working_set():
    """Get currently active working set."""
    try:
        current = manager.get_current_working_set()
        if current:
            working_set = manager.get_working_set(current)
            return {
                "working_set_id": current,
                "working_set": working_set.to_dict() if working_set else None
            }
        return {"working_set_id": None, "working_set": None}
    except Exception as e:
        logger.error(f"Failed to get current working set: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{working_set_id}")
async def get_working_set(working_set_id: str):
    """Get specific working set details."""
    try:
        working_set = manager.get_working_set(working_set_id)
        if not working_set:
            raise HTTPException(status_code=404, detail="Working set not found")
        
        current_working_set = manager.get_current_working_set()
        response = working_set.to_dict()
        response["is_current"] = (working_set_id == current_working_set)
        response["server_count"] = len(working_set.servers)
        
        return response
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get working set {working_set_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{working_set_id}/switch")
async def switch_working_set(working_set_id: str, request: SwitchRequest = None):
    """Switch to specified working set."""
    try:
        create_backup = request.create_backup if request else True
        success = manager.switch_to_working_set(working_set_id, create_backup)
        
        if success:
            return {
                "success": True,
                "message": f"Switched to working set: {working_set_id}",
                "working_set_id": working_set_id
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to switch working set")
            
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to switch to working set {working_set_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{working_set_id}/preview", response_model=PreviewResponse)
async def preview_working_set(working_set_id: str):
    """Preview config changes for working set without applying."""
    try:
        preview = manager.preview_working_set_config(working_set_id)
        return PreviewResponse(**preview)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to preview working set {working_set_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{working_set_id}/validate", response_model=ValidationResponse)
async def validate_working_set(working_set_id: str):
    """Validate that working set can be applied."""
    try:
        validation = manager.validate_working_set(working_set_id)
        return ValidationResponse(**validation)
    except Exception as e:
        logger.error(f"Failed to validate working set {working_set_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/backups/list", response_model=List[BackupResponse])
async def list_backups():
    """List all available config backups."""
    try:
        backups = manager.list_backups()
        return [BackupResponse(**backup) for backup in backups]
    except Exception as e:
        logger.error(f"Failed to list backups: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/backups/create")
async def create_backup(name: Optional[str] = None):
    """Create backup of current config."""
    try:
        backup_file = manager.create_backup(name)
        return {
            "success": True,
            "message": "Backup created successfully",
            "backup_file": backup_file
        }
    except Exception as e:
        logger.error(f"Failed to create backup: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/backups/{backup_name}/restore")
async def restore_backup(backup_name: str):
    """Restore config from backup."""
    try:
        success = manager.restore_backup(backup_name)
        if success:
            return {
                "success": True,
                "message": f"Restored backup: {backup_name}"
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to restore backup")
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to restore backup {backup_name}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/status/health")
async def health_check():
    """Health check endpoint."""
    try:
        # Check if config file exists
        config_exists = Path(CLAUDE_CONFIG_PATH).exists()
        
        # Check if templates are loaded
        working_sets = manager.list_working_sets()
        
        # Check backup directory
        backup_dir_exists = Path(BACKUP_DIR).exists()
        
        return {
            "healthy": True,
            "config_file_exists": config_exists,
            "working_sets_count": len(working_sets),
            "backup_dir_exists": backup_dir_exists,
            "claude_config_path": CLAUDE_CONFIG_PATH,
            "templates_dir": TEMPLATES_DIR,
            "backup_dir": BACKUP_DIR
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "healthy": False,
            "error": str(e)
        }
