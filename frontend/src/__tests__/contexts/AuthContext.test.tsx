import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { AuthProvider, useAuth } from '../../contexts/AuthContext';
import { MemoryRouter } from 'react-router-dom';
import { act } from 'react-dom/test-utils';

// Mock the API calls
const mockLogin = jest.fn();
const mockRegister = jest.fn();
const mockLogout = jest.fn();
const mockForgotPassword = jest.fn();
const mockResetPassword = jest.fn();

// Mock the API module
jest.mock('../../api/auth', () => ({
  login: (email: string, password: string) => mockLogin(email, password),
  register: (userData: any) => mockRegister(userData),
  logout: () => mockLogout(),
  forgotPassword: (email: string) => mockForgotPassword(email),
  resetPassword: (token: string, password: string) => mockResetPassword(token, password),
}));

// Test component that uses the auth hook
const TestComponent = () => {
  const {
    user,
    isAuthenticated,
    isLoading,
    login,
    register,
    logout,
    forgotPassword,
    resetPassword,
  } = useAuth();

  return (
    <div>
      <div data-testid="user">{JSON.stringify(user)}</div>
      <div data-testid="isAuthenticated">{isAuthenticated.toString()}</div>
      <div data-testid="isLoading">{isLoading.toString()}</div>
      <button onClick={() => login('test@example.com', 'password')}>Login</button>
      <button onClick={() => register({ name: 'Test', email: 'test@example.com', password: 'password' })}>
        Register
      </button>
      <button onClick={logout}>Logout</button>
      <button onClick={() => forgotPassword('test@example.com')}>Forgot Password</button>
      <button onClick={() => resetPassword('token', 'newpassword')}>Reset Password</button>
    </div>
  );
};

