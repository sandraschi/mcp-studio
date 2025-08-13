import { Injectable, OnDestroy } from '@angular/core';
import { BehaviorSubject, Observable, Subject, of, Subscription } from 'rxjs';
import { filter, takeUntil, switchMap } from 'rxjs/operators';
import { webSocket, WebSocketSubject, WebSocketSubjectConfig } from 'rxjs/webSocket';
import { environment } from '../../environments/environment';
import { AuthService } from './auth.service';

export type WebSocketMessageType = 
  | 'execute_tool'
  | 'subscribe_execution'
  | 'unsubscribe_execution'
  | 'execution_started'
  | 'execution_update'
  | 'execution_completed'
  | 'execution_failed'
  | 'execution_cancelled'
  | 'progress_update'
  | 'error'
  | 'subscribe'
  | 'unsubscribe';

export interface WebSocketMessage {
  type: WebSocketMessageType;
  [key: string]: any;
}

export interface ExecutionStartedMessage extends WebSocketMessage {
  type: 'execution_started';
  execution_id: string;
  tool_name: string;
  status: 'pending' | 'running' | 'completed' | 'failed' | 'cancelled';
}

export interface ProgressUpdateMessage extends WebSocketMessage {
  type: 'progress_update' | 'execution_update';
  execution_id: string;
  progress: number;
  message?: string;
  status: 'pending' | 'running' | 'completed' | 'failed' | 'cancelled';
}

export interface ExecutionCompletedMessage extends WebSocketMessage {
  type: 'execution_completed';
  execution_id: string;
  result: any;
  status: 'completed';
}

export interface ExecutionFailedMessage extends WebSocketMessage {
  type: 'execution_failed';
  execution_id: string;
  error: string;
  status: 'failed';
}

export interface ExecutionCancelledMessage extends WebSocketMessage {
  type: 'execution_cancelled';
  execution_id: string;
  status: 'cancelled';
}

export type TypedWebSocketMessage = 
  | ExecutionStartedMessage
  | ProgressUpdateMessage
  | ExecutionCompletedMessage
  | ExecutionFailedMessage
  | ExecutionCancelledMessage;

@Injectable({
  providedIn: 'root'
})
export class WebSocketService implements OnDestroy {
  private socket$: WebSocketSubject<WebSocketMessage>;
  private messageSubject = new Subject<TypedWebSocketMessage>();
  private executionSubjects = new Map<string, Subject<TypedWebSocketMessage>>();
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectDelay = 2000; // 2 seconds
  private clientId: string;
  private isConnected = false;
  private connectionStatus = new BehaviorSubject<boolean>(false);
  private destroy$ = new Subject<void>();
  private subscriptions: Subscription = new Subscription();

  constructor(private authService: AuthService) {
    this.clientId = this.generateClientId();
    this.initializeConnection();
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
    this.subscriptions.unsubscribe();
    this.disconnect();
  }

  /**
   * Generate a unique client ID
   */
  private generateClientId(): string {
    return 'client_' + Math.random().toString(36).substr(2, 9);
  }

  /**
   * Connect to the WebSocket server
   */
  /**
   * Initialize the WebSocket connection with reconnection logic
   */
  private initializeConnection(): void {
    this.subscriptions.add(
      this.connectionStatus.pipe(
        filter(connected => !connected && !this.isConnected),
        switchMap(() => this.connect())
      ).subscribe()
    );
    
    // Initial connection attempt
    this.connect().subscribe();
  }

