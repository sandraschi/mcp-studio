import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { useNavigate } from 'react-router-dom';
import { useToaster } from '../hooks';

interface User {
  id: string;
  email: string;
  name: string;
  avatar?: string;
  role: 'admin' | 'user';
}

interface AuthContextType {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (userData: { name: string; email: string; password: string }) => Promise<void>;
  logout: () => Promise<void>;
  updateProfile: (userData: Partial<User>) => Promise<void>;
  forgotPassword: (email: string) => Promise<void>;
  resetPassword: (token: string, password: string) => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const navigate = useNavigate();
  const { success, error } = useToaster();

  // Check if user is logged in on initial load
  useEffect(() => {
    const checkAuth = async () => {
      try {
        const token = localStorage.getItem('token');
        if (!token) {
          setIsLoading(false);
          return;
        }

        // Here you would typically validate the token with your backend
        // For now, we'll just simulate a user
        const mockUser: User = {
          id: '1',
          name: 'Demo User',
          email: 'demo@example.com',
          role: 'admin',
        };

        setUser(mockUser);
      } catch (err) {
        console.error('Auth check failed:', err);
        localStorage.removeItem('token');
      } finally {
        setIsLoading(false);
      }
    };

    checkAuth();
  }, []);

  const login = async (email: string, password: string) => {
    try {
      setIsLoading(true);
      // Simulate API call
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      // Replace with actual API call
      const mockUser: User = {
        id: '1',
        name: 'Demo User',
        email,
        role: 'admin',
      };
      
      setUser(mockUser);
      localStorage.setItem('token', 'dummy-jwt-token');
      success('Successfully logged in');
      navigate('/');
    } catch (err) {
      console.error('Login failed:', err);
      throw new Error('Invalid email or password');
    } finally {
      setIsLoading(false);
    }
  };

  const register = async (userData: { name: string; email: string; password: string }) => {
    try {
      setIsLoading(true);
      // Simulate API call
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      // Replace with actual API call
      const newUser: User = {
        id: '2',
        name: userData.name,
        email: userData.email,
        role: 'user',
      };
      
      setUser(newUser);
      localStorage.setItem('token', 'dummy-jwt-token');
      success('Account created successfully');
      navigate('/');
    } catch (err) {
      console.error('Registration failed:', err);
      throw new Error('Registration failed. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  const logout = async () => {
    try {
      // Simulate API call
      await new Promise(resolve => setTimeout(resolve, 500));
      
      // Clear user data
      setUser(null);
      localStorage.removeItem('token');
      success('Successfully logged out');
      navigate('/login');
    } catch (err) {
      console.error('Logout failed:', err);
      throw new Error('Failed to log out');
    }
  };

  const updateProfile = async (userData: Partial<User>) => {
    try {
      if (!user) throw new Error('Not authenticated');
      
      // Simulate API call
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      // Update user data
      setUser(prev => (prev ? { ...prev, ...userData } : null));
      success('Profile updated successfully');
    } catch (err) {
      console.error('Profile update failed:', err);
      throw new Error('Failed to update profile');
    }
  };

  const forgotPassword = async (email: string) => {
    try {
      // Simulate API call
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      success('Password reset link sent to your email');
      return true;
    } catch (err) {
      console.error('Forgot password failed:', err);
      throw new Error('Failed to send reset link');
    }
  };

  const resetPassword = async (token: string, password: string) => {
    try {
      // Simulate API call
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      success('Password reset successful. Please log in with your new password.');
      navigate('/login');
    } catch (err) {
      console.error('Password reset failed:', err);
      throw new Error('Failed to reset password');
    }
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        isAuthenticated: !!user,
        isLoading,
        login,
        register,
        logout,
        updateProfile,
        forgotPassword,
        resetPassword,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

// Protected route component
export const ProtectedRoute: React.FC<{ children: ReactNode }> = ({ children }) => {
  const { isAuthenticated, isLoading } = useAuth();
  const navigate = useNavigate();

  useEffect(() => {
    if (!isLoading && !isAuthenticated) {
      navigate('/login', { replace: true });
    }
  }, [isAuthenticated, isLoading, navigate]);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-blue-500"></div>
      </div>
    );
  }

  return isAuthenticated ? <>{children}</> : null;
};
