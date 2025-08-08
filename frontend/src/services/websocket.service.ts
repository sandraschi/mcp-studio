import { Injectable } from '@angular/core';
import { Observable, Subject, fromEvent, merge, of } from 'rxjs';
import { filter, map, retryWhen, delay, tap, takeUntil } from 'rxjs/operators';
import { webSocket, WebSocketSubject } from 'rxjs/webSocket';
import { environment } from '../../environments/environment';
import { AuthService } from './auth.service';

export interface WebSocketMessage {
  type: string;
  [key: string]: any;
}

@Injectable({
  providedIn: 'root'
})
export class WebSocketService {
  private socket$: WebSocketSubject<WebSocketMessage>;
  private messageSubject = new Subject<WebSocketMessage>();
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectDelay = 2000; // 2 seconds
  private clientId: string;
  private isConnected = false;
  private connectionStatus = new Subject<boolean>();

  constructor(private authService: AuthService) {
    this.clientId = this.generateClientId();
    this.connect();
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
  private connect(): void {
    if (this.isConnected) return;

    // Get the authentication token
    const token = this.authService.getToken();
    const wsUrl = `${environment.wsUrl}/ws/${this.clientId}${token ? `?token=${token}` : ''}`;

    // Create the WebSocket connection
    this.socket$ = webSocket({
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
          this.handleDisconnection();
        }
      }
    });

    // Handle incoming messages
    this.socket$.pipe(
      retryWhen(errors => errors.pipe(
        tap(err => console.error('WebSocket error, attempting to reconnect...', err)),
        delay(this.reconnectDelay)
      ))
    ).subscribe({
      next: (message) => this.messageSubject.next(message as WebSocketMessage),
      error: (err) => console.error('WebSocket error:', err),
      complete: () => console.log('WebSocket connection closed')
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
  public sendMessage(message: WebSocketMessage): void {
    if (this.isConnected) {
      this.socket$.next(message);
    } else {
      console.error('WebSocket is not connected');
    }
  }

  /**
   * Subscribe to messages of a specific type
   * @param messageType The type of message to listen for
   */
  public onMessage<T = any>(messageType: string): Observable<T> {
    return this.messageSubject.pipe(
      filter(message => message.type === messageType),
      map(message => message as unknown as T)
    );
  }

  /**
   * Subscribe to connection status changes
   */
  public onConnectionStatus(): Observable<boolean> {
    return this.connectionStatus.asObservable();
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
   * Close the WebSocket connection
   */
  public closeConnection(): void {
    if (this.socket$) {
      this.socket$.complete();
      this.isConnected = false;
    }
  }

  /**
   * Get the current client ID
   */
  public getClientId(): string {
    return this.clientId;
  }

  /**
   * Check if the WebSocket is connected
   */
  public isSocketConnected(): boolean {
    return this.isConnected;
  }
}
