"""
MCPB/DXT Package Loader for MCP Studio.

Handles loading of packaged MCP servers in MCPB and DXT formats.
Both are ZIP archives containing server code, manifest, and dependencies.
"""

import asyncio
import json
import shutil
import sys
import zipfile
from pathlib import Path
from typing import Any

from ..core.logging_utils import get_logger

logger = get_logger(__name__)

# Cache directory for extracted packages
PACKAGE_CACHE_DIR = Path.home() / ".mcp-studio" / "package-cache"
PACKAGE_CACHE_DIR.mkdir(parents=True, exist_ok=True)


class MCPBPackage:
    """Represents an extracted MCPB/DXT package."""

    def __init__(self, package_path: Path, package_type: str = "mcpb") -> None:
        """
        Initialize MCPB package.

        Args:
            package_path: Path to .mcpb or .dxt file
            package_type: Package type ("mcpb" or "dxt")
        """
        self.package_path = package_path
        self.package_type = package_type
        self.package_name = package_path.stem
        self.extract_dir: Path | None = None
        self.manifest: dict[str, Any] | None = None
        self.entry_point: Path | None = None

    async def extract(self) -> bool:
        """
        Extract the package to cache directory.

        Returns:
            True if extraction successful
        """
        try:
            # Check if already extracted and up-to-date
            cache_key = f"{self.package_name}_{self.package_path.stat().st_mtime}"
            self.extract_dir = PACKAGE_CACHE_DIR / cache_key

            if self.extract_dir.exists():
                logger.info("Using cached package", package=self.package_name, cache_dir=str(self.extract_dir))
                return await self._load_manifest()

            # Create fresh extraction directory
            self.extract_dir.mkdir(parents=True, exist_ok=True)

            # Extract ZIP archive
            logger.info(
                "Extracting package", package=self.package_name, type=self.package_type, path=str(self.package_path)
            )

            with zipfile.ZipFile(self.package_path, "r") as zip_ref:
                zip_ref.extractall(self.extract_dir)

            logger.info("Package extracted successfully", package=self.package_name, extract_dir=str(self.extract_dir))

            # Load manifest
            return await self._load_manifest()

        except zipfile.BadZipFile as e:
            logger.error("Invalid package file (not a valid ZIP)", package=self.package_name, error=str(e))
            return False
        except Exception as e:
            logger.error("Failed to extract package", package=self.package_name, error=str(e), exc_info=True)
            return False

    async def _load_manifest(self) -> bool:
        """
        Load and parse manifest.json.

        Returns:
            True if manifest loaded successfully
        """
        try:
            if self.extract_dir is None:
                raise RuntimeError("Package not extracted")
            extract_dir = self.extract_dir
            manifest_path = extract_dir / "manifest.json"

            if not manifest_path.exists():
                logger.warning("No manifest.json found in package", package=self.package_name)
                # Try to find entry point anyway
                return await self._find_entry_point_fallback()

            with open(manifest_path, encoding="utf-8") as f:
                manifest: dict[str, Any] = json.load(f)
            self.manifest = manifest

            logger.info("Manifest loaded", package=self.package_name, version=manifest.get("version", "unknown"))

            # Get entry point from manifest
            entry_point = manifest.get("main", "server.py")
            entry_path = extract_dir / entry_point
            self.entry_point = entry_path

            if not entry_path.exists():
                logger.error("Entry point not found", package=self.package_name, entry_point=str(self.entry_point))
                return await self._find_entry_point_fallback()

            return True

        except json.JSONDecodeError as e:
            logger.error("Invalid manifest.json", package=self.package_name, error=str(e))
            return await self._find_entry_point_fallback()
        except Exception as e:
            logger.error("Failed to load manifest", package=self.package_name, error=str(e), exc_info=True)
            return False

    async def _find_entry_point_fallback(self) -> bool:
        """
        Try to find entry point without manifest.

        Returns:
            True if entry point found
        """
        # Common entry point names
        common_names = [
            "server.py",
            "main.py",
            "__main__.py",
            f"{self.package_name}.py",
            "mcp_server.py",
        ]

        extract_dir = self.extract_dir
        if extract_dir is None:
            logger.error("Package not extracted", package=self.package_name)
            return False

        for name in common_names:
            potential_entry = extract_dir / name
            if potential_entry.exists():
                self.entry_point = potential_entry
                logger.info("Found entry point (fallback)", package=self.package_name, entry_point=name)
                return True

        # Check in subdirectories
        for subdir in extract_dir.iterdir():
            if subdir.is_dir():
                for name in common_names:
                    potential_entry = subdir / name
                    if potential_entry.exists():
                        self.entry_point = potential_entry
                        logger.info(
                            "Found entry point in subdirectory",
                            package=self.package_name,
                            entry_point=str(potential_entry.relative_to(extract_dir)),
                        )
                        return True

        logger.error("Could not find entry point", package=self.package_name)
        return False

    async def install_dependencies(self) -> bool:
        """
        Install package dependencies from requirements.txt.

        Returns:
            True if dependencies installed successfully
        """
        try:
            if self.extract_dir is None:
                raise RuntimeError("Package not extracted")
            requirements_path = self.extract_dir / "requirements.txt"

            if not requirements_path.exists():
                logger.info("No requirements.txt found, skipping dependency installation", package=self.package_name)
                return True

            logger.info("Installing dependencies", package=self.package_name, requirements=str(requirements_path))

            # Install dependencies using pip
            process = await asyncio.create_subprocess_exec(
                sys.executable,
                "-m",
                "pip",
                "install",
                "-q",
                "-r",
                str(requirements_path),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            _stdout, stderr = await process.communicate()

            if process.returncode != 0:
                logger.error(
                    "Failed to install dependencies",
                    package=self.package_name,
                    error=stderr.decode() if stderr else "Unknown error",
                )
                return False

            logger.info("Dependencies installed successfully", package=self.package_name)
            return True

        except Exception as e:
            logger.error("Error installing dependencies", package=self.package_name, error=str(e), exc_info=True)
            return False

    def get_server_config(self) -> dict[str, Any]:
        """
        Get server configuration for MCP Studio.

        Returns:
            Server configuration dictionary
        """
        config = {
            "id": self.package_name,
            "name": self.manifest.get("name", self.package_name) if self.manifest else self.package_name,
            "description": self.manifest.get("description", f"Packaged MCP server ({self.package_type})")
            if self.manifest
            else f"Packaged MCP server ({self.package_type})",
            "version": self.manifest.get("version", "unknown") if self.manifest else "unknown",
            "command": sys.executable,
            "args": [str(self.entry_point)],
            "cwd": str(self.extract_dir),
            "env": {},
            "type": self.package_type,
            "source": "package",
            "package_path": str(self.package_path),
        }

        # Add metadata from manifest
        if self.manifest:
            config["metadata"] = {
                "author": self.manifest.get("author", "unknown"),
                "license": self.manifest.get("license", "unknown"),
                "homepage": self.manifest.get("homepage"),
                "dependencies": self.manifest.get("dependencies", {}),
            }

        return config

    def cleanup(self) -> None:
        """Clean up extracted files."""
        if self.extract_dir and self.extract_dir.exists():
            try:
                shutil.rmtree(self.extract_dir)
                logger.info("Cleaned up package cache", package=self.package_name, dir=str(self.extract_dir))
            except Exception as e:
                logger.warning("Failed to clean up package cache", package=self.package_name, error=str(e))


async def load_mcpb_package(package_path: Path) -> dict[str, Any] | None:
    """
    Load an MCPB or DXT package and return server configuration.

    Args:
        package_path: Path to .mcpb or .dxt file

    Returns:
        Server configuration dictionary, or None if loading failed
    """
    # Determine package type
    package_type = "dxt" if package_path.suffix == ".dxt" else "mcpb"

    logger.info("Loading package", path=str(package_path), type=package_type)

    # Create package instance
    package = MCPBPackage(package_path, package_type)

    # Extract package
    if not await package.extract():
        logger.error("Failed to extract package", path=str(package_path))
        return None

    # Install dependencies
    if not await package.install_dependencies():
        logger.warning("Failed to install dependencies, server may not work correctly", path=str(package_path))

    # Return server configuration
    config = package.get_server_config()

    logger.info(
        "Package loaded successfully", package=config["name"], version=config["version"], entry_point=config["args"][0]
    )

    return config


def cleanup_old_packages(max_age_days: int = 7) -> None:
    """
    Clean up old package cache directories.

    Args:
        max_age_days: Maximum age in days before cleanup
    """
    import time

    try:
        current_time = time.time()
        max_age_seconds = max_age_days * 24 * 60 * 60

        for cache_dir in PACKAGE_CACHE_DIR.iterdir():
            if not cache_dir.is_dir():
                continue

            # Check age
            dir_age = current_time - cache_dir.stat().st_mtime
            if dir_age > max_age_seconds:
                logger.info("Cleaning up old package cache", dir=cache_dir.name, age_days=dir_age / (24 * 60 * 60))
                shutil.rmtree(cache_dir)

    except Exception as e:
        logger.warning("Error cleaning up package cache", error=str(e))
