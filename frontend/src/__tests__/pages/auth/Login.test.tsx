import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { Login } from '../../../pages/auth/Login';
import { authAPI } from '../../../api/auth';
import { ToasterProvider } from '../../../components/ui/Toast';

// Mock the authAPI
jest.mock('../../../api/auth');
const mockedAuthAPI = authAPI as jest.Mocked<typeof authAPI>;

describe('Login Page', () => {
  const mockNavigate = jest.fn();
  
  // Mock the useNavigate hook
  jest.mock('react-router-dom', () => ({
    ...jest.requireActual('react-router-dom'),
    useNavigate: () => mockNavigate,
    useLocation: () => ({}),
  }));

  beforeEach(() => {
    // Clear all mocks before each test
    jest.clearAllMocks();
    // Mock the login function
    mockedAuthAPI.login.mockResolvedValue({
      user: { id: '1', name: 'Test User', email: 'test@example.com' },
      token: 'test-token',
    });
  });

  const renderLogin = () => {
    return render(
      <ToasterProvider>
        <MemoryRouter>
          <Login />
        </MemoryRouter>
      </ToasterProvider>
    );
  };

  it('renders the login form', () => {
    renderLogin();
    
    // Check if the form elements are rendered
    expect(screen.getByLabelText(/email address/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/password/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /sign in/i })).toBeInTheDocument();
    expect(screen.getByRole('link', { name: /forgot your password/i })).toBeInTheDocument();
    expect(screen.getByText(/or continue with/i)).toBeInTheDocument();
  });

  it('validates the form fields', async () => {
    renderLogin();
    
    // Submit the form without filling any fields
    fireEvent.click(screen.getByRole('button', { name: /sign in/i }));
    
    // Check for validation errors
    expect(await screen.findByText(/email is required/i)).toBeInTheDocument();
    expect(await screen.findByText(/password is required/i)).toBeInTheDocument();
    
    // Test invalid email format
    const emailInput = screen.getByLabelText(/email address/i);
    fireEvent.change(emailInput, { target: { value: 'invalid-email' } });
    fireEvent.click(screen.getByRole('button', { name: /sign in/i }));
    
    expect(await screen.findByText(/email is invalid/i)).toBeInTheDocument();
    
    // Test password length
    const passwordInput = screen.getByLabelText(/password/i);
    fireEvent.change(passwordInput, { target: { value: 'short' } });
    fireEvent.click(screen.getByRole('button', { name: /sign in/i }));
    
    expect(await screen.findByText(/password must be at least 6 characters/i)).toBeInTheDocument();
  });

  it('handles successful login', async () => {
    renderLogin();
    
    // Fill in the form
    fireEvent.change(screen.getByLabelText(/email address/i), {
      target: { value: 'test@example.com' },
    });
    fireEvent.change(screen.getByLabelText(/password/i), {
      target: { value: 'password123' },
    });
    
    // Submit the form
    fireEvent.click(screen.getByRole('button', { name: /sign in/i }));
    
    // Check if the login API was called with the correct data
    await waitFor(() => {
      expect(mockedAuthAPI.login).toHaveBeenCalledWith('test@example.com', 'password123');
    });
    
    // Check if the user is redirected to the home page after successful login
    expect(mockNavigate).toHaveBeenCalledWith('/', { replace: true });
  });

  it('handles login error', async () => {
    // Mock a failed login
    const errorMessage = 'Invalid credentials';
    mockedAuthAPI.login.mockRejectedValueOnce(new Error(errorMessage));
    
    // Mock console.error to prevent error logs in test output
    const consoleError = jest.spyOn(console, 'error').mockImplementation(() => {});
    
    renderLogin();
    
    // Fill in the form
    fireEvent.change(screen.getByLabelText(/email address/i), {
      target: { value: 'test@example.com' },
    });
    fireEvent.change(screen.getByLabelText(/password/i), {
      target: { value: 'wrongpassword' },
    });
    
    // Submit the form
    fireEvent.click(screen.getByRole('button', { name: /sign in/i }));
    
    // Check if the error message is displayed
    expect(await screen.findByText(/invalid email or password/i)).toBeInTheDocument();
    
    // Clean up
    consoleError.mockRestore();
  });

  it('toggles password visibility', () => {
    renderLogin();
    
    const passwordInput = screen.getByLabelText(/password/i) as HTMLInputElement;
    const toggleButton = screen.getByRole('button', { name: /toggle password visibility/i });
    
    // Password should be hidden by default
    expect(passwordInput.type).toBe('password');
    
    // Click the toggle button
    fireEvent.click(toggleButton);
    
    // Password should be visible
    expect(passwordInput.type).toBe('text');
    
    // Click the toggle button again
    fireEvent.click(toggleButton);
    
    // Password should be hidden again
    expect(passwordInput.type).toBe('password');
  });

  it('navigates to the registration page', () => {
    renderLogin();
    
    // Click the registration link
    fireEvent.click(screen.getByRole('link', { name: /create a new account/i }));
    
    // Check if the navigate function was called with the correct path
    expect(mockNavigate).toHaveBeenCalledWith('/register');
  });

  it('navigates to the forgot password page', () => {
    renderLogin();
    
    // Click the forgot password link
    fireEvent.click(screen.getByRole('link', { name: /forgot your password/i }));
    
    // Check if the navigate function was called with the correct path
    expect(mockNavigate).toHaveBeenCalledWith('/forgot-password');
  });

  it('handles social login', async () => {
    // Mock the window.open function
    const mockOpen = jest.fn();
    const originalOpen = window.open;
    window.open = mockOpen;
    
    renderLogin();
    
    // Click the GitHub login button
    const githubButton = screen.getByRole('button', { name: /sign in with github/i });
    fireEvent.click(githubButton);
    
    // Check if the window.open was called with the correct URL
    expect(mockOpen).toHaveBeenCalledWith(
      expect.stringContaining('/auth/github'),
      '_self'
    );
    
    // Restore the original window.open
    window.open = originalOpen;
  });
});
