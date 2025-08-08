import { TestBed } from '@angular/core/testing';
import { WebSocketSubject, WebSocketSubjectConfig } from 'rxjs/webSocket';
import { of, throwError } from 'rxjs';

import { WebSocketService } from './websocket.service';
import { createSpy } from '../testing/test-helpers';

describe('WebSocketService', () => {
  let service: WebSocketService;
  let mockWebSocket: jasmine.SpyObj<WebSocketSubject<any>>;
  
  const testUrl = 'ws://test-url';
  const testMessage = { type: 'test', data: 'test data' };
  const testResponse = { type: 'response', data: 'response data' };

  beforeEach(() => {
    // Create a mock WebSocketSubject
    mockWebSocket = jasmine.createSpyObj<WebSocketSubject<any>>('WebSocketSubject', [
      'next',
      'complete',
      'error',
      'subscribe',
      'unsubscribe',
      'closed',
      'isStopped',
      'lift'
    ]);
    
    // Configure the mock to return a subscription when subscribe is called
    mockWebSocket.subscribe.and.returnValue({
      unsubscribe: jasmine.createSpy('unsubscribe')
    } as any);
    
    // Mock the WebSocketSubject constructor
    spyOn(WebSocketService as any, 'createWebSocket').and.returnValue(mockWebSocket);
    
    TestBed.configureTestingModule({
      providers: [
        WebSocketService,
        { provide: 'WEB_SOCKET_URL', useValue: testUrl }
      ]
    });
    
    service = TestBed.inject(WebSocketService);
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });

  describe('connect', () => {
    it('should create a new WebSocket connection', () => {
      // Act
      service.connect();
      
      // Assert
      expect(WebSocketService['createWebSocket']).toHaveBeenCalledWith(testUrl);
      expect(mockWebSocket.subscribe).toHaveBeenCalledWith(
        jasmine.any(Function),
        jasmine.any(Function),
        jasmine.any(Function)
      );
    });
    
    it('should not create a new connection if one already exists', () => {
      // Arrange
      service.connect();
      
      // Reset the call count
      (WebSocketService as any).createWebSocket.calls.reset();
      
      // Act
      service.connect();
      
      // Assert
      expect(WebSocketService['createWebSocket']).not.toHaveBeenCalled();
    });
  });

  describe('send', () => {
    it('should send a message through the WebSocket', () => {
      // Arrange
      service.connect();
      
      // Act
      service.send(testMessage);
      
      // Assert
      expect(mockWebSocket.next).toHaveBeenCalledWith(testMessage);
    });
    
    it('should throw an error if not connected', () => {
      // Act & Assert
      expect(() => service.send(testMessage)).toThrowError('Not connected to WebSocket');
    });
  });

  describe('onMessage', () => {
    it('should return an observable of messages', (done: DoneFn) => {
      // Arrange
      service.connect();
      
      // Get the message handler from the subscribe call
      const messageHandler = (WebSocketService as any).createWebSocket.calls.mostRecent().returnValue.subscribe.calls.argsFor(0)[0];
      
      // Act
      service.onMessage().subscribe(message => {
        // Assert
        expect(message).toEqual(testResponse);
        done();
      });
      
      // Simulate receiving a message
      messageHandler(testResponse);
    });
    
    it('should filter messages by type when a type is provided', (done: DoneFn) => {
      // Arrange
      service.connect();
      const messageHandler = (WebSocketService as any).createWebSocket.calls.mostRecent().returnValue.subscribe.calls.argsFor(0)[0];
      const testType = 'test-type';
      const testData = { id: 1 };
      
      // Act
      service.onMessage(testType).subscribe(message => {
        // Should only receive messages of the specified type
        expect(message).toEqual({ type: testType, data: testData });
        done();
      });
      
      // Simulate receiving messages (only one matches the filter)
      messageHandler({ type: 'other-type', data: 'ignore me' });
      messageHandler({ type: testType, data: testData });
    });
  });

  describe('disconnect', () => {
    it('should close the WebSocket connection', () => {
      // Arrange
      service.connect();
      
      // Act
      service.disconnect();
      
      // Assert
      expect(mockWebSocket.complete).toHaveBeenCalled();
    });
    
    it('should not throw if not connected', () => {
      // Act & Assert (should not throw)
      expect(() => service.disconnect()).not.toThrow();
    });
  });

  describe('reconnect', () => {
    it('should disconnect and then connect', () => {
      // Arrange
      const disconnectSpy = spyOn(service, 'disconnect').and.callThrough();
      const connectSpy = spyOn(service, 'connect').and.callThrough();
      
      // Act
      service.reconnect();
      
      // Assert
      expect(disconnectSpy).toHaveBeenCalled();
      expect(connectSpy).toHaveBeenCalled();
    });
  });

  describe('error handling', () => {
    it('should emit errors through the error$ observable', (done: DoneFn) => {
      // Arrange
      service.connect();
      const errorHandler = (WebSocketService as any).createWebSocket.calls.mostRecent().returnValue.subscribe.calls.argsFor(0)[1];
      const testError = new Error('WebSocket error');
      
      // Act
      service.error$.subscribe(error => {
        // Assert
        expect(error).toBe(testError);
        done();
      });
      
      // Simulate an error
      errorHandler(testError);
    });
    
    it('should attempt to reconnect on error when autoReconnect is true', (done: DoneFn) => {
      // Arrange
      const reconnectSpy = spyOn(service, 'reconnect');
      service.connect();
      
      // Configure the mock to throw an error on next connection attempt
      let reconnectAttempts = 0;
      (WebSocketService as any).createWebSocket.and.callFake(() => {
        if (reconnectAttempts++ === 0) {
          // First connection succeeds
          return mockWebSocket;
        } else {
          // Subsequent connections throw
          throw new Error('Connection failed');
        }
      });
      
      const errorHandler = (WebSocketService as any).createWebSocket.calls.mostRecent().returnValue.subscribe.calls.argsFor(0)[1];
      
      // Act
      errorHandler(new Error('Connection lost'));
      
      // Assert
      setTimeout(() => {
        expect(reconnectSpy).toHaveBeenCalled();
        done();
      }, 100);
    });
  });

  describe('connection status', () => {
    it('should track connection status', () => {
      // Initially not connected
      expect(service.isConnected()).toBeFalse();
      
      // After connecting
      service.connect();
      expect(service.isConnected()).toBeTrue();
      
      // After disconnecting
      service.disconnect();
      expect(service.isConnected()).toBeFalse();
    });
  });
});
