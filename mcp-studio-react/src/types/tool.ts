import { Server } from './server';

export interface ToolParameter {
  name: string;
  type: string;
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
  items?: {
    type: string;
    [key: string]: any;
  };
  [key: string]: any;
}

export interface ToolMetadata {
  category?: string;
  version?: string;
  author?: string;
  description?: string;
  documentationUrl?: string;
  icon?: string;
  tags?: string[];
  [key: string]: any;
}

export interface Tool {
  name: string;
  description: string;
  parameters: ToolParameter[];
  serverId: string;
  server?: Server;
  metadata?: ToolMetadata;
  createdAt?: string;
  updatedAt?: string;
}

export interface ToolExecutionRequest {
  serverId: string;
  toolName: string;
  parameters: Record<string, any>;
  executionId?: string;
  metadata?: Record<string, any>;
}

export interface ToolExecutionResult {
  executionId: string;
  status: 'pending' | 'running' | 'completed' | 'failed' | 'cancelled';
  result?: any;
  error?: string;
  progress?: number;
  logs?: string[];
  startedAt: string;
  completedAt?: string;
  metadata?: Record<string, any>;
}

export interface ToolExecutionUpdate extends ToolExecutionResult {
  type: 'status' | 'progress' | 'log' | 'result' | 'error';
  timestamp: string;
}

export interface ToolExecutionLog {
  timestamp: string;
  level: 'info' | 'warning' | 'error' | 'debug';
  message: string;
  data?: any;
}

export interface ToolExecutionOptions {
  timeout?: number;
  priority?: 'low' | 'normal' | 'high';
  metadata?: Record<string, any>;
  onProgress?: (update: ToolExecutionUpdate) => void;
  onLog?: (log: ToolExecutionLog) => void;
  onComplete?: (result: ToolExecutionResult) => void;
  onError?: (error: Error) => void;
}

export interface ToolSearchOptions {
  query?: string;
  serverId?: string;
  category?: string;
  tags?: string[];
  limit?: number;
  offset?: number;
  sortBy?: 'name' | 'createdAt' | 'updatedAt';
  sortOrder?: 'asc' | 'desc';
}

export interface ToolExecutionHistory {
  id: string;
  toolName: string;
  serverId: string;
  status: 'pending' | 'running' | 'completed' | 'failed' | 'cancelled';
  startedAt: string;
  completedAt?: string;
  duration?: number;
  parameters: Record<string, any>;
  result?: any;
  error?: string;
  metadata?: Record<string, any>;
}
