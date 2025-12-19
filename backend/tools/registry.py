"""
Tool Registry System for MCP Studio with FastMCP 2.11 Integration.

This module provides a comprehensive tool registration system that automatically
discovers, validates, and registers MCP tools with FastMCP instances.
"""

import asyncio
import importlib
import inspect
import logging
import time
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set, Type, Union

import structlog
from fastmcp import FastMCP

from .decorators import ToolMetadata, get_tool_metadata, list_tools_in_module

logger = structlog.get_logger(__name__)


class ToolRegistry:
    """Central registry for managing MCP tools with FastMCP integration."""

    def __init__(self):
        """Initialize the tool registry."""
        self.tools: Dict[str, Callable] = {}
        self.metadata: Dict[str, ToolMetadata] = {}
        self.categories: Dict[str, List[str]] = {}
        self.modules: Set[str] = set()
        self.fastmcp_instances: List[FastMCP] = []
        self._initialized = False
        self._lock = asyncio.Lock()

    async def initialize(self) -> None:
        """Initialize the registry and discover tools."""
        async with self._lock:
            if self._initialized:
                return

            logger.info("Initializing tool registry")
            start_time = time.time()

            # Auto-discover tools in the tools package
            await self._auto_discover_tools()

            self._initialized = True
            init_time = time.time() - start_time

            logger.info(
                "Tool registry initialized",
                total_tools=len(self.tools),
                categories=len(self.categories),
                modules=len(self.modules),
                init_time_ms=round(init_time * 1000, 2)
            )

    async def register_tool(
        self,
        func: Callable,
        name: Optional[str] = None,
        force: bool = False
    ) -> bool:
        """Register a single tool function.

        Args:
            func: Function to register as a tool
            name: Optional custom name (defaults to function name)
            force: Whether to overwrite existing tools

        Returns:
            True if registration was successful
        """
        tool_name = name or func.__name__

        # Check if tool is already registered
        if tool_name in self.tools and not force:
            logger.warning(
                "Tool already registered, skipping",
                tool_name=tool_name,
                existing_module=getattr(self.tools[tool_name], '__module__', 'unknown')
            )
            return False

        # Get tool metadata
        metadata = get_tool_metadata(func)
        if not metadata:
            logger.warning(
                "Function is not a valid MCP tool (missing metadata)",
                function_name=func.__name__,
                module=func.__module__
            )
            return False

        # Validate tool function
        if not await self._validate_tool(func, metadata):
            return False

        # Register the tool
        self.tools[tool_name] = func
        self.metadata[tool_name] = metadata

        # Update categories
        category = metadata.category.value
        if category not in self.categories:
            self.categories[category] = []
        if tool_name not in self.categories[category]:
            self.categories[category].append(tool_name)

        # Track module
        if hasattr(func, '__module__'):
            self.modules.add(func.__module__)

        logger.info(
            "Tool registered successfully",
            tool_name=tool_name,
            category=category,
            module=func.__module__,
            deprecated=metadata.deprecated,
            experimental=metadata.experimental
        )

        return True

    async def register_module(self, module_name: str, force: bool = False) -> int:
        """Register all tools from a module.

        Args:
            module_name: Name of the module to import and register tools from
            force: Whether to overwrite existing tools

        Returns:
            Number of tools successfully registered
        """
        try:
            logger.info("Registering tools from module", module_name=module_name)
            start_time = time.time()

            # Import the module
            module = importlib.import_module(module_name)

            # Find all tool functions in the module
            registered_count = 0
            for attr_name in dir(module):
                attr = getattr(module, attr_name)

                # Check if this is a tool function
                if (callable(attr) and
                    hasattr(attr, '_mcp_is_tool') and
                    hasattr(attr, '_mcp_tool_metadata')):

                    if await self.register_tool(attr, force=force):
                        registered_count += 1

            registration_time = time.time() - start_time

            logger.info(
                "Module registration completed",
                module_name=module_name,
                tools_registered=registered_count,
                registration_time_ms=round(registration_time * 1000, 2)
            )

            return registered_count

        except ImportError as e:
            logger.error(
                "Failed to import module for tool registration",
                module_name=module_name,
                error=str(e)
            )
            return 0
        except Exception as e:
            logger.error(
                "Error during module registration",
                module_name=module_name,
                error=str(e),
                exc_info=True
            )
            return 0

    async def register_with_fastmcp(self, mcp: FastMCP, tool_filter: Optional[Callable[[str, ToolMetadata], bool]] = None) -> int:
        """Register all tools with a FastMCP instance.

        Args:
            mcp: FastMCP instance to register tools with
            tool_filter: Optional filter function to select which tools to register

        Returns:
            Number of tools registered
        """
        if not self._initialized:
            await self.initialize()

        logger.info("Registering tools with FastMCP instance", total_tools=len(self.tools))
        start_time = time.time()

        registered_count = 0

        for tool_name, func in self.tools.items():
            metadata = self.metadata[tool_name]

            # Apply filter if provided
            if tool_filter and not tool_filter(tool_name, metadata):
                continue

            try:
                # Register with FastMCP using the tool decorator
                mcp.tool(
                    name=metadata.name,
                    description=metadata.description
                )(func)

                registered_count += 1

                logger.debug(
                    "Tool registered with FastMCP",
                    tool_name=tool_name,
                    category=metadata.category.value,
                    deprecated=metadata.deprecated
                )

            except Exception as e:
                logger.error(
                    "Failed to register tool with FastMCP",
                    tool_name=tool_name,
                    error=str(e),
                    exc_info=True
                )

        # Track this FastMCP instance
        if mcp not in self.fastmcp_instances:
            self.fastmcp_instances.append(mcp)

        registration_time = time.time() - start_time

        logger.info(
            "FastMCP registration completed",
            tools_registered=registered_count,
            total_tools=len(self.tools),
            registration_time_ms=round(registration_time * 1000, 2)
        )

        return registered_count

    def get_tool(self, name: str) -> Optional[Callable]:
        """Get a tool function by name.

        Args:
            name: Name of the tool

        Returns:
            Tool function if found, None otherwise
        """
        return self.tools.get(name)

    def get_metadata(self, name: str) -> Optional[ToolMetadata]:
        """Get metadata for a tool.

        Args:
            name: Name of the tool

        Returns:
            Tool metadata if found, None otherwise
        """
        return self.metadata.get(name)

    def list_tools(
        self,
        category: Optional[str] = None,
        include_deprecated: bool = True,
        include_experimental: bool = True
    ) -> List[str]:
        """List all registered tools.

        Args:
            category: Filter by category
            include_deprecated: Whether to include deprecated tools
            include_experimental: Whether to include experimental tools

        Returns:
            List of tool names
        """
        tools = []

        for tool_name, metadata in self.metadata.items():
            # Filter by category
            if category and metadata.category.value != category:
                continue

            # Filter deprecated tools
            if not include_deprecated and metadata.deprecated:
                continue

            # Filter experimental tools
            if not include_experimental and metadata.experimental:
                continue

            tools.append(tool_name)

        return sorted(tools)

    def get_tools_by_category(self) -> Dict[str, List[str]]:
        """Get tools organized by category.

        Returns:
            Dictionary mapping categories to lists of tool names
        """
        return dict(self.categories)

    def get_registry_stats(self) -> Dict[str, Any]:
        """Get statistics about the tool registry.

        Returns:
            Dictionary containing registry statistics
        """
        stats = {
            "total_tools": len(self.tools),
            "total_categories": len(self.categories),
            "total_modules": len(self.modules),
            "fastmcp_instances": len(self.fastmcp_instances),
            "initialized": self._initialized,
            "categories": {},
            "deprecated_tools": 0,
            "experimental_tools": 0,
            "tools_by_author": {}
        }

        # Category breakdown
        for category, tools in self.categories.items():
            stats["categories"][category] = len(tools)

        # Count deprecated and experimental tools
        for metadata in self.metadata.values():
            if metadata.deprecated:
                stats["deprecated_tools"] += 1
            if metadata.experimental:
                stats["experimental_tools"] += 1

            # Count by author
            author = metadata.author or "unknown"
            if author not in stats["tools_by_author"]:
                stats["tools_by_author"][author] = 0
            stats["tools_by_author"][author] += 1

        return stats

    async def validate_all_tools(self) -> Dict[str, Any]:
        """Validate all registered tools.

        Returns:
            Dictionary containing validation results
        """
        logger.info("Validating all registered tools", total_tools=len(self.tools))
        start_time = time.time()

        validation_results = {
            "total_tools": len(self.tools),
            "valid_tools": 0,
            "invalid_tools": 0,
            "errors": {},
            "warnings": {}
        }

        for tool_name, func in self.tools.items():
            metadata = self.metadata[tool_name]

            try:
                if await self._validate_tool(func, metadata):
                    validation_results["valid_tools"] += 1
                else:
                    validation_results["invalid_tools"] += 1
                    validation_results["errors"][tool_name] = "Validation failed"

            except Exception as e:
                validation_results["invalid_tools"] += 1
                validation_results["errors"][tool_name] = str(e)

        validation_time = time.time() - start_time
        validation_results["validation_time_ms"] = round(validation_time * 1000, 2)

        logger.info(
            "Tool validation completed",
            valid_tools=validation_results["valid_tools"],
            invalid_tools=validation_results["invalid_tools"],
            validation_time_ms=validation_results["validation_time_ms"]
        )

        return validation_results

    async def _auto_discover_tools(self) -> None:
        """Auto-discover tools in the tools package."""
        logger.info("Auto-discovering tools in package")

        # List of modules to scan for tools
        tool_modules = [
            'backend.tools.server',
            'backend.tools.discovery',
            'backend.tools.utility',
            'backend.tools.development',
            'backend.tools.data',
            'backend.tools.files'
        ]

        total_registered = 0

        for module_name in tool_modules:
            try:
                count = await self.register_module(module_name)
                total_registered += count
            except Exception as e:
                logger.warning(
                    "Failed to auto-discover tools in module",
                    module_name=module_name,
                    error=str(e)
                )

        logger.info(
            "Auto-discovery completed",
            total_tools_registered=total_registered,
            modules_scanned=len(tool_modules)
        )

    async def _validate_tool(self, func: Callable, metadata: ToolMetadata) -> bool:
        """Validate a tool function and its metadata.

        Args:
            func: Tool function to validate
            metadata: Tool metadata to validate

        Returns:
            True if tool is valid
        """
        try:
            # Check if function is callable
            if not callable(func):
                logger.error("Tool is not callable", tool_name=metadata.name)
                return False

            # Check function signature
            sig = inspect.signature(func)
            if len(sig.parameters) > 20:  # Reasonable limit
                logger.warning(
                    "Tool has many parameters, may be complex",
                    tool_name=metadata.name,
                    param_count=len(sig.parameters)
                )

            # Check for required metadata fields
            if not metadata.name or not metadata.name.strip():
                logger.error("Tool has empty name", function_name=func.__name__)
                return False

            if not metadata.description or not metadata.description.strip():
                logger.warning("Tool has empty description", tool_name=metadata.name)

            # Validate tool name format
            if not metadata.name.replace('_', '').replace('-', '').isalnum():
                logger.error(
                    "Tool name contains invalid characters",
                    tool_name=metadata.name
                )
                return False

            # Check for async compatibility if needed
            if asyncio.iscoroutinefunction(func):
                logger.debug("Tool is async function", tool_name=metadata.name)

            return True

        except Exception as e:
            logger.error(
                "Tool validation failed",
                tool_name=metadata.name,
                error=str(e),
                exc_info=True
            )
            return False


