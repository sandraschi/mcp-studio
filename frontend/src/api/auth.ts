import axios, { AxiosError, AxiosResponse } from 'axios';

// Define types for our API responses
export interface User {
  id: string;
  name: string;
  email: string;
  role?: string;
  avatar?: string;
  createdAt?: string;
  updatedAt?: string;
}

export interface AuthResponse {
  user: User;
  token: string;
  refreshToken?: string;
}

export interface ErrorResponse {
  message: string;
  statusCode?: number;
  errors?: Record<string, string[]>;
}

// Create an axios instance with default config
const api = axios.create({
  baseURL: process.env.REACT_APP_API_URL || 'http://localhost:8000/api',
  headers: {
    'Content-Type': 'application/json',
  },
  withCredentials: true, // Important for cookies if using httpOnly cookies
});

// Add a request interceptor to add the auth token to requests
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Add a response interceptor to handle errors globally
api.interceptors.response.use(
  (response: AxiosResponse) => response,
  async (error: AxiosError<ErrorResponse>) => {
    // Handle 401 Unauthorized errors (token expired, invalid token, etc.)
    if (error.response?.status === 401) {
      // If we have a refresh token, try to refresh the access token
      const refreshToken = localStorage.getItem('refreshToken');
      
      if (refreshToken && !error.config.url?.includes('auth/refresh')) {
        try {
          // Try to refresh the token
          const response = await api.post<AuthResponse>('/auth/refresh', { refreshToken });
          const { token, refreshToken: newRefreshToken } = response.data;
          
          // Update tokens in localStorage
          localStorage.setItem('token', token);
          if (newRefreshToken) {
            localStorage.setItem('refreshToken', newRefreshToken);
          }
          
          // Retry the original request with the new token
          if (error.config.headers) {
            error.config.headers.Authorization = `Bearer ${token}`;
          }
          return api(error.config);
        } catch (refreshError) {
          // If refresh fails, clear tokens and redirect to login
          localStorage.removeItem('token');
          localStorage.removeItem('refreshToken');
          window.location.href = '/login';
        }
      } else {
        // No refresh token or refresh failed, redirect to login
        localStorage.removeItem('token');
        localStorage.removeItem('refreshToken');
        window.location.href = '/login';
      }
    }
    
    // For other errors, just reject with the error
    return Promise.reject(error);
  }
);

// Authentication API functions
export const authAPI = {
  // Login with email and password
  async login(email: string, password: string): Promise<AuthResponse> {
    const response = await api.post<AuthResponse>('/auth/login', { email, password });
    return response.data;
  },
  
  // Register a new user
  async register(userData: {
    name: string;
    email: string;
    password: string;
    passwordConfirmation: string;
  }): Promise<AuthResponse> {
    const response = await api.post<AuthResponse>('/auth/register', userData);
    return response.data;
  },
  
  // Logout the current user
  async logout(): Promise<void> {
    try {
      await api.post('/auth/logout');
    } finally {
      // Always clear the tokens, even if the API call fails
      localStorage.removeItem('token');
      localStorage.removeItem('refreshToken');
    }
  },
  
  // Get the current authenticated user
  async getCurrentUser(): Promise<User> {
    const response = await api.get<User>('/auth/me');
    return response.data;
  },
  
  // Request a password reset email
  async forgotPassword(email: string): Promise<{ message: string }> {
    const response = await api.post<{ message: string }>('/auth/forgot-password', { email });
    return response.data;
  },
  
  // Reset password with a token
  async resetPassword(token: string, password: string): Promise<{ message: string }> {
    const response = await api.post<{ message: string }>('/auth/reset-password', { 
      token, 
      password 
    });
    return response.data;
  },
  
  // Verify email with a token
  async verifyEmail(token: string): Promise<{ message: string }> {
    const response = await api.post<{ message: string }>('/auth/verify-email', { token });
    return response.data;
  },
  
  // Resend verification email
  async resendVerificationEmail(email: string): Promise<{ message: string }> {
    const response = await api.post<{ message: string }>('/auth/resend-verification', { email });
    return response.data;
  },
  
  // Update user profile
  async updateProfile(userData: Partial<User>): Promise<User> {
    const response = await api.put<User>('/auth/profile', userData);
    return response.data;
  },
  
  // Change password
  async changePassword(currentPassword: string, newPassword: string): Promise<{ message: string }> {
    const response = await api.post<{ message: string }>('/auth/change-password', {
      currentPassword,
      newPassword,
    });
    return response.data;
  },
  
  // Social authentication
  async socialAuth(provider: string, accessToken: string): Promise<AuthResponse> {
    const response = await api.post<AuthResponse>(`/auth/${provider}`, { accessToken });
    return response.data;
  },
};

export default authAPI;
