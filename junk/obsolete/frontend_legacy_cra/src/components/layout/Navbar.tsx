import React, { useState, Fragment } from 'react';
import { useNavigate } from 'react-router-dom';
import { Menu, Transition } from '@headlessui/react';
import { 
  MagnifyingGlassIcon,
  BellIcon,
  Bars3Icon,
  XMarkIcon
} from '@heroicons/react/24/outline';
import { useTheme } from '../../contexts/ThemeContext';

interface NavbarProps {
  onMenuClick: () => void;
}

const userNavigation = [
  { name: 'Your Profile', href: '/profile' },
  { name: 'Settings', href: '/settings' },
  { name: 'Sign out', href: '/api/auth/logout' },
];

export const Navbar: React.FC<NavbarProps> = ({ onMenuClick }) => {
  const [searchQuery, setSearchQuery] = useState('');
  const navigate = useNavigate();
  const { theme } = useTheme();

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    if (searchQuery.trim()) {
      navigate(`/search?q=${encodeURIComponent(searchQuery)}`);
      setSearchQuery('');
    }
  };

  return (
    <div className="sticky top-0 z-10 flex-shrink-0 flex h-16 bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700">
      <button
        type="button"
        className="px-4 border-r border-gray-200 dark:border-gray-700 text-gray-500 focus:outline-none focus:ring-2 focus:ring-inset focus:ring-blue-500 lg:hidden"
        onClick={onMenuClick}
      >
        <span className="sr-only">Open sidebar</span>
        <Bars3Icon className="h-6 w-6" aria-hidden="true" />
      </button>
      
      <div className="flex-1 px-4 flex justify-between">
        <div className="flex-1 flex">
          <form className="w-full flex md:ml-0" onSubmit={handleSearch}>
            <label htmlFor="search-field" className="sr-only">
              Search
            </label>
            <div className="relative w-full text-gray-400 focus-within:text-gray-600 dark:focus-within:text-gray-300">
              <div className="absolute inset-y-0 left-0 flex items-center pointer-events-none">
                <MagnifyingGlassIcon className="h-5 w-5" aria-hidden="true" />
              </div>
              <input
                id="search-field"
                className="block w-full h-full pl-8 pr-3 py-2 border-transparent text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-gray-400 focus:outline-none focus:placeholder-gray-400 dark:focus:placeholder-gray-500 focus:ring-0 focus:border-transparent sm:text-sm bg-transparent"
                placeholder="Search servers, tools, etc..."
                type="search"
                name="search"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
              />
              {searchQuery && (
                <button
                  type="button"
                  className="absolute inset-y-0 right-0 flex items-center pr-3"
                  onClick={() => setSearchQuery('')}
                >
                  <XMarkIcon className="h-5 w-5" aria-hidden="true" />
                </button>
              )}
            </div>
          </form>
        </div>
        
        <div className="ml-4 flex items-center md:ml-6">
          <button
            type="button"
            className="p-1 rounded-full text-gray-400 hover:text-gray-500 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
          >
            <span className="sr-only">View notifications</span>
            <BellIcon className="h-6 w-6" aria-hidden="true" />
          </button>

          {/* Profile dropdown */}
          <Menu as="div" className="ml-3 relative">
            <div>
              <Menu.Button className="max-w-xs bg-white dark:bg-gray-800 rounded-full flex items-center text-sm focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500">
                <span className="sr-only">Open user menu</span>
                <div className="h-8 w-8 rounded-full bg-blue-500 flex items-center justify-center text-white font-medium">
                  U
                </div>
              </Menu.Button>
            </div>
            <Transition
              as={Fragment}
              enter="transition ease-out duration-100"
              enterFrom="transform opacity-0 scale-95"
              enterTo="transform opacity-100 scale-100"
              leave="transition ease-in duration-75"
              leaveFrom="transform opacity-100 scale-100"
              leaveTo="transform opacity-0 scale-95"
            >
              <Menu.Items className="origin-top-right absolute right-0 mt-2 w-48 rounded-md shadow-lg py-1 bg-white dark:bg-gray-800 ring-1 ring-black ring-opacity-5 focus:outline-none">
                {userNavigation.map((item) => (
                  <Menu.Item key={item.name}>
                    {({ active }) => (
                      <a
                        href={item.href}
                        className={`block px-4 py-2 text-sm ${
                          active ? 'bg-gray-100 dark:bg-gray-700' : ''
                        } text-gray-700 dark:text-gray-200`}
                      >
                        {item.name}
                      </a>
                    )}
                  </Menu.Item>
                ))}
              </Menu.Items>
            </Transition>
          </Menu>
        </div>
      </div>
    </div>
  );
};
