"""
Configuration management for MCP Studio.
Enhanced version with better path handling and error recovery.
"""

import os
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

try:
    from pydantic_settings import BaseSettings
    from pydantic import ConfigDict, Field, field_validator
except ImportError:
    try:
        # Fallback to pydantic v1
        from pydantic import BaseSettings, Field, validator as field_validator
        ConfigDict = dict  # Fallback for v1
    except ImportError:
        # Fallback if pydantic not available
        BaseSettings = object
        Field = lambda **kwargs: None
        field_validator = lambda *args, **kwargs: lambda f: f
        ConfigDict = dict

# Project root directory
ROOT_DIR = Path(__file__).parent.parent.parent.parent

def get_default_repos_path() -> str:
    """Get default repos path from environment or use sensible default."""
    # Check environment variables first
    repos_dir = os.getenv("REPOS_DIR") or os.getenv("REPOS_PATH") or os.getenv("MCP_REPOS_DIR")
    if repos_dir:
        return repos_dir
    
    # Platform-specific defaults
    if os.name == 'nt':  # Windows
        # Try common Windows dev locations
        for base in [Path.home() / "Dev" / "repos", Path("D:/Dev/repos"), Path("C:/Dev/repos")]:
            if base.exists():
                return str(base)
        # Fallback to user's home/Dev/repos even if it doesn't exist yet
        return str(Path.home() / "Dev" / "repos")
    else:  # Linux/Mac
        # Try common Unix dev locations
        for base in [Path.home() / "dev" / "repos", Path.home() / "repos", Path("/opt/repos")]:
            if base.exists():
                return str(base)
        return str(Path.home() / "dev" / "repos")

# Global default repos path
DEFAULT_REPOS_PATH = get_default_repos_path()

