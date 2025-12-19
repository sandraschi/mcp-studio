"""
WebSocket Manager for MCP Studio

Handles WebSocket connections for real-time communication with the frontend.
"""
import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Set, Any, Callable, Awaitable, Union, Literal
from uuid import UUID, uuid4
from enum import Enum
from dataclasses import dataclass

from fastapi import WebSocket, WebSocketDisconnect
from pydantic import BaseModel, ConfigDict, Field, field_validator

logger = logging.getLogger(__name__)

class ConnectionType(str, Enum):
    """Types of WebSocket connections."""
    CLIENT = "client"
    WORKER = "worker"
    MONITOR = "monitor"

@dataclass
class ConnectionInfo:
    """Information about a WebSocket connection."""
    websocket: WebSocket
    connection_type: ConnectionType
    authenticated: bool = False
    user_id: Optional[str] = None
    roles: List[str] = None
    subscriptions: Set[str] = None
    
    def __post_init__(self):
        if self.roles is None:
            self.roles = []
        if self.subscriptions is None:
            self.subscriptions = set()

class ConnectionManager:
    """Manages WebSocket connections and message broadcasting."""
    
    def __init__(self):
        """Initialize the connection manager."""
        self.connections: Dict[str, ConnectionInfo] = {}
        self.channel_subscribers: Dict[str, Set[str]] = {}
        self.execution_connections: Dict[str, Set[str]] = {}  # execution_id -> set of client_ids
    
    async def connect(
        self, 
        websocket: WebSocket, 
        client_id: str, 
        connection_type: ConnectionType = ConnectionType.CLIENT,
        user_id: Optional[str] = None,
        roles: Optional[List[str]] = None
    ) -> str:
        """Accept a new WebSocket connection.
        
        Args:
            websocket: The WebSocket connection
            client_id: Unique identifier for the connection
            connection_type: Type of connection (client, worker, monitor)
            user_id: Optional user ID for authenticated connections
            roles: Optional list of user roles
            
        Returns:
            str: The assigned connection ID
        """
        if roles is None:
            roles = []
            
        # Ensure client_id is unique
        if client_id in self.connections:
            client_id = f"{client_id}_{uuid4().hex[:4]}"
            
        await websocket.accept()
        self.connections[client_id] = ConnectionInfo(
            websocket=websocket,
            connection_type=connection_type,
            authenticated=user_id is not None,
            user_id=user_id,
            roles=roles,
            subscriptions=set()
        )
        
        logger.info(f"{connection_type.value.capitalize()} connected: {client_id}" + 
                   (f" (user: {user_id})" if user_id else ""))
        return client_id
    
    def disconnect(self, client_id: str):
        """Remove a WebSocket connection.
        
        Args:
            client_id: The client ID to disconnect
        """
        if client_id not in self.connections:
            return
            
        conn = self.connections[client_id]
        
        # Remove from all channels
        for channel in list(conn.subscriptions):
            self.unsubscribe(channel, client_id)
            
        # Remove from execution tracking
        for execution_id, subscribers in list(self.execution_connections.items()):
            subscribers.discard(client_id)
            if not subscribers:  # No more subscribers
                del self.execution_connections[execution_id]
        
        # Remove the connection
        del self.connections[client_id]
        
        logger.info(f"{conn.connection_type.value.capitalize()} disconnected: {client_id}")
    
    async def send_message(self, client_id: str, message: Union[str, dict], message_type: str = "message"):
        """Send a message to a specific client.
        
        Args:
            client_id: The target client ID
            message: The message to send (string or dict)
            message_type: Type of message (message, error, warning, etc.)
            
        Returns:
            bool: True if message was sent successfully, False otherwise
        """
        if client_id not in self.connections:
            return False
            
        try:
            if isinstance(message, dict):
                message_data = message
                if "type" not in message_data:
                    message_data["type"] = message_type
            else:
                message_data = {"type": message_type, "message": str(message)}
                
            await self.connections[client_id].websocket.send_json(message_data)
            return True
        except Exception as e:
            logger.error(f"Error sending message to {client_id}: {e}")
            self.disconnect(client_id)
            return False
    
    async def broadcast(
        self, 
        channel: str, 
        message: Union[str, dict], 
        message_type: str = "broadcast"
    ) -> int:
        """Broadcast a message to all clients in a channel.
        
        Args:
            channel: The channel to broadcast to
            message: The message to broadcast (string or dict)
            message_type: Type of message
            
        Returns:
            int: Number of clients that received the message
        """
        if channel not in self.channel_subscribers:
            return 0
            
        sent_count = 0
        for client_id in list(self.channel_subscribers[channel]):
            if await self.send_message(client_id, message, message_type):
                sent_count += 1
                
        return sent_count
        
    async def broadcast_execution_update(
        self, 
        execution_id: str, 
        message: Union[str, dict],
        message_type: str = "execution_update"
    ) -> int:
        """Broadcast an execution update to all subscribed clients.
        
        Args:
            execution_id: The execution ID to broadcast to
            message: The message to broadcast (string or dict)
            message_type: Type of message
            
        Returns:
            int: Number of clients that received the message
        """
        if execution_id not in self.execution_connections:
            return 0
            
        sent_count = 0
        for client_id in list(self.execution_connections[execution_id]):
            if await self.send_message(client_id, message, message_type):
                sent_count += 1
                
        return sent_count

    def subscribe(self, channel: str, client_id: str) -> bool:
        """Subscribe a client to a channel.
        
        Args:
            channel: The channel to subscribe to
            client_id: The client ID to subscribe
            
        Returns:
            bool: True if subscribed successfully, False otherwise
        """
        if client_id not in self.connections:
            return False
            
        if not channel:
            return False
            
        if channel not in self.channel_subscribers:
            self.channel_subscribers[channel] = set()
        
        self.channel_subscribers[channel].add(client_id)
        self.connections[client_id].subscriptions.add(channel)
        logger.debug(f"Client {client_id} subscribed to channel: {channel}")
        return True
        
    def subscribe_to_execution(self, execution_id: str, client_id: str) -> bool:
        """Subscribe a client to execution updates.
        
        Args:
            execution_id: The execution ID to subscribe to
            client_id: The client ID to subscribe
            
        Returns:
            bool: True if subscribed successfully, False otherwise
        """
        if client_id not in self.connections:
            return False
            
        if not execution_id:
            return False
            
        if execution_id not in self.execution_connections:
            self.execution_connections[execution_id] = set()
            
        self.execution_connections[execution_id].add(client_id)
        logger.debug(f"Client {client_id} subscribed to execution: {execution_id}")
        return True

    def unsubscribe(self, channel: str, client_id: str) -> bool:
        """Unsubscribe a client from a channel.
        
        Args:
            channel: The channel to unsubscribe from
            client_id: The client ID to unsubscribe
            
        Returns:
            bool: True if unsubscribed successfully, False otherwise
        """
        if client_id not in self.connections:
            return False
            
        if channel in self.connections[client_id].subscriptions:
            self.connections[client_id].subscriptions.remove(channel)
            
        if channel in self.channel_subscribers:
            self.channel_subscribers[channel].discard(client_id)
            if not self.channel_subscribers[channel]:  # No more subscribers
                del self.channel_subscribers[channel]
                
        logger.debug(f"Client {client_id} unsubscribed from channel: {channel}")
        return True
        
    def unsubscribe_from_execution(self, execution_id: str, client_id: str) -> bool:
        """Unsubscribe a client from execution updates.
        
        Args:
            execution_id: The execution ID to unsubscribe from
            client_id: The client ID to unsubscribe
            
        Returns:
            bool: True if unsubscribed successfully, False otherwise
        """
        if execution_id in self.execution_connections:
            self.execution_connections[execution_id].discard(client_id)
            if not self.execution_connections[execution_id]:  # No more subscribers
                del self.execution_connections[execution_id]
                
        logger.debug(f"Client {client_id} unsubscribed from execution: {execution_id}")
        return True

