import axios, { AxiosInstance, AxiosRequestConfig, AxiosResponse, AxiosError } from 'axios';
import { 
  Server, 
  Tool, 
  ToolExecutionRequest, 
  ToolExecutionResult, 
  PromptTemplate,
  User,
  LoginCredentials,
  RegisterData,
  ServerStatus,
  AuthResponse,
  PasswordResetRequest,
  PasswordResetConfirm
} from '../../types';

// Default API configuration
const DEFAULT_CONFIG: AxiosRequestConfig = {
  timeout: 30000, // 30 seconds
  headers: {
    'Content-Type': 'application/json',
    'Accept': 'application/json',
  },
  withCredentials: true, // Important for cookies, authorization headers with HTTPS
};

export class ApiError extends Error {
  status: number;
  code?: string;
  data: any;
  timestamp: string;

  constructor(message: string, status: number, data: any = null) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.code = data?.code;
    this.data = data;
    this.timestamp = new Date().toISOString();
    Object.setPrototypeOf(this, ApiError.prototype);
  }

  isUnauthorized(): boolean {
    return this.status === 401;
  }

  isForbidden(): boolean {
    return this.status === 403;
  }

  isNotFound(): boolean {
    return this.status === 404;
  }

  isServerError(): boolean {
    return this.status >= 500;
  }

  toJSON() {
    return {
      name: this.name,
      message: this.message,
      status: this.status,
      code: this.code,
      data: this.data,
      timestamp: this.timestamp,
      stack: this.stack,
    };
  }
}

export class ApiService {
  private static instance: ApiService;
  private api: AxiosInstance;
  private baseUrl: string;
  private refreshTokenRequest: Promise<string> | null = null;

  private constructor(baseUrl: string = process.env.REACT_APP_API_BASE_URL || '/api') {
    this.baseUrl = baseUrl;
    this.api = axios.create({
      ...DEFAULT_CONFIG,
      baseURL: this.baseUrl,
    });

    this.setupInterceptors();
  }

  // Setup request and response interceptors
  private setupInterceptors() {
    // Request interceptor for auth tokens
    this.api.interceptors.request.use(
      this.handleRequest,
      this.handleRequestError
    );

    // Response interceptor for error handling and token refresh
    this.api.interceptors.response.use(
      this.handleResponse,
      this.handleResponseError
    );
  }

  // Request interceptor to add auth token
  private handleRequest = (config: AxiosRequestConfig) => {
    const token = localStorage.getItem('access_token');
    if (token) {
      config.headers = config.headers || {};
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  };

  // Request error handler
  private handleRequestError = (error: any) => {
    return Promise.reject(error);
  };

  // Response interceptor for successful responses
  private handleResponse = (response: AxiosResponse) => {
    return response;
  };

  // Response error handler with token refresh logic
  private handleResponseError = async (error: AxiosError) => {
    const originalRequest = error.config as any;
    
    // If the error is 401 and we haven't tried to refresh the token yet
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;
      
      try {
        // Try to refresh the token
        const newToken = await this.refreshToken();
        
        // Update the authorization header
        if (newToken) {
          originalRequest.headers.Authorization = `Bearer ${newToken}`;
          
          // Retry the original request
          return this.api(originalRequest);
        }
      } catch (refreshError) {
        // If refresh fails, clear auth state
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        window.location.href = '/login';
        return Promise.reject(refreshError);
      }
    }
    
    // Handle other errors
    if (error.response) {
      // The request was made and the server responded with a status code
      // that falls out of the range of 2xx
      const { status, data } = error.response;
      const message = data?.message || error.message || 'An unknown error occurred';
      const errorData = {
        ...data,
        status,
        isApiError: true,
      };
      
      return Promise.reject(new ApiError(message, status, errorData));
    } else if (error.request) {
      // The request was made but no response was received
      return Promise.reject(new ApiError('No response received from server. Please check your connection.', 0));
    } else {
      // Something happened in setting up the request that triggered an Error
      return Promise.reject(new ApiError(error.message, 0));
    }
  };
  
  // Refresh the access token using the refresh token
  private async refreshToken(): Promise<string | null> {
    // If we're already trying to refresh the token, return the existing promise
    if (this.refreshTokenRequest) {
      return this.refreshTokenRequest;
    }
    
    const refreshToken = localStorage.getItem('refresh_token');
    if (!refreshToken) {
      return null;
    }
    
    try {
      this.refreshTokenRequest = new Promise(async (resolve, reject) => {
        try {
          const response = await axios.post(
            `${this.baseUrl}/auth/refresh-token`,
            { refreshToken },
            { ...DEFAULT_CONFIG, skipAuthRefresh: true } as any
          );
          
          const { accessToken, refreshToken: newRefreshToken } = response.data;
          
          // Update tokens in storage
          localStorage.setItem('access_token', accessToken);
          if (newRefreshToken) {
            localStorage.setItem('refresh_token', newRefreshToken);
          }
          
          resolve(accessToken);
        } catch (error) {
          // Clear tokens on refresh failure
          localStorage.removeItem('access_token');
          localStorage.removeItem('refresh_token');
          reject(error);
        } finally {
          this.refreshTokenRequest = null;
        }
      });
      
      return this.refreshTokenRequest;
    } catch (error) {
      this.refreshTokenRequest = null;
      throw error;
    }
  }

