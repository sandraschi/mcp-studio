import { Component, EventEmitter, Input, OnDestroy, OnInit, Output } from '@angular/core';
import { FormBuilder, FormGroup, Validators, FormControl, FormArray } from '@angular/forms';
import { ToolExecutionService, ToolMetadata, ToolParameter, ExecutionProgress } from 'src/app/services/tool-execution.service';
import { Subscription } from 'rxjs';

@Component({
  selector: 'app-tool-execution-form',
  templateUrl: './tool-execution-form.component.html',
  styleUrls: ['./tool-execution-form.component.scss']
})
export class ToolExecutionFormComponent implements OnInit, OnDestroy {
  @Input() tool: ToolMetadata;
  @Output() executionComplete = new EventEmitter<ExecutionProgress>();
  
  executionForm: FormGroup;
  isExecuting = false;
  executionProgress: number = 0;
  executionStatus: string = '';
  executionMessage: string = '';
  executionResult: any = null;
  executionError: string | null = null;
  executionId: string | null = null;
  
  private subscriptions: Subscription = new Subscription();

  constructor(
    private fb: FormBuilder,
    private toolService: ToolExecutionService
  ) {}

  ngOnInit(): void {
    this.createForm();
  }

  ngOnDestroy(): void {
    this.subscriptions.unsubscribe();
  }

  createForm(): void {
    const formGroup: any = {};
    
    // Add form controls for each parameter
    if (this.tool?.parameters) {
      Object.entries(this.tool.parameters).forEach(([paramName, paramDef]) => {
        const validators = [];
        
        if (paramDef.required) {
          validators.push(Validators.required);
        }
        
        // Add type-specific validators
        if (paramDef.type === 'number' || paramDef.type === 'integer') {
          validators.push(Validators.pattern(/^-?\d*\.?\d+$/));
        } else if (paramDef.type === 'email') {
          validators.push(Validators.email);
        } else if (paramDef.type === 'url') {
          validators.push(Validators.pattern(/^https?:\/\/[\w\-]+(\.[\w\-]+)+[/#?]?.*$/));
        }
        
        // Set default value if available
        const defaultValue = paramDef.default !== undefined ? paramDef.default : '';
        
        formGroup[paramName] = [defaultValue, validators];
      });
    }
    
    this.executionForm = this.fb.group(formGroup);
  }

  onSubmit(): void {
    if (this.executionForm.invalid) {
      this.markFormGroupTouched(this.executionForm);
      return;
    }
    
    this.isExecuting = true;
    this.executionProgress = 0;
    this.executionStatus = 'pending';
    this.executionMessage = 'Starting execution...';
    this.executionResult = null;
    this.executionError = null;
    
    // Execute the tool with the form values
    const execution$ = this.toolService.executeTool(
      this.tool.name,
      this.executionForm.value
    );
    
    this.subscriptions.add(
      execution$.subscribe({
        next: (progress: ExecutionProgress) => {
          this.executionProgress = progress.progress;
          this.executionStatus = progress.status;
          this.executionMessage = progress.message || '';
          this.executionId = progress.execution_id;
          
          if (progress.status === 'completed') {
            this.executionResult = progress['result'];
            this.isExecuting = false;
            this.executionComplete.emit(progress);
          } else if (progress.status === 'failed') {
            this.executionError = progress.message || 'Execution failed';
            this.isExecuting = false;
            this.executionComplete.emit(progress);
          }
        },
        error: (error) => {
          console.error('Tool execution error:', error);
          this.executionError = error.message || 'An error occurred during execution';
          this.executionStatus = 'failed';
          this.isExecuting = false;
          this.executionComplete.emit({
            execution_id: this.executionId || `error_${Date.now()}`,
            tool: this.tool.name,
            progress: 0,
            status: 'failed',
            message: this.executionError,
            timestamp: Date.now()
          });
        }
      })
    );
  }

  onCancel(): void {
    if (this.executionId) {
      this.toolService.cancelExecution(this.executionId);
    }
    this.resetForm();
  }

  resetForm(): void {
    this.isExecuting = false;
    this.executionProgress = 0;
    this.executionStatus = '';
    this.executionMessage = '';
    this.executionResult = null;
    this.executionError = null;
    this.executionId = null;
    this.executionForm.reset();
    
    // Reset form to default values
    if (this.tool?.parameters) {
      Object.entries(this.tool.parameters).forEach(([paramName, paramDef]) => {
        if (paramDef.default !== undefined) {
          this.executionForm.get(paramName)?.setValue(paramDef.default);
        }
      });
    }
  }

  getParamType(param: ToolParameter): string {
    switch (param.type) {
      case 'number':
      case 'integer':
      case 'float':
        return 'number';
      case 'boolean':
        return 'checkbox';
      case 'date':
        return 'date';
      case 'datetime':
        return 'datetime-local';
      case 'time':
        return 'time';
      case 'email':
        return 'email';
      case 'url':
        return 'url';
      case 'textarea':
        return 'textarea';
      case 'password':
        return 'password';
      case 'file':
        return 'file';
      default:
        return 'text';
    }
  }

  getEnumOptions(param: ToolParameter): any[] {
    if (param.enum) {
      return param.enum.map((value: any) => ({
        value,
        label: String(value)
      }));
    }
    return [];
  }

  private markFormGroupTouched(formGroup: FormGroup | FormArray) {
    Object.values(formGroup.controls).forEach(control => {
      control.markAsTouched();
      
      if (control instanceof FormGroup || control instanceof FormArray) {
        this.markFormGroupTouched(control);
      }
    });
  }

  get showProgress(): boolean {
    return this.isExecuting || this.executionStatus === 'completed' || this.executionStatus === 'failed';
  }
}