class Settings(BaseSettings if BaseSettings != object else object):
    """Application settings with fallbacks."""
    
    # Application
    APP_NAME: str = "MCP Studio"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = True
    
    # Server
    HOST: str = "0.0.0.0"  # Bind to all interfaces
    PORT: int = 7787
    RELOAD: bool = True
    WORKERS: int = 1
    
    # Logging
    LOG_LEVEL: str = "INFO"
    JSON_LOGS: bool = False
    
    # Security
    SECRET_KEY: str = "mcp-studio-dev-key-change-in-production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days
    
    # CORS
    BACKEND_CORS_ORIGINS: List[str] = ["*"]  # Allow all origins for development
    
    # Database
    DATABASE_URL: str = "sqlite:///./mcp-studio.db"
    
    # MCP Discovery
    MCP_DISCOVERY_PATHS: List[str] = []

    # Repo Scanner
    REPOS_PATH: str = DEFAULT_REPOS_PATH
    REPO_SCAN_DEPTH: int = 2  # How deep to scan subdirectories
    REPO_SCAN_EXCLUDE: List[str] = [".git", "node_modules", "__pycache__", ".venv", "venv"]

    # UI Settings
    UI_THEME: str = "dark"
    UI_REFRESH_INTERVAL: int = 30  # seconds
    
    # DXT Packaging
    DXT_PACKAGE_NAME: str = "mcp-studio"
    DXT_PACKAGE_VERSION: str = "0.1.0"
    DXT_PACKAGE_DESCRIPTION: str = "MCP Studio - UI for managing MCP servers"
    
    def __init__(self, **kwargs):
        if BaseSettings != object:
            super().__init__(**kwargs)
        else:
            # Basic fallback initialization
            for key, value in kwargs.items():
                if hasattr(self, key):
                    setattr(self, key, value)
        
        # Set up MCP discovery paths
        if not self.MCP_DISCOVERY_PATHS:
            self._setup_discovery_paths()
    
    def _setup_discovery_paths(self):
        """Set up default MCP discovery paths."""
        try:
            paths = [
                str(ROOT_DIR / "mcp_servers"),
                str(Path.home() / ".mcp" / "servers"),
            ]
            
            # Check for environment variable first
            env_paths = os.getenv("MCP_DISCOVERY_PATHS") or os.getenv("DISCOVERY_PATHS")
            if env_paths:
                # Parse comma-separated paths from environment
                env_path_list = [p.strip() for p in env_paths.split(",") if p.strip()]
                paths.extend(env_path_list)
            
            # Add platform-specific paths
            if os.name == 'nt':  # Windows
                paths.extend([
                    str(Path(os.environ.get("APPDATA", "")) / "Claude"),
                    str(Path(os.environ.get("APPDATA", "")) / "Windsurf"),
                    str(Path(os.environ.get("APPDATA", "")) / "Cursor"),
                ])
                # Add default repos path if REPOS_DIR env var is set
                repos_dir = os.getenv("REPOS_DIR") or os.getenv("REPOS_PATH")
                if repos_dir:
                    paths.append(repos_dir)
            else:  # Linux/Mac
                paths.extend([
                    str(Path.home() / ".config" / "claude"),
                    str(Path.home() / ".config" / "windsurf"),
                    str(Path.home() / ".config" / "cursor"),
                ])
                # Add default repos path if REPOS_DIR env var is set
                repos_dir = os.getenv("REPOS_DIR") or os.getenv("REPOS_PATH")
                if repos_dir:
                    paths.append(repos_dir)
            
            # Filter out empty paths and validate existence
            valid_paths = []
            for p in paths:
                if p:
                    try:
                        path_obj = Path(p).expanduser()
                        # Don't require existence - user might create it later
                        valid_paths.append(str(path_obj))
                    except Exception:
                        pass
            
            self.MCP_DISCOVERY_PATHS = valid_paths
        except Exception as e:
            # Use logger instead of print to reduce spam
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Could not set up discovery paths: {e}")
            self.MCP_DISCOVERY_PATHS = []
    
    if BaseSettings != object:
        try:
            model_config = ConfigDict(
                case_sensitive=True,
                env_file=None,  # Temporarily disable .env loading to avoid parsing errors
                env_file_encoding="utf-8",
                env_ignore_empty=True,  # Ignore empty values
            )
        except TypeError:
            # Fallback for older pydantic versions
            class Config:
                case_sensitive = True
                env_file = None
                env_file_encoding = "utf-8"
                env_ignore_empty = True
        
        @field_validator("BACKEND_CORS_ORIGINS", mode="before")
        @classmethod
        def assemble_cors_origins(cls, v: Any) -> List[str]:
            if v is None:
                return []
            if isinstance(v, str):
                if v.startswith("["):
                    import json
                    try:
                        return json.loads(v)
                    except:
                        return []
                return [i.strip() for i in v.split(",") if i.strip()]
            elif isinstance(v, list):
                return v
            return []
        
        @field_validator("MCP_DISCOVERY_PATHS", mode="before")
        @classmethod
        def assemble_mcp_paths(cls, v: Any) -> List[str]:
            if v is None:
                return []
            if isinstance(v, str):
                return [i.strip() for i in v.split(";") if i.strip()]
            return v if isinstance(v, list) else []

@lru_cache()
def get_settings() -> Settings:
    """Get application settings."""
    try:
        return Settings()
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.warning(f"Error creating settings, using defaults: {e}")
        # Return settings with defaults, ignoring env file errors
        try:
            return Settings(_env_file=None)  # Disable env file loading on error
        except:
            # Last resort - create with minimal config
            return Settings()

# Global settings instance
settings = get_settings()

def update_settings(**kwargs: Any) -> None:
    """Update settings and refresh the cached instance."""
    global settings
    
    try:
        # Clear the cache and create new settings
        get_settings.cache_clear()
        settings = Settings(**kwargs)
    except Exception as e:
        print(f"Warning: Error updating settings: {e}")

# Test configuration loading
def test_config():
    """Test that configuration loads correctly."""
    try:
        test_settings = get_settings()
        print(f"✅ Config loaded: {test_settings.APP_NAME} v{test_settings.APP_VERSION}")
        print(f"   Server: {test_settings.HOST}:{test_settings.PORT}")
        print(f"   Debug: {test_settings.DEBUG}")
        print(f"   Discovery paths: {len(test_settings.MCP_DISCOVERY_PATHS)} configured")
        return True
    except Exception as e:
        print(f"❌ Config test failed: {e}")
        return False

if __name__ == "__main__":
    test_config()
