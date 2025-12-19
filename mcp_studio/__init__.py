# MCP Studio module - redirects to backend
# This allows backward compatibility while we transition to the new structure

import sys
from pathlib import Path

# Add the backend directory to Python path
backend_path = Path(__file__).parent / "backend"
if str(backend_path) not in sys.path:
    sys.path.insert(0, str(backend_path))

# Import everything from backend
try:
    from backend import *
except ImportError:
    # Fallback: import specific modules
    pass

# Make backend modules available at package level
def __getattr__(name):
    try:
        import backend
        return getattr(backend, name)
    except (ImportError, AttributeError):
        raise AttributeError(f"module 'mcp_studio' has no attribute '{name}'")