  /**
   * Connect to the WebSocket server with retry logic
   */
  private connect(): Observable<void> {
    if (this.isConnected) return of(undefined);

    this.isConnected = false;
    
    // Get the authentication token
    const token = this.authService.getToken();
    const wsUrl = `${environment.wsUrl}/ws/${this.clientId}${token ? `?token=${token}` : ''}`;

    const config: WebSocketSubjectConfig<WebSocketMessage> = {
      url: wsUrl,
      openObserver: {
        next: () => {
          console.log('WebSocket connected');
          this.isConnected = true;
          this.reconnectAttempts = 0;
          this.connectionStatus.next(true);
        }
      },
      closeObserver: {
        next: (event: CloseEvent) => {
          console.log('WebSocket disconnected:', event);
          this.isConnected = false;
          this.connectionStatus.next(false);
          this.attemptReconnect();
        }
      }
    };

    // Create the WebSocket connection
    this.socket$ = webSocket(config);

    return new Observable<void>(subscriber => {
      const messageSub = this.socket$.subscribe({
        next: (message: WebSocketMessage) => this.handleIncomingMessage(message),
        error: (error) => {
          console.error('WebSocket error:', error);
          this.isConnected = false;
          this.connectionStatus.next(false);
          this.attemptReconnect();
          subscriber.error(error);
        },
        complete: () => {
          console.log('WebSocket connection closed');
          this.isConnected = false;
          this.connectionStatus.next(false);
          this.attemptReconnect();
          subscriber.complete();
        }
      });

      return () => {
        messageSub.unsubscribe();
        this.disconnect();
      };
    });
  }

