import { 
  Server, 
  Tool, 
  ToolExecutionRequest, 
  ToolExecutionResult, 
  User, 
  LoginCredentials, 
  AuthResponse, 
  PromptTemplate,
  ServerStatus
} from '../types';

const API_BASE_URL = '/api';

class ApiService {
  private authToken: string | null = null;
  private refreshToken: string | null = null;
  private refreshPromise: Promise<AuthResponse> | null = null;

  constructor() {
    // Load tokens from localStorage on initialization
    if (typeof window !== 'undefined') {
      this.authToken = localStorage.getItem('authToken');
      this.refreshToken = localStorage.getItem('refreshToken');
    }
  }

  private async fetchJson<T>(
    url: string, 
    options: RequestInit = {},
    isRetry = false
  ): Promise<T> {
    const headers = new Headers(options.headers);
    
    // Add auth token if available
    if (this.authToken && !headers.has('Authorization')) {
      headers.set('Authorization', `Bearer ${this.authToken}`);
    }

    // Set default headers
    if (!headers.has('Content-Type') && !(options.body instanceof FormData)) {
      headers.set('Content-Type', 'application/json');
    }

    try {
      const response = await fetch(`${API_BASE_URL}${url}`, {
        ...options,
        headers,
        credentials: 'include',
      });

      // Handle 401 Unauthorized (token expired)
      if (response.status === 401 && !isRetry && this.refreshToken) {
        try {
          // Ensure we only make one refresh request at a time
          if (!this.refreshPromise) {
            this.refreshPromise = this.refreshAuthToken();
          }
          
          const authData = await this.refreshPromise;
          this.setAuthTokens(authData);
          
          // Retry the original request with new token
          return this.fetchJson<T>(url, options, true);
        } catch (error) {
          // Clear tokens if refresh fails
          this.clearAuth();
          throw error;
        } finally {
          this.refreshPromise = null;
        }
      }

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        const error = new Error(errorData.message || 'API request failed');
        (error as any).status = response.status;
        (error as any).code = errorData.code;
        throw error;
      }

      return response.json();
    } catch (error) {
      console.error('API request failed:', error);
      throw error;
    }
  }

  // Auth methods
  public async login(credentials: LoginCredentials): Promise<AuthResponse> {
    const response = await this.fetchJson<AuthResponse>('/auth/login', {
      method: 'POST',
      body: JSON.stringify(credentials),
    });
    
    this.setAuthTokens(response);
    return response;
  }

  public async refreshAuthToken(): Promise<AuthResponse> {
    if (!this.refreshToken) {
      throw new Error('No refresh token available');
    }

    const response = await fetch(`${API_BASE_URL}/auth/refresh`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ refreshToken: this.refreshToken }),
    });

    if (!response.ok) {
      this.clearAuth();
      throw new Error('Failed to refresh token');
    }

    const authData = await response.json();
    this.setAuthTokens(authData);
    return authData;
  }

  public logout(): void {
    // Call logout endpoint
    fetch(`${API_BASE_URL}/auth/logout`, {
      method: 'POST',
      credentials: 'include',
    }).catch(console.error);
    
    this.clearAuth();
  }

  public isAuthenticated(): boolean {
    return !!this.authToken;
  }

  private setAuthTokens(authData: AuthResponse): void {
    this.authToken = authData.accessToken;
    this.refreshToken = authData.refreshToken;
    
    if (typeof window !== 'undefined') {
      if (authData.accessToken) {
        localStorage.setItem('authToken', authData.accessToken);
      }
      if (authData.refreshToken) {
        localStorage.setItem('refreshToken', authData.refreshToken);
      }
    }
  }

  private clearAuth(): void {
    this.authToken = null;
    this.refreshToken = null;
    
    if (typeof window !== 'undefined') {
      localStorage.removeItem('authToken');
      localStorage.removeItem('refreshToken');
    }
  }

  // Server endpoints
  public async getServers(): Promise<Server[]> {
    return this.fetchJson<Server[]>('/servers');
  }

  public async getServer(serverId: string): Promise<Server> {
    return this.fetchJson<Server>(`/servers/${serverId}`);
  }

  public async getServerStatus(serverId: string): Promise<ServerStatus> {
    return this.fetchJson<ServerStatus>(`/servers/${serverId}/status`);
  }

  public async startServer(serverId: string): Promise<void> {
    await this.fetchJson(`/servers/${serverId}/start`, {
      method: 'POST',
    });
  }

  public async stopServer(serverId: string): Promise<void> {
    await this.fetchJson(`/servers/${serverId}/stop`, {
      method: 'POST',
    });
  }

  public async restartServer(serverId: string): Promise<void> {
    await this.fetchJson(`/servers/${serverId}/restart`, {
      method: 'POST',
    });
  }

  public async getServerLogs(serverId: string, lines = 100): Promise<string[]> {
    return this.fetchJson<string[]>(`/servers/${serverId}/logs?lines=${lines}`);
  }

  // Tool endpoints
  public async getTools(serverId: string): Promise<Tool[]> {
    return this.fetchJson<Tool[]>(`/servers/${serverId}/tools`);
  }

  public async getTool(serverId: string, toolName: string): Promise<Tool> {
    return this.fetchJson<Tool>(`/servers/${serverId}/tools/${encodeURIComponent(toolName)}`);
  }

  public async executeTool(request: ToolExecutionRequest): Promise<{ executionId: string }> {
    return this.fetchJson<{ executionId: string }>('/tools/execute', {
      method: 'POST',
      body: JSON.stringify(request),
    });
  }

  public async getToolResult(executionId: string): Promise<ToolExecutionResult> {
    return this.fetchJson<ToolExecutionResult>(`/tools/results/${executionId}`);
  }

  public async cancelToolExecution(executionId: string): Promise<void> {
    await this.fetchJson(`/tools/execute/${executionId}/cancel`, {
      method: 'POST',
    });
  }

  // Prompt Template endpoints
  public async getTemplates(): Promise<PromptTemplate[]> {
    return this.fetchJson<PromptTemplate[]>('/templates');
  }

  public async getTemplate(templateId: string): Promise<PromptTemplate> {
    return this.fetchJson<PromptTemplate>(`/templates/${templateId}`);
  }

  public async createTemplate(template: Omit<PromptTemplate, 'id' | 'createdAt' | 'updatedAt'>): Promise<PromptTemplate> {
    return this.fetchJson<PromptTemplate>('/templates', {
      method: 'POST',
      body: JSON.stringify(template),
    });
  }

  public async updateTemplate(templateId: string, updates: Partial<PromptTemplate>): Promise<PromptTemplate> {
    return this.fetchJson<PromptTemplate>(`/templates/${templateId}`, {
      method: 'PATCH',
      body: JSON.stringify(updates),
    });
  }

  public async deleteTemplate(templateId: string): Promise<void> {
    await this.fetchJson(`/templates/${templateId}`, {
      method: 'DELETE',
    });
  }

  // Discovery endpoints
  public async discoverServers(): Promise<void> {
    await this.fetchJson('/discovery/scan', {
      method: 'POST',
    });
  }

  // User endpoints
  public async getCurrentUser(): Promise<User> {
    return this.fetchJson<User>('/users/me');
  }

  public async updateUserProfile(updates: Partial<User>): Promise<User> {
    return this.fetchJson<User>('/users/me', {
      method: 'PATCH',
      body: JSON.stringify(updates),
    });
  }

  // Settings endpoints
  public async getSettings(): Promise<Record<string, any>> {
    return this.fetchJson<Record<string, any>>('/settings');
  }

  public async updateSettings(settings: Record<string, any>): Promise<Record<string, any>> {
    return this.fetchJson<Record<string, any>>('/settings', {
      method: 'PUT',
      body: JSON.stringify(settings),
    });
  }
}

