import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { ForgotPassword } from '../../../pages/auth/ForgotPassword';
import { authAPI } from '../../../api/auth';
import { ToasterProvider } from '../../../components/ui/Toast';

// Mock the authAPI
jest.mock('../../../api/auth');
const mockedAuthAPI = authAPI as jest.Mocked<typeof authAPI>;

describe('ForgotPassword Page', () => {
  const mockNavigate = jest.fn();
  
  // Mock the useNavigate hook
  jest.mock('react-router-dom', () => ({
    ...jest.requireActual('react-router-dom'),
    useNavigate: () => mockNavigate,
  }));

  beforeEach(() => {
    jest.clearAllMocks();
    mockedAuthAPI.forgotPassword.mockResolvedValue({
      message: 'Password reset email sent',
    });
  });

  const renderForgotPassword = () => {
    return render(
      <ToasterProvider>
        <MemoryRouter>
          <ForgotPassword />
        </MemoryRouter>
      </ToasterProvider>
    );
  };

  it('renders the forgot password form', () => {
    renderForgotPassword();
    
    expect(screen.getByText(/forgot your password/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/email address/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /send reset link/i })).toBeInTheDocument();
    expect(screen.getByRole('link', { name: /back to login/i })).toBeInTheDocument();
  });

  it('validates the email field', async () => {
    renderForgotPassword();
    
    // Submit the form without filling the email
    fireEvent.click(screen.getByRole('button', { name: /send reset link/i }));
    
    // Check for validation error
    expect(await screen.findByText(/email is required/i)).toBeInTheDocument();
    
    // Test invalid email format
    const emailInput = screen.getByLabelText(/email address/i);
    fireEvent.change(emailInput, { target: { value: 'invalid-email' } });
    fireEvent.click(screen.getByRole('button', { name: /send reset link/i }));
    
    expect(await screen.findByText(/email is invalid/i)).toBeInTheDocument();
  });

  it('handles successful password reset request', async () => {
    renderForgotPassword();
    
    // Fill in the email
    fireEvent.change(screen.getByLabelText(/email address/i), {
      target: { value: 'test@example.com' },
    });
    
    // Submit the form
    fireEvent.click(screen.getByRole('button', { name: /send reset link/i }));
    
    // Check if the API was called with the correct email
    await waitFor(() => {
      expect(mockedAuthAPI.forgotPassword).toHaveBeenCalledWith('test@example.com');
    });
    
    // Check if the success message is displayed
    expect(await screen.findByText(/password reset email sent/i)).toBeInTheDocument();
    
    // Check if the form is hidden and success message is shown
    expect(screen.queryByLabelText(/email address/i)).not.toBeInTheDocument();
    expect(screen.getByText(/check your email/i)).toBeInTheDocument();
  });

  it('handles password reset request error', async () => {
    // Mock a failed API call
    const errorMessage = 'User not found';
    mockedAuthAPI.forgotPassword.mockRejectedValueOnce(new Error(errorMessage));
    
    // Mock console.error to prevent error logs in test output
    const consoleError = jest.spyOn(console, 'error').mockImplementation(() => {});
    
    renderForgotPassword();
    
    // Fill in the email
    fireEvent.change(screen.getByLabelText(/email address/i), {
      target: { value: 'nonexistent@example.com' },
    });
    
    // Submit the form
    fireEvent.click(screen.getByRole('button', { name: /send reset link/i }));
    
    // Check if the error message is displayed
    expect(await screen.findByText(/error sending reset email/i)).toBeInTheDocument();
    
    // Clean up
    consoleError.mockRestore();
  });

  it('navigates back to login', () => {
    renderForgotPassword();
    
    // Click the back to login link
    fireEvent.click(screen.getByRole('link', { name: /back to login/i }));
    
    // Check if the navigate function was called with the correct path
    expect(mockNavigate).toHaveBeenCalledWith('/login');
  });
});
