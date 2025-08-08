import { TestBed } from '@angular/core/testing';
import { HttpClientTestingModule, HttpTestingController } from '@angular/common/http/testing';
import { of, throwError } from 'rxjs';

import { ToolExecutionService } from './tool-execution.service';
import { WebSocketService } from '../core/services/websocket.service';
import { AuthService } from '../core/services/auth.service';
import { createSpy } from '../core/testing/test-helpers';

describe('ToolExecutionService', () => {
  let service: ToolExecutionService;
  let httpMock: HttpTestingController;
  let websocketService: jasmine.SpyObj<WebSocketService>;
  let authService: jasmine.SpyObj<AuthService>;
  
  const mockTool = {
    name: 'test-tool',
    description: 'A test tool',
    parameters: [
      { name: 'param1', type: 'string', required: true },
      { name: 'param2', type: 'number', required: false }
    ]
  };
  
  const mockExecution = {
    executionId: 'test-execution-123',
    tool: 'test-tool',
    status: 'running',
    progress: 0,
    startTime: new Date().toISOString(),
    parameters: { param1: 'value1' }
  };
  
  const mockExecutionUpdate = {
    executionId: 'test-execution-123',
    status: 'completed',
    progress: 100,
    result: { success: true },
    endTime: new Date().toISOString()
  };

  beforeEach(() => {
    // Create spies
    const webSocketSpy = jasmine.createSpyObj('WebSocketService', [
      'connect', 'disconnect', 'send', 'onMessage', 'isConnected'
    ]);
    
    const authSpy = jasmine.createSpyObj('AuthService', [
      'isAuthenticated', 'currentUserValue'
    ]);
    
    // Configure WebSocket spy
    webSocketSpy.isConnected.and.returnValue(true);
    webSocketSpy.onMessage.and.returnValue(of({}));
    
    // Configure AuthService spy
    authSpy.isAuthenticated.and.returnValue(true);
    authSpy.currentUserValue = { token: 'test-token' };
    
    TestBed.configureTestingModule({
      imports: [HttpClientTestingModule],
      providers: [
        ToolExecutionService,
        { provide: WebSocketService, useValue: webSocketSpy },
        { provide: AuthService, useValue: authSpy }
      ]
    });
    
    service = TestBed.inject(ToolExecutionService);
    httpMock = TestBed.inject(HttpTestingController);
    websocketService = TestBed.inject(WebSocketService) as jasmine.SpyObj<WebSocketService>;
    authService = TestBed.inject(AuthService) as jasmine.SpyObj<AuthService>;
    
    // Set up WebSocket message handling
    (websocketService.onMessage as jasmine.Spy).and.returnValue(
      of({
        type: 'execution_update',
        data: mockExecutionUpdate
      })
    );
  });
  
  afterEach(() => {
    httpMock.verify();
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });
  
  describe('getAvailableTools', () => {
    it('should fetch available tools from the API', () => {
      // Arrange
      const mockTools = [mockTool];
      
      // Act
      service.getAvailableTools().subscribe(tools => {
        expect(tools).toEqual(mockTools);
      });
      
      // Assert
      const req = httpMock.expectOne('/api/tools');
      expect(req.request.method).toBe('GET');
      
      // Respond with mock data
      req.flush(mockTools);
    });
    
    it('should handle errors when fetching tools', (done: DoneFn) => {
      // Act
      service.getAvailableTools().subscribe({
        next: () => fail('expected an error'),
        error: (error) => {
          expect(error).toBeDefined();
          done();
        }
      });
      
      // Assert
      const req = httpMock.expectOne('/api/tools');
      req.flush('Error loading tools', { status: 500, statusText: 'Server Error' });
    });
  });
  
  describe('executeTool', () => {
    it('should execute a tool and return execution updates', (done: DoneFn) => {
      // Arrange
      const toolName = 'test-tool';
      const params = { param1: 'value1' };
      
      // Spy on WebSocket send
      (websocketService.send as jasmine.Spy).and.callThrough();
      
      // Act
      service.executeTool(toolName, params).subscribe(update => {
        // First update should be the initial execution
        if (update.executionId === mockExecution.executionId) {
          expect(update.status).toBe('running');
          expect(update.progress).toBe(0);
        }
        // Second update should be the completion
        else if (update.executionId === mockExecutionUpdate.executionId) {
          expect(update.status).toBe('completed');
          expect(update.progress).toBe(100);
          expect(update.result).toEqual(mockExecutionUpdate.result);
          done();
        }
      });
      
      // Assert
      const req = httpMock.expectOne('/api/execute');
      expect(req.request.method).toBe('POST');
      expect(req.request.body).toEqual({
        tool: toolName,
        parameters: params
      });
      
      // Respond with initial execution
      req.flush(mockExecution);
      
      // WebSocket should have been set up
      expect(websocketService.connect).toHaveBeenCalled();
      expect(websocketService.onMessage).toHaveBeenCalledWith('execution_update');
    });
    
    it('should handle execution errors', (done: DoneFn) => {
      // Arrange
      const toolName = 'test-tool';
      const params = { param1: 'value1' };
      const errorMessage = 'Execution failed';
      
      // Configure WebSocket to throw an error
      (websocketService.onMessage as jasmine.Spy).and.returnValue(
        throwError(() => new Error(errorMessage))
      );
      
      // Act
      service.executeTool(toolName, params).subscribe({
        next: () => fail('expected an error'),
        error: (error) => {
          expect(error.message).toContain(errorMessage);
          done();
        }
      });
      
      // Respond with initial execution
      const req = httpMock.expectOne('/api/execute');
      req.flush(mockExecution);
    });
  });
  
  describe('getExecutionHistory', () => {
    it('should fetch execution history from the API', () => {
      // Arrange
      const mockHistory = [mockExecution];
      const limit = 10;
      const offset = 0;
      
      // Act
      service.getExecutionHistory(limit, offset).subscribe(history => {
        expect(history).toEqual(mockHistory);
      });
      
      // Assert
      const req = httpMock.expectOne(
        `/api/executions?limit=${limit}&offset=${offset}`
      );
      expect(req.request.method).toBe('GET');
      
      // Respond with mock data
      req.flush(mockHistory);
    });
    
    it('should include status filter when provided', () => {
      // Arrange
      const status = 'completed';
      const limit = 10;
      const offset = 0;
      
      // Act
      service.getExecutionHistory(limit, offset, status).subscribe();
      
      // Assert
      const req = httpMock.expectOne(
        `/api/executions?limit=${limit}&offset=${offset}&status=${status}`
      );
      expect(req.request.method).toBe('GET');
      
      // Respond with empty array
      req.flush([]);
    });
  });
  
  describe('getExecution', () => {
    it('should fetch a specific execution by ID', () => {
      // Arrange
      const executionId = 'test-execution-123';
      
      // Act
      service.getExecution(executionId).subscribe(execution => {
        expect(execution).toEqual(mockExecution);
      });
      
      // Assert
      const req = httpMock.expectOne(`/api/executions/${executionId}`);
      expect(req.request.method).toBe('GET');
      
      // Respond with mock data
      req.flush(mockExecution);
    });
  });
  
  describe('cancelExecution', () => {
    it('should send a cancel request for the specified execution', () => {
      // Arrange
      const executionId = 'test-execution-123';
      
      // Act
      service.cancelExecution(executionId).subscribe(response => {
        expect(response).toBeTrue();
      });
      
      // Assert
      const req = httpMock.expectOne(`/api/executions/${executionId}/cancel`);
      expect(req.request.method).toBe('POST');
      
      // Respond with success
      req.flush({ success: true });
    });
    
    it('should handle cancellation errors', (done: DoneFn) => {
      // Arrange
      const executionId = 'test-execution-123';
      const errorMessage = 'Failed to cancel execution';
      
      // Act
      service.cancelExecution(executionId).subscribe({
        next: () => fail('expected an error'),
        error: (error) => {
          expect(error.message).toContain(errorMessage);
          done();
        }
      });
      
      // Assert
      const req = httpMock.expectOne(`/api/executions/${executionId}/cancel`);
      req.flush(
        { message: errorMessage },
        { status: 400, statusText: 'Bad Request' }
      );
    });
  });
  
  describe('getExecutionOutput', () => {
    it('should stream execution output via WebSocket', (done: DoneFn) => {
      // Arrange
      const executionId = 'test-execution-123';
      const outputData = { line: 'Test output', timestamp: new Date().toISOString() };
      
      // Configure WebSocket to return output data
      (websocketService.onMessage as jasmine.Spy).and.returnValue(
        of({
          type: 'execution_output',
          data: { executionId, output: outputData }
        })
      );
      
      // Act
      service.getExecutionOutput(executionId).subscribe(output => {
        // Assert
        expect(output).toEqual({ executionId, output: outputData });
        done();
      });
      
      // WebSocket should have been set up
      expect(websocketService.connect).toHaveBeenCalled();
      expect(websocketService.onMessage).toHaveBeenCalledWith('execution_output');
    });
  });
  
  describe('onExecutionStarted', () => {
    it('should emit when a new execution starts', (done: DoneFn) => {
      // Arrange
      const newExecution = { ...mockExecution, executionId: 'new-execution-123' };
      
      // Configure WebSocket to emit a new execution
      (websocketService.onMessage as jasmine.Spy).and.returnValue(
        of({
          type: 'execution_started',
          data: newExecution
        })
      );
      
      // Act
      service.onExecutionStarted().subscribe(execution => {
        // Assert
        expect(execution).toEqual(newExecution);
        done();
      });
      
      // WebSocket should have been set up
      expect(websocketService.connect).toHaveBeenCalled();
      expect(websocketService.onMessage).toHaveBeenCalledWith('execution_started');
    });
  });
  
  describe('onExecutionUpdated', () => {
    it('should emit when an execution is updated', (done: DoneFn) => {
      // Arrange
      const updatedExecution = { ...mockExecution, status: 'completed', progress: 100 };
      
      // Configure WebSocket to emit an update
      (websocketService.onMessage as jasmine.Spy).and.returnValue(
        of({
          type: 'execution_updated',
          data: updatedExecution
        })
      );
      
      // Act
      service.onExecutionUpdated().subscribe(update => {
        // Assert
        expect(update).toEqual(updatedExecution);
        done();
      });
      
      // WebSocket should have been set up
      expect(websocketService.connect).toHaveBeenCalled();
      expect(websocketService.onMessage).toHaveBeenCalledWith('execution_updated');
    });
  });
  
  describe('cleanup', () => {
    it('should disconnect WebSocket when service is destroyed', () => {
      // Act
      service.ngOnDestroy();
      
      // Assert
      expect(websocketService.disconnect).toHaveBeenCalled();
    });
  });
});
