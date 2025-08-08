import { Injectable } from '@angular/core';
import { Observable, Subject, BehaviorSubject, of, throwError } from 'rxjs';
import { catchError, map, switchMap, takeUntil, tap } from 'rxjs/operators';
import { HttpClient } from '@angular/common/http';
import { WebSocketService, WebSocketMessage } from './websocket.service';
import { AuthService } from './auth.service';
import { environment } from '../../environments/environment';

export interface ToolParameter {
  name: string;
  type: string;
  required: boolean;
  default?: any;
  description?: string;
  [key: string]: any;
}

export interface ToolMetadata {
  name: string;
  description: string;
  parameters: { [key: string]: ToolParameter };
  tags: string[];
  is_async: boolean;
  requires_auth: boolean;
  allowed_roles: string[];
}

export interface ToolExecutionResult {
  success: boolean;
  result?: any;
  error?: string;
  execution_time: number;
  metadata: {
    tool: string;
    execution_id: string;
    user?: string;
  };
}

export interface ExecutionProgress {
  execution_id: string;
  tool: string;
  progress: number;
  message?: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  timestamp: number;
}

@Injectable({
  providedIn: 'root'
})
export class ToolExecutionService {
  private apiUrl = `${environment.apiUrl}/api/v1`;
  private activeExecutions: Map<string, Subject<ExecutionProgress>> = new Map();

  constructor(
    private http: HttpClient,
    private wsService: WebSocketService,
    private authService: AuthService
  ) {
    // Listen for execution updates
    this.wsService.onMessage<ExecutionProgress>('progress').subscribe(progress => {
      this.handleExecutionProgress(progress);
    });

    // Listen for execution completion
    this.wsService.onMessage<ExecutionProgress>('execution_completed').subscribe(progress => {
      this.handleExecutionProgress({
        ...progress,
        status: 'completed',
        progress: 100
      });
    });

    // Listen for execution failures
    this.wsService.onMessage<{ execution_id: string; error: string }>('execution_failed').subscribe(data => {
      this.handleExecutionProgress({
        execution_id: data.execution_id,
        progress: 0,
        status: 'failed',
        message: data.error,
        timestamp: Date.now(),
        tool: ''
      });
    });
  }

  /**
   * Get all available tools
   */
  getTools(): Observable<ToolMetadata[]> {
    return this.http.get<ToolMetadata[]>(`${this.apiUrl}/tools`).pipe(
      catchError(error => {
        console.error('Error fetching tools:', error);
        return throwError(error);
      })
    );
  }

  /**
   * Get a specific tool by name
   */
  getTool(toolName: string): Observable<ToolMetadata> {
    return this.http.get<ToolMetadata>(`${this.apiUrl}/tools/${toolName}`).pipe(
      catchError(error => {
        console.error(`Error fetching tool ${toolName}:`, error);
        return throwError(error);
      })
    );
  }

  /**
   * Execute a tool with the given parameters
   */
  executeTool(
    toolName: string, 
    parameters: { [key: string]: any },
    options: { useWebSocket?: boolean } = { useWebSocket: true }
  ): Observable<ExecutionProgress> {
    const executionId = `exec_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    const progressSubject = new BehaviorSubject<ExecutionProgress>({
      execution_id: executionId,
      tool: toolName,
      progress: 0,
      status: 'pending',
      timestamp: Date.now()
    });

    this.activeExecutions.set(executionId, progressSubject);

    if (options.useWebSocket && this.wsService.isSocketConnected()) {
      // Use WebSocket for real-time updates
      this.wsService.sendMessage({
        type: 'execute_tool',
        tool_name: toolName,
        parameters,
        execution_id: executionId
      });
    } else {
      // Fall back to HTTP if WebSocket is not available
      this.http.post<ToolExecutionResult>(
        `${this.apiUrl}/tools/execute/${toolName}`,
        { parameters }
      ).pipe(
        tap(result => {
          progressSubject.next({
            execution_id: executionId,
            tool: toolName,
            progress: 100,
            status: 'completed',
            result: result.result,
            timestamp: Date.now()
          });
          progressSubject.complete();
          this.activeExecutions.delete(executionId);
        }),
        catchError(error => {
          progressSubject.next({
            execution_id: executionId,
            tool: toolName,
            progress: 0,
            status: 'failed',
            message: error.error?.error || 'Execution failed',
            timestamp: Date.now()
          });
          progressSubject.complete();
          this.activeExecutions.delete(executionId);
          return throwError(error);
        })
      ).subscribe();
    }

    return progressSubject.asObservable();
  }

  /**
   * Cancel an ongoing execution
   */
  cancelExecution(executionId: string): void {
    const subject = this.activeExecutions.get(executionId);
    if (subject) {
      subject.complete();
      this.activeExecutions.delete(executionId);
      
      // Notify the server to cancel the execution
      this.wsService.sendMessage({
        type: 'cancel_execution',
        execution_id: executionId
      });
    }
  }

  /**
   * Get an observable for a specific execution's progress
   */
  getExecutionProgress(executionId: string): Observable<ExecutionProgress> | null {
    const subject = this.activeExecutions.get(executionId);
    return subject ? subject.asObservable() : null;
  }

  /**
   * Get all active executions
   */
  getActiveExecutions(): string[] {
    return Array.from(this.activeExecutions.keys());
  }

  /**
   * Handle execution progress updates
   */
  private handleExecutionProgress(progress: ExecutionProgress): void {
    const { execution_id } = progress;
    const subject = this.activeExecutions.get(execution_id);
    
    if (subject) {
      subject.next(progress);
      
      // If the execution is completed or failed, complete the subject
      if (progress.status === 'completed' || progress.status === 'failed') {
        subject.complete();
        // Keep the subject for a short time after completion
        setTimeout(() => {
          this.activeExecutions.delete(execution_id);
        }, 5000);
      }
    }
  }
}
