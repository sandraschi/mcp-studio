"""
Utility Tools for MCP Studio

This module provides various utility tools that can be used across the MCP Studio application.
"""
import asyncio
import hashlib
import json
import logging
import random
import re
import string
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Type, TypeVar, Union

import aiohttp
from pydantic import BaseModel, Field, validator

from mcp_studio.tools import (
    tool,
    structured_log,
    validate_input,
    rate_limited,
    retry_on_failure,
    cache_result,
    timed
)

logger = logging.getLogger("mcp.tools.utility")

T = TypeVar('T', bound=BaseModel)

class TextProcessingInput(BaseModel):
    """Input for text processing tools."""
    text: str = Field(..., description="The text to process")
    max_length: Optional[int] = Field(None, description="Maximum length of the output text")
    encoding: str = Field("utf-8", description="Text encoding to use")

@tool(
    name="generate_id",
    description="Generate a unique identifier",
    tags=["utility", "id", "generator"]
)
@structured_log()
def generate_id(prefix: str = "", length: int = 8) -> str:
    """
    Generate a unique identifier.
    
    Args:
        prefix: Optional prefix for the ID
        length: Length of the random part of the ID
        
    Returns:
        A unique identifier string
    """
    chars = string.ascii_letters + string.digits
    random_part = ''.join(random.choices(chars, k=length))
    return f"{prefix}{random_part}" if prefix else random_part

@tool(
    name="format_text",
    description="Format text with variables",
    tags=["utility", "text", "formatting"]
)
@structured_log()
@validate_input(TextProcessingInput)
def format_text(
    text: str,
    variables: Dict[str, Any],
    template_syntax: str = "mustache"
) -> str:
    """
    Format text with variables using different template syntaxes.
    
    Args:
        text: The template text with placeholders
        variables: Dictionary of variables to substitute
        template_syntax: Template syntax to use (mustache, fstring, format)
        
    Returns:
        Formatted text with variables substituted
    """
    if template_syntax == "mustache":
        # Simple mustache-style {{variable}} substitution
        for key, value in variables.items():
            text = text.replace(f"{{{{ {key} }}}}", str(value))
            text = text.replace(f"{{{{ {key.lower()} }}}}", str(value))
    elif template_syntax == "fstring":
        # Python f-string style {variable} substitution
        try:
            text = text.format(**variables)
        except KeyError as e:
            logger.warning(f"Missing variable in template: {e}")
            raise
    elif template_syntax == "format":
        # Python str.format() style {0} or {name} substitution
        try:
            if all(isinstance(k, int) for k in variables.keys()):
                # Positional arguments
                text = text.format(*[variables[i] for i in range(len(variables))])
            else:
                # Named arguments
                text = text.format(**variables)
        except (KeyError, IndexError) as e:
            logger.warning(f"Error formatting template: {e}")
            raise
    else:
        raise ValueError(f"Unsupported template syntax: {template_syntax}")
    
    return text

@tool(
    name="validate_json",
    description="Validate JSON data against a schema",
    tags=["utility", "validation", "json"]
)
@structured_log()
def validate_json(
    data: Union[str, dict],
    schema: Optional[dict] = None,
    model: Optional[Type[BaseModel]] = None
) -> Dict[str, Any]:
    """
    Validate JSON data against a schema or Pydantic model.
    
    Args:
        data: JSON data to validate (as string or dict)
        schema: JSON Schema to validate against (optional)
        model: Pydantic model to validate against (optional)
        
    Returns:
        Dictionary with validation results
    """
    result = {
        "valid": False,
        "errors": [],
        "normalized_data": None
    }
    
    # Parse JSON string if needed
    if isinstance(data, str):
        try:
            data = json.loads(data)
        except json.JSONDecodeError as e:
            result["errors"].append(f"Invalid JSON: {str(e)}")
            return result
    
    # Validate against Pydantic model if provided
    if model is not None:
        try:
            instance = model(**data)
            result["valid"] = True
            result["normalized_data"] = instance.dict()
            return result
        except Exception as e:
            if hasattr(e, 'errors'):
                result["errors"].extend([str(err) for err in e.errors()])
            else:
                result["errors"].append(str(e))
    
    # Validate against JSON Schema if provided
    elif schema is not None:
        from jsonschema import validate, ValidationError
        
        try:
            validate(instance=data, schema=schema)
            result["valid"] = True
            result["normalized_data"] = data
        except ValidationError as e:
            result["errors"].append(str(e))
    else:
        # Just check if it's valid JSON if no schema/model provided
        result["valid"] = True
        result["normalized_data"] = data
    
    return result

