"""
Tool Service for MCP Studio

This service handles tool discovery, execution, and management with WebSocket support.
"""
import asyncio
import inspect
import json
import logging
from typing import Any, Callable, Dict, List, Optional, Union, Awaitable
from uuid import UUID, uuid4

from fastapi import WebSocket
from pydantic import BaseModel, Field

from ..core.websocket import manager, ProgressUpdateMessage, ToolExecutionMessage
from ..models.user import User

logger = logging.getLogger(__name__)

class ToolExecutionResult(BaseModel):
    """Result of a tool execution."""
    success: bool
    result: Optional[Any] = None
    error: Optional[str] = None
    execution_time: float
    metadata: Dict[str, Any] = Field(default_factory=dict)

class ToolMetadata(BaseModel):
    """Metadata for a tool."""
    name: str
    description: str
    parameters: Dict[str, Any] = Field(default_factory=dict)
    tags: List[str] = Field(default_factory=list)
    is_async: bool = False
    requires_auth: bool = False
    allowed_roles: List[str] = Field(default_factory=list)

class Tool(BaseModel):
    """A tool that can be executed."""
    func: Callable
    metadata: ToolMetadata
    
    class Config:
        arbitrary_types_allowed = True

class ToolService:
    """Service for managing and executing tools."""
    
    def __init__(self):
        """Initialize the tool service."""
        self._tools: Dict[str, Tool] = {}
        self._executions: Dict[str, asyncio.Task] = {}
    
    def register_tool(
        self,
        func: Callable,
        name: Optional[str] = None,
        description: Optional[str] = None,
        parameters: Optional[Dict[str, Any]] = None,
        tags: Optional[List[str]] = None,
        requires_auth: bool = False,
        allowed_roles: Optional[List[str]] = None
    ) -> None:
        """Register a new tool.
        
        Args:
            func: The function to register as a tool
            name: Name of the tool (defaults to function name)
            description: Description of the tool
            parameters: Parameter schema for the tool
            tags: Tags for categorizing the tool
            requires_auth: Whether the tool requires authentication
            allowed_roles: List of roles allowed to execute this tool
        """
        if name is None:
            name = func.__name__
        
        if description is None:
            description = func.__doc__ or ""
        
        if parameters is None:
            # Try to extract parameters from function signature
            sig = inspect.signature(func)
            parameters = {}
            for param in sig.parameters.values():
                param_info = {
                    'type': param.annotation.__name__ if param.annotation != inspect.Parameter.empty else 'Any',
                    'required': param.default == inspect.Parameter.empty,
                }
                if param.default != inspect.Parameter.empty:
                    param_info['default'] = param.default
                parameters[param.name] = param_info
        
        if tags is None:
            tags = []
        
        if allowed_roles is None:
            allowed_roles = []
        
        # Create tool metadata
        metadata = ToolMetadata(
            name=name,
            description=description,
            parameters=parameters,
            tags=tags,
            is_async=asyncio.iscoroutinefunction(func),
            requires_auth=requires_auth,
            allowed_roles=allowed_roles
        )
        
        # Register the tool
        self._tools[name] = Tool(func=func, metadata=metadata)
        logger.info(f"Registered tool: {name}")
    
    def get_tool(self, name: str) -> Optional[Tool]:
        """Get a tool by name.
        
        Args:
            name: Name of the tool to get
            
        Returns:
            The tool if found, None otherwise
        """
        return self._tools.get(name)
    
    def list_tools(self) -> List[ToolMetadata]:
        """List all available tools.
        
        Returns:
            List of tool metadata
        """
        return [tool.metadata for tool in self._tools.values()]
    
    async def execute_tool(
        self,
        tool_name: str,
        parameters: Dict[str, Any],
        user: Optional[User] = None,
        execution_id: Optional[str] = None,
        websocket: Optional[WebSocket] = None,
        progress_callback: Optional[Callable[[float, str], Awaitable[None]]] = None
    ) -> ToolExecutionResult:
        """Execute a tool with the given parameters.
        
        Args:
            tool_name: Name of the tool to execute
            parameters: Parameters to pass to the tool
            user: The user executing the tool
            execution_id: Optional execution ID for tracking
            websocket: Optional WebSocket for real-time updates
            progress_callback: Optional callback for progress updates
            
        Returns:
            The result of the tool execution
        """
        import time
        start_time = time.time()
        
        if execution_id is None:
            execution_id = f"exec_{uuid4().hex[:8]}"
        
        # Get the tool
        tool = self.get_tool(tool_name)
        if not tool:
            return ToolExecutionResult(
                success=False,
                error=f"Tool not found: {tool_name}",
                execution_time=time.time() - start_time
            )
        
        # Check authentication
        if tool.metadata.requires_auth and not user:
            return ToolExecutionResult(
                success=False,
                error="Authentication required",
                execution_time=time.time() - start_time
            )
        
        # Check authorization
        if tool.metadata.allowed_roles and user:
            if not any(role in user.roles for role in tool.metadata.allowed_roles):
                return ToolExecutionResult(
                    success=False,
                    error="Insufficient permissions",
                    execution_time=time.time() - start_time
                )
        
        # Prepare parameters
        func_params = {}
        sig = inspect.signature(tool.func)
        
        # Add user to parameters if the function accepts a 'user' parameter
        if 'user' in sig.parameters:
            func_params['user'] = user
        
        # Add progress callback if the function accepts it
        if 'progress_callback' in sig.parameters:
            func_params['progress_callback'] = progress_callback
        
        # Add other parameters
        for param_name, param_info in sig.parameters.items():
            if param_name in ['user', 'progress_callback']:
                continue
                
            if param_name in parameters:
                func_params[param_name] = parameters[param_name]
            elif param_info.default != inspect.Parameter.empty:
                func_params[param_name] = param_info.default
            elif param_info.kind == inspect.Parameter.VAR_POSITIONAL:
                func_params[param_name] = []
            elif param_info.kind == inspect.Parameter.VAR_KEYWORD:
                func_params[param_name] = {}
            else:
                return ToolExecutionResult(
                    success=False,
                    error=f"Missing required parameter: {param_name}",
                    execution_time=time.time() - start_time
                )
        
        # Execute the tool
        try:
            # Send start notification
            if websocket:
                await websocket.send_json({
                    "type": "execution_started",
                    "execution_id": execution_id,
                    "tool": tool_name,
                    "timestamp": start_time
                })
            
            # Execute the tool
            if tool.metadata.is_async:
                result = await tool.func(**func_params)
            else:
                # Run synchronous functions in a thread pool
                loop = asyncio.get_event_loop()
                result = await loop.run_in_executor(
                    None,
                    lambda: tool.func(**func_params)
                )
            
            execution_time = time.time() - start_time
            
            # Send completion notification
            if websocket:
                await websocket.send_json({
                    "type": "execution_completed",
                    "execution_id": execution_id,
                    "tool": tool_name,
                    "execution_time": execution_time,
                    "timestamp": time.time()
                })
            
            return ToolExecutionResult(
                success=True,
                result=result,
                execution_time=execution_time,
                metadata={
                    "tool": tool_name,
                    "execution_id": execution_id,
                    "user": user.username if user else None
                }
            )
            
        except Exception as e:
            logger.error(f"Error executing tool {tool_name}: {e}", exc_info=True)
            
            # Send error notification
            if websocket:
                await websocket.send_json({
                    "type": "execution_failed",
                    "execution_id": execution_id,
                    "tool": tool_name,
                    "error": str(e),
                    "execution_time": time.time() - start_time,
                    "timestamp": time.time()
                })
            
            return ToolExecutionResult(
                success=False,
                error=str(e),
                execution_time=time.time() - start_time,
                metadata={
                    "tool": tool_name,
                    "execution_id": execution_id,
                    "user": user.username if user else None
                }
            )
    
    async def execute_tool_ws(
        self,
        tool_name: str,
        parameters: Dict[str, Any],
        websocket: WebSocket,
        user: Optional[User] = None,
        execution_id: Optional[str] = None
    ) -> None:
        """Execute a tool and stream results over WebSocket.
        
        Args:
            tool_name: Name of the tool to execute
            parameters: Parameters to pass to the tool
            websocket: WebSocket connection for streaming results
            user: The user executing the tool
            execution_id: Optional execution ID for tracking
        """
        if execution_id is None:
            execution_id = f"ws_exec_{uuid4().hex[:8]}"
        
        # Create a progress callback
        async def progress_callback(progress: float, message: str = "") -> None:
            """Send progress updates to the WebSocket."""
            await websocket.send_json({
                "type": "progress",
                "execution_id": execution_id,
                "tool": tool_name,
                "progress": progress,
                "message": message,
                "timestamp": time.time()
            })
        
        # Execute the tool
        result = await self.execute_tool(
            tool_name=tool_name,
            parameters=parameters,
            user=user,
            execution_id=execution_id,
            websocket=websocket,
            progress_callback=progress_callback
        )
        
        # Send the final result
        await websocket.send_json({
            "type": "result",
            "execution_id": execution_id,
            "tool": tool_name,
            "success": result.success,
            "result": result.result,
            "error": result.error,
            "execution_time": result.execution_time,
            "timestamp": time.time()
        })

# Global tool service instance
tool_service = ToolService()

def tool(
    name: Optional[str] = None,
    description: Optional[str] = None,
    parameters: Optional[Dict[str, Any]] = None,
    tags: Optional[List[str]] = None,
    requires_auth: bool = False,
    allowed_roles: Optional[List[str]] = None
):
    """Decorator to register a function as a tool.
    
    Args:
        name: Name of the tool (defaults to function name)
        description: Description of the tool
        parameters: Parameter schema for the tool
        tags: Tags for categorizing the tool
        requires_auth: Whether the tool requires authentication
        allowed_roles: List of roles allowed to execute this tool
        
    Returns:
        The decorated function
    """
    def decorator(func):
        nonlocal name, description
        
        if name is None:
            name = func.__name__
        
        if description is None:
            description = func.__doc__ or ""
        
        tool_service.register_tool(
            func=func,
            name=name,
            description=description,
            parameters=parameters,
            tags=tags or [],
            requires_auth=requires_auth,
            allowed_roles=allowed_roles or []
        )
        return func
    
    return decorator