# Global registry instance
registry = ToolRegistry()


# Convenience functions

async def initialize_registry() -> None:
    """Initialize the global tool registry."""
    await registry.initialize()


async def register_tool(func: Callable, name: Optional[str] = None, force: bool = False) -> bool:
    """Register a tool with the global registry."""
    return await registry.register_tool(func, name, force)


async def register_module(module_name: str, force: bool = False) -> int:
    """Register all tools from a module with the global registry."""
    return await registry.register_module(module_name, force)


async def register_with_fastmcp(
    mcp: FastMCP,
    tool_filter: Optional[Callable[[str, ToolMetadata], bool]] = None
) -> int:
    """Register all tools with a FastMCP instance."""
    return await registry.register_with_fastmcp(mcp, tool_filter)


def get_tool(name: str) -> Optional[Callable]:
    """Get a tool from the global registry."""
    return registry.get_tool(name)


def get_metadata(name: str) -> Optional[ToolMetadata]:
    """Get tool metadata from the global registry."""
    return registry.get_metadata(name)


def list_tools(
    category: Optional[str] = None,
    include_deprecated: bool = True,
    include_experimental: bool = True
) -> List[str]:
    """List tools from the global registry."""
    return registry.list_tools(category, include_deprecated, include_experimental)


def get_registry_stats() -> Dict[str, Any]:
    """Get statistics about the global registry."""
    return registry.get_registry_stats()


