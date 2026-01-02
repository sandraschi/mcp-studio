import React from 'react';
import { Server } from '../types';
import { Tooltip } from './ui/Tooltip';
import { Button } from './ui/Button';
import { StatusBadge } from './ui/StatusBadge';

interface ServerCardProps {
  server: Server;
  onStart: (id: string) => void;
  onStop: (id: string) => void;
  onExecuteTool: (serverId: string, toolName: string) => void;
}

export const ServerCard: React.FC<ServerCardProps> = ({
  server,
  onStart,
  onStop,
  onExecuteTool,
}) => {
  const isOnline = server.status === 'online';
  const isOffline = server.status === 'offline';
  const isError = server.status === 'error';

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md overflow-hidden border border-gray-200 dark:border-gray-700">
      <div className="p-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className={`w-3 h-3 rounded-full ${
              isOnline ? 'bg-green-500' : 
              isError ? 'bg-red-500' : 
              'bg-gray-400'
            }`}></div>
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
              {server.name}
            </h3>
            <StatusBadge status={server.status} />
          </div>
          <div className="flex space-x-2">
            {isOffline && (
              <Button 
                variant="primary" 
                size="sm"
                onClick={() => onStart(server.id)}
              >
                Start
              </Button>
            )}
            {isOnline && (
              <Button 
                variant="danger" 
                size="sm"
                onClick={() => onStop(server.id)}
              >
                Stop
              </Button>
            )}
          </div>
        </div>
        
        <div className="mt-3 text-sm text-gray-600 dark:text-gray-300">
          <div className="flex items-center">
            <span className="font-medium">Source:</span>
            <span className="ml-2 px-2 py-0.5 bg-gray-100 dark:bg-gray-700 rounded text-xs">
              {server.source}
            </span>
          </div>
          <div className="mt-1">
            <span className="font-medium">Command:</span>
            <code className="ml-2 px-2 py-0.5 bg-gray-100 dark:bg-gray-700 rounded text-xs">
              {server.command} {server.args?.join(' ')}
            </code>
          </div>
        </div>
        
        {server.tools && server.tools.length > 0 && (
          <div className="mt-4">
            <h4 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Available Tools ({server.tools.length})
            </h4>
            <div className="space-y-2 max-h-40 overflow-y-auto">
              {server.tools.map((tool) => (
                <div 
                  key={`${server.id}-${tool.name}`}
                  className="flex items-center justify-between p-2 bg-gray-50 dark:bg-gray-700 rounded hover:bg-gray-100 dark:hover:bg-gray-600 cursor-pointer"
                  onClick={() => onExecuteTool(server.id, tool.name)}
                >
                  <div>
                    <div className="font-medium text-sm text-gray-900 dark:text-white">
                      {tool.name}
                    </div>
                    {tool.description && (
                      <div className="text-xs text-gray-500 dark:text-gray-400 truncate">
                        {tool.description}
                      </div>
                    )}
                  </div>
                  <svg 
                    className="w-4 h-4 text-gray-400" 
                    fill="none" 
                    stroke="currentColor" 
                    viewBox="0 0 24 24"
                  >
                    <path 
                      strokeLinecap="round" 
                      strokeLinejoin="round" 
                      strokeWidth={2} 
                      d="M9 5l7 7-7 7" 
                    />
                  </svg>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
      
      {server.last_seen && (
        <div className="px-4 py-2 bg-gray-50 dark:bg-gray-700 text-xs text-gray-500 dark:text-gray-400">
          Last seen: {new Date(server.last_seen).toLocaleString()}
        </div>
      )}
    </div>
  );
};
