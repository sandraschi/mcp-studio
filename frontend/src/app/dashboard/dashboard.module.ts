import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule, Routes } from '@angular/router';
import { FormsModule, ReactiveFormsModule } from '@angular/forms';

// Angular Material
import { MatButtonModule } from '@angular/material/button';
import { MatCardModule } from '@angular/material/card';
import { MatTableModule } from '@angular/material/table';
import { MatPaginatorModule } from '@angular/material/paginator';
import { MatSortModule } from '@angular/material/sort';
import { MatProgressBarModule } from '@angular/material/progress-bar';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatTabsModule } from '@angular/material/tabs';
import { MatIconModule } from '@angular/material/icon';
import { MatTooltipModule } from '@angular/material/tooltip';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatSelectModule } from '@angular/material/select';
import { MatMenuModule } from '@angular/material/menu';
import { MatSnackBarModule } from '@angular/material/snack-bar';
import { MatDialogModule } from '@angular/material/dialog';

// NgBootstrap
import { NgbModule } from '@ng-bootstrap/ng-bootstrap';
import { NgbPaginationModule } from '@ng-bootstrap/ng-bootstrap';

// Components
import { DashboardComponent } from './dashboard.component';
import { ExecutionDashboardComponent } from '../components/dashboard/execution-dashboard/execution-dashboard.component';

// Services
import { ToolExecutionService } from '../services/tool-execution.service';
import { WebSocketService } from '../services/websocket.service';
import { AuthGuard } from '../core/guards/auth.guard';

// Pipes
import { SafeHtmlPipe } from '../shared/pipes/safe-html.pipe';
import { KeysPipe } from '../shared/pipes/keys.pipe';

const dashboardRoutes: Routes = [
  {
    path: '',
    component: DashboardComponent,
    canActivate: [AuthGuard],
    children: [
      { path: '', redirectTo: 'executions', pathMatch: 'full' },
      { 
        path: 'executions', 
        component: ExecutionDashboardComponent,
        data: { title: 'Execution Dashboard' }
      },
      // Add more dashboard routes here as needed
    ]
  }
];

@NgModule({
  declarations: [
    DashboardComponent,
    ExecutionDashboardComponent,
    SafeHtmlPipe,
    KeysPipe
  ],
  imports: [
    CommonModule,
    FormsModule,
    ReactiveFormsModule,
    RouterModule.forChild(dashboardRoutes),
    
    // Angular Material
    MatButtonModule,
    MatCardModule,
    MatTableModule,
    MatPaginatorModule,
    MatSortModule,
    MatProgressBarModule,
    MatProgressSpinnerModule,
    MatTabsModule,
    MatIconModule,
    MatTooltipModule,
    MatFormFieldModule,
    MatInputModule,
    MatSelectModule,
    MatMenuModule,
    MatSnackBarModule,
    MatDialogModule,
    
    // NgBootstrap
    NgbModule,
    NgbPaginationModule
  ],
  providers: [
    ToolExecutionService,
    WebSocketService
  ]
})
export class DashboardModule { }
