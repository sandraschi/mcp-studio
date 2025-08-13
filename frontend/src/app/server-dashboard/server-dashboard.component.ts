import { Component, OnInit, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ServerService, Server, ServerStatus, ServerType } from '../../services/server.service';
import { Subscription } from 'rxjs';

@Component({
  selector: 'app-server-dashboard',
  templateUrl: './server-dashboard.component.html',
  styleUrls: ['./server-dashboard.component.css']
})
export class ServerDashboardComponent implements OnInit, OnDestroy {
  servers: Server[] = [];
  loading = false;
  error: string | null = null;
  private subscriptions = new Subscription();

  constructor(private serverService: ServerService) {}

  ngOnInit(): void {
    this.loadServers();
    
    // Subscribe to server updates
    this.subscriptions.add(
      this.serverService.servers$.subscribe(servers => {
        this.servers = servers;
      })
    );
    
    // Subscribe to loading state
    this.subscriptions.add(
      this.serverService.loading$.subscribe(loading => {
        this.loading = loading;
      })
    );
    
    // Subscribe to errors
    this.subscriptions.add(
      this.serverService.error$.subscribe(error => {
        this.error = error;
      })
    );
  }

  ngOnDestroy(): void {
    this.subscriptions.unsubscribe();
  }

  loadServers(): void {
    this.serverService.loadServers();
  }

  startServer(serverId: string, event?: Event): void {
    if (event) {
      event.stopPropagation();
    }
    
    this.serverService.startServer(serverId).subscribe({
      next: () => {
        console.log(`Server ${serverId} started`);
      },
      error: (err) => {
        console.error('Failed to start server:', err);
      }
    });
  }

  stopServer(serverId: string, event?: Event): void {
    if (event) {
      event.stopPropagation();
    }
    
    this.serverService.stopServer(serverId).subscribe({
      next: () => {
        console.log(`Server ${serverId} stopped`);
      },
      error: (err) => {
        console.error('Failed to stop server:', err);
      }
    });
  }

  getStatusClass(status: ServerStatus): string {
    return this.serverService.getStatusClass(status);
  }

  getTypeIcon(type: ServerType): string {
    return this.serverService.getTypeIcon(type);
  }

  getTypeDisplayName(type: ServerType): string {
    return this.serverService.getTypeDisplayName(type);
  }

  refresh(): void {
    this.loadServers();
  }
}
