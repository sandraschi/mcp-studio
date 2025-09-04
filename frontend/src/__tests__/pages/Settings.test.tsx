import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { Settings } from '../../pages/Settings';
import { useAuth } from '../../contexts/AuthContext';
import { ToasterProvider } from '../../components/ui/Toast';

// Mock the AuthContext
jest.mock('../../contexts/AuthContext');
const mockedUseAuth = useAuth as jest.MockedFunction<typeof useAuth>;

describe('Settings Page', () => {
  const mockUpdateProfile = jest.fn();
  const mockChangePassword = jest.fn();
  
  const mockUser = {
    id: '1',
    name: 'Test User',
    email: 'test@example.com',
    avatar: 'https://example.com/avatar.jpg',
  };

  beforeEach(() => {
    jest.clearAllMocks();
    
    // Mock the AuthContext
    mockedUseAuth.mockReturnValue({
      user: mockUser,
      isAuthenticated: true,
      isLoading: false,
      login: jest.fn(),
      register: jest.fn(),
      logout: jest.fn(),
      forgotPassword: jest.fn(),
      resetPassword: jest.fn(),
      updateProfile: mockUpdateProfile,
      changePassword: mockChangePassword,
    });
    
    // Mock localStorage
    Storage.prototype.setItem = jest.fn();
    Storage.prototype.getItem = jest.fn();
  });

  const renderSettings = () => {
    return render(
      <ToasterProvider>
        <MemoryRouter>
          <Settings />
        </MemoryRouter>
      </ToasterProvider>
    );
  };

  it('renders all settings tabs', () => {
    renderSettings();
    
    // Check if all tab buttons are rendered
    expect(screen.getByRole('tab', { name: /profile/i })).toBeInTheDocument();
    expect(screen.getByRole('tab', { name: /account/i })).toBeInTheDocument();
    expect(screen.getByRole('tab', { name: /appearance/i })).toBeInTheDocument();
    expect(screen.getByRole('tab', { name: /notifications/i })).toBeInTheDocument();
    expect(screen.getByRole('tab', { name: /billing/i })).toBeInTheDocument();
  });

  it('displays user profile information', () => {
    renderSettings();
    
    // Check if user information is displayed
    expect(screen.getByDisplayValue(mockUser.name)).toBeInTheDocument();
    expect(screen.getByDisplayValue(mockUser.email)).toBeInTheDocument();
    expect(screen.getByAltText('Profile')).toHaveAttribute('src', mockUser.avatar);
  });

  it('updates profile information', async () => {
    mockUpdateProfile.mockResolvedValueOnce({
      ...mockUser,
      name: 'Updated Name',
    });
    
    renderSettings();
    
    // Change the name
    const nameInput = screen.getByLabelText(/name/i);
    fireEvent.change(nameInput, { target: { value: 'Updated Name' } });
    
    // Submit the form
    fireEvent.click(screen.getByRole('button', { name: /save changes/i }));
    
    // Check if the update function was called with the correct data
    await waitFor(() => {
      expect(mockUpdateProfile).toHaveBeenCalledWith({
        name: 'Updated Name',
        email: mockUser.email,
        avatar: mockUser.avatar,
      });
    });
    
    // Check if success message is shown
    expect(await screen.findByText(/profile updated successfully/i)).toBeInTheDocument();
  });

  it('changes password', async () => {
    mockChangePassword.mockResolvedValueOnce({ message: 'Password changed successfully' });
    
    renderSettings();
    
    // Switch to the Account tab
    fireEvent.click(screen.getByRole('tab', { name: /account/i }));
    
    // Fill in the password form
    fireEvent.change(screen.getByLabelText(/current password/i), {
      target: { value: 'oldpassword' },
    });
    fireEvent.change(screen.getByLabelText(/new password/i), {
      target: { value: 'NewPassword123!' },
    });
    fireEvent.change(screen.getByLabelText(/confirm new password/i), {
      target: { value: 'NewPassword123!' },
    });
    
    // Submit the form
    fireEvent.click(screen.getByRole('button', { name: /change password/i }));
    
    // Check if the change password function was called with the correct data
    await waitFor(() => {
      expect(mockChangePassword).toHaveBeenCalledWith('oldpassword', 'NewPassword123!');
    });
    
    // Check if success message is shown
    expect(await screen.findByText(/password changed successfully/i)).toBeInTheDocument();
  });

  it('updates appearance settings', async () => {
    renderSettings();
    
    // Switch to the Appearance tab
    fireEvent.click(screen.getByRole('tab', { name: /appearance/i }));
    
    // Change the theme
    const themeSelect = screen.getByLabelText(/theme/i);
    fireEvent.change(themeSelect, { target: { value: 'dark' } });
    
    // Change the font size
    const fontSizeInput = screen.getByLabelText(/font size/i);
    fireEvent.change(fontSizeInput, { target: { value: '16' } });
    
    // Toggle the compact mode
    const compactToggle = screen.getByLabelText(/compact mode/i);
    fireEvent.click(compactToggle);
    
    // Save the settings
    fireEvent.click(screen.getByRole('button', { name: /save appearance settings/i }));
    
    // Check if the settings were saved to localStorage
    expect(localStorage.setItem).toHaveBeenCalledWith(
      'appearanceSettings',
      JSON.stringify({
        theme: 'dark',
        fontSize: 16,
        compact: true,
      })
    );
    
    // Check if success message is shown
    expect(await screen.findByText(/appearance settings saved/i)).toBeInTheDocument();
  });

  it('updates notification settings', async () => {
    renderSettings();
    
    // Switch to the Notifications tab
    fireEvent.click(screen.getByRole('tab', { name: /notifications/i }));
    
    // Toggle email notifications
    const emailToggle = screen.getByLabelText(/email notifications/i);
    fireEvent.click(emailToggle);
    
    // Toggle push notifications
    const pushToggle = screen.getByLabelText(/push notifications/i);
    fireEvent.click(pushToggle);
    
    // Save the settings
    fireEvent.click(screen.getByRole('button', { name: /save notification settings/i }));
    
    // Check if the settings were saved to localStorage
    expect(localStorage.setItem).toHaveBeenCalledWith(
      'notificationSettings',
      JSON.stringify({
        email: false,
        push: false,
      })
    );
    
    // Check if success message is shown
    expect(await screen.findByText(/notification settings saved/i)).toBeInTheDocument();
  });

  it('displays billing information', () => {
    renderSettings();
    
    // Switch to the Billing tab
    fireEvent.click(screen.getByRole('tab', { name: /billing/i }));
    
    // Check if billing information is displayed
    expect(screen.getByText(/current plan/i)).toBeInTheDocument();
    expect(screen.getByText(/payment method/i)).toBeInTheDocument();
    expect(screen.getByText(/billing history/i)).toBeInTheDocument();
  });

  it('handles errors when updating profile', async () => {
    const errorMessage = 'Failed to update profile';
    mockUpdateProfile.mockRejectedValueOnce(new Error(errorMessage));
    
    // Mock console.error to prevent error logs in test output
    const consoleError = jest.spyOn(console, 'error').mockImplementation(() => {});
    
    renderSettings();
    
    // Change the name
    const nameInput = screen.getByLabelText(/name/i);
    fireEvent.change(nameInput, { target: { value: 'Updated Name' } });
    
    // Submit the form
    fireEvent.click(screen.getByRole('button', { name: /save changes/i }));
    
    // Check if error message is shown
    expect(await screen.findByText(/failed to update profile/i)).toBeInTheDocument();
    
    // Clean up
    consoleError.mockRestore();
  });

  it('validates password change form', async () => {
    renderSettings();
    
    // Switch to the Account tab
    fireEvent.click(screen.getByRole('tab', { name: /account/i }));
    
    // Try to submit the form without filling in the fields
    fireEvent.click(screen.getByRole('button', { name: /change password/i }));
    
    // Check for validation errors
    expect(await screen.findByText(/current password is required/i)).toBeInTheDocument();
    expect(screen.getByText(/new password is required/i)).toBeInTheDocument();
    
    // Fill in the form with invalid data
    fireEvent.change(screen.getByLabelText(/current password/i), {
      target: { value: 'short' },
    });
    fireEvent.change(screen.getByLabelText(/new password/i), {
      target: { value: 'new' },
    });
    fireEvent.change(screen.getByLabelText(/confirm new password/i), {
      target: { value: 'different' },
    });
    
    // Submit the form
    fireEvent.click(screen.getByRole('button', { name: /change password/i }));
    
    // Check for validation errors
    expect(await screen.findByText(/password must be at least 8 characters/i)).toBeInTheDocument();
    expect(screen.getByText(/passwords do not match/i)).toBeInTheDocument();
  });
});
