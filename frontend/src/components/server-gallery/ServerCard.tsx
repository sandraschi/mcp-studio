import React from 'react';
import { Server } from '../../types';

interface ServerCardProps {
  server: Server;
  onClick: () => void;
}

const ServerCard: React.FC<ServerCardProps> = ({ server, onClick }) => {
  const getStatusColor = () => {
    switch (server.status) {
      case 'online':
        return 'bg-green-500';
      case 'warning':
        return 'bg-yellow-500';
      case 'error':
        return 'bg-red-500';
      default:
        return 'bg-gray-500';
    }
  };

  return (
    <div 
      className="bg-white dark:bg-gray-800 rounded-xl shadow-lg overflow-hidden hover:shadow-xl transition-shadow duration-300 cursor-pointer"
      onClick={onClick}
    >
      <div className="p-6">
        <div className="flex justify-between items-start">
          <h3 className="text-xl font-semibold text-gray-900 dark:text-white">
            {server.name}
          </h3>
          <span className={`inline-block w-3 h-3 rounded-full ${getStatusColor()}`}></span>
        </div>
        
        <p className="mt-2 text-gray-600 dark:text-gray-300">
          {server.description}
        </p>
        
        <div className="mt-4 flex items-center text-sm text-gray-500 dark:text-gray-400">
          <span className="flex items-center">
            <svg className="w-4 h-4 mr-1" fill="currentColor" viewBox="0 0 20 20">
              <path d="M13.586 3.586a2 2 0 112.828 2.828l-.793.793-2.828-2.828.793-.793zM11.379 5.793L3 14.172V17h2.828l8.38-8.379-2.83-2.828z" />
            </svg>
            {server.tools.length} tools
          </span>
          
          <span className="mx-2">•</span>
          
          <span className="flex items-center">
            <svg className="w-4 h-4 mr-1" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm1-12a1 1 0 10-2 0v4a1 1 0 00.293.707l2.828 2.829a1 1 0 101.415-1.415L11 9.586V6z" clipRule="evenodd" />
            </svg>
            {server.latency}ms
          </span>
        </div>
      </div>
      
      <div className="bg-gray-50 dark:bg-gray-700 px-6 py-3">
        <div className="flex justify-between items-center">
          <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
            {server.version}
          </span>
          <button 
            className="px-3 py-1 bg-blue-600 text-white text-sm font-medium rounded-md hover:bg-blue-700 transition-colors"
            onClick={(e) => {
              e.stopPropagation();
              // Handle quick test
            }}
          >
            Test
          </button>
        </div>
      </div>
    </div>
  );
};

export default ServerCard;