export const apiService = new ApiService();

// React hook for API
import { useCallback, useEffect, useState } from 'react';

interface UseApiReturn extends Omit<ApiService, 'login' | 'logout' | 'isAuthenticated'> {
  isAuthenticated: boolean;
  user: User | null;
  loading: boolean;
  error: Error | null;
  login: (credentials: LoginCredentials) => Promise<AuthResponse>;
  logout: () => Promise<void>;
  refreshUser: () => Promise<void>;
}

export const useApi = (): UseApiReturn => {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);

  // Check auth status on mount
  useEffect(() => {
    const checkAuth = async () => {
      if (apiService.isAuthenticated()) {
        try {
          const userData = await apiService.getCurrentUser();
          setUser(userData);
        } catch (err) {
          console.error('Failed to fetch user data:', err);
          apiService.logout();
        }
      }
      setLoading(false);
    };

    checkAuth();
  }, []);

  const login = useCallback(async (credentials: LoginCredentials) => {
    try {
      setLoading(true);
      const authData = await apiService.login(credentials);
      const userData = await apiService.getCurrentUser();
      setUser(userData);
      setError(null);
      return authData;
    } catch (err) {
      setError(err as Error);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  const logout = useCallback(async () => {
    try {
      setLoading(true);
      await apiService.logout();
      setUser(null);
      setError(null);
    } catch (err) {
      setError(err as Error);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  const refreshUser = useCallback(async () => {
    if (!apiService.isAuthenticated()) return;
    
    try {
      setLoading(true);
      const userData = await apiService.getCurrentUser();
      setUser(userData);
      setError(null);
    } catch (err) {
      setError(err as Error);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  // Create a wrapped version of executeTool for convenience
  const executeTool = useCallback(async (serverId: string, toolName: string, parameters: Record<string, any>) => {
    try {
      setLoading(true);
      const { executionId } = await apiService.executeTool({
        serverId,
        toolName,
        parameters,
      });
      return executionId;
    } catch (err) {
      setError(err as Error);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  return {
    ...apiService,
    executeTool,
    isAuthenticated: apiService.isAuthenticated(),
    user,
    loading,
    error,
    login,
    logout,
    refreshUser,
  };
};
