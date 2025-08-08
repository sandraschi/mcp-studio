"""
WebSocket endpoints for MCP Studio

This module provides WebSocket endpoints for real-time communication.
"""
import uuid
from typing import Optional

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, status
from fastapi.responses import JSONResponse

from ....app.core.websocket import manager, websocket_endpoint
from ....app.core.security import get_current_user_ws
from ....app.core.logging import logger

router = APIRouter()

@router.websocket("/ws/{client_id}")
async def websocket_connection(
    websocket: WebSocket,
    client_id: str,
    token: Optional[str] = None
):
    """WebSocket endpoint for real-time communication.
    
    Args:
        websocket: The WebSocket connection
        client_id: Unique client identifier
        token: Optional authentication token
    """
    # Authenticate the WebSocket connection if token is provided
    if token:
        try:
            # This will raise an exception if the token is invalid
            await get_current_user_ws(token)
        except Exception as e:
            logger.warning(f"WebSocket authentication failed: {e}")
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return
    
    # Generate a unique client ID if not provided
    if not client_id or client_id == "new":
        client_id = f"client_{uuid.uuid4().hex[:8]}"
    
    # Handle the WebSocket connection
    await websocket_endpoint(websocket, client_id)

@router.websocket("/tool/execute/{tool_name}")
async def execute_tool_ws(
    websocket: WebSocket,
    tool_name: str,
    token: Optional[str] = None
):
    """WebSocket endpoint for executing tools with real-time updates.
    
    Args:
        websocket: The WebSocket connection
        tool_name: Name of the tool to execute
        token: Optional authentication token
    """
    from ....app.services.tool_service import ToolService
    from ....app.core.websocket import ToolExecutionMessage
    import json
    import asyncio
    
    # Authenticate the WebSocket connection if token is provided
    current_user = None
    if token:
        try:
            current_user = await get_current_user_ws(token)
        except Exception as e:
            logger.warning(f"Tool execution authentication failed: {e}")
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return
    
    await websocket.accept()
    
    try:
        # Get tool service
        tool_service = ToolService()
        
        # Get the tool
        tool = tool_service.get_tool(tool_name)
        if not tool:
            await websocket.send_json({
                "type": "error",
                "error": f"Tool not found: {tool_name}"
            })
            await websocket.close()
            return
        
        # Wait for execution parameters
        data = await websocket.receive_text()
        try:
            params = json.loads(data)
            if not isinstance(params, dict):
                raise ValueError("Parameters must be a JSON object")
        except json.JSONDecodeError:
            await websocket.send_json({
                "type": "error",
                "error": "Invalid JSON parameters"
            })
            await websocket.close()
            return
        
        # Create a progress callback
        async def progress_callback(progress: float, message: str = None):
            """Send progress updates to the client."""
            await websocket.send_json({
                "type": "progress",
                "progress": progress,
                "message": message or "",
                "status": "running"
            })
        
        # Execute the tool
        try:
            # Send initial status
            await websocket.send_json({
                "type": "status",
                "status": "executing",
                "tool": tool_name,
                "message": f"Starting execution of {tool_name}"
            })
            
            # Execute the tool with progress updates
            result = await tool_service.execute_tool(
                tool_name=tool_name,
                parameters=params,
                user=current_user,
                progress_callback=progress_callback
            )
            
            # Send the result
            await websocket.send_json({
                "type": "result",
                "status": "completed",
                "tool": tool_name,
                "result": result
            })
            
        except Exception as e:
            logger.error(f"Error executing tool {tool_name}: {e}", exc_info=True)
            await websocket.send_json({
                "type": "error",
                "status": "failed",
                "tool": tool_name,
                "error": str(e)
            })
        
    except WebSocketDisconnect:
        logger.info(f"Client disconnected during tool execution: {tool_name}")
    except Exception as e:
        logger.error(f"WebSocket error during tool execution: {e}", exc_info=True)
        try:
            await websocket.send_json({
                "type": "error",
                "status": "failed",
                "error": f"Internal server error: {str(e)}"
            })
        except:
            pass
    finally:
        try:
            await websocket.close()
        except:
            pass

# Add WebSocket endpoints to the router
router.websocket_route("/ws/{client_id}")(websocket_connection)
router.websocket_route("/tool/execute/{tool_name}")(execute_tool_ws)
