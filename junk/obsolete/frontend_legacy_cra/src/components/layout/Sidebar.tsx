import React from 'react';
import { NavLink, useLocation } from 'react-router-dom';
import { 
  HomeIcon, 
  ServerStackIcon, 
  WrenchScrewdriverIcon, 
  Cog6ToothIcon, 
  PlusIcon,
  DocumentTextIcon,
  ArrowLeftOnRectangleIcon
} from '@heroicons/react/24/outline';

interface SidebarProps {
  onNavigate?: () => void;
}

const navigation = [
  { name: 'Dashboard', href: '/dashboard', icon: HomeIcon },
  { name: 'Servers', href: '/servers', icon: ServerStackIcon },
  { name: 'Tools', href: '/tools', icon: WrenchScrewdriverIcon },
  { name: 'Documentation', href: '/docs', icon: DocumentTextIcon },
  { name: 'Settings', href: '/settings', icon: Cog6ToothIcon },
];

export const Sidebar: React.FC<SidebarProps> = ({ onNavigate }) => {
  const location = useLocation();

  const handleNavClick = () => {
    if (onNavigate) {
      onNavigate();
    }
  };

  return (
    <div className="flex-1 flex flex-col">
      <div className="px-4 py-4">
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white">MCP Studio</h1>
      </div>
      
      <nav className="flex-1 px-2 space-y-1">
        {navigation.map((item) => {
          const isActive = location.pathname.startsWith(item.href);
          return (
            <NavLink
              key={item.name}
              to={item.href}
              onClick={handleNavClick}
              className={`group flex items-center px-2 py-2 text-sm font-medium rounded-md ${
                isActive 
                  ? 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400' 
                  : 'text-gray-700 hover:bg-gray-100 hover:text-gray-900 dark:text-gray-300 dark:hover:bg-gray-700 dark:hover:text-white'
              }`}
            >
              <item.icon 
                className={`mr-3 flex-shrink-0 h-6 w-6 ${
                  isActive 
                    ? 'text-blue-500 dark:text-blue-400' 
                    : 'text-gray-400 group-hover:text-gray-500 dark:text-gray-500 dark:group-hover:text-gray-300'
                }`}
                aria-hidden="true"
              />
              {item.name}
            </NavLink>
          );
        })}
      </nav>
      
      <div className="flex-shrink-0 flex border-t border-gray-200 dark:border-gray-700 p-4">
        <button
          type="button"
          className="inline-flex items-center px-3 py-2 border border-transparent text-sm leading-4 font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 w-full justify-center"
        >
          <PlusIcon className="-ml-0.5 mr-2 h-4 w-4" aria-hidden="true" />
          Add Server
        </button>
      </div>
      
      <div className="flex-shrink-0 flex border-t border-gray-200 dark:border-gray-700 p-4">
        <a
          href="/api/auth/logout"
          className="group flex items-center px-2 py-2 text-sm font-medium rounded-md text-gray-700 hover:bg-gray-100 hover:text-gray-900 dark:text-gray-300 dark:hover:bg-gray-700 dark:hover:text-white w-full"
        >
          <ArrowLeftOnRectangleIcon 
            className="mr-3 h-6 w-6 text-gray-400 group-hover:text-gray-500 dark:text-gray-500 dark:group-hover:text-gray-300"
            aria-hidden="true"
          />
          Sign out
        </a>
      </div>
    </div>
  );
};