  public static getInstance(baseUrl?: string): ApiService {
    if (!ApiService.instance) {
      ApiService.instance = new ApiService(baseUrl);
    }
    return ApiService.instance;
  }

  // ===== Auth API =====
  
  /**
   * Login with username/email and password
   */
  public async login(credentials: LoginCredentials): Promise<AuthResponse> {
    const response = await this.api.post('/auth/login', credentials);
    
    // Store tokens
    const { accessToken, refreshToken } = response.data;
    localStorage.setItem('access_token', accessToken);
    if (refreshToken) {
      localStorage.setItem('refresh_token', refreshToken);
    }
    
    return response.data;
  }
  
  /**
   * Register a new user
   */
  public async register(userData: RegisterData): Promise<AuthResponse> {
    const response = await this.api.post('/auth/register', userData);
    
    // Store tokens
    const { accessToken, refreshToken } = response.data;
    localStorage.setItem('access_token', accessToken);
    if (refreshToken) {
      localStorage.setItem('refresh_token', refreshToken);
    }
    
    return response.data;
  }

  /**
   * Logout the current user
   */
  public async logout(): Promise<void> {
    try {
      await this.api.post('/auth/logout');
    } finally {
      // Always clear local tokens
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');
      
      // Clear any pending requests
      this.refreshTokenRequest = null;
    }
  }

  /**
   * Get the current authenticated user
   */
  public async getCurrentUser(): Promise<User> {
    const response = await this.api.get('/auth/me');
    return response.data;
  }
  
  /**
   * Request a password reset email
   */
  public async forgotPassword(email: string): Promise<void> {
    await this.api.post('/auth/forgot-password', { email });
  }
  
  /**
   * Reset password with a reset token
   */
  public async resetPassword(token: string, newPassword: string): Promise<void> {
    await this.api.post('/auth/reset-password', { token, newPassword });
  }

  // ===== Server API =====
  
  /**
   * Get all servers
   */
  public async getServers(): Promise<Server[]> {
    const response = await this.api.get('/servers');
    return response.data;
  }
  
  /**
   * Get server status
   */
  public async getServerStatus(): Promise<{ [key: string]: ServerStatus }> {
    const response = await this.api.get('/servers/status');
    return response.data;
  }

  /**
   * Get server by ID
   */
  public async getServerById(serverId: string): Promise<Server> {
    const response = await this.api.get(`/servers/${serverId}`);
    return response.data;
  }

  /**
   * Register a new server
   */
  public async registerServer(serverData: Partial<Server>): Promise<Server> {
    const response = await this.api.post('/servers', serverData);
    return response.data;
  }

  /**
   * Update server
   */
  public async updateServer(serverId: string, serverData: Partial<Server>): Promise<Server> {
    const response = await this.api.patch(`/servers/${serverId}`, serverData);
    return response.data;
  }

  /**
   * Delete a server
   */
  public async deleteServer(serverId: string): Promise<void> {
    await this.api.delete(`/servers/${serverId}`);
  }

  /**
   * Start a server
   */
  public async startServer(serverId: string): Promise<Server> {
    const response = await this.api.post(`/servers/${serverId}/start`);
    return response.data;
  }

  /**
   * Stop a server
   */
  public async stopServer(serverId: string): Promise<Server> {
    const response = await this.api.post(`/servers/${serverId}/stop`);
    return response.data;
  }
  
  /**
   * Restart a server
   */
  public async restartServer(serverId: string): Promise<Server> {
    const response = await this.api.post(`/servers/${serverId}/restart`);
    return response.data;
  }
  
  /**
   * Get server logs
   */
  public async getServerLogs(serverId: string, lines: number = 100): Promise<string[]> {
    const response = await this.api.get(`/servers/${serverId}/logs?lines=${lines}`);
    return response.data;
  }

  // ===== Tools API =====
  
  /**
   * Get all tools, optionally filtered by server
   */
  public async getTools(serverId?: string): Promise<Tool[]> {
    const params = serverId ? { serverId } : undefined;
    const response = await this.api.get('/tools', { params });
    return response.data;
  }
  
  /**
   * Search tools by name or description
   */
  public async searchTools(query: string, serverId?: string): Promise<Tool[]> {
    const params = { q: query, serverId };
    const response = await this.api.get('/tools/search', { params });
    return response.data;
  }

