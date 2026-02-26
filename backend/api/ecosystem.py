"""
Ecosystem API Endpoints for MCP Studio

This module provides API endpoints for service discovery across the MCP ecosystem.
"""

import json
import os
from pathlib import Path
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

router = APIRouter()

# Path configuration
CENTRAL_DOCS_PATH = Path("D:/Dev/repos/mcp-central-docs")
WEBAPP_REGISTRY = CENTRAL_DOCS_PATH / "docs/operations/webapp-registry.json"
CONTAINER_REGISTRY = CENTRAL_DOCS_PATH / "docs/operations/container-registry.json"


class AppMetadata(BaseModel):
    """Webapp metadata model."""

    id: str
    name: str
    port: int
    repository: str
    description: Optional[str] = None
    category: Optional[str] = "utility"
    status: Optional[str] = "stable"


class ContainerMetadata(BaseModel):
    """Container metadata model."""

    id: str
    name: str
    image: str
    port: int
    description: Optional[str] = None


class EcosystemData(BaseModel):
    """Unified ecosystem data model."""

    webapps: List[AppMetadata]
    containers: List[ContainerMetadata]


def load_json_file(file_path: Path) -> Any:
    """Helper to load JSON file safely."""
    if not file_path.exists():
        return []
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []


@router.get("/apps", response_model=EcosystemData)
async def get_ecosystem_apps():
    """
    Returns the unified registry of all webapps and containers in the ecosystem.
    Used by SOTA topbars for dynamic navigation.
    """
    webapps_data = load_json_file(WEBAPP_REGISTRY)
    containers_data = load_json_file(CONTAINER_REGISTRY)

    # Process webapps (flatten if needed or return as is)
    # The registry is usually a list of dicts

    return {"webapps": webapps_data, "containers": containers_data}


@router.get("/webapps", response_model=List[AppMetadata])
async def get_webapps():
    """Returns only the webapp registry."""
    return load_json_file(WEBAPP_REGISTRY)


@router.get("/containers", response_model=List[ContainerMetadata])
async def get_containers():
    """Returns only the container registry."""
    return load_json_file(CONTAINER_REGISTRY)
