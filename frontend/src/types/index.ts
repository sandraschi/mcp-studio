// Server-related types
export interface Server {
  id: string;
  name: string;
  description?: string;
  version?: string;
  status: 'online' | 'offline' | 'error' | 'starting' | 'stopping' | 'warning';
  latency?: number;
  tools: Tool[];
  last_seen?: string;
  error?: string;
  metadata?: Record<string, any>;
}

export interface Tool {
  id: string;
  name: string;
  description: string;
  categories?: string[];
  parameters?: ToolParameter[];
  returnType?: string;
  examples?: ToolExample[];
  metadata?: Record<string, any>;
  serverId?: string;
  formattedDocstring?: {
    html?: string;
    markdown?: string;
    parsed?: Record<string, any>;
  };
}

export interface ToolExample {
  name: string;
  description?: string;
  input: Record<string, any>;
  output: any;
}

export interface ToolCategory {
  id: string;
  name: string;
  description?: string;
  icon?: string;
  count?: number;
}

export interface ToolParameter {
  name: string;
  type: 'string' | 'number' | 'boolean' | 'array' | 'object' | 'file' | string;
  description?: string;
  required?: boolean;
  default?: any;
  enum?: string[];
  format?: string;
  minimum?: number;
  maximum?: number;
  minLength?: number;
  maxLength?: number;
  pattern?: string;
  items?: ToolParameter;
  properties?: Record<string, ToolParameter>;
  additionalProperties?: boolean | ToolParameter;
}

// API response types
export interface ApiResponse<T = any> {
  data?: T;
  error?: string;
  status: 'success' | 'error' | 'partial';
  meta?: {
    page?: number;
    pageSize?: number;
    total?: number;
    hasMore?: boolean;
  };
  warnings?: string[];
  requestId?: string;
  timestamp?: string;
}

// Search and filter types
export interface SearchOptions {
  query?: string;
  filters?: Record<string, any>;
  sortBy?: string;
  sortOrder?: 'asc' | 'desc';
  page?: number;
  pageSize?: number;
}

export interface SearchResult<T> {
  items: T[];
  total: number;
  page: number;
  pageSize: number;
  hasMore: boolean;
}

// WebSocket message types
export type WebSocketMessage =
  | { type: 'update'; data: Server[] }
  | { type: 'server_status'; serverId: string; status: Server['status'] }
  | { type: 'tool_execution'; serverId: string; toolName: string; result: any }
  | { type: 'error'; message: string };

// UI state types
export interface UiState {
  darkMode: boolean;
  sidebarOpen: boolean;
  currentView: 'dashboard' | 'servers' | 'tools' | 'settings' | 'explore';
  selectedServerId: string | null;
  selectedTool: {
    serverId: string;
    toolId: string;
    tab?: 'test' | 'documentation' | 'history';
  } | null;
  theme: {
    primaryColor: string;
    secondaryColor: string;
    fontFamily: string;
    borderRadius: string;
  };
  layout: {
    cardView: 'grid' | 'list';
    density: 'compact' | 'normal' | 'comfortable';
    showToolIcons: boolean;
  };
  notifications: Notification[];
}

export interface Notification {
  id: string;
  type: 'info' | 'success' | 'warning' | 'error';
  title: string;
  message: string;
  timestamp: string;
  read: boolean;
  action?: {
    label: string;
    onClick: () => void;
  };
}

// Form types
export interface ServerFormData {
  name: string;
  command: string;
  args: string;
  cwd?: string;
  autoStart: boolean;
}

// Event types
export interface ServerEvent {
  type: 'start' | 'stop' | 'restart' | 'status_change' | 'health_check';
  serverId: string;
  serverName?: string;
  timestamp: string;
  status?: Server['status'];
  error?: string;
  metadata?: {
    cpuUsage?: number;
    memoryUsage?: number;
    uptime?: number;
    activeConnections?: number;
  };
}

export interface UIEvents {
  type: 'notification' | 'navigation' | 'theme_change' | 'layout_change';
  timestamp: string;
  payload: any;
}

export interface AnalyticsEvent {
  event: string;
  category: string;
  label?: string;
  value?: number;
  metadata?: Record<string, any>;
  timestamp: string;
  userId?: string;
  sessionId?: string;
}

export interface ToolExecutionEvent {
  serverId: string;
  toolName: string;
  parameters: Record<string, any>;
  timestamp: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  result?: any;
  error?: string;
}

export interface ToolExecutionResult {
  stdout?: string;
  stderr?: string;
  result?: any;
  status?: string;
  execution_time?: number;
}
