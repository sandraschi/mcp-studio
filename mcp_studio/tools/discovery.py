"""
MCP Tool Discovery and Management

This module provides functionality to discover, register, and manage MCP tools.
"""
import importlib
import inspect
import json
import logging
import pkgutil
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Type, TypeVar, Union, cast

from pydantic import BaseModel, ValidationError

from .decorators import ToolMetadata, tool

logger = logging.getLogger("mcp.tools")

# Type variable for generic functions
T = TypeVar('T')

class ToolRegistry:
    """Registry for MCP tools."""
    
    def __init__(self):
        self._tools: Dict[str, Dict[str, Any]] = {}
        self._tool_metadata: Dict[str, ToolMetadata] = {}
        self._discovered = False
    
    def register(self, func: callable, metadata: Optional[ToolMetadata] = None) -> None:
        """
        Register a tool function with optional metadata.
        
        Args:
            func: The tool function to register
            metadata: Optional metadata for the tool
        """
        tool_name = func.__name__
        
        # Get or create metadata
        if metadata is None:
            metadata = getattr(func, "__mcp_metadata__", None) or ToolMetadata(
                name=tool_name,
                description=func.__doc__ or ""
            )
        
        # Store the tool and its metadata
        self._tools[tool_name] = {
            "function": func,
            "module": func.__module__,
            "docstring": func.__doc__ or "",
            "signature": str(inspect.signature(func))
        }
        self._tool_metadata[tool_name] = metadata
        
        logger.debug(
            "tool_registered",
            extra={
                "tool": tool_name,
                "module": func.__module__,
                "metadata": metadata.to_dict() if hasattr(metadata, 'to_dict') else str(metadata)
            }
        )
    
    def discover_tools(self, 
                      package: Union[str, List[str]], 
                      recursive: bool = True,
                      skip_errors: bool = True) -> None:
        """
        Discover and register tools from Python packages.
        
        Args:
            package: Package name or list of package names to search for tools
            recursive: Whether to search subpackages recursively
            skip_errors: Whether to skip errors during discovery
        """
        if isinstance(package, str):
            packages = [package]
        else:
            packages = package
        
        for pkg in packages:
            try:
                self._discover_package(pkg, recursive, skip_errors)
            except Exception as e:
                if skip_errors:
                    logger.warning(
                        "package_discovery_failed",
                        extra={
                            "package": pkg,
                            "error": str(e)
                        },
                        exc_info=True
                    )
                else:
                    raise
        
        self._discovered = True
        logger.info(
            "tool_discovery_complete",
            extra={
                "tools_registered": len(self._tools),
                "packages_searched": packages
            }
        )
    
    def _discover_package(self, 
                         package: str, 
                         recursive: bool = True, 
                         skip_errors: bool = True) -> None:
        """Discover tools in a package."""
        try:
            # Import the package
            module = importlib.import_module(package)
            
            # Get the package path
            if not hasattr(module, "__path__"):
                return
            
            # Find all modules in the package
            for _, name, is_pkg in pkgutil.iter_modules(module.__path__):
                full_name = f"{package}.{name}"
                
                try:
                    # Import the module
                    mod = importlib.import_module(full_name)
                    
                    # Register tools in the module
                    self._register_tools_in_module(mod)
                    
                    # Recursively process subpackages
                    if recursive and is_pkg:
                        self._discover_package(full_name, recursive, skip_errors)
                
                except Exception as e:
                    if skip_errors:
                        logger.warning(
                            "module_import_failed",
                            extra={
                                "module": full_name,
                                "error": str(e)
                            },
                            exc_info=True
                        )
                    else:
                        raise
        
        except ImportError as e:
            if skip_errors:
                logger.warning(
                    "package_import_failed",
                    extra={
                        "package": package,
                        "error": str(e)
                    },
                    exc_info=True
                )
            else:
                raise
    
    def _register_tools_in_module(self, module: Any) -> None:
        """Register all tools found in a module."""
        for name, obj in inspect.getmembers(module):
            # Skip private members
            if name.startswith('_'):
                continue
            
            # Check if the object is a function with MCP metadata
            if inspect.isfunction(obj) and hasattr(obj, "__mcp_metadata__"):
                self.register(obj)
            
            # Check if the object is a class with MCP metadata
            elif inspect.isclass(obj) and hasattr(obj, "__mcp_metadata__"):
                # Register the class itself if it's callable
                if callable(obj):
                    self.register(obj)
                
                # Register class methods with MCP metadata
                for method_name, method in inspect.getmembers(obj, inspect.isfunction):
                    if hasattr(method, "__mcp_metadata__"):
                        self.register(method)
    
    def get_tool(self, name: str) -> Optional[callable]:
        """
        Get a tool function by name.
        
        Args:
            name: Name of the tool to get
            
        Returns:
            The tool function if found, None otherwise
        """
        if not self._discovered:
            self.discover_tools(["mcp_studio.tools"])
        
        return self._tools.get(name, {}).get("function")
    
    def get_metadata(self, name: str) -> Optional[ToolMetadata]:
        """
        Get metadata for a tool.
        
        Args:
            name: Name of the tool
            
        Returns:
            The tool's metadata if found, None otherwise
        """
        if not self._discovered:
            self.discover_tools(["mcp_studio.tools"])
        
        return self._tool_metadata.get(name)
    
    def list_tools(self) -> List[Dict[str, Any]]:
        """
        List all registered tools with their metadata.
        
        Returns:
            List of dictionaries containing tool information
        """
        if not self._discovered:
            self.discover_tools(["mcp_studio.tools"])
        
        result = []
        for name, tool_info in self._tools.items():
            metadata = self._tool_metadata.get(name, {})
            result.append({
                "name": name,
                "module": tool_info["module"],
                "description": metadata.description if hasattr(metadata, 'description') else "",
                "version": metadata.version if hasattr(metadata, 'version') else "1.0.0",
                "tags": metadata.tags if hasattr(metadata, 'tags') else [],
                "signature": tool_info["signature"]
            })
        
        return result
    
    def execute_tool(self, name: str, *args, **kwargs) -> Any:
        """
        Execute a tool by name with the given arguments.
        
        Args:
            name: Name of the tool to execute
            *args: Positional arguments to pass to the tool
            **kwargs: Keyword arguments to pass to the tool
            
        Returns:
            The result of the tool execution
            
        Raises:
            KeyError: If the tool is not found
            Exception: Any exception raised by the tool
        """
        if not self._discovered:
            self.discover_tools(["mcp_studio.tools"])
        
        if name not in self._tools:
            raise KeyError(f"Tool not found: {name}")
        
        tool_func = self._tools[name]["function"]
        
        # Log the tool execution
        logger.info(
            "tool_execution_start",
            extra={
                "tool": name,
                "args": args,
                "kwargs": kwargs,
                "metadata": self._tool_metadata.get(name, {}).to_dict() 
                           if hasattr(self._tool_metadata.get(name), 'to_dict') 
                           else str(self._tool_metadata.get(name))
            }
        )
        
        try:
            # Execute the tool
            result = tool_func(*args, **kwargs)
            
            # Log successful execution
            logger.info(
                "tool_execution_success",
                extra={
                    "tool": name,
                    "result": str(result)[:1000]  # Limit result size
                }
            )
            
            return result
            
        except Exception as e:
            # Log the error
            logger.error(
                "tool_execution_error",
                extra={
                    "tool": name,
                    "error": str(e),
                    "error_type": type(e).__name__
                },
                exc_info=True
            )
            raise