# Tool filters for FastMCP registration

def production_tools_filter(tool_name: str, metadata: ToolMetadata) -> bool:
    """Filter for production-ready tools only."""
    return not metadata.deprecated and not metadata.experimental


def safe_tools_filter(tool_name: str, metadata: ToolMetadata) -> bool:
    """Filter for safe tools (no auth required, not rate limited)."""
    return not metadata.requires_auth and not metadata.rate_limited


def category_filter(allowed_categories: List[str]) -> Callable[[str, ToolMetadata], bool]:
    """Create a filter for specific categories."""
    def filter_func(tool_name: str, metadata: ToolMetadata) -> bool:
        return metadata.category.value in allowed_categories
    return filter_func


# Registration utilities for FastMCP integration

async def setup_fastmcp_with_all_tools(
    mcp: FastMCP,
    include_experimental: bool = False,
    include_deprecated: bool = False
) -> int:
    """Set up a FastMCP instance with all available tools.

    Args:
        mcp: FastMCP instance to configure
        include_experimental: Whether to include experimental tools
        include_deprecated: Whether to include deprecated tools

    Returns:
        Number of tools registered
    """
    logger.info("Setting up FastMCP with MCP Studio tools")

    # Initialize registry if needed
    await initialize_registry()

    # Create filter based on parameters
    def setup_filter(tool_name: str, metadata: ToolMetadata) -> bool:
        if not include_experimental and metadata.experimental:
            return False
        if not include_deprecated and metadata.deprecated:
            return False
        return True

    # Register tools
    count = await register_with_fastmcp(mcp, setup_filter)

    logger.info(
        "FastMCP setup completed",
        tools_registered=count,
        include_experimental=include_experimental,
        include_deprecated=include_deprecated
    )

    return count


async def setup_fastmcp_minimal(mcp: FastMCP) -> int:
    """Set up a FastMCP instance with minimal, safe tools only.

    Args:
        mcp: FastMCP instance to configure

    Returns:
        Number of tools registered
    """
    logger.info("Setting up FastMCP with minimal tool set")

    # Initialize registry if needed
    await initialize_registry()

    # Register only safe, production-ready tools
    def minimal_filter(tool_name: str, metadata: ToolMetadata) -> bool:
        return (production_tools_filter(tool_name, metadata) and
                safe_tools_filter(tool_name, metadata))

    count = await register_with_fastmcp(mcp, minimal_filter)

    logger.info("Minimal FastMCP setup completed", tools_registered=count)

    return count
