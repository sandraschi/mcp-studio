import json
import os
from pathlib import Path
from typing import Dict, Any, List
from fastapi import APIRouter, HTTPException
from ..core.logging_utils import get_logger

logger = get_logger(__name__)
router = APIRouter()

# Default paths for registries in the ecosystem
CENTRAL_DOCS_ROOT = Path("D:/Dev/repos/mcp-central-docs")
WEBAPP_REGISTRY_PATH = CENTRAL_DOCS_ROOT / "docs/operations/webapp-registry.json"
CONTAINER_REGISTRY_PATH = CENTRAL_DOCS_ROOT / "docs/operations/container-registry.json"


def load_json_registry(path: Path) -> Dict[str, Any]:
    """Load and return a JSON registry file."""
    if not path.exists():
        logger.warning(f"Registry not found at {path}")
        return {"error": f"Registry not found at {path}"}

    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error loading registry from {path}: {e}")
        return {"error": str(e)}


@router.get("/apps", tags=["ecosystem"])
async def get_webapp_registry():
    """Get the central webapp registry."""
    return load_json_registry(WEBAPP_REGISTRY_PATH)


@router.get("/containers", tags=["ecosystem"])
async def get_container_registry():
    """Get the central container registry."""
    return load_json_registry(CONTAINER_REGISTRY_PATH)


@router.get("/all", tags=["ecosystem"])
async def get_all_registries():
    """Get both webapp and container registries."""
    return {
        "webapps": load_json_registry(WEBAPP_REGISTRY_PATH).get("webapps", []),
        "containers": load_json_registry(CONTAINER_REGISTRY_PATH).get("containers", []),
    }
