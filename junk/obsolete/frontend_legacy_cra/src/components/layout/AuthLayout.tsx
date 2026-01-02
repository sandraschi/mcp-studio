import React from 'react';
import { Link } from 'react-router-dom';
import { Logo } from '../ui/Logo';

interface AuthLayoutProps {
  children: React.ReactNode;
  title: string;
  subtitle?: string;
  footer?: React.ReactNode;
}

export const AuthLayout: React.FC<AuthLayoutProps> = ({ 
  children, 
  title, 
  subtitle,
  footer 
}) => {
  return (
    <div className="min-h-screen flex flex-col bg-gray-50 dark:bg-gray-900">
      {/* Header */}
      <header className="bg-white dark:bg-gray-800 shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex justify-between items-center">
            <Link to="/" className="flex items-center">
              <Logo className="h-8 w-auto" />
              <span className="ml-2 text-xl font-bold text-gray-900 dark:text-white">MCP Studio</span>
            </Link>
            <div className="flex items-center space-x-4">
              <Link 
                to="/login" 
                className="text-sm font-medium text-blue-600 hover:text-blue-500 dark:text-blue-400 dark:hover:text-blue-300"
              >
                Sign in
              </Link>
              <Link
                to="/register"
                className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
              >
                Sign up
              </Link>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="flex-grow flex items-center justify-center py-12 px-4 sm:px-6 lg:px-8">
        <div className="max-w-md w-full space-y-8">
          <div className="text-center">
            <h2 className="mt-6 text-3xl font-extrabold text-gray-900 dark:text-white">
              {title}
            </h2>
            {subtitle && (
              <p className="mt-2 text-sm text-gray-600 dark:text-gray-400">
                {subtitle}
              </p>
            )}
          </div>
          
          {children}
          
          {footer && (
            <div className="mt-6 text-center">
              {footer}
            </div>
          )}
        </div>
      </main>

      {/* Footer */}
      <footer className="bg-white dark:bg-gray-800 shadow-inner">
        <div className="max-w-7xl mx-auto py-6 px-4 overflow-hidden sm:px-6 lg:px-8">
          <nav className="flex flex-wrap justify-center space-x-6">
            <Link to="/about" className="text-sm text-gray-500 hover:text-gray-900 dark:text-gray-400 dark:hover:text-white">
              About
            </Link>
            <Link to="/privacy" className="text-sm text-gray-500 hover:text-gray-900 dark:text-gray-400 dark:hover:text-white">
              Privacy
            </Link>
            <Link to="/terms" className="text-sm text-gray-500 hover:text-gray-900 dark:text-gray-400 dark:hover:text-white">
              Terms
            </Link>
            <Link to="/contact" className="text-sm text-gray-500 hover:text-gray-900 dark:text-gray-400 dark:hover:text-white">
              Contact
            </Link>
          </nav>
          <p className="mt-4 text-center text-sm text-gray-500 dark:text-gray-400">
            &copy; {new Date().getFullYear()} MCP Studio. All rights reserved.
          </p>
        </div>
      </footer>
    </div>
  );
};