  /**
   * Handle disconnection and attempt to reconnect
   */
  private handleDisconnection(): void {
    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      this.reconnectAttempts++;
      console.log(`Attempting to reconnect (${this.reconnectAttempts}/${this.maxReconnectAttempts})...`);
      setTimeout(() => this.connect(), this.reconnectDelay);
    } else {
      console.error('Max reconnection attempts reached');
    }
  }

  /**
   * Send a message through the WebSocket
   * @param message The message to send
   */
  sendMessage(message: WebSocketMessage): void {
    if (this.isConnected && this.socket$) {
      this.socket$.next(message);
    } else {
      console.error('Cannot send message: WebSocket not connected');
      this.connectionStatus.next(false);
    }
  }

  /**
   * Execute a tool via WebSocket
   * @param toolName Name of the tool to execute
   * @param parameters Parameters for the tool
   * @param subscribe Whether to subscribe to execution updates
   * @returns Observable for the execution
   */
  executeTool(toolName: string, parameters: any = {}, subscribe = true): Observable<TypedWebSocketMessage> {
    const executionId = `exec_${this.generateClientId()}`;
    
    // Create a subject for this execution
    const executionSubject = new Subject<TypedWebSocketMessage>();
    this.executionSubjects.set(executionId, executionSubject);
    
    // Send the execution request
    this.sendMessage({
      type: 'execute_tool' as WebSocketMessageType,
      tool_name: toolName,
      data: {
        execution_id: executionId,
        parameters,
        subscribe
      }
    });
    
    // Clean up the subject when the execution completes, fails, or is cancelled
    const cleanup = () => {
      executionSubject.complete();
      this.executionSubjects.delete(executionId);
    };
    
    const subscription = executionSubject.subscribe({
      next: (message) => {
        if (['execution_completed', 'execution_failed', 'execution_cancelled'].includes(message.type)) {
          cleanup();
        }
      },
      error: () => cleanup(),
      complete: () => cleanup()
    });
    
    // Ensure we clean up if the consumer unsubscribes
    return new Observable<TypedWebSocketMessage>(subscriber => {
      const execSubscription = executionSubject.subscribe(subscriber);
      
      return () => {
        execSubscription.unsubscribe();
        subscription.unsubscribe();
        cleanup();
      };
    });
  }
  
  /**
   * Subscribe to execution updates for a specific execution
   * @param executionId The execution ID to subscribe to
   * @returns Observable for the execution updates
   */
  subscribeToExecution(executionId: string): Observable<TypedWebSocketMessage> {
    if (this.executionSubjects.has(executionId)) {
      return this.executionSubjects.get(executionId)!.asObservable();
    }
    
    const subject = new Subject<TypedWebSocketMessage>();
    this.executionSubjects.set(executionId, subject);
    
    // Send subscription message
    this.sendMessage({
      type: 'subscribe_execution' as WebSocketMessageType,
      data: { execution_id: executionId }
    });
    
    return subject.asObservable().pipe(
      takeUntil(this.destroy$)
    );
  }
  
  /**
   * Unsubscribe from execution updates
   * @param executionId The execution ID to unsubscribe from
   */
  unsubscribeFromExecution(executionId: string): void {
    if (this.executionSubjects.has(executionId)) {
      this.executionSubjects.get(executionId)?.complete();
      this.executionSubjects.delete(executionId);
      
      // Send unsubscribe message
      this.sendMessage({
        type: 'unsubscribe_execution' as WebSocketMessageType,
        data: { execution_id: executionId }
      });
    }
  }
  
  /**
   * Check if the WebSocket is currently connected
   * @returns True if connected, false otherwise
   */
  isConnectedNow(): boolean {
    return this.isConnected;
  }

  /**
   * Handle incoming WebSocket messages
   * @param message The incoming message
   */
  private handleIncomingMessage(message: WebSocketMessage): void {
    try {
      const typedMessage = message as TypedWebSocketMessage;
      this.messageSubject.next(typedMessage);

      // Route execution-specific messages to their respective subjects
      if ('execution_id' in typedMessage) {
        const executionId = typedMessage.execution_id;
        if (this.executionSubjects.has(executionId)) {
          this.executionSubjects.get(executionId)?.next(typedMessage);
        }
      }
    } catch (error) {
      console.error('Error processing WebSocket message:', error, message);
    }
  }

  /**
   * Attempt to reconnect to the WebSocket server
   */
  private attemptReconnect(): void {
    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      this.reconnectAttempts++;
      const delayTime = this.reconnectDelay * Math.pow(1.5, this.reconnectAttempts - 1);
      
      console.log(`Attempting to reconnect (${this.reconnectAttempts}/${this.maxReconnectAttempts})...`);
      
      setTimeout(() => {
        if (!this.isConnected) {
          this.connect().subscribe();
        }
      }, delayTime);
    } else {
      console.error('Max reconnection attempts reached. Please refresh the page to try again.');
    }
  }

  /**
   * Listen for messages from the WebSocket
   * @param messageType Optional message type to filter by
   */
  onMessage<T extends TypedWebSocketMessage = TypedWebSocketMessage>(
    messageType?: T['type']
  ): Observable<T> {
    if (messageType) {
      return this.messageSubject.pipe(
        filter((message): message is T => message.type === messageType)
      ) as Observable<T>;
    }
    return this.messageSubject.asObservable() as Observable<T>;
  }

  /**
   * Check if the WebSocket is currently connected
   * @returns True if connected, false otherwise
   */
  isSocketConnected(): boolean {
    return this.isConnected;
  }

  /**
   * Subscribe to a specific channel
   * @param channel The channel to subscribe to
   */
  public subscribe(channel: string): void {
    this.sendMessage({
      type: 'subscribe',
      channel
    });
  }

  /**
   * Unsubscribe from a specific channel
   * @param channel The channel to unsubscribe from
   */
  public unsubscribe(channel: string): void {
    this.sendMessage({
      type: 'unsubscribe',
      channel
    });
  }

  /**
   * Disconnect from the WebSocket server
   */
  public disconnect(): void {
    if (this.socket$) {
      try {
        this.socket$.complete();
      } catch (e) {
        console.error('Error disconnecting WebSocket:', e);
      }
      this.isConnected = false;
      this.connectionStatus.next(false);
      // Clean up all execution subjects
      this.executionSubjects.forEach(subject => subject.complete());
      this.executionSubjects.clear();
    }
  }

  /**
   * Get the current client ID
   * @returns The current client ID
   */
  public getClientId(): string {
    return this.clientId;
  }

  /**
   * Get the current connection status as an observable
   * @returns Observable that emits the current connection status
   */
  public getConnectionStatus(): Observable<boolean> {
    return this.connectionStatus.asObservable();
  }
}
