import React, { createContext, useContext, useEffect, useRef, ReactNode, useCallback, useState } from 'react';
import { webSocketService, WebSocketService } from '../services/websocket/websocket.service';
import { WebSocketMessage, ServerStatusUpdate, ToolExecutionUpdate, Server } from '../types';

type WebSocketContextType = {
  // Connection state
  isConnected: boolean;
  isConnecting: boolean;
  error: Error | null;
  connect: (url: string) => Promise<boolean>;
  disconnect: () => void;
  
  // Message handling
  send: <T = any>(message: any, timeout?: number) => Promise<T>;
  
  // Server operations
  startServer: (serverId: string) => Promise<Server>;
  stopServer: (serverId: string) => Promise<Server>;
  
  // Tool execution
  executeTool: (executionRequest: any) => Promise<ToolExecutionUpdate>;
  
  // Subscription methods
  subscribeToServerStatus: (
    serverId: string, 
    callback: (update: ServerStatusUpdate) => void
  ) => () => void;
  
  subscribeToToolExecution: (
    executionId: string, 
    callback: (update: ToolExecutionUpdate) => void
  ) => () => void;
  
  // Raw WebSocket access (for advanced use cases)
  subscribe: (event: 'open' | 'close' | 'error' | 'message', handler: (data: any) => void) => () => void;
};

const WebSocketContext = createContext<WebSocketContextType | undefined>(undefined);

interface WebSocketProviderProps {
  children: ReactNode;
  webSocketService?: WebSocketService;
  autoConnect?: boolean;
  webSocketUrl?: string;
}

export const WebSocketProvider: React.FC<WebSocketProviderProps> = ({
  children,
  webSocketService: wsService = webSocketService,
  autoConnect = true,
  webSocketUrl = process.env.REACT_APP_WS_URL || `ws://${window.location.host}/ws`
}) => {
  const [isConnected, setIsConnected] = useState(false);
  const [isConnecting, setIsConnecting] = useState(false);
  const [error, setError] = useState<Error | null>(null);
  const messageHandlers = useRef<Map<string, Set<Function>>>(new Map());

  // Initialize WebSocket connection
  useEffect(() => {
    if (autoConnect) {
      connect(webSocketUrl).catch(console.error);
    }

    return () => {
      if (wsService) {
        wsService.disconnect();
      }
    };
  }, [autoConnect, webSocketUrl, wsService, connect]);

  // Set up event listeners
  useEffect(() => {
    if (!wsService) return;

    const onOpen = () => {
      setIsConnected(true);
      setError(null);
    };

    const onClose = () => {
      setIsConnected(false);
    };

    const onError = (error: Error) => {
      setError(error);
    };

    const onMessage = (message: WebSocketMessage) => {
      const handlers = messageHandlers.current.get('message') || [];
      handlers.forEach(handler => {
        try {
          handler(message);
        } catch (err) {
          console.error('Error in WebSocket message handler:', err);
        }
      });
    };

    const unsubOpen = wsService.on('open', onOpen);
    const unsubClose = wsService.on('close', onClose);
    const unsubError = wsService.on('error', onError);
    const unsubMessage = wsService.on('message', onMessage);

    return () => {
      unsubOpen();
      unsubClose();
      unsubError();
      unsubMessage();
    };
  }, [wsService]);

  const connect = useCallback(async (url: string): Promise<boolean> => {
    if (!wsService) return false;
    
    try {
      setIsConnecting(true);
      const connected = await wsService.connect(url);
      setIsConnected(connected);
      return connected;
    } catch (err) {
      setError(err instanceof Error ? err : new Error('Failed to connect to WebSocket'));
      return false;
    } finally {
      setIsConnecting(false);
    }
  }, [wsService]);

  const disconnect = useCallback(() => {
    if (wsService) {
      wsService.disconnect();
      setIsConnected(false);
    }
  }, [wsService]);

  const send = useCallback(async <T = any,>(message: any, timeout: number = 30000): Promise<T> => {
    if (!wsService) {
      throw new Error('WebSocket service is not available');
    }
    return wsService.send<T>(message, timeout);
  }, [wsService]);

  const startServer = useCallback(async (serverId: string): Promise<Server> => {
    return wsService.startServer(serverId);
  }, [wsService]);

  const stopServer = useCallback(async (serverId: string): Promise<Server> => {
    return wsService.stopServer(serverId);
  }, [wsService]);

  const executeTool = useCallback(async (executionRequest: any): Promise<ToolExecutionUpdate> => {
    return wsService.executeTool(executionRequest);
  }, [wsService]);

  const subscribeToServerStatus = useCallback((
    serverId: string, 
    callback: (update: ServerStatusUpdate) => void
  ) => {
    return wsService.subscribeToServerStatus(serverId, callback);
  }, [wsService]);

  const subscribeToToolExecution = useCallback((
    executionId: string,
    callback: (update: ToolExecutionUpdate) => void
  ) => {
    return wsService.subscribeToToolExecution(executionId, callback);
  }, [wsService]);

  const subscribe = useCallback((
    event: 'open' | 'close' | 'error' | 'message',
    handler: (data: any) => void
  ) => {
    if (!messageHandlers.current.has(event)) {
      messageHandlers.current.set(event, new Set());
    }
    
    const handlers = messageHandlers.current.get(event)!;
    handlers.add(handler);
    
    return () => {
      handlers.delete(handler);
    };
  }, []);

  const value = {
    isConnected,
    isConnecting,
    error,
    connect,
    disconnect,
    send,
    startServer,
    stopServer,
    executeTool,
    subscribeToServerStatus,
    subscribeToToolExecution,
    subscribe,
  };

  return (
    <WebSocketContext.Provider value={value}>
      {children}
    </WebSocketContext.Provider>
  );
};

export const useWebSocket = (): WebSocketContextType => {
  const context = useContext(WebSocketContext);
  if (context === undefined) {
    throw new Error('useWebSocket must be used within a WebSocketProvider');
  }
  return context;
};

// Convenience hook for direct WebSocket access
export const useWebSocketService = (): WebSocketService => {
  const { send, ...rest } = useWebSocket();
  return {
    send,
    ...rest,
  } as unknown as WebSocketService;
};
