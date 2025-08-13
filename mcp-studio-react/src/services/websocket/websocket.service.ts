import { v4 as uuidv4 } from 'uuid';
import { Server, ToolExecutionUpdate, ServerStatusUpdate, WebSocketMessage } from '../../types';

type WebSocketEvent = 'open' | 'close' | 'error' | 'message';
type WebSocketHandler = (data: any) => void;

interface PendingRequest {
  resolve: (value: any) => void;
  reject: (reason?: any) => void;
  timeoutId: NodeJS.Timeout;
}

export class WebSocketService {
  private static instance: WebSocketService;
  private socket: WebSocket | null = null;
  private pendingRequests: Map<string, PendingRequest> = new Map();
  private eventHandlers: Map<WebSocketEvent, Set<WebSocketHandler>> = new Map();
  private reconnectAttempts: number = 0;
  private maxReconnectAttempts: number = 5;
  private reconnectInterval: number = 3000; // 3 seconds
  private isConnecting: boolean = false;
  private connectionUrl: string = '';
  private connectionPromise: Promise<boolean> | null = null;

  private constructor() {
    // Initialize event handlers
    this.eventHandlers.set('open', new Set());
    this.eventHandlers.set('close', new Set());
    this.eventHandlers.set('error', new Set());
    this.eventHandlers.set('message', new Set());
  }

  public static getInstance(): WebSocketService {
    if (!WebSocketService.instance) {
      WebSocketService.instance = new WebSocketService();
    }
    return WebSocketService.instance;
  }

  public async connect(url: string): Promise<boolean> {
    // If already connected or connecting, return the existing connection promise
    if (this.socket?.readyState === WebSocket.OPEN) {
      return true;
    }

    if (this.connectionPromise) {
      return this.connectionPromise;
    }

    this.connectionUrl = url;
    this.connectionPromise = new Promise<boolean>((resolve, reject) => {
      try {
        if (this.isConnecting) {
          return;
        }

        this.isConnecting = true;
        this.socket = new WebSocket(url);

        this.socket.onopen = (event) => {
          console.log('WebSocket connected');
          this.reconnectAttempts = 0;
          this.isConnecting = false;
          this.emit('open', event);
          resolve(true);
          this.connectionPromise = null;
        };

        this.socket.onclose = (event) => {
          console.log('WebSocket disconnected');
          this.emit('close', event);
          this.socket = null;
          this.isConnecting = false;
          this.connectionPromise = null;

          // Attempt to reconnect if this wasn't an explicit close
          if (event.code !== 1000) {
            this.handleReconnect();
          }
        };

        this.socket.onerror = (error) => {
          console.error('WebSocket error:', error);
          this.emit('error', error);
          this.isConnecting = false;
          
          // Reject the connection promise on error
          if (this.connectionPromise) {
            reject(new Error('WebSocket connection failed'));
            this.connectionPromise = null;
          }
          
          // Attempt to reconnect
          this.handleReconnect();
        };

        this.socket.onmessage = (event) => {
          try {
            const message = JSON.parse(event.data);
            this.emit('message', message);
            this.handleIncomingMessage(message);
          } catch (error) {
            console.error('Error parsing WebSocket message:', error);
          }
        };
      } catch (error) {
        console.error('WebSocket connection error:', error);
        this.isConnecting = false;
        this.connectionPromise = null;
        reject(error);
      }
    });

    return this.connectionPromise;
  }

  public disconnect(code: number = 1000, reason?: string): void {
    if (this.socket) {
      this.socket.close(code, reason);
      this.socket = null;
    }
    this.pendingRequests.forEach((request) => {
      request.timeoutId && clearTimeout(request.timeoutId);
      request.reject(new Error('Connection closed'));
    });
    this.pendingRequests.clear();
  }

  public send<T = any>(message: any, timeout: number = 30000): Promise<T> {
    return new Promise((resolve, reject) => {
      if (!this.socket || this.socket.readyState !== WebSocket.OPEN) {
        return reject(new Error('WebSocket is not connected'));
      }

      const messageId = uuidv4();
      const messageWithId = { ...message, id: messageId };

      const timeoutId = setTimeout(() => {
        this.pendingRequests.delete(messageId);
        reject(new Error('Request timed out'));
      }, timeout);

      this.pendingRequests.set(messageId, {
        resolve,
        reject,
        timeoutId,
      });n
      this.socket.send(JSON.stringify(messageWithId));
    });
  }

  public on(event: WebSocketEvent, handler: WebSocketHandler): () => void {
    const handlers = this.eventHandlers.get(event) || new Set();
    handlers.add(handler);
    this.eventHandlers.set(event, handlers);

    // Return unsubscribe function
    return () => {
      const currentHandlers = this.eventHandlers.get(event) || new Set();
      currentHandlers.delete(handler);
    };
  }

  public off(event: WebSocketEvent, handler: WebSocketHandler): void {
    const handlers = this.eventHandlers.get(event);
    if (handlers) {
      handlers.delete(handler);
    }
  }

  // Server-specific methods
  public async startServer(serverId: string): Promise<Server> {
    return this.send<Server>({
      type: 'START_SERVER',
      data: { serverId },
    });
  }

  public async stopServer(serverId: string): Promise<Server> {
    return this.send<Server>({
      type: 'STOP_SERVER',
      data: { serverId },
    });
  }

  public async executeTool(executionRequest: any): Promise<ToolExecutionUpdate> {
    return this.send<ToolExecutionUpdate>({
      type: 'EXECUTE_TOOL',
      data: executionRequest,
    });
  }

  public subscribeToServerStatus(serverId: string, callback: (update: ServerStatusUpdate) => void): () => void {
    const handler = (message: WebSocketMessage) => {
      if (message.type === 'SERVER_STATUS_UPDATE' && message.data.serverId === serverId) {
        callback(message.data);
      }
    };

    return this.on('message', handler);
  }

  public subscribeToToolExecution(
    executionId: string,
    callback: (update: ToolExecutionUpdate) => void
  ): () => void {
    const handler = (message: WebSocketMessage) => {
      if (message.type === 'TOOL_EXECUTION_UPDATE' && message.data.executionId === executionId) {
        callback(message.data);
      }
    };

    return this.on('message', handler);
  }

  private handleReconnect(): void {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      console.error('Max reconnection attempts reached');
      return;
    }

    this.reconnectAttempts++;
    const delay = this.reconnectInterval * Math.pow(2, this.reconnectAttempts - 1);

    console.log(`Attempting to reconnect (${this.reconnectAttempts}/${this.maxReconnectAttempts}) in ${delay}ms`);
    
    setTimeout(() => {
      if (this.socket?.readyState !== WebSocket.OPEN) {
        this.connect(this.connectionUrl).catch(console.error);
      }
    }, delay);
  }

  private handleIncomingMessage(message: WebSocketMessage): void {
    // Handle response to a specific request
    if (message.id && this.pendingRequests.has(message.id)) {
      const { resolve, reject, timeoutId } = this.pendingRequests.get(message.id)!;
      clearTimeout(timeoutId);
      this.pendingRequests.delete(message.id);

      if (message.error) {
        reject(new Error(message.error));
      } else {
        resolve(message.data);
      }
    }
  }

  private emit(event: WebSocketEvent, data: any): void {
    const handlers = this.eventHandlers.get(event);
    if (handlers) {
      handlers.forEach((handler) => handler(data));
    }
  }
}

export const webSocketService = WebSocketService.getInstance();
