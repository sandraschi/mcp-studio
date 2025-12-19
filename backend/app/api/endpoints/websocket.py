"""
WebSocket endpoints for MCP Studio

This module provides WebSocket endpoints for real-time communication and tool execution.
"""
import asyncio
import json
import uuid
from typing import Any, Dict, List, Optional, Union

from fastapi import (
    APIRouter, 
    WebSocket, 
    WebSocketDisconnect, 
    Depends, 
    status,
    HTTPException
)
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, ValidationError

from ....app.core.websocket import (
    manager, 
    ToolExecutionMessage,
    ToolExecutionStatus,
    SystemMessage,
    ConnectionType
)
from ....app.core.security import get_current_user_ws, get_current_user
from ....app.services.tool_service import tool_service, ToolExecutionError
from ....app.models.user import User
from ....app.core.logging import logger

router = APIRouter()

class ToolExecutionRequest(BaseModel):
    """Request model for tool execution."""
    execution_id: Optional[str] = Field(
        None,
        description="Optional execution ID (will be generated if not provided)"
    )
    parameters: Dict[str, Any] = Field(
        default_factory=dict,
        description="Parameters for the tool"
    )
    subscribe: bool = Field(
        True,
        description="Whether to subscribe to execution updates"
    )

class WebSocketMessage(BaseModel):
    """Base WebSocket message model."""
    type: str = Field(..., description="Message type")
    data: Optional[Dict[str, Any]] = Field(None, description="Message data")
    request_id: Optional[str] = Field(None, description="Request ID for correlation")

async def authenticate_websocket(
    websocket: WebSocket,
    token: Optional[str] = None
) -> Optional[User]:
    """Authenticate WebSocket connection.
    
    Args:
        websocket: The WebSocket connection
        token: Optional authentication token
        
    Returns:
        User object if authenticated, None otherwise
    """
    if not token:
        return None
        
    try:
        return await get_current_user_ws(token)
    except HTTPException as e:
        logger.warning(f"WebSocket authentication failed: {e.detail}")
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return None
    except Exception as e:
        logger.error(f"Unexpected error during WebSocket auth: {str(e)}")
        await websocket.close(code=status.WS_1011_INTERNAL_ERROR)
        return None

@router.websocket("/ws/{client_id}")
async def websocket_connection(
    websocket: WebSocket,
    client_id: str,
    token: Optional[str] = None
):
    """WebSocket endpoint for real-time communication and tool execution.
    
    Handles:
    - Connection management
    - Authentication
    - Message routing
    - Tool execution
    - Progress updates
    
    Args:
        websocket: The WebSocket connection
        client_id: Unique client identifier
        token: Optional authentication token for protected endpoints
    """
    # Accept the WebSocket connection
    await websocket.accept()
    
    # Authenticate the user
    user = await authenticate_websocket(websocket, token)
    
    # Generate a unique client ID if not provided
    if not client_id or client_id == "new":
        client_id = f"client_{uuid.uuid4().hex[:8]}"
    
    # Register the connection
    connection_id = await manager.connect(
        websocket=websocket,
        client_id=client_id,
        connection_type=ConnectionType.CLIENT,
        user_id=user.id if user else None,
        roles=user.roles if user else []
    )
    
    try:
        # Main message handling loop
        while True:
            try:
                # Wait for a message from the client
                data = await websocket.receive_text()
                
                try:
                    message = json.loads(data)
                    message_type = message.get('type')
                    
                    # Route the message based on its type
                    if message_type == 'execute_tool':
                        await _handle_tool_execution(
                            websocket=websocket,
                            message=message,
                            user=user,
                            client_id=connection_id
                        )
                    elif message_type == 'subscribe_execution':
                        await _handle_execution_subscription(
                            websocket=websocket,
                            message=message,
                            client_id=connection_id
                        )
                    elif message_type == 'unsubscribe_execution':
                        await _handle_execution_unsubscription(
                            message=message,
                            client_id=connection_id
                        )
                    else:
                        logger.warning(f"Unknown message type: {message_type}")
                        
                except json.JSONDecodeError:
                    await manager.send_message(
                        connection_id,
                        SystemMessage.error("Invalid JSON received").dict(),
                        "error"
                    )
                except ValidationError as e:
                    await manager.send_message(
                        connection_id,
                        SystemMessage.error("Invalid message format", e).dict(),
                        "error"
                    )
                except Exception as e:
                    logger.error(f"Error processing message: {str(e)}", exc_info=True)
                    await manager.send_message(
                        connection_id,
                        SystemMessage.error("Internal server error").dict(),
                        "error"
                    )
                    
            except WebSocketDisconnect:
                logger.info(f"Client {client_id} disconnected")
                break
            except Exception as e:
                logger.error(f"WebSocket error: {str(e)}", exc_info=True)
                break
                
    except Exception as e:
        logger.error(f"WebSocket connection error: {str(e)}", exc_info=True)
    finally:
        # Clean up the connection
        manager.disconnect(connection_id)

