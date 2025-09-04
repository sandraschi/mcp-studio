import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { Register } from '../../../pages/auth/Register';
import { authAPI } from '../../../api/auth';
import { ToasterProvider } from '../../../components/ui/Toast';

// Mock the authAPI
jest.mock('../../../api/auth');
const mockedAuthAPI = authAPI as jest.Mocked<typeof authAPI>;

describe('Register Page', () => {
  const mockNavigate = jest.fn();
  
  // Mock the useNavigate hook
  jest.mock('react-router-dom', () => ({
    ...jest.requireActual('react-router-dom'),
    useNavigate: () => mockNavigate,
  }));

  beforeEach(() => {
    jest.clearAllMocks();
    mockedAuthAPI.register.mockResolvedValue({
      user: { 
        id: '1', 
        name: 'Test User', 
        email: 'test@example.com',
        emailVerified: false
      },
      token: 'test-token',
    });
  });

  const renderRegister = () => {
    return render(
      <ToasterProvider>
        <MemoryRouter>
          <Register />
        </MemoryRouter>
      </ToasterProvider>
    );
  };

  it('renders the registration form', () => {
    renderRegister();
    expect(screen.getByLabelText(/full name/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/email address/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/password/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/confirm password/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /create account/i })).toBeInTheDocument();
  });

  it('validates the form fields', async () => {
    renderRegister();
    fireEvent.click(screen.getByRole('button', { name: /create account/i }));
    
    expect(await screen.findByText(/name is required/i)).toBeInTheDocument();
    expect(await screen.findByText(/email is required/i)).toBeInTheDocument();
    expect(await screen.findByText(/password is required/i)).toBeInTheDocument();
  });

  it('handles successful registration', async () => {
    renderRegister();
    
    fireEvent.change(screen.getByLabelText(/full name/i), {
      target: { value: 'Test User' },
    });
    fireEvent.change(screen.getByLabelText(/email address/i), {
      target: { value: 'test@example.com' },
    });
    fireEvent.change(screen.getByLabelText(/password/i), {
      target: { value: 'Password123!' },
    });
    fireEvent.change(screen.getByLabelText(/confirm password/i), {
      target: { value: 'Password123!' },
    });
    
    fireEvent.click(screen.getByRole('button', { name: /create account/i }));
    
    await waitFor(() => {
      expect(mockedAuthAPI.register).toHaveBeenCalledWith({
        name: 'Test User',
        email: 'test@example.com',
        password: 'Password123!',
        passwordConfirmation: 'Password123!',
      });
    });
    
    expect(mockNavigate).toHaveBeenCalledWith('/', { replace: true });
  });
});
