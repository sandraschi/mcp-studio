"""
WebSocket Manager for MCP Studio

Handles WebSocket connections for real-time communication with the frontend.
"""
import asyncio
import json
import logging
from typing import Dict, List, Optional, Set, Any
from uuid import UUID, uuid4

from fastapi import WebSocket, WebSocketDisconnect
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

class ConnectionManager:
    """Manages WebSocket connections and message broadcasting."""
    
    def __init__(self):
        """Initialize the connection manager."""
        self.active_connections: Dict[str, WebSocket] = {}
        self.connection_subscriptions: Dict[str, Set[str]] = {}
        self.channel_subscribers: Dict[str, Set[str]] = {}
    
    async def connect(self, websocket: WebSocket, client_id: str):
        """Accept a new WebSocket connection.
        
        Args:
            websocket: The WebSocket connection
            client_id: Unique identifier for the client
        """
        await websocket.accept()
        self.active_connections[client_id] = websocket
        self.connection_subscriptions[client_id] = set()
        logger.info(f"Client connected: {client_id}")
    
    def disconnect(self, client_id: str):
        """Remove a WebSocket connection.
        
        Args:
            client_id: The client ID to disconnect
        """
        # Remove from all channels
        if client_id in self.connection_subscriptions:
            for channel in self.connection_subscriptions[client_id]:
                self.unsubscribe(channel, client_id)
            del self.connection_subscriptions[client_id]
        
        # Remove the connection
        if client_id in self.active_connections:
            del self.active_connections[client_id]
        
        logger.info(f"Client disconnected: {client_id}")
    
    async def send_personal_message(self, message: str, client_id: str):
        """Send a message to a specific client.
        
        Args:
            message: The message to send
            client_id: The target client ID
        """
        if client_id in self.active_connections:
            try:
                await self.active_connections[client_id].send_text(message)
            except Exception as e:
                logger.error(f"Error sending message to {client_id}: {e}")
                self.disconnect(client_id)
    
    async def broadcast(self, message: str, channel: str):
        """Broadcast a message to all clients in a channel.
        
        Args:
            message: The message to broadcast
            channel: The channel to broadcast to
        """
        if channel in self.channel_subscribers:
            for client_id in list(self.channel_subscribers[channel]):
                await self.send_personal_message(message, client_id)
    
    def subscribe(self, channel: str, client_id: str):
        """Subscribe a client to a channel.
        
        Args:
            channel: The channel to subscribe to
            client_id: The client ID to subscribe
        """
        if client_id not in self.active_connections:
            return
            
        if channel not in self.channel_subscribers:
            self.channel_subscribers[channel] = set()
        
        self.channel_subscribers[channel].add(client_id)
        self.connection_subscriptions[client_id].add(channel)
        logger.info(f"Client {client_id} subscribed to {channel}")
    
    def unsubscribe(self, channel: str, client_id: str):
        """Unsubscribe a client from a channel.
        
        Args:
            channel: The channel to unsubscribe from
            client_id: The client ID to unsubscribe
        """
        if channel in self.channel_subscribers and client_id in self.channel_subscribers[channel]:
            self.channel_subscribers[channel].remove(client_id)
            
        if client_id in self.connection_subscriptions and channel in self.connection_subscriptions[client_id]:
            self.connection_subscriptions[client_id].remove(channel)
            
        logger.info(f"Client {client_id} unsubscribed from {channel}")

class WebSocketMessage(BaseModel):
    """Base WebSocket message model."""
    type: str
    data: Optional[Dict[str, Any]] = None
    request_id: Optional[str] = None
    error: Optional[str] = None

class ToolExecutionMessage(WebSocketMessage):
    """Tool execution message model."""
    tool_name: Optional[str] = None
    parameters: Optional[Dict[str, Any]] = None
    progress: Optional[float] = None
    status: Optional[str] = None  # 'pending', 'running', 'completed', 'failed'
    result: Optional[Any] = None

class ProgressUpdateMessage(WebSocketMessage):
    """Progress update message model."""
    progress: float
    message: Optional[str] = None
    status: str

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
