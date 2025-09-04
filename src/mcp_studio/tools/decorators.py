"""
Comprehensive tool decorators for MCP Studio with FastMCP 2.11 support.

This module provides decorators and utilities for creating MCP tools with proper
multiline descriptions, parameter validation, error handling, and performance monitoring.
"""

import asyncio
import functools
import inspect
import json
import logging
import time
import uuid
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional, TypeVar, Union, get_type_hints
from enum import Enum

import structlog
from fastmcp import FastMCP
from pydantic import BaseModel, Field, ValidationError, create_model

logger = structlog.get_logger(__name__)

# Type variable for decorated functions
F = TypeVar('F', bound=Callable[..., Any])


class ToolCategory(str, Enum):
    """Predefined tool categories for organization."""
    DISCOVERY = "discovery"
    UTILITY = "utility"
    DEVELOPMENT = "development"
    DATA = "data"
    FILES = "files"
    SERVER = "server"
    MONITORING = "monitoring"
    SECURITY = "security"
    NETWORK = "network"
    DATABASE = "database"


class ToolMetadata(BaseModel):
    """Enhanced metadata for MCP tools."""
    name: str = Field(..., description="Tool name")
    description: str = Field(..., description="Tool description")
    category: ToolCategory = Field(ToolCategory.UTILITY, description="Tool category")
    version: str = Field("1.0.0", description="Tool version")
    author: Optional[str] = Field(None, description="Tool author")
    tags: List[str] = Field(default_factory=list, description="Tool tags")
    deprecated: bool = Field(False, description="Whether the tool is deprecated")
    experimental: bool = Field(False, description="Whether the tool is experimental")
    examples: List[Dict[str, Any]] = Field(default_factory=list, description="Usage examples")

    # Performance metadata
    estimated_runtime: Optional[str] = Field(None, description="Estimated runtime (e.g., '< 1s', '1-5s')")
    requires_auth: bool = Field(False, description="Whether tool requires authentication")
    rate_limited: bool = Field(False, description="Whether tool has rate limits")

    # Internal tracking
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_modified: datetime = Field(default_factory=datetime.utcnow)
    usage_count: int = Field(0, description="Number of times tool has been used")


def clean_docstring(docstring: str) -> str:
    """Clean and format a multiline docstring for tool descriptions.

    Args:
        docstring: Raw docstring to clean

    Returns:
        Cleaned and formatted description
    """
    if not docstring:
        return ""

    lines = docstring.strip().split('\n')

    # Remove leading/trailing empty lines
    while lines and not lines[0].strip():
        lines.pop(0)
    while lines and not lines[-1].strip():
        lines.pop()

    if not lines:
        return ""

    # Find minimum indentation (excluding first line)
    min_indent = float('inf')
    for line in lines[1:]:
        if line.strip():  # Skip empty lines
            indent = len(line) - len(line.lstrip())
            min_indent = min(min_indent, indent)

    # Remove common indentation
    if min_indent != float('inf'):
        for i in range(1, len(lines)):
            if lines[i].strip():
                lines[i] = lines[i][min_indent:]

    return '\n'.join(lines)


def extract_parameter_info(func: Callable) -> Dict[str, Any]:
    """Extract parameter information from function signature and docstring.

    Args:
        func: Function to analyze

    Returns:
        Dictionary mapping parameter names to their schema information
    """
    sig = inspect.signature(func)
    type_hints = get_type_hints(func)

    parameters = {}

    for param_name, param in sig.parameters.items():
        # Skip 'self' parameter
        if param_name == 'self':
            continue

        param_info = {
            "type": "string",  # Default type
            "required": param.default == inspect.Parameter.empty,
            "description": f"Parameter: {param_name}"
        }

        # Get type information
        if param_name in type_hints:
            type_hint = type_hints[param_name]
            param_info["type"] = _python_type_to_json_schema_type(type_hint)

        # Set default value if available
        if param.default != inspect.Parameter.empty:
            param_info["default"] = param.default

        parameters[param_name] = param_info

    return parameters


