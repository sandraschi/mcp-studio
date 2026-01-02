export interface ServerStatus {
  id: string;
  name: string;
  status: 'online' | 'offline' | 'error';
  lastSeen: string;
  toolCount: number;
  cpuUsage: number;
  memoryUsage: number;
}

export interface RecentActivity {
  id: string;
  type: 'tool_run' | 'server_connect' | 'template_created' | 'error';
  title: string;
  description: string;
  timestamp: string;
  status?: 'success' | 'error' | 'warning' | 'info';
}

export interface ResourceUsage {
  cpu: number;
  memory: number;
  storage: number;
}

export interface UsageStats {
  dailyExecutions: number[];
  serverLoad: number[];
  resourceUsage: ResourceUsage;
}

export interface DashboardState {
  lastUpdated: Date;
  isRefreshing: boolean;
  serverStatus: ServerStatus[];
  recentActivity: RecentActivity[];
  usageStats: UsageStats | null;
}

export type ActivityType = RecentActivity['type'];
export type StatusType = ServerStatus['status'];

// Chart data types
export interface ChartDataPoint {
  x: string | number | Date;
  y: number;
}

export interface ChartDataset {
  label: string;
  data: ChartDataPoint[] | number[];
  backgroundColor?: string | string[];
  borderColor?: string | string[];
  borderWidth?: number;
  fill?: boolean;
  tension?: number;
}

export interface ChartConfig {
  labels: string[];
  datasets: ChartDataset[];
}

// Utility types for API responses
export interface ApiResponse<T> {
  data: T;
  error: string | null;
  timestamp: string;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  pageSize: number;
  hasMore: boolean;
}

// Server status metrics
export interface ServerMetrics {
  cpu: number;
  memory: number;
  uptime: number;
  activeConnections: number;
  errorRate: number;
}

// Tool execution stats
export interface ToolExecutionStats {
  totalExecutions: number;
  successRate: number;
  averageDuration: number;
  byTool: Record<string, number>;
  byUser: Record<string, number>;
  byDay: Record<string, number>;
}
