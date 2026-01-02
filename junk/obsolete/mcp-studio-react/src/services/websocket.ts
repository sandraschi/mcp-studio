import { WebSocketMessage, ServerStatusUpdate, ToolExecutionUpdate } from '../types';

type MessageHandler = (message: WebSocketMessage) => void;
type ConnectionHandler = (isConnected: boolean) => void;

class WebSocketService {
  private socket: WebSocket | null = null;
  private messageHandlers: Set<MessageHandler> = new Set();
  private connectionHandlers: Set<ConnectionHandler> = new Set();
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectDelay = 3000; // 3 seconds
  private reconnectTimeout: NodeJS.Timeout | null = null;
  private url: string;

  constructor() {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const host = window.location.host;
    this.url = `${protocol}//${host}/ws`;
    this.connect();
  }

  private connect() {
    try {
      this.socket = new WebSocket(this.url);
      this.setupEventListeners();
    } catch (error) {
      console.error('WebSocket connection error:', error);
      this.handleReconnect();
    }
  }

  private setupEventListeners() {
    if (!this.socket) return;

    this.socket.onopen = () => {
      console.log('WebSocket connected');
      this.reconnectAttempts = 0;
      this.notifyConnectionChange(true);
    };

    this.socket.onmessage = (event) => {
      try {
        const message: WebSocketMessage = JSON.parse(event.data);
        this.notifyMessageHandlers(message);
      } catch (error) {
        console.error('Error parsing WebSocket message:', error);
      }
    };

    this.socket.onclose = () => {
      console.log('WebSocket disconnected');
      this.notifyConnectionChange(false);
      this.handleReconnect();
    };

    this.socket.onerror = (error) => {
      console.error('WebSocket error:', error);
      this.socket?.close();
    };
  }

  private handleReconnect() {
    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      this.reconnectAttempts++;
      const delay = this.reconnectDelay * Math.pow(1.5, this.reconnectAttempts - 1);
      
      console.log(`Attempting to reconnect (${this.reconnectAttempts}/${this.maxReconnectAttempts}) in ${delay}ms`);
      
      this.reconnectTimeout = setTimeout(() => {
        this.connect();
      }, delay);
    } else {
      console.error('Max reconnection attempts reached');
    }
  }

  private notifyMessageHandlers(message: WebSocketMessage) {
    this.messageHandlers.forEach(handler => {
      try {
        handler(message);
      } catch (error) {
        console.error('Error in message handler:', error);
      }
    });
  }

  private notifyConnectionChange(isConnected: boolean) {
    this.connectionHandlers.forEach(handler => {
      try {
        handler(isConnected);
      } catch (error) {
        console.error('Error in connection handler:', error);
      }
    });
  }

  public subscribe(handler: MessageHandler): () => void {
    this.messageHandlers.add(handler);
    return () => this.messageHandlers.delete(handler);
  }

  public onConnectionChange(handler: ConnectionHandler): () => void {
    this.connectionHandlers.add(handler);
    return () => this.connectionHandlers.delete(handler);
  }

  public sendMessage(message: any) {
    if (this.socket?.readyState === WebSocket.OPEN) {
      this.socket.send(JSON.stringify(message));
      return true;
    }
    console.error('WebSocket is not connected');
    return false;
  }

  public executeTool(serverId: string, toolName: string, parameters: Record<string, any>): string {
    const executionId = `exec_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    
    this.sendMessage({
      type: 'EXECUTE_TOOL',
      data: {
        executionId,
        serverId,
        toolName,
        parameters
      }
    });
    
    return executionId;
  }

  public dispose() {
    if (this.reconnectTimeout) {
      clearTimeout(this.reconnectTimeout);
      this.reconnectTimeout = null;
    }
    
    this.socket?.close();
    this.messageHandlers.clear();
    this.connectionHandlers.clear();
  }
}

export const webSocketService = new WebSocketService();

// React hook for WebSocket
import { useEffect, useState } from 'react';

export const useWebSocket = () => {
  const [isConnected, setIsConnected] = useState(webSocketService.socket?.readyState === WebSocket.OPEN);
  const [lastMessage, setLastMessage] = useState<WebSocketMessage | null>(null);

  useEffect(() => {
    const handleMessage = (message: WebSocketMessage) => {
      setLastMessage(message);
    };

    const handleConnectionChange = (connected: boolean) => {
      setIsConnected(connected);
    };

    const unsubscribeMessage = webSocketService.subscribe(handleMessage);
    const unsubscribeConnection = webSocketService.onConnectionChange(handleConnectionChange);

    return () => {
      unsubscribeMessage();
      unsubscribeConnection();
    };
  }, []);

  return {
    isConnected,
    lastMessage,
    sendMessage: webSocketService.sendMessage.bind(webSocketService),
    executeTool: webSocketService.executeTool.bind(webSocketService)
  };
};