async def _handle_tool_execution(
    websocket: WebSocket,
    message: Dict[str, Any],
    user: Optional[User],
    client_id: str
) -> None:
    """Handle tool execution request."""
    try:
        # Parse and validate the request
        request = ToolExecutionRequest(**message.get('data', {}))
        tool_name = message.get('tool_name')
        
        if not tool_name:
            raise ValueError("Tool name is required")
            
        # Generate an execution ID if not provided
        execution_id = request.execution_id or f"exec_{uuid.uuid4().hex[:8]}"
        
        # Subscribe to execution updates if requested
        if request.subscribe:
            manager.subscribe_to_execution(execution_id, client_id)
        
        # Start the tool execution in the background
        asyncio.create_task(_execute_tool_background(
            tool_name=tool_name,
            parameters=request.parameters,
            execution_id=execution_id,
            user=user,
            client_id=client_id
        ))
        
        # Send acknowledgment
        await manager.send_message(
            client_id,
            {
                "type": "execution_started",
                "execution_id": execution_id,
                "tool_name": tool_name,
                "status": "pending"
            },
            "execution_update"
        )
        
    except ValidationError as e:
        await manager.send_message(
            client_id,
            SystemMessage.error("Invalid request format", e).dict(),
            "error"
        )
    except Exception as e:
        logger.error(f"Tool execution error: {str(e)}", exc_info=True)
        await manager.send_message(
            client_id,
            SystemMessage.error(f"Failed to start tool execution: {str(e)}").dict(),
            "error"
        )

async def _execute_tool_background(
    tool_name: str,
    parameters: Dict[str, Any],
    execution_id: str,
    user: Optional[User],
    client_id: str
) -> None:
    """Execute a tool in the background and send updates via WebSocket."""
    try:
        # Execute the tool
        result = await tool_service.execute_tool(
            tool_name=tool_name,
            parameters=parameters,
            user=user,
            client_id=client_id,
            execution_id=execution_id
        )
        
        # Send completion message
        await manager.broadcast_execution_update(
            execution_id,
            {
                "type": "execution_completed",
                "execution_id": execution_id,
                "tool_name": tool_name,
                "status": "completed",
                "result": result
            },
            "execution_update"
        )
        
    except asyncio.CancelledError:
        # Handle cancellation
        await manager.broadcast_execution_update(
            execution_id,
            {
                "type": "execution_cancelled",
                "execution_id": execution_id,
                "tool_name": tool_name,
                "status": "cancelled"
            },
            "execution_update"
        )
    except Exception as e:
        logger.error(f"Tool execution failed: {str(e)}", exc_info=True)
        await manager.broadcast_execution_update(
            execution_id,
            {
                "type": "execution_failed",
                "execution_id": execution_id,
                "tool_name": tool_name,
                "status": "failed",
                "error": str(e)
            },
            "execution_update"
        )

async def _handle_execution_subscription(
    websocket: WebSocket,
    message: Dict[str, Any],
    client_id: str
) -> None:
    """Handle subscription to execution updates."""
    try:
        execution_id = message.get('data', {}).get('execution_id')
        if not execution_id:
            raise ValueError("execution_id is required")
            
        if manager.subscribe_to_execution(execution_id, client_id):
            await manager.send_message(
                client_id,
                {
                    "type": "subscription_success",
                    "execution_id": execution_id,
                    "message": f"Subscribed to updates for execution {execution_id}"
                },
                "subscription_update"
            )
        else:
            await manager.send_message(
                client_id,
                {
                    "type": "subscription_error",
                    "execution_id": execution_id,
                    "error": "Failed to subscribe to execution updates"
                },
                "error"
            )
            
    except Exception as e:
        logger.error(f"Subscription error: {str(e)}", exc_info=True)
        await manager.send_message(
            client_id,
            SystemMessage.error("Failed to subscribe to execution").dict(),
            "error"
        )