describe('AuthContext', () => {
  beforeEach(() => {
    // Reset all mocks before each test
    jest.clearAllMocks();
    // Clear localStorage
    localStorage.clear();
  });

  const renderAuthProvider = () => {
    return render(
      <MemoryRouter>
        <AuthProvider>
          <TestComponent />
        </AuthProvider>
      </MemoryRouter>
    );
  };

  it('should initialize with default values', () => {
    renderAuthProvider();
    
    expect(screen.getByTestId('user').textContent).toBe('null');
    expect(screen.getByTestId('isAuthenticated').textContent).toBe('false');
    expect(screen.getByTestId('isLoading').textContent).toBe('true');
  });

  it('should handle successful login', async () => {
    const mockUser = { id: '1', name: 'Test User', email: 'test@example.com' };
    mockLogin.mockResolvedValueOnce({ user: mockUser, token: 'test-token' });
    
    renderAuthProvider();
    
    // Wait for initial load
    await waitFor(() => {
      expect(screen.getByTestId('isLoading').textContent).toBe('false');
    });
    
    // Trigger login
    fireEvent.click(screen.getByText('Login'));
    
    // Check loading state
    expect(screen.getByTestId('isLoading').textContent).toBe('true');
    
    // Wait for login to complete
    await waitFor(() => {
      expect(mockLogin).toHaveBeenCalledWith('test@example.com', 'password');
      expect(screen.getByTestId('isLoading').textContent).toBe('false');
      expect(screen.getByTestId('isAuthenticated').textContent).toBe('true');
      expect(JSON.parse(screen.getByTestId('user').textContent || '{}')).toEqual(mockUser);
    });
    
    // Check if token is stored in localStorage
    expect(localStorage.getItem('token')).toBe('test-token');
  });

  it('should handle login error', async () => {
    const errorMessage = 'Invalid credentials';
    mockLogin.mockRejectedValueOnce(new Error(errorMessage));
    
    // Mock console.error to prevent error logs in test output
    const consoleError = jest.spyOn(console, 'error').mockImplementation(() => {});
    
    renderAuthProvider();
    
    // Wait for initial load
    await waitFor(() => {
      expect(screen.getByTestId('isLoading').textContent).toBe('false');
    });
    
    // Trigger login
    fireEvent.click(screen.getByText('Login'));
    
    // Wait for login to complete
    await waitFor(() => {
      expect(screen.getByTestId('isLoading').textContent).toBe('false');
      expect(screen.getByTestId('isAuthenticated').textContent).toBe('false');
      expect(consoleError).toHaveBeenCalledWith('Login failed:', expect.any(Error));
    });
    
    // Clean up
    consoleError.mockRestore();
  });

  it('should handle successful registration', async () => {
    const mockUser = { id: '1', name: 'Test User', email: 'test@example.com' };
    mockRegister.mockResolvedValueOnce({ user: mockUser, token: 'test-token' });
    
    renderAuthProvider();
    
    // Wait for initial load
    await waitFor(() => {
      expect(screen.getByTestId('isLoading').textContent).toBe('false');
    });
    
    // Trigger registration
    fireEvent.click(screen.getByText('Register'));
    
    // Check loading state
    expect(screen.getByTestId('isLoading').textContent).toBe('true');
    
    // Wait for registration to complete
    await waitFor(() => {
      expect(mockRegister).toHaveBeenCalledWith({
        name: 'Test',
        email: 'test@example.com',
        password: 'password'
      });
      expect(screen.getByTestId('isLoading').textContent).toBe('false');
      expect(screen.getByTestId('isAuthenticated').textContent).toBe('true');
      expect(JSON.parse(screen.getByTestId('user').textContent || '{}')).toEqual(mockUser);
    });
  });

  it('should handle logout', async () => {
    // Mock initial auth state
    localStorage.setItem('token', 'test-token');
    
    renderAuthProvider();
    
    // Wait for initial load
    await waitFor(() => {
      expect(screen.getByTestId('isLoading').textContent).toBe('false');
    });
    
    // Trigger logout
    fireEvent.click(screen.getByText('Logout'));
    
    // Wait for logout to complete
    await waitFor(() => {
      expect(mockLogout).toHaveBeenCalled();
      expect(screen.getByTestId('isAuthenticated').textContent).toBe('false');
      expect(screen.getByTestId('user').textContent).toBe('null');
      expect(localStorage.getItem('token')).toBeNull();
    });
  });

  it('should handle forgot password', async () => {
    mockForgotPassword.mockResolvedValueOnce({ success: true });
    
    renderAuthProvider();
    
    // Wait for initial load
    await waitFor(() => {
      expect(screen.getByTestId('isLoading').textContent).toBe('false');
    });
    
    // Trigger forgot password
    fireEvent.click(screen.getByText('Forgot Password'));
    
    // Check if the API was called with the correct email
    await waitFor(() => {
      expect(mockForgotPassword).toHaveBeenCalledWith('test@example.com');
    });
  });

  it('should handle reset password', async () => {
    mockResetPassword.mockResolvedValueOnce({ success: true });
    
    renderAuthProvider();
    
    // Wait for initial load
    await waitFor(() => {
      expect(screen.getByTestId('isLoading').textContent).toBe('false');
    });
    
    // Trigger reset password
    fireEvent.click(screen.getByText('Reset Password'));
    
    // Check if the API was called with the correct token and password
    await waitFor(() => {
      expect(mockResetPassword).toHaveBeenCalledWith('token', 'newpassword');
    });
  });

  it('should restore session from localStorage on mount', async () => {
    // Mock user data in localStorage
    const mockUser = { id: '1', name: 'Test User', email: 'test@example.com' };
    localStorage.setItem('token', 'test-token');
    localStorage.setItem('user', JSON.stringify(mockUser));
    
    // Mock the API call to get the current user
    const mockGetCurrentUser = jest.fn().mockResolvedValue(mockUser);
    jest.mock('../../api/auth', () => ({
      ...jest.requireActual('../../api/auth'),
      getCurrentUser: mockGetCurrentUser,
    }));
    
    renderAuthProvider();
    
    // Check if the user is authenticated after mount
    await waitFor(() => {
      expect(screen.getByTestId('isLoading').textContent).toBe('false');
      expect(screen.getByTestId('isAuthenticated').textContent).toBe('true');
      expect(JSON.parse(screen.getByTestId('user').textContent || '{}')).toEqual(mockUser);
    });
  });
});
