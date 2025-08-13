export interface PromptTemplateParameter {
  name: string;
  type: 'string' | 'number' | 'boolean' | 'array' | 'object';
  description?: string;
  required?: boolean;
  default?: any;
  enum?: string[];
  format?: string;
  minLength?: number;
  maxLength?: number;
  minimum?: number;
  maximum?: number;
  pattern?: string;
  items?: {
    type: string;
    [key: string]: any;
  };
  [key: string]: any;
}

export interface PromptTemplateMetadata {
  category?: string;
  version?: string;
  author?: string;
  tags?: string[];
  [key: string]: any;
}

export interface PromptTemplate {
  id: string;
  name: string;
  description?: string;
  template: string;
  parameters: PromptTemplateParameter[];
  metadata?: PromptTemplateMetadata;
  createdAt: string;
  updatedAt: string;
  createdBy?: string;
  updatedBy?: string;
}

export interface PromptExecutionResult {
  id: string;
  templateId: string;
  templateName?: string;
  input: Record<string, any>;
  output: string;
  metadata?: Record<string, any>;
  createdAt: string;
  durationMs?: number;
  error?: string;
}

export interface PromptExecutionRequest {
  templateId: string;
  parameters: Record<string, any>;
  options?: {
    temperature?: number;
    maxTokens?: number;
    topP?: number;
    frequencyPenalty?: number;
    presencePenalty?: number;
    stopSequences?: string[];
    [key: string]: any;
  };
  metadata?: Record<string, any>;
}

export interface PromptSearchOptions {
  query?: string;
  category?: string;
  tags?: string[];
  limit?: number;
  offset?: number;
  sortBy?: 'name' | 'createdAt' | 'updatedAt' | 'usageCount';
  sortOrder?: 'asc' | 'desc';
}

export interface PromptTemplateVersion {
  id: string;
  templateId: string;
  version: string;
  name: string;
  description?: string;
  template: string;
  parameters: PromptTemplateParameter[];
  metadata?: PromptTemplateMetadata;
  createdAt: string;
  createdBy?: string;
  isCurrent: boolean;
}

export interface PromptTemplateUsage {
  id: string;
  templateId: string;
  count: number;
  lastUsedAt: string;
  averageRating?: number;
  metadata?: Record<string, any>;
}