def _python_type_to_json_schema_type(python_type) -> str:
    """Convert Python type to JSON Schema type string.

    Args:
        python_type: Python type annotation

    Returns:
        JSON Schema type string
    """
    type_mapping = {
        str: "string",
        int: "integer",
        float: "number",
        bool: "boolean",
        list: "array",
        dict: "object",
        List: "array",
        Dict: "object",
    }

    # Handle Union types (like Optional)
    if hasattr(python_type, '__origin__'):
        if python_type.__origin__ is Union:
            # For Optional[X], return the non-None type
            non_none_types = [t for t in python_type.__args__ if t is not type(None)]
            if non_none_types:
                return _python_type_to_json_schema_type(non_none_types[0])
        elif python_type.__origin__ in (list, List):
            return "array"
        elif python_type.__origin__ in (dict, Dict):
            return "object"

    return type_mapping.get(python_type, "string")


def tool(
    name: Optional[str] = None,
    description: Optional[str] = None,
    category: ToolCategory = ToolCategory.UTILITY,
    version: str = "1.0.0",
    author: Optional[str] = None,
    tags: Optional[List[str]] = None,
    deprecated: bool = False,
    experimental: bool = False,
    examples: Optional[List[Dict[str, Any]]] = None,
    estimated_runtime: Optional[str] = None,
    requires_auth: bool = False,
    rate_limited: bool = False,
) -> Callable[[F], F]:
    """Enhanced tool decorator for MCP tools with comprehensive metadata.

    This decorator provides:
    - Automatic multiline docstring processing
    - Parameter type inference from annotations
    - Comprehensive metadata collection
    - Performance tracking
    - Error handling and logging

    Args:
        name: Tool name (defaults to function name)
        description: Tool description (defaults to cleaned docstring)
        category: Tool category for organization
        version: Tool version
        author: Tool author
        tags: List of tags for categorization
        deprecated: Whether the tool is deprecated
        experimental: Whether the tool is experimental
        examples: Usage examples
        estimated_runtime: Estimated runtime description
        requires_auth: Whether tool requires authentication
        rate_limited: Whether tool has rate limits

    Returns:
        Decorated function with MCP tool metadata

    Example:
        ```python
        @tool(
            category=ToolCategory.UTILITY,
            tags=["math", "calculation"],
            examples=[{"input": {"a": 5, "b": 3}, "output": 8}],
            estimated_runtime="< 1s"
        )
        def add_numbers(a: int, b: int) -> int:
            '''Add two numbers together.

            This is a simple utility function that performs
            addition of two integer values.

            Args:
                a: First number to add
                b: Second number to add

            Returns:
                Sum of the two numbers
            '''
            return a + b
        ```
    """
    def decorator(func: F) -> F:
        # Extract function information
        func_name = name or func.__name__
        func_description = description or clean_docstring(func.__doc__ or "")

        # Create metadata
        metadata = ToolMetadata(
            name=func_name,
            description=func_description,
            category=category,
            version=version,
            author=author,
            tags=tags or [],
            deprecated=deprecated,
            experimental=experimental,
            examples=examples or [],
            estimated_runtime=estimated_runtime,
            requires_auth=requires_auth,
            rate_limited=rate_limited,
        )

        # Extract parameter information
        parameters = extract_parameter_info(func)

        # Store metadata on function
        func._mcp_tool_metadata = metadata
        func._mcp_tool_parameters = parameters
        func._mcp_tool_name = func_name
        func._mcp_is_tool = True

        # Create wrapper for async functions
        if asyncio.iscoroutinefunction(func):
            @functools.wraps(func)
            async def async_wrapper(*args, **kwargs):
                return await _execute_tool_with_monitoring(func, metadata, *args, **kwargs)
            return async_wrapper
        else:
            @functools.wraps(func)
            def sync_wrapper(*args, **kwargs):
                return _execute_tool_with_monitoring(func, metadata, *args, **kwargs)
            return sync_wrapper

    return decorator


