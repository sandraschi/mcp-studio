import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, BehaviorSubject, of } from 'rxjs';
import { catchError, map, tap } from 'rxjs/operators';
import { environment } from '../../environments/environment';

export enum ServerStatus {
  ONLINE = 'online',
  OFFLINE = 'offline',
  STARTING = 'starting',
  STOPPING = 'stopping',
  ERROR = 'error',
  UNKNOWN = 'unknown'
}

export enum ServerType {
  DOCKER = 'docker',
  PYTHON = 'python',
  NODE = 'node',
  UNKNOWN = 'unknown'
}

export interface Server {
  id: string;
  name: string;
  type: ServerType;
  status: ServerStatus;
  command: string;
  args: string[];
  cwd?: string;
  env?: string[];
  description: string;
}

@Injectable({
  providedIn: 'root'
})
export class ServerService {
  private apiUrl = `${environment.apiUrl}/api/servers`;
  private serversSubject = new BehaviorSubject<Server[]>([]);
  private loadingSubject = new BehaviorSubject<boolean>(false);
  private errorSubject = new BehaviorSubject<string | null>(null);

  // Public observables
  servers$ = this.serversSubject.asObservable();
  loading$ = this.loadingSubject.asObservable();
  error$ = this.errorSubject.asObservable();

  constructor(private http: HttpClient) {
    this.loadServers();
  }

  /**
   * Load all MCP servers
   */
  loadServers(): void {
    this.loadingSubject.next(true);
    this.errorSubject.next(null);

    this.http.get<Server[]>(this.apiUrl)
      .pipe(
        catchError(error => {
          console.error('Failed to load servers:', error);
          this.errorSubject.next('Failed to load servers. Please try again.');
          return of([]);
        }),
        tap(() => this.loadingSubject.next(false))
      )
      .subscribe(servers => {
        this.serversSubject.next(servers);
      });
  }

  /**
   * Get a server by ID
   * @param id Server ID
   */
  getServer(id: string): Observable<Server | undefined> {
    return this.servers$.pipe(
      map(servers => servers.find(server => server.id === id))
    );
  }

  /**
   * Start a server
   * @param id Server ID
   */
  startServer(id: string): Observable<Server> {
    this.loadingSubject.next(true);
    return this.http.post<Server>(`${this.apiUrl}/${id}/start`, {}).pipe(
      tap(() => {
        // Update the server status in the local state
        const servers = this.serversSubject.value;
        const index = servers.findIndex(s => s.id === id);
        if (index >= 0) {
          servers[index] = { ...servers[index], status: ServerStatus.STARTING };
          this.serversSubject.next(servers);
        }
        this.loadServers(); // Refresh the list after a short delay
      }),
      catchError(error => {
        console.error(`Failed to start server ${id}:`, error);
        this.errorSubject.next(`Failed to start server: ${error.message}`);
        throw error;
      }),
      finalize(() => this.loadingSubject.next(false))
    );
  }

  /**
   * Stop a server
   * @param id Server ID
   */
  stopServer(id: string): Observable<Server> {
    this.loadingSubject.next(true);
    return this.http.post<Server>(`${this.apiUrl}/${id}/stop`, {}).pipe(
      tap(() => {
        // Update the server status in the local state
        const servers = this.serversSubject.value;
        const index = servers.findIndex(s => s.id === id);
        if (index >= 0) {
          servers[index] = { ...servers[index], status: ServerStatus.STOPPING };
          this.serversSubject.next(servers);
        }
        this.loadServers(); // Refresh the list after a short delay
      }),
      catchError(error => {
        console.error(`Failed to stop server ${id}:`, error);
        this.errorSubject.next(`Failed to stop server: ${error.message}`);
        throw error;
      }),
      finalize(() => this.loadingSubject.next(false))
    );
  }

  /**
   * Get the status class for a server
   * @param status Server status
   */
  getStatusClass(status: ServerStatus): string {
    switch (status) {
      case ServerStatus.ONLINE:
        return 'status-online';
      case ServerStatus.OFFLINE:
        return 'status-offline';
      case ServerStatus.STARTING:
        return 'status-starting';
      case ServerStatus.STOPPING:
        return 'status-stopping';
      case ServerStatus.ERROR:
        return 'status-error';
      default:
        return 'status-unknown';
    }
  }

  /**
   * Get the display name for a server type
   * @param type Server type
   */
  getTypeDisplayName(type: ServerType): string {
    switch (type) {
      case ServerType.DOCKER:
        return 'Docker';
      case ServerType.PYTHON:
        return 'Python';
      case ServerType.NODE:
        return 'Node.js';
      default:
        return 'Unknown';
    }
  }

  /**
   * Get the icon for a server type
   * @param type Server type
   */
  getTypeIcon(type: ServerType): string {
    switch (type) {
      case ServerType.DOCKER:
        return 'fab fa-docker';
      case ServerType.PYTHON:
        return 'fab fa-python';
      case ServerType.NODE:
        return 'fab fa-node-js';
      default:
        return 'fas fa-server';
    }
  }
}

// Helper operator to handle finalize in a type-safe way
function finalize<T>(callback: () => void) {
  return (source: Observable<T>): Observable<T> => {
    return new Observable(subscriber => {
      const subscription = source.subscribe({
        next: value => subscriber.next(value),
        error: err => {
          try {
            callback();
          } catch (e) {
            subscriber.error(e);
            return;
          }
          subscriber.error(err);
        },
        complete: () => {
          try {
            callback();
          } catch (e) {
            subscriber.error(e);
            return;
          }
          subscriber.complete();
        }
      });

      return () => {
        subscription.unsubscribe();
      };
    });
  };
}
