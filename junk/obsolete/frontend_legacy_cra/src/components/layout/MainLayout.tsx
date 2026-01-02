import React from 'react';
import { useApp } from '../../contexts/AppContext';
import Sidebar from './Sidebar';
import Header from './Header';
import Notifications from '../common/Notifications';

interface MainLayoutProps {
  children: React.ReactNode;
}

const MainLayout: React.FC<MainLayoutProps> = ({ children }) => {
  const { state, toggleSidebar } = useApp();
  const { darkMode, sidebarOpen } = state;

  return (
    <div className={`min-h-screen flex flex-col ${darkMode ? 'dark' : ''}`}>
      <div className="flex flex-1 overflow-hidden">
        {/* Mobile sidebar backdrop */}
        <div
          className={`fixed inset-0 bg-gray-900 bg-opacity-50 z-20 lg:hidden ${
            sidebarOpen ? 'block' : 'hidden'
          }`}
          onClick={toggleSidebar}
          aria-hidden="true"
        />

        {/* Sidebar */}
        <div
          className={`fixed inset-y-0 left-0 z-30 w-64 transform ${
            sidebarOpen ? 'translate-x-0' : '-translate-x-64'
          } lg:translate-x-0 transition-transform duration-200 ease-in-out`}
        >
          <Sidebar />
        </div>

        {/* Main content */}
        <div className="flex-1 flex flex-col overflow-hidden">
          {/* Header */}
          <Header />

          {/* Main content area */}
          <main className="flex-1 overflow-y-auto focus:outline-none bg-gray-50 dark:bg-gray-900 p-4 lg:p-6">
            <div className="max-w-7xl mx-auto">
              <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm p-4 lg:p-6">
                {children}
              </div>
            </div>
          </main>
        </div>
      </div>

      {/* Notifications */}
      <Notifications />
    </div>
  );
};

export default MainLayout;