async def _handle_execution_unsubscription(
    message: Dict[str, Any],
    client_id: str
) -> None:
    """Handle unsubscription from execution updates."""
    try:
        execution_id = message.get('data', {}).get('execution_id')
        if not execution_id:
            raise ValueError("execution_id is required")
            
        if manager.unsubscribe_from_execution(execution_id, client_id):
            await manager.send_message(
                client_id,
                {
                    "type": "unsubscription_success",
                    "execution_id": execution_id,
                    "message": f"Unsubscribed from updates for execution {execution_id}"
                },
                "subscription_update"
            )
        else:
            await manager.send_message(
                client_id,
                {
                    "type": "unsubscription_error",
                    "execution_id": execution_id,
                    "error": "Not subscribed to this execution"
                },
                "error"
            )
            
    except Exception as e:
        logger.error(f"Unsubscription error: {str(e)}", exc_info=True)
        await manager.send_message(
            client_id,
            SystemMessage.error("Failed to unsubscribe from execution").dict(),
            "error"
        )

@router.websocket("/tool/execute/{tool_name}")
async def execute_tool_ws(
    websocket: WebSocket,
    tool_name: str,
    token: Optional[str] = None
):
    """Legacy WebSocket endpoint for executing tools with real-time progress.
    
    This is maintained for backward compatibility. New clients should use the 
    general-purpose WebSocket endpoint at /ws/{client_id} instead.
    
    Args:
        websocket: The WebSocket connection
        tool_name: Name of the tool to execute
        token: Optional authentication token
    """
    # Accept the WebSocket connection
    await websocket.accept()
    
    # Authenticate the user if required
    user = None
    if token:
        try:
            user = await get_current_user_ws(token)
        except Exception as e:
            logger.warning(f"WebSocket authentication failed: {e}")
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return
    
    # Generate a unique client ID for this legacy connection
    client_id = f"legacy_{uuid.uuid4().hex[:6]}"
    
    try:
        # Register the connection
        connection_id = await manager.connect(
            websocket=websocket,
            client_id=client_id,
            connection_type=ConnectionType.LEGACY,
            user_id=user.id if user else None,
            roles=user.roles if user else []
        )
        
        # Generate an execution ID
        execution_id = f"exec_{uuid.uuid4().hex[:8]}"
        
        # Send initial message
        await manager.send_message(
            connection_id,
            {
                "type": "execution_started",
                "execution_id": execution_id,
                "tool_name": tool_name,
                "status": "pending"
            },
            "execution_update"
        )
        
        # Subscribe to execution updates
        manager.subscribe_to_execution(execution_id, connection_id)
        
        # Main execution loop
        while True:
            try:
                # Wait for parameters from the client
                data = await websocket.receive_text()
                
                try:
                    # Parse the parameters
                    params = json.loads(data)
                    
                    # Execute the tool in the background
                    asyncio.create_task(_execute_tool_background(
                        tool_name=tool_name,
                        parameters=params,
                        execution_id=execution_id,
                        user=user,
                        client_id=connection_id
                    ))
                    
                except json.JSONDecodeError:
                    await manager.send_message(
                        connection_id,
                        SystemMessage.error("Invalid JSON").dict(),
                        "error"
                    )
                except Exception as e:
                    logger.error(f"Tool execution setup error: {e}", exc_info=True)
                    await manager.send_message(
                        connection_id,
                        SystemMessage.error(f"Failed to start tool: {str(e)}").dict(),
                        "error"
                    )
                    
            except WebSocketDisconnect:
                logger.info(f"Legacy client disconnected during execution {execution_id}")
                break
                
    except Exception as e:
        logger.error(f"Legacy WebSocket error: {e}", exc_info=True)
        try:
            if 'connection_id' in locals():
                await manager.send_message(
                    connection_id,
                    SystemMessage.error(f"Internal server error: {str(e)}").dict(),
                    "error"
                )
        except:
            pass
    finally:
        # Clean up the connection
        if 'connection_id' in locals():
            manager.disconnect(connection_id)

# Add WebSocket endpoints to the router
router.websocket_route("/ws/{client_id}")(websocket_connection)
router.websocket_route("/tool/execute/{tool_name}")(execute_tool_ws)