class WebSocketMessage(BaseModel):
    """Base WebSocket message model."""
    type: str = Field(..., description="Message type")
    timestamp: float = Field(default_factory=lambda: datetime.utcnow().timestamp())
    request_id: Optional[str] = Field(
        None, 
        description="Optional request ID for request/response correlation"
    )
    data: Optional[Dict[str, Any]] = Field(
        None, 
        description="Message payload data"
    )
    error: Optional[Dict[str, Any]] = Field(
        None, 
        description="Error information if applicable"
    )
    
    model_config = ConfigDict()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert message to dictionary."""
        return self.dict(exclude_unset=True, exclude_none=True)
    
    def to_json(self) -> str:
        """Convert message to JSON string."""
        return self.json(exclude_unset=True, exclude_none=True)


class ToolExecutionStatus(str, Enum):
    """Status of a tool execution."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    

class ToolExecutionMessage(WebSocketMessage):
    """Tool execution message model."""
    type: Literal["tool_execution"] = "tool_execution"
    execution_id: str = Field(..., description="Unique ID for this execution")
    tool_name: str = Field(..., description="Name of the tool being executed")
    status: ToolExecutionStatus = Field(..., description="Current status of the execution")
    progress: float = Field(0.0, ge=0.0, le=1.0, description="Progress from 0.0 to 1.0")
    parameters: Optional[Dict[str, Any]] = Field(
        None, 
        description="Input parameters for the tool"
    )
    result: Optional[Any] = Field(
        None,
        description="Execution result (only present when status is COMPLETED)"
    )
    error: Optional[Dict[str, Any]] = Field(
        None,
        description="Error details (only present when status is FAILED or CANCELLED)"
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata about the execution"
    )
    
    @field_validator('progress')
    @classmethod
    def validate_progress(cls, v):
        """Ensure progress is between 0 and 1."""
        return max(0.0, min(1.0, v))
    
    @classmethod
    def create(
        cls,
        execution_id: str,
        tool_name: str,
        status: ToolExecutionStatus,
        progress: float = 0.0,
        parameters: Optional[Dict[str, Any]] = None,
        result: Optional[Any] = None,
        error: Optional[Union[str, Exception, Dict[str, Any]]] = None,
        request_id: Optional[str] = None,
        **metadata
    ) -> 'ToolExecutionMessage':
        """Create a new tool execution message."""
        error_dict = None
        if error is not None:
            if isinstance(error, dict):
                error_dict = error
            elif isinstance(error, Exception):
                error_dict = {
                    "type": error.__class__.__name__,
                    "message": str(error),
                    "details": getattr(error, "details", None)
                }
            else:
                error_dict = {"message": str(error)}
                
        return cls(
            execution_id=execution_id,
            tool_name=tool_name,
            status=status,
            progress=progress,
            parameters=parameters or {},
            result=result,
            error=error_dict,
            request_id=request_id,
            metadata=metadata
        )


