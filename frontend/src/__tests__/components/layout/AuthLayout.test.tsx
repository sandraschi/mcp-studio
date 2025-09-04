import React from 'react';
import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { AuthLayout } from '../../../components/layout/AuthLayout';

describe('AuthLayout', () => {
  const renderAuthLayout = (children: React.ReactNode = null) => {
    return render(
      <MemoryRouter>
        <AuthLayout>{children}</AuthLayout>
      </MemoryRouter>
    );
  };

  it('renders the logo and navigation links', () => {
    renderAuthLayout();
    
    // Check if the logo is rendered
    const logo = screen.getByAltText('MCP Studio');
    expect(logo).toBeInTheDocument();
    expect(logo).toHaveAttribute('src', '/logo.png');
    
    // Check if the navigation links are rendered
    expect(screen.getByRole('link', { name: /home/i })).toBeInTheDocument();
    expect(screen.getByRole('link', { name: /documentation/i })).toBeInTheDocument();
    expect(screen.getByRole('link', { name: /github/i })).toBeInTheDocument();
  });

  it('renders the children content', () => {
    const testContent = 'Test Content';
    renderAuthLayout(<div>{testContent}</div>);
    
    // Check if the children content is rendered
    expect(screen.getByText(testContent)).toBeInTheDocument();
  });

  it('renders the footer with current year', () => {
    const currentYear = new Date().getFullYear();
    renderAuthLayout();
    
    // Check if the footer contains the current year
    expect(screen.getByText(new RegExp(`© ${currentYear} MCP Studio`))).toBeInTheDocument();
    
    // Check if the footer links are rendered
    expect(screen.getByRole('link', { name: /privacy/i })).toBeInTheDocument();
    expect(screen.getByRole('link', { name: /terms/i })).toBeInTheDocument();
    expect(screen.getByRole('link', { name: /contact/i })).toBeInTheDocument();
  });

  it('applies the correct CSS classes', () => {
    renderAuthLayout();
    
    // Check if the main container has the correct classes
    const main = screen.getByRole('main');
    expect(main).toHaveClass('min-h-screen', 'bg-gray-50', 'flex', 'flex-col');
    
    // Check if the content container has the correct classes
    const content = screen.getByTestId('auth-content');
    expect(content).toHaveClass('flex-1', 'flex', 'items-center', 'justify-center', 'py-12', 'px-4', 'sm:px-6', 'lg:px-8');
  });
});
