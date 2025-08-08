import { Component, OnDestroy, OnInit } from '@angular/core';
import { NavigationEnd, Router, RouterOutlet } from '@angular/router';
import { Subscription } from 'rxjs';
import { filter } from 'rxjs/operators';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-dashboard',
  template: `
    <div class="dashboard-container">
      <div class="dashboard-sidenav">
        <div class="sidenav-header">
          <h3>MCP Studio</h3>
        </div>
        <nav class="sidenav-menu">
          <a [routerLink]="['/dashboard/executions']" 
             [class.active]="isActive('/dashboard/executions')"
             class="sidenav-menu-item">
            <i class="bi bi-speedometer2 me-2"></i>
            <span>Execution Dashboard</span>
          </a>
          <!-- Add more navigation items here -->
        </nav>
      </div>
      
      <div class="dashboard-content">
        <header class="dashboard-toolbar">
          <div class="toolbar-left">
            <h4 class="mb-0">{{ pageTitle }}</h4>
          </div>
          <div class="toolbar-right">
            <!-- Add user menu or other controls here -->
          </div>
        </header>
        
        <main class="dashboard-main">
          <router-outlet></router-outlet>
        </main>
      </div>
    </div>
  `,
  styles: [`
    .dashboard-container {
      display: flex;
      min-height: 100vh;
      background-color: #f5f7fa;
    }
    
    .dashboard-sidenav {
      width: 250px;
      background-color: #2c3e50;
      color: #ecf0f1;
      padding: 1.5rem 0;
      box-shadow: 2px 0 5px rgba(0, 0, 0, 0.1);
      z-index: 10;
    }
    
    .sidenav-header {
      padding: 0 1.5rem 1.5rem;
      border-bottom: 1px solid rgba(255, 255, 255, 0.1);
      margin-bottom: 1rem;
    }
    
    .sidenav-header h3 {
      color: #fff;
      margin: 0;
      font-weight: 600;
    }
    
    .sidenav-menu {
      display: flex;
      flex-direction: column;
    }
    
    .sidenav-menu-item {
      display: flex;
      align-items: center;
      padding: 0.75rem 1.5rem;
      color: #bdc3c7;
      text-decoration: none;
      transition: all 0.3s ease;
    }
    
    .sidenav-menu-item:hover {
      background-color: rgba(255, 255, 255, 0.1);
      color: #ecf0f1;
    }
    
    .sidenav-menu-item.active {
      background-color: #3498db;
      color: white;
      border-left: 4px solid #2980b9;
    }
    
    .sidenav-menu-item i {
      margin-right: 0.5rem;
      font-size: 1.1rem;
    }
    
    .dashboard-content {
      flex: 1;
      display: flex;
      flex-direction: column;
      overflow: hidden;
    }
    
    .dashboard-toolbar {
      background-color: #fff;
      padding: 1rem 2rem;
      display: flex;
      justify-content: space-between;
      align-items: center;
      box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
      z-index: 5;
    }
    
    .dashboard-main {
      flex: 1;
      padding: 2rem;
      overflow-y: auto;
    }
    
    /* Responsive adjustments */
    @media (max-width: 992px) {
      .dashboard-sidenav {
        width: 220px;
      }
    }
    
    @media (max-width: 768px) {
      .dashboard-sidenav {
        width: 60px;
        overflow: hidden;
      }
      
      .sidenav-header h3,
      .sidenav-menu-item span {
        display: none;
      }
      
      .sidenav-menu-item {
        justify-content: center;
        padding: 1rem 0;
      }
      
      .sidenav-menu-item i {
        margin-right: 0;
        font-size: 1.25rem;
      }
    }
  `],
  standalone: true,
  imports: [
    CommonModule,
    RouterOutlet
  ]
})
export class DashboardComponent implements OnInit, OnDestroy {
  pageTitle = 'Dashboard';
  private routerSub: Subscription;

  constructor(private router: Router) {}

  ngOnInit(): void {
    // Set initial title based on current route
    this.updateTitle(this.router.url);
    
    // Update title on route changes
    this.routerSub = this.router.events.pipe(
      filter(event => event instanceof NavigationEnd)
    ).subscribe((event: any) => {
      this.updateTitle(event.url);
    });
  }

  ngOnDestroy(): void {
    if (this.routerSub) {
      this.routerSub.unsubscribe();
    }
  }

  isActive(url: string): boolean {
    return this.router.isActive(url, true);
  }

  private updateTitle(url: string): void {
    // Extract the route and set the page title accordingly
    if (url.includes('executions')) {
      this.pageTitle = 'Execution Dashboard';
    } else if (url.includes('tools')) {
      this.pageTitle = 'Tool Explorer';
    } else {
      this.pageTitle = 'Dashboard';
    }
  }
}
