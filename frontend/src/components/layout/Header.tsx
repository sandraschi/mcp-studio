import React from 'react';
import { useApp } from '../../contexts/AppContext';
import { BellIcon, MenuIcon, MoonIcon, SunIcon } from '../common/Icons';
import SearchBar from '../common/SearchBar';
import UserMenu from '../common/UserMenu';

const Header: React.FC = () => {
  const { state, toggleDarkMode, toggleSidebar, addNotification } = useApp();
  const { darkMode, notifications } = state;
  
  const unreadCount = notifications.filter(n => !n.read).length;

  return (
    <header className="bg-white dark:bg-gray-800 shadow-sm z-10">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between h-16">
          <div className="flex items-center">
            {/* Mobile menu button */}
            <button
              type="button"
              className="inline-flex items-center justify-center p-2 rounded-md text-gray-500 hover:text-gray-600 hover:bg-gray-100 dark:text-gray-400 dark:hover:bg-gray-700 focus:outline-none focus:ring-2 focus:ring-inset focus:ring-blue-500"
              onClick={toggleSidebar}
            >
              <span className="sr-only">Open main menu</span>
              <MenuIcon className="h-6 w-6" />
            </button>

            {/* Logo */}
            <div className="hidden md:flex items-center ml-4">
              <span className="text-xl font-bold text-blue-600 dark:text-blue-400">MCP Studio</span>
            </div>
          </div>

          {/* Search bar */}
          <div className="flex-1 flex items-center justify-center px-2 lg:ml-6 lg:justify-end">
            <div className="max-w-lg w-full lg:max-w-xs">
              <SearchBar />
            </div>
          </div>

          <div className="flex items-center">
            {/* Theme toggle */}
            <button
              type="button"
              className="p-2 rounded-full text-gray-500 hover:text-gray-600 hover:bg-gray-100 dark:text-gray-400 dark:hover:bg-gray-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
              onClick={toggleDarkMode}
            >
              <span className="sr-only">Toggle dark mode</span>
              {darkMode ? (
                <SunIcon className="h-5 w-5" />
              ) : (
                <MoonIcon className="h-5 w-5" />
              )}
            </button>

            {/* Notifications */}
            <div className="ml-4 relative">
              <button
                type="button"
                className="p-2 rounded-full text-gray-500 hover:text-gray-600 hover:bg-gray-100 dark:text-gray-400 dark:hover:bg-gray-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 relative"
                onClick={() => {
                  // Show notifications panel
                  addNotification({
                    type: 'info',
                    title: 'Notifications',
                    message: 'Notification panel will be implemented here',
                  });
                }}
              >
                <span className="sr-only">View notifications</span>
                <BellIcon className="h-5 w-5" />
                {unreadCount > 0 && (
                  <span className="absolute top-1 right-1 h-3 w-3 rounded-full bg-red-500 border-2 border-white dark:border-gray-800">
                    <span className="sr-only">{unreadCount} unread notifications</span>
                  </span>
                )}
              </button>
            </div>

            {/* User menu */}
            <div className="ml-4 flex items-center">
              <UserMenu />
            </div>
          </div>
        </div>
      </div>
    </header>
  );
};

export default Header;