# Global registry instance
registry = ToolRegistry()


def get_tool(name: str) -> Optional[callable]:
    """Get a tool function by name."""
    return registry.get_tool(name)


def get_metadata(name: str) -> Optional[ToolMetadata]:
    """Get metadata for a tool."""
    return registry.get_metadata(name)


def list_tools() -> List[Dict[str, Any]]:
    """List all registered tools with their metadata."""
    return registry.list_tools()


def execute_tool(name: str, *args, **kwargs) -> Any:
    """Execute a tool by name with the given arguments."""
    return registry.execute_tool(name, *args, **kwargs)


def discover_tools(package: Union[str, List[str]], 
                  recursive: bool = True, 
                  skip_errors: bool = True) -> None:
    """
    Discover and register tools from Python packages.
    
    Args:
        package: Package name or list of package names to search for tools
        recursive: Whether to search subpackages recursively
        skip_errors: Whether to skip errors during discovery
    """
    registry.discover_tools(package, recursive, skip_errors)


# Example usage
if __name__ == "__main__":
    import logging
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('tool_discovery.log')
        ]
    )
    
    # Example tool
    @tool(
        name="example_tool",
        description="An example MCP tool",
        version="1.0.0",
        tags=["example", "test"]
    )
    def example_tool(text: str, repeat: int = 1) -> str:
        """Repeat the input text the specified number of times."""
        if repeat < 0:
            raise ValueError("Repeat count must be non-negative")
        return " ".join([text] * repeat)
    
    # Discover and register tools
    discover_tools(["__main__"])
    
    # List all tools
    print("\nRegistered tools:")
    for tool_info in list_tools():
        print(f"- {tool_info['name']}: {tool_info['description']}")
    
    # Execute a tool
    print("\nExecuting example_tool:")
    result = execute_tool("example_tool", "Hello", repeat=3)
    print(f"Result: {result}")
