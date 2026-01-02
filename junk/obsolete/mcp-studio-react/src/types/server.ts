export enum ServerStatus {
  OFFLINE = 'offline',
  STARTING = 'starting',
  ONLINE = 'online',
  ERROR = 'error',
  STOPPING = 'stopping',
  UNKNOWN = 'unknown',
}

export interface Server {
  id: string;
  name: string;
  description?: string;
  status: ServerStatus;
  host: string;
  port: number;
  protocol: 'http' | 'https' | 'ws' | 'wss';
  basePath?: string;
  lastSeen?: string;
  lastError?: string;
  metadata?: Record<string, any>;
  tags?: string[];
  createdAt: string;
  updatedAt: string;
}

export interface ServerStatusUpdate {
  serverId: string;
  status: ServerStatus;
  timestamp: string;
  error?: string;
}

export interface ServerLog {
  timestamp: string;
  level: 'info' | 'warning' | 'error' | 'debug';
  message: string;
  meta?: Record<string, any>;
}

export interface ServerStats {
  cpuUsage: number;
  memoryUsage: number;
  uptime: number;
  activeConnections: number;
  lastUpdated: string;
}

export interface ServerConnectionInfo {
  serverId: string;
  isConnected: boolean;
  lastConnectionAttempt?: string;
  lastError?: string;
  connectionUrl: string;
}

export interface ServerRegistration {
  name: string;
  host: string;
  port: number;
  protocol?: 'http' | 'https' | 'ws' | 'wss';
  basePath?: string;
  description?: string;
  authToken?: string;
  metadata?: Record<string, any>;
  tags?: string[];
}

export interface ServerUpdate extends Partial<ServerRegistration> {
  id: string;
}

export interface ServerDiscoveryOptions {
  scanLocalNetwork?: boolean;
  scanPorts?: number[];
  timeout?: number;
  protocolFilter?: ('http' | 'https' | 'ws' | 'wss')[];
}
