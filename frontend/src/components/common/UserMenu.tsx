import React, { useState, useRef, useEffect } from 'react';
import { useApp } from '../../contexts/AppContext';
import { 
  UserCircleIcon, 
  Cog6ToothIcon, 
  ArrowRightOnRectangleIcon, 
  ChevronDownIcon 
} from './Icons';

const UserMenu: React.FC = () => {
  const [isOpen, setIsOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);
  const { addNotification } = useApp();

  // Mock user data - replace with actual user data from context
  const user = {
    name: 'John Doe',
    email: 'john@example.com',
    avatar: null,
  };

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, []);

  const handleSignOut = () => {
    // Handle sign out logic here
    addNotification({
      type: 'info',
      title: 'Signed out',
      message: 'You have been successfully signed out.',
    });
  };

  return (
    <div className="relative ml-3" ref={dropdownRef}>
      <div>
        <button
          type="button"
          className="flex items-center max-w-xs rounded-full bg-white dark:bg-gray-800 text-sm focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
          id="user-menu"
          aria-expanded="false"
          aria-haspopup="true"
          onClick={() => setIsOpen(!isOpen)}
        >
          <span className="sr-only">Open user menu</span>
          {user.avatar ? (
            <img
              className="h-8 w-8 rounded-full"
              src={user.avatar}
              alt={user.name}
            />
          ) : (
            <UserCircleIcon className="h-8 w-8 text-gray-400" />
          )}
          <span className="ml-2 hidden md:inline-block text-sm font-medium text-gray-700 dark:text-gray-200">
            {user.name}
          </span>
          <ChevronDownIcon 
            className={`ml-1 h-4 w-4 text-gray-400 transition-transform ${
              isOpen ? 'transform rotate-180' : ''
            }`} 
          />
        </button>
      </div>

      {/* Dropdown menu */}
      {isOpen && (
        <div
          className="origin-top-right absolute right-0 mt-2 w-48 rounded-md shadow-lg py-1 bg-white dark:bg-gray-800 ring-1 ring-black ring-opacity-5 focus:outline-none z-50"
          role="menu"
          aria-orientation="vertical"
          aria-labelledby="user-menu"
        >
          <div className="px-4 py-2 border-b border-gray-200 dark:border-gray-700">
            <p className="text-sm font-medium text-gray-900 dark:text-white truncate">
              {user.name}
            </p>
            <p className="text-xs text-gray-500 dark:text-gray-400 truncate">
              {user.email}
            </p>
          </div>
          
          <a
            href="#"
            className="flex items-center px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 dark:text-gray-300 dark:hover:bg-gray-700"
            role="menuitem"
          >
            <UserCircleIcon className="mr-3 h-5 w-5 text-gray-400" />
            Your Profile
          </a>
          
          <a
            href="#"
            className="flex items-center px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 dark:text-gray-300 dark:hover:bg-gray-700"
            role="menuitem"
          >
            <Cog6ToothIcon className="mr-3 h-5 w-5 text-gray-400" />
            Settings
          </a>
          
          <div className="border-t border-gray-200 dark:border-gray-700 my-1"></div>
          
          <button
            onClick={handleSignOut}
            className="w-full text-left flex items-center px-4 py-2 text-sm text-red-600 hover:bg-gray-100 dark:text-red-400 dark:hover:bg-gray-700"
            role="menuitem"
          >
            <ArrowRightOnRectangleIcon className="mr-3 h-5 w-5 text-red-400" />
            Sign out
          </button>
        </div>
      )}
    </div>
  );
};

export default UserMenu;
