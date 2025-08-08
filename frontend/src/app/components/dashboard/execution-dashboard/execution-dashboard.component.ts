import { Component, OnDestroy, OnInit } from '@angular/core';
import { ToolExecutionService, ExecutionProgress, ToolMetadata } from 'src/app/services/tool-execution.service';
import { Subscription, combineLatest, BehaviorSubject } from 'rxjs';
import { debounceTime, distinctUntilChanged, map } from 'rxjs/operators';
import { FormControl } from '@angular/forms';

interface Execution extends ExecutionProgress {
  id: string;
  tool: string;
  status: 'pending' | 'running' | 'completed' | 'failed' | 'cancelled';
  progress: number;
  startTime: Date;
  endTime?: Date;
  duration?: number;
  result?: any;
  error?: string;
}

@Component({
  selector: 'app-execution-dashboard',
  templateUrl: './execution-dashboard.component.html',
  styleUrls: ['./execution-dashboard.component.scss']
})
export class ExecutionDashboardComponent implements OnInit, OnDestroy {
  // Execution data
  executions: Execution[] = [];
  filteredExecutions: Execution[] = [];
  activeExecutions: Execution[] = [];
  completedExecutions: Execution[] = [];
  
  // Filter controls
  statusFilter = new FormControl<string>('all');
  toolFilter = new FormControl<string>('all');
  searchTerm = new FormControl<string>('');
  
  // Pagination
  currentPage = 1;
  itemsPerPage = 10;
  totalItems = 0;
  
  // UI state
  isLoading = false;
  isInitialized = false;
  selectedExecution: Execution | null = null;
  
  // Available filters
  statuses = [
    { value: 'all', label: 'All Statuses' },
    { value: 'running', label: 'Running' },
    { value: 'completed', label: 'Completed' },
    { value: 'failed', label: 'Failed' },
    { value: 'cancelled', label: 'Cancelled' }
  ];
  
  tools: { value: string; label: string }[] = [];
  
  private subscriptions = new Subscription();
  private refresh$ = new BehaviorSubject<void>(undefined);

  constructor(private toolService: ToolExecutionService) {}

  ngOnInit(): void {
    this.initializeFilters();
    this.setupSubscriptions();
    this.loadInitialData();
  }

  ngOnDestroy(): void {
    this.subscriptions.unsubscribe();
  }

  private initializeFilters(): void {
    // Load available tools for filter
    this.tools = [
      { value: 'all', label: 'All Tools' },
      ...this.toolService.getAvailableTools().map(tool => ({
        value: tool.name,
        label: tool.name
      }))
    ];
  }

  private setupSubscriptions(): void {
    // Combine all filter changes
    const filterChanges$ = combineLatest([
      this.statusFilter.valueChanges.pipe(distinctUntilChanged()),
      this.toolFilter.valueChanges.pipe(distinctUntilChanged()),
      this.searchTerm.valueChanges.pipe(
        debounceTime(300),
        distinctUntilChanged()
      ),
      this.refresh$
    ]);

    // Subscribe to filter changes
    this.subscriptions.add(
      filterChanges$.subscribe(([status, tool, search]) => {
        this.currentPage = 1; // Reset to first page on filter change
        this.applyFilters();
      })
    );

    // Listen for new execution events
    this.subscriptions.add(
      this.toolService.onExecutionStarted().subscribe(execution => {
        this.handleNewExecution(execution);
      })
    );

    // Listen for execution updates
    this.subscriptions.add(
      this.toolService.onExecutionUpdated().subscribe(update => {
        this.updateExecution(update);
      })
    );
  }

  private loadInitialData(): void {
    this.isLoading = true;
    
    // Load initial execution history
    this.subscriptions.add(
      this.toolService.getExecutionHistory().subscribe({
        next: (executions) => {
          this.executions = executions.map(exec => ({
            ...exec,
            id: exec.execution_id,
            startTime: new Date(exec.timestamp),
            status: exec.status || 'completed',
            progress: exec.progress || 100
          }));
          
          this.applyFilters();
          this.isLoading = false;
          this.isInitialized = true;
        },
        error: (error) => {
          console.error('Failed to load execution history:', error);
          this.isLoading = false;
          this.isInitialized = true;
        }
      })
    );
  }

  private handleNewExecution(execution: ExecutionProgress): void {
    const existingIndex = this.executions.findIndex(e => e.id === execution.execution_id);
    
    const newExecution: Execution = {
      ...execution,
      id: execution.execution_id,
      tool: execution.tool || 'Unknown',
      status: execution.status || 'running',
      progress: execution.progress || 0,
      startTime: new Date(),
      result: execution['result'],
      error: execution.error
    };
    
    if (existingIndex >= 0) {
      this.executions[existingIndex] = newExecution;
    } else {
      this.executions.unshift(newExecution);
    }
    
    this.applyFilters();
  }