def _execute_tool_with_monitoring(func: Callable, metadata: ToolMetadata, *args, **kwargs) -> Any:
    """Execute a tool with performance monitoring and error handling.

    Args:
        func: Function to execute
        metadata: Tool metadata
        *args: Function arguments
        **kwargs: Function keyword arguments

    Returns:
        Function result
    """
    start_time = time.time()
    execution_id = str(uuid.uuid4())

    logger.info(
        "Tool execution started",
        tool_name=metadata.name,
        execution_id=execution_id,
        category=metadata.category,
        args_count=len(args),
        kwargs_keys=list(kwargs.keys())
    )

    try:
        # Execute function
        if asyncio.iscoroutinefunction(func):
            result = asyncio.run(func(*args, **kwargs))
        else:
            result = func(*args, **kwargs)

        execution_time = time.time() - start_time

        # Update usage count
        metadata.usage_count += 1
        metadata.last_modified = datetime.utcnow()

        logger.info(
            "Tool execution completed",
            tool_name=metadata.name,
            execution_id=execution_id,
            execution_time=f"{execution_time:.3f}s",
            success=True
        )

        return result

    except Exception as e:
        execution_time = time.time() - start_time

        logger.error(
            "Tool execution failed",
            tool_name=metadata.name,
            execution_id=execution_id,
            execution_time=f"{execution_time:.3f}s",
            error=str(e),
            error_type=type(e).__name__,
            exc_info=True
        )

        # Re-raise the exception
        raise


def structured_log(level: str = "info", message: Optional[str] = None):
    """Decorator to add structured logging to tool functions.

    Args:
        level: Log level (debug, info, warning, error)
        message: Custom log message (defaults to function name)

    Example:
        ```python
        @structured_log(level="debug", message="Processing data file")
        @tool()
        def process_file(filename: str) -> str:
            # Function implementation
            pass
        ```
    """
    def decorator(func: F) -> F:
        log_message = message or f"Executing {func.__name__}"

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            getattr(logger, level)(
                log_message,
                function=func.__name__,
                args_count=len(args),
                kwargs_keys=list(kwargs.keys())
            )
            return func(*args, **kwargs)

        return wrapper
    return decorator


def validate_input(**field_validators):
    """Decorator to add input validation to tool functions.

    Args:
        **field_validators: Field name to validator function mapping

    Example:
        ```python
        @validate_input(
            filename=lambda x: x.endswith('.txt'),
            count=lambda x: x > 0
        )
        @tool()
        def process_files(filename: str, count: int) -> str:
            # Function implementation
            pass
        ```
    """
    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Get function signature
            sig = inspect.signature(func)
            bound_args = sig.bind(*args, **kwargs)
            bound_args.apply_defaults()

            # Validate inputs
            for field_name, validator in field_validators.items():
                if field_name in bound_args.arguments:
                    value = bound_args.arguments[field_name]
                    if not validator(value):
                        raise ValueError(f"Validation failed for parameter '{field_name}': {value}")

            return func(*args, **kwargs)

        return wrapper
    return decorator


def rate_limited(calls_per_minute: int = 60):
    """Decorator to add rate limiting to tool functions.

    Args:
        calls_per_minute: Maximum number of calls per minute

    Example:
        ```python
        @rate_limited(calls_per_minute=10)
        @tool()
        def expensive_operation() -> str:
            # Function implementation
            pass
        ```
    """
    def decorator(func: F) -> F:
        calls = []

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            now = time.time()
            # Remove calls older than 1 minute
            calls[:] = [call_time for call_time in calls if now - call_time < 60]

            if len(calls) >= calls_per_minute:
                raise RuntimeError(f"Rate limit exceeded: {calls_per_minute} calls per minute")

            calls.append(now)
            return func(*args, **kwargs)

        return wrapper
    return decorator


def retry_on_failure(max_retries: int = 3, delay: float = 1.0):
    """Decorator to add retry logic to tool functions.

    Args:
        max_retries: Maximum number of retry attempts
        delay: Delay between retries in seconds

    Example:
        ```python
        @retry_on_failure(max_retries=3, delay=2.0)
        @tool()
        def unreliable_operation() -> str:
            # Function implementation that might fail
            pass
        ```
    """
    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None

            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < max_retries:
                        logger.warning(
                            f"Tool execution failed, retrying in {delay}s",
                            tool=func.__name__,
                            attempt=attempt + 1,
                            max_retries=max_retries,
                            error=str(e)
                        )
                        time.sleep(delay)
                    else:
                        logger.error(
                            "Tool execution failed after all retries",
                            tool=func.__name__,
                            attempts=max_retries + 1,
                            error=str(e)
                        )

            # Re-raise the last exception
            raise last_exception

        return wrapper
    return decorator