class SystemMessage(WebSocketMessage):
    """System-level WebSocket messages."""
    type: Literal["system"] = "system"
    code: str = Field(..., description="System message code")
    message: str = Field(..., description="Human-readable message")
    
    @classmethod
    def info(cls, message: str, **kwargs) -> 'SystemMessage':
        """Create an info message."""
        return cls(code="info", message=message, **kwargs)
    
    @classmethod
    def warning(cls, message: str, **kwargs) -> 'SystemMessage':
        """Create a warning message."""
        return cls(code="warning", message=message, **kwargs)
    
    @classmethod
    def error(cls, message: str, error: Optional[Exception] = None, **kwargs) -> 'SystemMessage':
        """Create an error message."""
        error_data = {"message": str(message)}
        if error is not None:
            error_data["type"] = error.__class__.__name__
            error_data["details"] = getattr(error, "details", str(error))
        return cls(code="error", message=message, error=error_data, **kwargs)


class ProgressUpdateMessage(WebSocketMessage):
    """Progress update message model."""
    type: Literal["progress_update"] = "progress_update"
    progress: float = Field(..., ge=0.0, le=1.0, description="Progress from 0.0 to 1.0")
    message: Optional[str] = Field(None, description="Optional progress message")
    status: str = Field("processing", description="Current status")
    total: Optional[float] = Field(None, description="Total work units")
    current: Optional[float] = Field(None, description="Current work units completed")
    
    @field_validator('progress')
    @classmethod
    def validate_progress(cls, v):
        """Ensure progress is between 0 and 1."""
        return max(0.0, min(1.0, v))

# Global WebSocket manager instance
manager = ConnectionManager()

async def websocket_endpoint(websocket: WebSocket, client_id: str):
    """Handle WebSocket connections.
    
    Args:
        websocket: The WebSocket connection
        client_id: The client ID
    """
    await manager.connect(websocket, client_id)
    
    try:
        while True:
            # Wait for messages from the client
            data = await websocket.receive_text()
            
            try:
                message = json.loads(data)
                message_type = message.get('type')
                
                if message_type == 'subscribe':
                    # Handle channel subscription
                    channel = message.get('channel')
                    if channel:
                        manager.subscribe(channel, client_id)
                        await manager.send_personal_message(
                            json.dumps({
                                'type': 'subscription',
                                'channel': channel,
                                'status': 'subscribed'
                            }),
                            client_id
                        )
                
                elif message_type == 'unsubscribe':
                    # Handle channel unsubscription
                    channel = message.get('channel')
                    if channel:
                        manager.unsubscribe(channel, client_id)
                        await manager.send_personal_message(
                            json.dumps({
                                'type': 'subscription',
                                'channel': channel,
                                'status': 'unsubscribed'
                            }),
                            client_id
                        )
                
                elif message_type == 'ping':
                    # Respond to ping
                    await manager.send_personal_message(
                        json.dumps({'type': 'pong'}),
                        client_id
                    )
                
                # Add more message types as needed
                
            except json.JSONDecodeError:
                await manager.send_personal_message(
                    json.dumps({
                        'type': 'error',
                        'error': 'Invalid JSON message'
                    }),
                    client_id
                )
            except Exception as e:
                logger.error(f"Error processing WebSocket message: {e}")
                await manager.send_personal_message(
                    json.dumps({
                        'type': 'error',
                        'error': str(e)
                    }),
                    client_id
                )
    
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected: {client_id}")
    except Exception as e:
        logger.error(f"WebSocket error for {client_id}: {e}")
    finally:
        manager.disconnect(client_id)