  private updateExecution(update: ExecutionProgress): void {
    const index = this.executions.findIndex(e => e.id === update.execution_id);
    
    if (index >= 0) {
      const updatedExecution: Execution = {
        ...this.executions[index],
        ...update,
        progress: update.progress || this.executions[index].progress,
        status: update.status || this.executions[index].status,
        result: update['result'] !== undefined ? update['result'] : this.executions[index].result,
        error: update.error || this.executions[index].error
      };
      
      if (['completed', 'failed', 'cancelled'].includes(updatedExecution.status)) {
        updatedExecution.endTime = new Date();
        updatedExecution.duration = updatedExecution.endTime.getTime() - updatedExecution.startTime.getTime();
      }
      
      this.executions[index] = updatedExecution;
      this.applyFilters();
      
      // Update selected execution if it's the one being updated
      if (this.selectedExecution?.id === updatedExecution.id) {
        this.selectedExecution = { ...updatedExecution };
      }
    }
  }

  private applyFilters(): void {
    // Apply status filter
    let filtered = [...this.executions];
    
    const statusFilter = this.statusFilter.value;
    if (statusFilter && statusFilter !== 'all') {
      filtered = filtered.filter(exec => exec.status === statusFilter);
    }
    
    // Apply tool filter
    const toolFilter = this.toolFilter.value;
    if (toolFilter && toolFilter !== 'all') {
      filtered = filtered.filter(exec => exec.tool === toolFilter);
    }
    
    // Apply search term
    const search = this.searchTerm.value?.toLowerCase();
    if (search) {
      filtered = filtered.filter(exec => 
        exec.tool.toLowerCase().includes(search) ||
        (exec.message && exec.message.toLowerCase().includes(search)) ||
        (exec.error && exec.error.toLowerCase().includes(search)) ||
        exec.id.toLowerCase().includes(search)
      );
    }
    
    // Update filtered executions
    this.filteredExecutions = [...filtered];
    
    // Update active/completed executions
    this.activeExecutions = filtered.filter(exec => 
      ['pending', 'running'].includes(exec.status)
    );
    
    this.completedExecutions = filtered.filter(exec => 
      !['pending', 'running'].includes(exec.status)
    );
    
    // Update pagination
    this.totalItems = this.filteredExecutions.length;
    this.updatePaginatedExecutions();
  }

  private updatePaginatedExecutions(): void {
    const startIndex = (this.currentPage - 1) * this.itemsPerPage;
    const endIndex = startIndex + this.itemsPerPage;
    
    // The template will handle pagination
    // This method is a placeholder for future pagination logic
  }

  // UI Event Handlers
  onPageChange(page: number): void {
    this.currentPage = page;
    this.updatePaginatedExecutions();
  }

  onItemsPerPageChange(itemsPerPage: number): void {
    this.itemsPerPage = itemsPerPage;
    this.currentPage = 1;
    this.updatePaginatedExecutions();
  }

  onSelectExecution(execution: Execution): void {
    this.selectedExecution = execution;
  }

  onCloseDetails(): void {
    this.selectedExecution = null;
  }

  onCancelExecution(executionId: string): void {
    this.toolService.cancelExecution(executionId).subscribe({
      next: () => {
        // The execution update will be handled by the subscription
      },
      error: (error) => {
        console.error('Failed to cancel execution:', error);
      }
    });
  }

  onRefresh(): void {
    this.refresh$.next();
  }

  // Helper methods for the template
  getStatusBadgeClass(status: string): string {
    switch (status) {
      case 'running':
        return 'badge bg-primary';
      case 'completed':
        return 'badge bg-success';
      case 'failed':
        return 'badge bg-danger';
      case 'cancelled':
        return 'badge bg-warning text-dark';
      case 'pending':
        return 'badge bg-secondary';
      default:
        return 'badge bg-light text-dark';
    }
  }

  formatDuration(durationMs: number): string {
    if (!durationMs) return 'N/A';
    
    const seconds = Math.floor(durationMs / 1000);
    const minutes = Math.floor(seconds / 60);
    const hours = Math.floor(minutes / 60);
    
    if (hours > 0) {
      return `${hours}h ${minutes % 60}m`;
    } else if (minutes > 0) {
      return `${minutes}m ${seconds % 60}s`;
    } else {
      return `${seconds}s`;
    }
  }

  formatTimestamp(timestamp: Date | string | number): string {
    if (!timestamp) return 'N/A';
    
    const date = timestamp instanceof Date ? timestamp : new Date(timestamp);
    return date.toLocaleString();
  }

  // For the template to track items in ngFor
  trackByExecutionId(index: number, execution: Execution): string {
    return execution.id;
  }
}