@tool(
    name="make_http_request",
    description="Make an HTTP request",
    tags=["utility", "http", "api"]
)
@structured_log()
@retry_on_failure(max_attempts=3, delay=1.0)
async def make_http_request(
    url: str,
    method: str = "GET",
    headers: Optional[Dict[str, str]] = None,
    params: Optional[Dict[str, Any]] = None,
    json_data: Optional[Union[Dict[str, Any], List[Any]]] = None,
    data: Optional[Union[Dict[str, Any], str, bytes]] = None,
    timeout: float = 30.0,
    verify_ssl: bool = True
) -> Dict[str, Any]:
    """
    Make an HTTP request and return the response.
    
    Args:
        url: The URL to request
        method: HTTP method (GET, POST, PUT, DELETE, etc.)
        headers: HTTP headers to include
        params: URL parameters
        json_data: JSON data to send in the request body
        data: Form data or raw data to send in the request body
        timeout: Request timeout in seconds
        verify_ssl: Whether to verify SSL certificates
        
    Returns:
        Dictionary containing the response status, headers, and data
    """
    if headers is None:
        headers = {}
    
    # Set default content type for JSON if not specified
    if json_data is not None and "Content-Type" not in headers:
        headers["Content-Type"] = "application/json"
    
    start_time = time.monotonic()
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.request(
                method=method,
                url=url,
                headers=headers,
                params=params,
                json=json_data,
                data=data,
                timeout=timeout,
                ssl=None if verify_ssl else False
            ) as response:
                # Read response data
                content_type = response.headers.get("Content-Type", "")
                
                # Handle different content types
                if "application/json" in content_type:
                    response_data = await response.json()
                else:
                    response_data = await response.text()
                
                # Calculate request duration
                duration = time.monotonic() - start_time
                
                # Prepare result
                result = {
                    "status": response.status,
                    "headers": dict(response.headers),
                    "data": response_data,
                    "url": str(response.url),
                    "duration": duration,
                    "success": 200 <= response.status < 400
                }
                
                # Log the request
                logger.info(
                    "http_request_complete",
                    extra={
                        "method": method,
                        "url": url,
                        "status": response.status,
                        "duration": duration,
                        "success": result["success"]
                    }
                )
                
                return result
                
    except Exception as e:
        duration = time.monotonic() - start_time
        logger.error(
            "http_request_failed",
            extra={
                "method": method,
                "url": url,
                "error": str(e),
                "duration": duration
            },
            exc_info=True
        )
        raise

@tool(
    name="schedule_task",
    description="Schedule a task to run after a delay",
    tags=["utility", "scheduling", "async"]
)
async def schedule_task(
    func: callable,
    delay: float = 0.0,
    *args: Any,
    **kwargs: Any
) -> str:
    """
    Schedule a function to run after a delay.
    
    Args:
        func: The function to schedule
        delay: Delay in seconds before running the function
        *args: Positional arguments to pass to the function
        **kwargs: Keyword arguments to pass to the function
        
    Returns:
        Task ID that can be used to cancel the task
    """
    from mcp_studio.tasks import scheduler
    
    task_id = f"scheduled_{int(time.time())}_{generate_id()}"
    
    async def wrapped():
        try:
            if asyncio.iscoroutinefunction(func):
                return await func(*args, **kwargs)
            else:
                return func(*args, **kwargs)
        except Exception as e:
            logger.error(
                "scheduled_task_failed",
                extra={
                    "task_id": task_id,
                    "function": func.__name__,
                    "error": str(e)
                },
                exc_info=True
            )
            raise
    
    scheduler.schedule_task(task_id, wrapped, delay)
    
    logger.info(
        "task_scheduled",
        extra={
            "task_id": task_id,
            "function": func.__name__,
            "delay": delay,
            "scheduled_time": time.time() + delay
        }
    )
    
    return task_id

@tool(
    name="cancel_scheduled_task",
    description="Cancel a scheduled task",
    tags=["utility", "scheduling"]
)
async def cancel_scheduled_task(task_id: str) -> bool:
    """
    Cancel a scheduled task.
    
    Args:
        task_id: ID of the task to cancel
        
    Returns:
        True if the task was cancelled, False if it wasn't found
    """
    from mcp_studio.tasks import scheduler
    
    cancelled = scheduler.cancel_task(task_id)
    
    if cancelled:
        logger.info("task_cancelled", extra={"task_id": task_id})
    else:
        logger.warning("task_not_found", extra={"task_id": task_id})
    
    return cancelled
