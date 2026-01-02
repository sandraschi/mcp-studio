import React, { useState, useCallback } from 'react';
import { Outlet } from 'react-router-dom';
import { Sidebar } from './Sidebar';
import { Navbar } from './Navbar';
import { useTheme } from '../../contexts/ThemeContext';
import { MoonIcon, SunIcon } from '@heroicons/react/24/outline';

interface LayoutProps {
  children?: React.ReactNode;
}

export const Layout: React.FC<LayoutProps> = ({ children }) => {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const { theme, toggleTheme } = useTheme();

  const toggleSidebar = useCallback(() => {
    setSidebarOpen((prev) => !prev);
  }, []);

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900 text-gray-900 dark:text-gray-100 flex">
      {/* Mobile sidebar */}
      <div
        className={`fixed inset-0 z-40 lg:hidden ${
          sidebarOpen ? 'block' : 'hidden'
        }`}
      >
        <div
          className="fixed inset-0 bg-gray-600 bg-opacity-75"
          onClick={toggleSidebar}
        ></div>
        <div className="fixed inset-0 flex z-40">
          <div className="relative flex-1 flex flex-col w-64 max-w-xs bg-white dark:bg-gray-800">
            <div className="flex-1 h-0 pt-5 pb-4 overflow-y-auto">
              <Sidebar onNavigate={toggleSidebar} />
            </div>
          </div>
        </div>
      </div>

      {/* Static sidebar for desktop */}
      <div className="hidden lg:flex lg:flex-shrink-0">
        <div className="flex flex-col w-64 border-r border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800">
          <div className="flex-1 flex flex-col pt-5 pb-4 overflow-y-auto">
            <Sidebar />
          </div>
        </div>
      </div>

      <div className="flex-1 flex flex-col overflow-hidden">
        <Navbar onMenuClick={toggleSidebar} />
        
        <main className="flex-1 overflow-y-auto focus:outline-none p-4 md:p-6">
          {children || <Outlet />}
        </main>
        
        <footer className="bg-white dark:bg-gray-800 border-t border-gray-200 dark:border-gray-700 py-4 px-6">
          <div className="flex items-center justify-between">
            <p className="text-sm text-gray-500 dark:text-gray-400">
              MCP Studio © {new Date().getFullYear()}
            </p>
            <button
              type="button"
              onClick={toggleTheme}
              className="p-2 rounded-full text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
            >
              {theme === 'dark' ? (
                <SunIcon className="h-5 w-5" aria-hidden="true" />
              ) : (
                <MoonIcon className="h-5 w-5" aria-hidden="true" />
              )}
              <span className="sr-only">
                {theme === 'dark' ? 'Switch to light mode' : 'Switch to dark mode'}
              </span>
            </button>
          </div>
        </footer>
      </div>
    </div>
  );
};
