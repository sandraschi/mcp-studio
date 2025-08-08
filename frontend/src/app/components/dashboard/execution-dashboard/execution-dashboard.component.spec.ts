import { ComponentFixture, TestBed, fakeAsync, tick } from '@angular/core/testing';
import { RouterTestingModule } from '@angular/router/testing';
import { NoopAnimationsModule } from '@angular/platform-browser/animations';
import { MatDialog, MatDialogModule, MatDialogRef } from '@angular/material/dialog';
import { MatTableModule } from '@angular/material/table';
import { MatPaginatorModule } from '@angular/material/paginator';
import { MatProgressBarModule } from '@angular/material/progress-bar';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatSelectModule } from '@angular/material/select';
import { MatChipsModule } from '@angular/material/chips';
import { MatTooltipModule } from '@angular/material/tooltip';
import { of, throwError } from 'rxjs';

import { ExecutionDashboardComponent } from './execution-dashboard.component';
import { ToolExecutionService } from '../../../../services/tool-execution.service';
import { AuthService } from '../../../../core/services/auth.service';
import { ExecutionDetailsDialogComponent } from '../execution-details-dialog/execution-details-dialog.component';
import { createComponent, click, setFormControlValue } from '../../../../core/testing/test-helpers';

describe('ExecutionDashboardComponent', () => {
  let component: ExecutionDashboardComponent;
  let fixture: ComponentFixture<ExecutionDashboardComponent>;
  let toolExecutionService: jasmine.SpyObj<ToolExecutionService>;
  let authService: jasmine.SpyObj<AuthService>;
  let dialog: jasmine.SpyObj<MatDialog>;
  
  const mockExecutions = [
    {
      executionId: 'exec-1',
      tool: 'test-tool',
      status: 'completed',
      progress: 100,
      startTime: '2023-01-01T00:00:00Z',
      endTime: '2023-01-01T00:01:30Z',
      parameters: { param1: 'value1' },
      result: { success: true }
    },
    {
      executionId: 'exec-2',
      tool: 'another-tool',
      status: 'running',
      progress: 50,
      startTime: '2023-01-01T01:00:00Z',
      parameters: { param2: 'value2' }
    },
    {
      executionId: 'exec-3',
      tool: 'failing-tool',
      status: 'failed',
      progress: 75,
      startTime: '2023-01-01T02:00:00Z',
      endTime: '2023-01-01T02:02:00Z',
      parameters: { param3: 'value3' },
      error: 'Something went wrong'
    }
  ];

  beforeEach(async () => {
    // Create spies
    const toolExecutionServiceSpy = jasmine.createSpyObj('ToolExecutionService', [
      'getExecutionHistory',
      'cancelExecution',
      'onExecutionUpdated',
      'onExecutionStarted'
    ]);
    
    const authServiceSpy = jasmine.createSpyObj('AuthService', ['hasRole']);
    const dialogSpy = jasmine.createSpyObj('MatDialog', ['open']);
    
    // Configure spies
    toolExecutionServiceSpy.getExecutionHistory.and.returnValue(of(mockExecutions));
    toolExecutionServiceSpy.cancelExecution.and.returnValue(of(true));
    toolExecutionServiceSpy.onExecutionUpdated.and.returnValue(of(mockExecutions[1]));
    toolExecutionServiceSpy.onExecutionStarted.and.returnValue(of(mockExecutions[0]));
    
    authServiceSpy.hasRole.and.returnValue(true);
    
    // Configure dialog mock
    const dialogRefSpy = jasmine.createSpyObj('MatDialogRef', ['afterClosed']);
    dialogRefSpy.afterClosed.and.returnValue(of(undefined));
    dialogSpy.open.and.returnValue(dialogRefSpy);
    
    await TestBed.configureTestingModule({
      imports: [
        RouterTestingModule,
        NoopAnimationsModule,
        MatDialogModule,
        MatTableModule,
        MatPaginatorModule,
        MatProgressBarModule,
        MatButtonModule,
        MatIconModule,
        MatFormFieldModule,
        MatInputModule,
        MatSelectModule,
        MatChipsModule,
        MatTooltipModule
      ],
      declarations: [
        ExecutionDashboardComponent,
        // Mock the dialog component
        ExecutionDetailsDialogComponent
      ],
      providers: [
        { provide: ToolExecutionService, useValue: toolExecutionServiceSpy },
        { provide: AuthService, useValue: authServiceSpy },
        { provide: MatDialog, useValue: dialogSpy }
      ]
    }).compileComponents();
    
    // Get the test dependencies
    toolExecutionService = TestBed.inject(ToolExecutionService) as jasmine.SpyObj<ToolExecutionService>;
    authService = TestBed.inject(AuthService) as jasmine.SpyObj<AuthService>;
    dialog = TestBed.inject(MatDialog) as jasmine.SpyObj<MatDialog>;
    
    // Create the component
    const result = await createComponent(ExecutionDashboardComponent);
    fixture = result.fixture;
    component = result.component;
    
    // Initial change detection
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
  
  it('should load executions on init', () => {
    // Assert that the component made the API call to get executions
    expect(toolExecutionService.getExecutionHistory).toHaveBeenCalledWith(10, 0);
    
    // Check that the executions are assigned to the component
    expect(component.executions.data).toEqual(mockExecutions);
  });
  
  it('should subscribe to execution updates', () => {
    // Check that the component subscribed to execution updates
    expect(toolExecutionService.onExecutionUpdated).toHaveBeenCalled();
    
    // Simulate an execution update
    const updatedExecution = { ...mockExecutions[1], progress: 75 };
    (toolExecutionService.onExecutionUpdated as jasmine.Spy).calls.mostRecent().args[0].next(updatedExecution);
    
    // Check that the execution was updated in the table
    const updatedExec = component.executions.data.find(e => e.executionId === updatedExecution.executionId);
    expect(updatedExec?.progress).toBe(75);
  });
  
  it('should handle page change events', () => {
    // Reset the spy to track new calls
    (toolExecutionService.getExecutionHistory as jasmine.Spy).calls.reset();
    
    // Simulate a page change event
    component.onPageChange({ pageIndex: 1, pageSize: 20, length: 50 });
    
    // Check that the component made a new API call with the correct pagination
    expect(toolExecutionService.getExecutionHistory).toHaveBeenCalledWith(20, 20);
  });
  
  it('should filter executions by status', fakeAsync(() => {
    // Reset the spy to track new calls
    (toolExecutionService.getExecutionHistory as jasmine.Spy).calls.reset();
    
    // Set the status filter to 'completed'
    component.filtersForm.get('status')?.setValue('completed');
    tick(300); // Wait for debounce
    
    // Check that the component made a new API call with the status filter
    expect(toolExecutionService.getExecutionHistory).toHaveBeenCalledWith(10, 0, 'completed');
  }));
  
  it('should search executions by tool name', fakeAsync(() => {
    // Reset the spy to track new calls
    (toolExecutionService.getExecutionHistory as jasmine.Spy).calls.reset();
    
    // Set the search term
    component.filtersForm.get('search')?.setValue('test');
    tick(300); // Wait for debounce
    
    // Check that the component made a new API call with the search term
    expect(toolExecutionService.getExecutionHistory).toHaveBeenCalledWith(10, 0, undefined, 'test');
  }));
  
  it('should open execution details dialog', () => {
    // Click on the first row in the table
    const row = { ...mockExecutions[0] };
    component.openExecutionDetails(row);
    
    // Check that the dialog was opened with the correct data
    expect(dialog.open).toHaveBeenCalledWith(ExecutionDetailsDialogComponent, {
      width: '80%',
      maxWidth: '1000px',
      data: { execution: row }
    });
  });
  
  it('should cancel an execution', () => {
    // Reset the spy to track new calls
    (toolExecutionService.cancelExecution as jasmine.Spy).calls.reset();
    
    // Call the cancel method
    const executionId = 'exec-2';
    component.cancelExecution(executionId);
    
    // Check that the service was called with the correct execution ID
    expect(toolExecutionService.cancelExecution).toHaveBeenCalledWith(executionId);
  });
  
  it('should handle errors when loading executions', () => {
    // Reset the spy to throw an error
    const errorMessage = 'Failed to load executions';
    (toolExecutionService.getExecutionHistory as jasmine.Spy).and.returnValue(
      throwError(() => ({ message: errorMessage }))
    );
    
    // Spy on console.error
    spyOn(console, 'error');
    
    // Call the method that loads executions
    component.loadExecutions();
    
    // Check that the error was handled
    expect(console.error).toHaveBeenCalledWith('Error loading executions:', jasmine.any(Object));
    expect(component.isLoading).toBeFalse();
  });
  
  it('should format duration correctly', () => {
    // Test with start and end time
    const executionWithDuration = { 
      startTime: '2023-01-01T00:00:00Z',
      endTime: '2023-01-01T01:30:15Z'
    };
    expect(component.formatDuration(executionWithDuration as any)).toBe('1h 30m 15s');
    
    // Test with only start time (in progress)
    const inProgressExecution = { 
      startTime: '2023-01-01T00:00:00Z'
    };
    expect(component.formatDuration(inProgressExecution as any)).toBe('In progress');
    
    // Test with invalid times
    const invalidExecution = { 
      startTime: 'invalid',
      endTime: 'invalid'
    };
    expect(component.formatDuration(invalidExecution as any)).toBe('N/A');
  });
  
  it('should refresh the executions list', () => {
    // Reset the spy to track new calls
    (toolExecutionService.getExecutionHistory as jasmine.Spy).calls.reset();
    
    // Call the refresh method
    component.refresh();
    
    // Check that the component made a new API call
    expect(toolExecutionService.getExecutionHistory).toHaveBeenCalledWith(10, 0);
  });
  
  it('should unsubscribe from observables on destroy', () => {
    // Spy on the unsubscribe method of the subscriptions
    const spy1 = spyOn(component['executionUpdateSub'], 'unsubscribe');
    const spy2 = spyOn(component['executionStartSub'], 'unsubscribe');
    
    // Call ngOnDestroy
    component.ngOnDestroy();
    
    // Check that unsubscribe was called on all subscriptions
    expect(spy1).toHaveBeenCalled();
    expect(spy2).toHaveBeenCalled();
  });
  
  it('should display the correct status badge class', () => {
    expect(component.getStatusBadgeClass('completed')).toBe('status-completed');
    expect(component.getStatusBadgeClass('running')).toBe('status-running');
    expect(component.getStatusBadgeClass('failed')).toBe('status-failed');
    expect(component.getStatusBadgeClass('pending')).toBe('status-pending');
    expect(component.getStatusBadgeClass('cancelled')).toBe('status-cancelled');
    expect(component.getStatusBadgeClass('unknown')).toBe('status-unknown');
  });
  
  it('should reset filters', () => {
    // Set some filter values
    component.filtersForm.patchValue({
      status: 'completed',
      search: 'test',
      dateRange: {
        start: new Date('2023-01-01'),
        end: new Date('2023-01-31')
      }
    });
    
    // Reset the filters
    component.resetFilters();
    
    // Check that the form was reset
    expect(component.filtersForm.get('status')?.value).toBe('');
    expect(component.filtersForm.get('search')?.value).toBe('');
    expect(component.filtersForm.get('dateRange')?.value).toEqual({ start: null, end: null });
  });
  
  it('should handle empty execution list', () => {
    // Reset the spy to return an empty array
    (toolExecutionService.getExecutionHistory as jasmine.Spy).and.returnValue(of([]));
    
    // Reload the executions
    component.loadExecutions();
    
    // Check that the empty state is handled
    expect(component.executions.data.length).toBe(0);
    expect(component.executions.paginator).toBeDefined();
  });
});
