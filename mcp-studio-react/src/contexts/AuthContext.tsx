import React, { createContext, useContext, useState, useEffect, useCallback, ReactNode } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { apiService } from '../services/api/api.service';
import { User, LoginCredentials, RegisterData, AuthResponse } from '../types/auth';

interface AuthContextType {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;
  login: (credentials: LoginCredentials) => Promise<void>;
  register: (data: RegisterData) => Promise<void>;
  logout: () => Promise<void>;
  refreshUser: () => Promise<void>;
  clearError: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

// Helper function to get user from localStorage
const getUserFromStorage = (): User | null => {
  const userData = localStorage.getItem('user');
  return userData ? JSON.parse(userData) : null;
};

// Helper function to set auth token in axios headers
const setAuthToken = (token: string | null) => {
  if (token) {
    apiService.api.defaults.headers.common['Authorization'] = `Bearer ${token}`;
    localStorage.setItem('token', token);
  } else {
    delete apiService.api.defaults.headers.common['Authorization'];
    localStorage.removeItem('token');
  }
};

interface AuthProviderProps {
  children: ReactNode;
}

export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const [user, setUser] = useState<User | null>(() => getUserFromStorage());
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const navigate = useNavigate();
  const location = useLocation();

  // Initialize auth state on mount
  useEffect(() => {
    const token = localStorage.getItem('token');
    if (token) {
      setAuthToken(token);
      // If we have a token but no user data, fetch the user
      if (!user) {
        refreshUser().catch(console.error);
      }
    }
  }, []);

  // Clear error when location changes
  useEffect(() => {
    setError(null);
  }, [location.pathname]);

  const login = useCallback(async (credentials: LoginCredentials) => {
    setIsLoading(true);
    setError(null);
    
    try {
      const { token, user } = await apiService.login(credentials);
      setAuthToken(token);
      setUser(user);
      localStorage.setItem('user', JSON.stringify(user));
      
      // Redirect to the dashboard or the intended page
      const from = location.state?.from?.pathname || '/dashboard';
      navigate(from, { replace: true });
    } catch (err: any) {
      setError(err.message || 'Failed to login. Please check your credentials.');
      throw err;
    } finally {
      setIsLoading(false);
    }
  }, [navigate, location.state]);

  const register = useCallback(async (data: RegisterData) => {
    setIsLoading(true);
    setError(null);
    
    try {
      const { token, user } = await apiService.register(data);
      setAuthToken(token);
      setUser(user);
      localStorage.setItem('user', JSON.stringify(user));
      
      // Redirect to dashboard after successful registration
      navigate('/dashboard', { replace: true });
    } catch (err: any) {
      setError(err.message || 'Failed to register. Please try again.');
      throw err;
    } finally {
      setIsLoading(false);
    }
  }, [navigate]);

  const logout = useCallback(async () => {
    setIsLoading(true);
    
    try {
      await apiService.logout();
    } catch (err) {
      console.error('Logout error:', err);
      // Continue with local logout even if API call fails
    } finally {
      // Clear auth state
      setUser(null);
      setAuthToken(null);
      localStorage.removeItem('user');
      
      // Redirect to login page
      navigate('/login', { replace: true });
      setIsLoading(false);
    }
  }, [navigate]);

  const refreshUser = useCallback(async () => {
    try {
      const user = await apiService.getCurrentUser();
      setUser(user);
      localStorage.setItem('user', JSON.stringify(user));
      return user;
    } catch (err) {
      // If we can't refresh the user, log them out
      console.error('Failed to refresh user:', err);
      await logout();
      return null;
    }
  }, [logout]);

  const clearError = useCallback(() => {
    setError(null);
  }, []);

  const value = {
    user,
    isAuthenticated: !!user,
    isLoading,
    error,
    login,
    register,
    logout,
    refreshUser,
    clearError,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

// Higher-order component for protecting routes
export const withAuth = <P extends object>(
  Component: React.ComponentType<P>,
  options: { redirectTo?: string } = {}
) => {
  const WithAuth: React.FC<P> = (props) => {
    const { isAuthenticated, isLoading } = useAuth();
    const navigate = useNavigate();

    useEffect(() => {
      if (!isLoading && !isAuthenticated) {
        navigate(options.redirectTo || '/login', {
          state: { from: window.location.pathname },
          replace: true,
        });
      }
    }, [isAuthenticated, isLoading, navigate]);

    if (isLoading) {
      return <div>Loading...</div>; // Or a loading spinner
    }

    if (!isAuthenticated) {
      return null; // Or a redirect component
    }

    return <Component {...props} />;
  };

  return WithAuth;
};

// Higher-order component for guest-only routes
export const withGuest = <P extends object>(
  Component: React.ComponentType<P>,
  options: { redirectTo?: string } = {}
) => {
  const WithGuest: React.FC<P> = (props) => {
    const { isAuthenticated, isLoading } = useAuth();
    const navigate = useNavigate();

    useEffect(() => {
      if (!isLoading && isAuthenticated) {
        navigate(options.redirectTo || '/dashboard', { replace: true });
      }
    }, [isAuthenticated, isLoading, navigate]);

    if (isLoading) {
      return <div>Loading...</div>; // Or a loading spinner
    }

    if (isAuthenticated) {
      return null; // Or a redirect component
    }

    return <Component {...props} />;
  };

  return WithGuest;
};
