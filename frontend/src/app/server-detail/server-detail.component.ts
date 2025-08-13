import { Component, OnInit, OnDestroy } from '@angular/core';
import { ActivatedRoute, Router } from '@angular/router';
import { Subscription } from 'rxjs';
import { ServerService, Server, ServerStatus, ServerType } from '../../services/server.service';

@Component({
  selector: 'app-server-detail',
  templateUrl: './server-detail.component.html',
  styleUrls: ['./server-detail.component.css']
})
export class ServerDetailComponent implements OnInit, OnDestroy {
  server: Server | null = null;
  tools: any[] = [];
  loading = true;
  loadingTools = false;
  error: string | null = null;
  private subscriptions = new Subscription();

  constructor(
    private route: ActivatedRoute,
    private router: Router,
    private serverService: ServerService
  ) {}

  ngOnInit(): void {
    const serverId = this.route.snapshot.paramMap.get('id');
    if (!serverId) {
      this.error = 'No server ID provided';
      this.loading = false;
      return;
    }

    this.loadServer(serverId);

    // Subscribe to server updates
    this.subscriptions.add(
      this.serverService.servers$.subscribe(servers => {
        const server = servers.find(s => s.id === serverId);
        if (server) {
          this.server = server;
        }
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

  loadServer(serverId: string): void {
    this.serverService.getServer(serverId).subscribe({
      next: (server) => {
        if (server) {
          this.server = server;
          this.loadTools(serverId);
        } else {
          this.error = 'Server not found';
        }
        this.loading = false;
      },
      error: (error) => {
        this.error = `Failed to load server: ${error.message}`;
        this.loading = false;
      }
    });
  }

  loadTools(serverId: string): void {
    if (this.loadingTools) return;
    
    this.loadingTools = true;
    this.serverService.getServerTools(serverId).subscribe({
      next: (tools) => {
        this.tools = tools;
        this.loadingTools = false;
      },
      error: (error) => {
        console.error('Failed to load tools:', error);
        this.error = `Failed to load tools: ${error.message}`;
        this.loadingTools = false;
      }
    });
  }

  onStartServer(): void {
    if (!this.server) return;
    
    this.serverService.startServer(this.server.id).subscribe({
      next: () => {
        console.log(`Server ${this.server?.id} started`);
      },
      error: (err) => {
        console.error('Failed to start server:', err);
      }
    });
  }

  onStopServer(): void {
    if (!this.server) return;
    
    this.serverService.stopServer(this.server.id).subscribe({
      next: () => {
        console.log(`Server ${this.server?.id} stopped`);
      },
      error: (err) => {
        console.error('Failed to stop server:', err);
      }
    });
  }

  onBack(): void {
    this.router.navigate(['/servers']);
  }

  onExecuteTool(toolName: string): void {
    if (!this.server) return;
    
    // TODO: Implement tool execution
    console.log(`Executing tool ${toolName} on server ${this.server.id}`);
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
}