def cache_result(ttl_seconds: int = 300):
    """Decorator to cache tool function results.

    Args:
        ttl_seconds: Time to live for cached results in seconds

    Example:
        ```python
        @cache_result(ttl_seconds=600)  # Cache for 10 minutes
        @tool()
        def expensive_calculation(data: str) -> str:
            # Expensive operation
            return result
        ```
    """
    def decorator(func: F) -> F:
        cache = {}

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Create cache key from arguments
            cache_key = json.dumps({
                'args': args,
                'kwargs': sorted(kwargs.items())
            }, sort_keys=True, default=str)

            now = time.time()

            # Check if we have a valid cached result
            if cache_key in cache:
                result, timestamp = cache[cache_key]
                if now - timestamp < ttl_seconds:
                    logger.debug(f"Returning cached result for {func.__name__}")
                    return result
                else:
                    # Remove expired entry
                    del cache[cache_key]

            # Execute function and cache result
            result = func(*args, **kwargs)
            cache[cache_key] = (result, now)

            logger.debug(f"Cached new result for {func.__name__}")
            return result

        return wrapper
    return decorator


def timed(log_threshold: float = 1.0):
    """Decorator to measure and log execution time for tool functions.

    Args:
        log_threshold: Only log if execution time exceeds this threshold (seconds)

    Example:
        ```python
        @timed(log_threshold=0.5)  # Log if takes more than 500ms
        @tool()
        def slow_operation() -> str:
            # Function implementation
            pass
        ```
    """
    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                execution_time = time.time() - start_time

                if execution_time > log_threshold:
                    logger.info(
                        f"Tool execution time",
                        tool=func.__name__,
                        execution_time=f"{execution_time:.3f}s"
                    )

                return result
            except Exception as e:
                execution_time = time.time() - start_time
                logger.error(
                    f"Tool execution failed",
                    tool=func.__name__,
                    execution_time=f"{execution_time:.3f}s",
                    error=str(e)
                )
                raise

        return wrapper
    return decorator


def register_tools_with_fastmcp(mcp: FastMCP, tools_module) -> None:
    """Register all tools from a module with a FastMCP instance.

    Args:
        mcp: FastMCP instance to register tools with
        tools_module: Module containing tool functions

    Example:
        ```python
        from fastmcp import FastMCP
        from . import server_tools

        mcp = FastMCP("My Server")
        register_tools_with_fastmcp(mcp, server_tools)
        ```
    """
    registered_count = 0

    for attr_name in dir(tools_module):
        attr = getattr(tools_module, attr_name)

        # Check if this is a tool function
        if (callable(attr) and
            hasattr(attr, '_mcp_is_tool') and
            hasattr(attr, '_mcp_tool_metadata')):

            metadata = attr._mcp_tool_metadata
            parameters = getattr(attr, '_mcp_tool_parameters', {})

            # Register with FastMCP
            mcp.tool(name=metadata.name, description=metadata.description)(attr)

            logger.info(
                "Registered MCP tool",
                tool_name=metadata.name,
                category=metadata.category,
                version=metadata.version,
                deprecated=metadata.deprecated,
                experimental=metadata.experimental
            )

            registered_count += 1

    logger.info(
        "Tool registration completed",
        total_tools=registered_count,
        module=tools_module.__name__
    )


def get_tool_metadata(func: Callable) -> Optional[ToolMetadata]:
    """Get metadata for a tool function.

    Args:
        func: Function to get metadata for

    Returns:
        Tool metadata if function is a tool, None otherwise
    """
    return getattr(func, '_mcp_tool_metadata', None)


def list_tools_in_module(module) -> List[Dict[str, Any]]:
    """List all tools in a module with their metadata.

    Args:
        module: Module to scan for tools

    Returns:
        List of dictionaries containing tool information
    """
    tools = []

    for attr_name in dir(module):
        attr = getattr(module, attr_name)

        if (callable(attr) and
            hasattr(attr, '_mcp_is_tool') and
            hasattr(attr, '_mcp_tool_metadata')):

            metadata = attr._mcp_tool_metadata
            tools.append({
                'function_name': attr_name,
                'tool_name': metadata.name,
                'description': metadata.description,
                'category': metadata.category,
                'version': metadata.version,
                'author': metadata.author,
                'tags': metadata.tags,
                'deprecated': metadata.deprecated,
                'experimental': metadata.experimental,
                'usage_count': metadata.usage_count,
                'estimated_runtime': metadata.estimated_runtime,
                'requires_auth': metadata.requires_auth,
                'rate_limited': metadata.rate_limited,
            })

    return tools