  /**
   * Get tool by name and optional server ID
   */
  public async getToolByName(toolName: string, serverId?: string): Promise<Tool> {
    const params = serverId ? { serverId } : undefined;
    const response = await this.api.get(`/tools/${encodeURIComponent(toolName)}`, { params });
    return response.data;
  }
  
  /**
   * Get tool by ID
   */
  public async getToolById(toolId: string): Promise<Tool> {
    const response = await this.api.get(`/tools/id/${toolId}`);
    return response.data;
  }

  /**
   * Execute a tool
   */
  public async executeTool(executionRequest: ToolExecutionRequest): Promise<ToolExecutionResult> {
    const response = await this.api.post('/tools/execute', executionRequest);
    return response.data;
  }
  
  /**
   * Execute a tool asynchronously (returns immediately with execution ID)
   */
  public async executeToolAsync(executionRequest: ToolExecutionRequest): Promise<{ executionId: string }> {
    const response = await this.api.post('/tools/execute/async', executionRequest);
    return response.data;
  }

  /**
   * Get tool execution status
   */
  public async getToolExecution(executionId: string): Promise<ToolExecutionResult> {
    const response = await this.api.get(`/tools/executions/${executionId}`);
    return response.data;
  }
  
  /**
   * Get recent tool executions
   */
  public async getRecentExecutions(limit: number = 10): Promise<ToolExecutionResult[]> {
    const response = await this.api.get('/tools/executions/recent', { params: { limit } });
    return response.data;
  }

  /**
   * Cancel a running tool execution
   */
  public async cancelToolExecution(executionId: string): Promise<void> {
    await this.api.post(`/tools/executions/${executionId}/cancel`);
  }

  // ===== Prompt Templates API =====
  
  /**
   * Get all prompt templates
   */
  public async getPromptTemplates(params?: {
    search?: string;
    category?: string;
    limit?: number;
    offset?: number;
  }): Promise<{ templates: PromptTemplate[]; total: number }> {
    const response = await this.api.get('/prompts/templates', { params });
    return response.data;
  }
  
  /**
   * Get prompt template categories
   */
  public async getPromptTemplateCategories(): Promise<string[]> {
    const response = await this.api.get('/prompts/templates/categories');
    return response.data;
  }

  /**
   * Get prompt template by ID
   */
  public async getPromptTemplateById(templateId: string): Promise<PromptTemplate> {
    const response = await this.api.get(`/prompts/templates/${templateId}`);
    return response.data;
  }
  
  /**
   * Get prompt template by name
   */
  public async getPromptTemplateByName(name: string): Promise<PromptTemplate> {
    const response = await this.api.get(`/prompts/templates/name/${encodeURIComponent(name)}`);
    return response.data;
  }

  /**
   * Create a new prompt template
   */
  public async createPromptTemplate(templateData: Partial<PromptTemplate>): Promise<PromptTemplate> {
    const response = await this.api.post('/prompts/templates', templateData);
    return response.data;
  }

  /**
   * Update a prompt template
   */
  public async updatePromptTemplate(
    templateId: string,
    templateData: Partial<PromptTemplate>
  ): Promise<PromptTemplate> {
    const response = await this.api.put(`/prompts/templates/${templateId}`, templateData);
    return response.data;
  }
  
  /**
   * Partially update a prompt template
   */
  public async patchPromptTemplate(
    templateId: string,
    templateData: Partial<PromptTemplate>
  ): Promise<PromptTemplate> {
    const response = await this.api.patch(`/prompts/templates/${templateId}`, templateData);
    return response.data;
  }

  /**
   * Delete a prompt template
   */
  public async deletePromptTemplate(templateId: string): Promise<void> {
    await this.api.delete(`/prompts/templates/${templateId}`);
  }

  /**
   * Execute a prompt template with the given parameters
   */
  public async executePromptTemplate(
    templateId: string,
    parameters: Record<string, any>,
    options: {
      stream?: boolean;
      format?: 'text' | 'html' | 'markdown';
    } = {}
  ): Promise<{ result: string }> {
    const response = await this.api.post(
      `/prompts/templates/${templateId}/execute`,
      { parameters, options }
    );
    return response.data;
  }
  
  /**
   * Execute a prompt template by name with the given parameters
   */
  public async executePromptTemplateByName(
    name: string,
    parameters: Record<string, any>,
    options: {
      stream?: boolean;
      format?: 'text' | 'html' | 'markdown';
    } = {}
  ): Promise<{ result: string }> {
    const response = await this.api.post(
      `/prompts/templates/name/${encodeURIComponent(name)}/execute`,
      { parameters, options }
    );
    return response.data;
  }

  // Generic request method for custom API calls
  public async request<T = any>(config: AxiosRequestConfig): Promise<AxiosResponse<T>> {
    return this.api.request<T>(config);
  }
}

// Export a singleton instance
export const apiService = ApiService.getInstance(process.env.REACT_APP_API_BASE_URL);
