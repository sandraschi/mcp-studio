"""
Settings API Routes for MCP Studio.

Provides endpoints for managing application settings.
"""

from typing import Dict, Any
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from ..app.core.config import settings, update_settings
from ..app.core.logging_utils import get_logger

logger = get_logger(__name__)

router = APIRouter()


class SettingsResponse(BaseModel):
    """Response model for settings."""
    repos_path: str = Field(..., description="Root directory for repository scanning")
    repo_scan_depth: int = Field(..., description="How deep to scan subdirectories")
    repo_scan_exclude: list[str] = Field(..., description="Directories to exclude from scanning")
    ui_theme: str = Field(..., description="UI theme (dark/light)")
    ui_refresh_interval: int = Field(..., description="UI refresh interval in seconds")
    debug: bool = Field(..., description="Debug mode enabled")
    log_level: str = Field(..., description="Logging level")
    host: str = Field(..., description="Server host")
    port: int = Field(..., description="Server port")


class SettingsUpdate(BaseModel):
    """Request model for updating settings."""
    repos_path: str = Field(None, description="Root directory for repository scanning")
    repo_scan_depth: int = Field(None, description="How deep to scan subdirectories")
    repo_scan_exclude: list[str] = Field(None, description="Directories to exclude from scanning")
    ui_theme: str = Field(None, description="UI theme (dark/light)")
    ui_refresh_interval: int = Field(None, description="UI refresh interval in seconds")


@router.get("/", response_model=SettingsResponse)
async def get_settings():
    """
    Get current application settings.

    Returns all configurable settings.
    """
    return SettingsResponse(
        repos_path=settings.REPOS_PATH,
        repo_scan_depth=settings.REPO_SCAN_DEPTH,
        repo_scan_exclude=settings.REPO_SCAN_EXCLUDE,
        ui_theme=settings.UI_THEME,
        ui_refresh_interval=settings.UI_REFRESH_INTERVAL,
        debug=settings.DEBUG,
        log_level=settings.LOG_LEVEL,
        host=settings.HOST,
        port=settings.PORT,
    )


@router.put("/")
async def update_settings_endpoint(settings_update: SettingsUpdate):
    """
    Update application settings.

    Only updates the provided fields.
    """
    updates = {}

    if settings_update.repos_path is not None:
        updates["REPOS_PATH"] = settings_update.repos_path

    if settings_update.repo_scan_depth is not None:
        updates["REPO_SCAN_DEPTH"] = settings_update.repo_scan_depth

    if settings_update.repo_scan_exclude is not None:
        updates["REPO_SCAN_EXCLUDE"] = settings_update.repo_scan_exclude

    if settings_update.ui_theme is not None:
        updates["UI_THEME"] = settings_update.ui_theme

    if settings_update.ui_refresh_interval is not None:
        updates["UI_REFRESH_INTERVAL"] = settings_update.ui_refresh_interval

    if updates:
        update_settings(**updates)
        logger.info("Settings updated", updates=updates)
        return {"message": "Settings updated successfully", "updated": list(updates.keys())}

    return {"message": "No settings to update"}


@router.post("/reset")
async def reset_settings():
    """
    Reset all settings to defaults.

    This will reload the application configuration from environment variables and defaults.
    """
    # This is a simple implementation - in a real app you'd want to be more careful
    # about what gets reset and handle persistence properly
    logger.warning("Settings reset requested - this is not fully implemented yet")
    return {"message": "Settings reset not fully implemented yet"}



