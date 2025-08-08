"""
Configuration management for MCP Studio.
Enhanced version with better path handling and error recovery.
"""

import os
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

try:
    from pydantic import BaseSettings, Field, validator
except ImportError:
    # Fallback for older pydantic versions or if not installed
    print("Warning: Pydantic not available, using basic configuration")
    BaseSettings = object
    Field = lambda **kwargs: None
    validator = lambda *args, **kwargs: lambda f: f

# Project root directory
ROOT_DIR = Path(__file__).parent.parent.parent.parent

class Settings(BaseSettings if BaseSettings != object else object):
    """Application settings with fallbacks."""
    
    # Application
    APP_NAME: str = "MCP Studio"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = True
    
    # Server
    HOST: str = "127.0.0.1"
    PORT: int = 8000
    RELOAD: bool = True
    WORKERS: int = 1
    
    # Logging
    LOG_LEVEL: str = "INFO"
    JSON_LOGS: bool = False
    
    # Security
    SECRET_KEY: str = "mcp-studio-dev-key-change-in-production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days
    
    # CORS
    BACKEND_CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:8000"]
    
    # Database
    DATABASE_URL: str = "sqlite:///./mcp-studio.db"
    
    # MCP Discovery
    MCP_DISCOVERY_PATHS: List[str] = []
    
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
            
            # Add platform-specific paths
            if os.name == 'nt':  # Windows
                paths.extend([
                    str(Path(os.environ.get("APPDATA", "")) / "Claude"),
                    str(Path(os.environ.get("APPDATA", "")) / "Windsurf"),
                    str(Path(os.environ.get("APPDATA", "")) / "Cursor"),
                ])
            else:  # Linux/Mac
                paths.extend([
                    str(Path.home() / ".config" / "claude"),
                    str(Path.home() / ".config" / "windsurf"),
                    str(Path.home() / ".config" / "cursor"),
                ])
            
            self.MCP_DISCOVERY_PATHS = [p for p in paths if p]
        except Exception as e:
            print(f"Warning: Could not set up discovery paths: {e}")
            self.MCP_DISCOVERY_PATHS = []
    
    if BaseSettings != object:
        class Config:
            case_sensitive = True
            env_file = ".env"
            env_file_encoding = "utf-8"
        
        @validator("BACKEND_CORS_ORIGINS", pre=True)
        def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
            if isinstance(v, str) and not v.startswith("["):
                return [i.strip() for i in v.split(",")]
            elif isinstance(v, (list, str)):
                return v if isinstance(v, list) else [v]
            return []
        
        @validator("MCP_DISCOVERY_PATHS", pre=True)
        def assemble_mcp_paths(cls, v: Union[str, List[str]]) -> List[str]:
            if isinstance(v, str):
                return [i.strip() for i in v.split(";") if i.strip()]
            return v if isinstance(v, list) else []

@lru_cache()
def get_settings() -> Settings:
    """Get application settings."""
    try:
        return Settings()
    except Exception as e:
        print(f"Warning: Error creating settings: {e}")
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
