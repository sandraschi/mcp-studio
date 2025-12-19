import { Server, Tool, ToolExecutionResult, Notification } from '../types';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:3001/api';

interface ApiResponse<T> {
  data?: T;
  error?: string;
  message?: string;
}

class ApiService {
  private async request<T>(endpoint: string, options: RequestInit = {}): Promise<ApiResponse<T>> {
    const defaultHeaders = {
      'Content-Type': 'application/json',
      'Accept': 'application/json',
    };

    try {
      const response = await fetch(`${API_BASE_URL}${endpoint}`, {
        ...options,
        headers: {
          ...defaultHeaders,
          ...options.headers,
        },
        credentials: 'include',
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.error || 'Something went wrong');
      }

      return { data };
    } catch (error) {
      console.error('API Error:', error);
      return {
        error: error instanceof Error ? error.message : 'An unknown error occurred',
      };
    }
  }

  // Server Management
  async getServers(): Promise<ApiResponse<Server[]>> {
    return this.request<Server[]>('/servers');
  }

  async getServer(id: string): Promise<ApiResponse<Server>> {
    return this.request<Server>(`/servers/${id}`);
  }

  async createServer(server: Omit<Server, 'id' | 'status'>): Promise<ApiResponse<Server>> {
    return this.request<Server>('/servers', {
      method: 'POST',
      body: JSON.stringify(server),
    });
  }

  async updateServer(id: string, updates: Partial<Server>): Promise<ApiResponse<Server>> {
    return this.request<Server>(`/servers/${id}`, {
      method: 'PATCH',
      body: JSON.stringify(updates),
    });
  }

  async deleteServer(id: string): Promise<ApiResponse<void>> {
    return this.request<void>(`/servers/${id}`, {
      method: 'DELETE',
    });
  }

  // Tool Management
  async getTools(serverId: string): Promise<ApiResponse<Tool[]>> {
    return this.request<Tool[]>(`/servers/${serverId}/tools`);
  }

  async getTool(serverId: string, toolId: string): Promise<ApiResponse<Tool>> {
    return this.request<Tool>(`/servers/${serverId}/tools/${toolId}`);
  }

  // Tool Execution
  async executeTool(
    serverId: string,
    toolId: string,
    parameters: Record<string, any>
  ): Promise<ApiResponse<ToolExecutionResult>> {
    return this.request<ToolExecutionResult>(`/servers/${serverId}/tools/${toolId}/execute`, {
      method: 'POST',
      body: JSON.stringify({ parameters }),
    });
  }

  // Docstring Formatting
  async formatDocstring(
    docstring: string,
    format: 'html' | 'markdown' = 'html'
  ): Promise<ApiResponse<{ formatted: string; parsed: Record<string, any> }>> {
    return this.request<{ formatted: string; parsed: Record<string, any> }>('/tools/format-docstring', {
      method: 'POST',
      body: JSON.stringify({ docstring, format }),
    });
  }

  // Notifications
  async getNotifications(): Promise<ApiResponse<Notification[]>> {
    return this.request<Notification[]>('/notifications');
  }

  async markNotificationAsRead(id: string): Promise<ApiResponse<Notification>> {
    return this.request<Notification>(`/notifications/${id}/read`, {
      method: 'PATCH',
    });
  }

  // Authentication
  async login(credentials: { username: string; password: string }): Promise<ApiResponse<{ token: string }>> {
    return this.request<{ token: string }>('/auth/login', {
      method: 'POST',
      body: JSON.stringify(credentials),
    });
  }

  async logout(): Promise<ApiResponse<void>> {
    return this.request<void>('/auth/logout', {
      method: 'POST',
    });
  }
}

export const api = new ApiService();
