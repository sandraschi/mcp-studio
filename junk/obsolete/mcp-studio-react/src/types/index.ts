// Re-export all types from individual modules
export * from './auth';
export * from './server';
export * from './tool';
export * from './prompt';

// Keep the original types for backward compatibility
export type ServerStatus = 'ONLINE' | 'OFFLINE' | 'STARTING' | 'STOPPING' | 'ERROR';

// Legacy types (deprecated, use the new types from the respective modules instead)
/** @deprecated Use types from './server' instead */
export interface Server {
  id: string;
  name: string;
  status: ServerStatus;
  type?: string;
  tools?: LegacyTool[];
  metadata?: Record<string, any>;
  lastSeen?: string;
}

/** @deprecated Use types from './tool' instead */
export interface LegacyTool {
  name: string;
  description: string;
  parameters: LegacyToolParameter[];
}

/** @deprecated Use types from './tool' instead */
export interface LegacyToolParameter {
  name: string;
  type: string;
  description?: string;
  required?: boolean;
  default?: any;
  enum?: string[];
}

/** @deprecated Use types from './tool' instead */
export interface ToolExecutionRequest {
  serverId: string;
  toolName: string;
  parameters: Record<string, any>;
}

/** @deprecated Use types from './tool' instead */
export interface LegacyToolExecutionResult {
  success: boolean;
  result?: any;
  error?: string;
  executionTime?: number;
  timestamp?: string;
  metadata?: Record<string, any>;
}

export interface WebSocketMessage<T = any> {
  type: string;
  data: T;
  timestamp: string;
  id?: string;
  error?: string;
}

export interface ServerStatusUpdate {
  serverId: string;
  status: ServerStatus;
  timestamp: string;
  message?: string;
  error?: string;
}

/** @deprecated Use types from './tool' instead */
export interface ToolExecutionUpdate {
  executionId: string;
  serverId: string;
  toolName: string;
  status: 'PENDING' | 'RUNNING' | 'COMPLETED' | 'FAILED' | 'CANCELLED';
  progress?: number;
  result?: any;
  error?: string;
  timestamp: string;
  logs?: string[];
}

// Type guards
export function isServerStatusUpdate(msg: WebSocketMessage): msg is WebSocketMessage<ServerStatusUpdate> {
  return msg.type === 'STATUS_UPDATE';
}

export function isToolExecutionUpdate(msg: WebSocketMessage): msg is WebSocketMessage<ToolExecutionUpdate> {
  return msg.type === 'TOOL_EXECUTION_UPDATE';
}

export function isLegacyToolExecutionResult(msg: WebSocketMessage): msg is WebSocketMessage<LegacyToolExecutionResult> {
  return msg.type === 'TOOL_RESULT';
}
