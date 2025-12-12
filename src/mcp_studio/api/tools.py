"""
Tools API Endpoints for MCP Studio

This module provides API endpoints for interacting with MCP tools.
"""
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query, WebSocket, WebSocketDisconnect
from pydantic import BaseModel, Field

from mcp_studio.tools import (
    list_tools,
    get_tool,
    execute_tool,
    ToolMetadata
)
from .auth import get_current_active_user

router = APIRouter()

# Pydantic models for request/response
class ToolExecutionRequest(BaseModel):
    """Request model for executing a tool."""
    parameters: Dict[str, Any] = Field(
        default_factory=dict,
        description="Parameters to pass to the tool"
    )
    timeout: Optional[float] = Field(
        None,
        description="Execution timeout in seconds"
    )

class ToolExecutionResponse(BaseModel):
    """Response model for tool execution."""
    success: bool
    result: Any
    execution_time: float
    error: Optional[str] = None

class ToolInfo(BaseModel):
    """Tool information model."""
    name: str
    description: str
    parameters: Dict[str, Any] = {}
    tags: List[str] = []
    metadata: Dict[str, Any] = {}

# API Endpoints
@router.get("/", response_model=List[ToolInfo])
async def list_available_tools(
    skip: int = 0,
    limit: int = 100,
    tag: Optional[str] = None,
    current_user: Any = Depends(get_current_active_user)
):
    """
    List all available tools with optional filtering.
    
    Args:
        skip: Number of tools to skip
        limit: Maximum number of tools to return
        tag: Filter tools by tag
        
    Returns:
        List of tool information objects
    """
    tools = []
    for tool_name in list_tools():
        try:
            tool_meta = get_tool(tool_name)
            if tool_meta:
                if tag and tag not in tool_meta.get('tags', []):
                    continue
                    
                tools.append(ToolInfo(
                    name=tool_meta['name'],
                    description=tool_meta.get('description', ''),
                    parameters=tool_meta.get('parameters', {}),
                    tags=tool_meta.get('tags', []),
                    metadata={
                        k: v for k, v in tool_meta.items()
                        if k not in ['name', 'description', 'parameters', 'tags']
                    }
                ))
        except Exception as e:
            # Skip tools that can't be loaded
            continue
    
    return tools[skip : skip + limit]

@router.get("/{tool_name}", response_model=ToolInfo)
async def get_tool_info(
    tool_name: str,
    current_user: Any = Depends(get_current_active_user)
):
    """
    Get detailed information about a specific tool.
    
    Args:
        tool_name: Name of the tool to get information about
        
    Returns:
        Detailed tool information
    """
    tool_meta = get_tool(tool_name)
    if not tool_meta:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tool '{tool_name}' not found"
        )
    
    return ToolInfo(
        name=tool_meta['name'],
        description=tool_meta.get('description', ''),
        parameters=tool_meta.get('parameters', {}),
        tags=tool_meta.get('tags', []),
        metadata={
            k: v for k, v in tool_meta.items()
            if k not in ['name', 'description', 'parameters', 'tags']
        }
    )

@router.post("/{tool_name}/execute", response_model=ToolExecutionResponse)
async def execute_tool_endpoint(
    tool_name: str,
    request: ToolExecutionRequest,
    current_user: Any = Depends(get_current_active_user)
):
    """
    Execute a tool with the given parameters.
    
    Args:
        tool_name: Name of the tool to execute
        request: Tool execution request containing parameters
        
    Returns:
        Tool execution result
    """
    import time
    
    tool_func = get_tool(tool_name)
    if not tool_func:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tool '{tool_name}' not found"
        )
    
    try:
        start_time = time.time()
        
        # Execute the tool with the provided parameters
        if asyncio.iscoroutinefunction(tool_func):
            result = await tool_func(**request.parameters)
        else:
            # Run synchronous functions in a thread pool
            import asyncio
            from functools import partial
            
            loop = asyncio.get_event_loop()
            func = partial(tool_func, **request.parameters)
            result = await loop.run_in_executor(None, func)
        
        execution_time = time.time() - start_time
        
        return ToolExecutionResponse(
            success=True,
            result=result,
            execution_time=execution_time
        )
        
    except Exception as e:
        return ToolExecutionResponse(
            success=False,
            result=None,
            execution_time=0,
            error=str(e)
        )

# WebSocket endpoint for real-time tool execution
@router.websocket("/{tool_name}/ws")
async def websocket_tool_execution(
    websocket: WebSocket,
    tool_name: str,
    token: str = Query(...)
):
    """
    WebSocket endpoint for real-time tool execution.
    
    Args:
        websocket: WebSocket connection
        tool_name: Name of the tool to execute
        token: Authentication token
    """
    from fastapi import WebSocket
    import json
    
    # Authenticate the WebSocket connection
    try:
        await websocket.accept()
        current_user = await get_current_active_user(token)
    except Exception as e:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return
    
    tool_func = get_tool(tool_name)
    if not tool_func:
        await websocket.close(
            code=status.WS_1003_UNSUPPORTED_DATA,
            reason=f"Tool '{tool_name}' not found"
        )
        return
    
    try:
        while True:
            # Receive parameters from the client
            data = await websocket.receive_text()
            try:
                params = json.loads(data)
                if not isinstance(params, dict):
                    raise ValueError("Parameters must be a JSON object")
            except json.JSONDecodeError:
                await websocket.send_json({
                    "type": "error",
                    "message": "Invalid JSON payload"
                })
                continue
            
            # Execute the tool
            try:
                if asyncio.iscoroutinefunction(tool_func):
                    result = await tool_func(**params)
                else:
                    # Run synchronous functions in a thread pool
                    loop = asyncio.get_event_loop()
                    func = partial(tool_func, **params)
                    result = await loop.run_in_executor(None, func)
                
                await websocket.send_json({
                    "type": "result",
                    "data": result
                })
                
            except Exception as e:
                await websocket.send_json({
                    "type": "error",
                    "message": str(e)
                })
                
    except WebSocketDisconnect:
        # Client disconnected
        pass
    except Exception as e:
        await websocket.close(code=status.WS_1011_INTERNAL_ERROR)
