import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { MemoryRouter, useSearchParams } from 'react-router-dom';
import { ResetPassword } from '../../../pages/auth/ResetPassword';
import { authAPI } from '../../../api/auth';
import { ToasterProvider } from '../../../components/ui/Toast';

// Mock the authAPI
jest.mock('../../../api/auth');
const mockedAuthAPI = authAPI as jest.Mocked<typeof authAPI>;

// Mock useSearchParams
jest.mock('react-router-dom', () => ({
  ...jest.requireActual('react-router-dom'),
  useSearchParams: jest.fn(),
}));

const mockUseSearchParams = useSearchParams as jest.MockedFunction<typeof useSearchParams>;

describe('ResetPassword Page', () => {
  const mockNavigate = jest.fn();
  const mockSetSearchParams = jest.fn();
  
  // Mock the useNavigate hook
  jest.mock('react-router-dom', () => ({
    ...jest.requireActual('react-router-dom'),
    useNavigate: () => mockNavigate,
  }));

  beforeEach(() => {
    jest.clearAllMocks();
    
    // Default mock implementation for useSearchParams
    mockUseSearchParams.mockReturnValue([
      // @ts-ignore
      { get: (key: string) => (key === 'token' ? 'test-token' : null) },
      mockSetSearchParams,
    ]);
    
    // Mock the resetPassword function
    mockedAuthAPI.resetPassword.mockResolvedValue({
      message: 'Password has been reset successfully',
    });
  });

  const renderResetPassword = () => {
    return render(
      <ToasterProvider>
        <MemoryRouter>
          <ResetPassword />
        </MemoryRouter>
      </ToasterProvider>
    );
  };

  it('renders the reset password form with token', () => {
    renderResetPassword();
    
    expect(screen.getByText(/reset your password/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/new password/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/confirm new password/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /reset password/i })).toBeInTheDocument();
  });

  it('shows error when token is missing', () => {
    // Mock useSearchParams to return null for token
    mockUseSearchParams.mockReturnValueOnce([
      // @ts-ignore
      { get: () => null },
      mockSetSearchParams,
    ]);
    
    renderResetPassword();
    
    expect(screen.getByText(/invalid or expired token/i)).toBeInTheDocument();
    expect(screen.queryByLabelText(/new password/i)).not.toBeInTheDocument();
    expect(screen.getByRole('link', { name: /request a new link/i })).toBeInTheDocument();
  });

  it('validates the password fields', async () => {
    renderResetPassword();
    
    // Submit the form without filling any fields
    fireEvent.click(screen.getByRole('button', { name: /reset password/i }));
    
    // Check for validation errors
    expect(await screen.findByText(/password is required/i)).toBeInTheDocument();
    
    // Test password length
    const passwordInput = screen.getByLabelText(/new password/i);
    fireEvent.change(passwordInput, { target: { value: 'short' } });
    fireEvent.click(screen.getByRole('button', { name: /reset password/i }));
    
    expect(await screen.findByText(/password must be at least 8 characters/i)).toBeInTheDocument();
    
    // Test password match
    fireEvent.change(passwordInput, { target: { value: 'Password123!' } });
    fireEvent.change(screen.getByLabelText(/confirm new password/i), {
      target: { value: 'Different123!' },
    });
    fireEvent.click(screen.getByRole('button', { name: /reset password/i }));
    
    expect(await screen.findByText(/passwords do not match/i)).toBeInTheDocument();
  });

  it('handles successful password reset', async () => {
    renderResetPassword();
    
    // Fill in the form
    fireEvent.change(screen.getByLabelText(/new password/i), {
      target: { value: 'NewPassword123!' },
    });
    fireEvent.change(screen.getByLabelText(/confirm new password/i), {
      target: { value: 'NewPassword123!' },
    });
    
    // Submit the form
    fireEvent.click(screen.getByRole('button', { name: /reset password/i }));
    
    // Check if the API was called with the correct data
    await waitFor(() => {
      expect(mockedAuthAPI.resetPassword).toHaveBeenCalledWith(
        'test-token',
        'NewPassword123!'
      );
    });
    
    // Check if the success message is displayed
    expect(await screen.findByText(/password has been reset/i)).toBeInTheDocument();
    
    // Check if the form is hidden and success message is shown
    expect(screen.queryByLabelText(/new password/i)).not.toBeInTheDocument();
    expect(screen.getByRole('link', { name: /back to login/i })).toBeInTheDocument();
  });

  it('handles password reset error', async () => {
    // Mock a failed API call
    const errorMessage = 'Invalid or expired token';
    mockedAuthAPI.resetPassword.mockRejectedValueOnce(new Error(errorMessage));
    
    // Mock console.error to prevent error logs in test output
    const consoleError = jest.spyOn(console, 'error').mockImplementation(() => {});
    
    renderResetPassword();
    
    // Fill in the form
    fireEvent.change(screen.getByLabelText(/new password/i), {
      target: { value: 'NewPassword123!' },
    });
    fireEvent.change(screen.getByLabelText(/confirm new password/i), {
      target: { value: 'NewPassword123!' },
    });
    
    // Submit the form
    fireEvent.click(screen.getByRole('button', { name: /reset password/i }));
    
    // Check if the error message is displayed
    expect(await screen.findByText(/error resetting password/i)).toBeInTheDocument();
    
    // Clean up
    consoleError.mockRestore();
  });

  it('navigates to login after successful reset', async () => {
    renderResetPassword();
    
    // Fill in the form
    fireEvent.change(screen.getByLabelText(/new password/i), {
      target: { value: 'NewPassword123!' },
    });
    fireEvent.change(screen.getByLabelText(/confirm new password/i), {
      target: { value: 'NewPassword123!' },
    });
    
    // Submit the form
    fireEvent.click(screen.getByRole('button', { name: /reset password/i }));
    
    // Wait for the success message
    await screen.findByText(/password has been reset/i);
    
    // Click the back to login link
    fireEvent.click(screen.getByRole('link', { name: /back to login/i }));
    
    // Check if the navigate function was called with the correct path
    expect(mockNavigate).toHaveBeenCalledWith('/login');
  });

  it('requests a new reset link when token is invalid', () => {
    // Mock useSearchParams to return null for token
    mockUseSearchParams.mockReturnValueOnce([
      // @ts-ignore
      { get: () => null },
      mockSetSearchParams,
    ]);
    
    renderResetPassword();
    
    // Click the request new link button
    fireEvent.click(screen.getByRole('link', { name: /request a new link/i }));
    
    // Check if the navigate function was called with the correct path
    expect(mockNavigate).toHaveBeenCalledWith('/forgot-password');
  });
});
