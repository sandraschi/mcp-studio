import React from 'react';
import { Server } from '../../types';
import { ServerCard } from './ServerCard';
import { Button } from '../common/Button';
import { PlusIcon } from '../common/Icons';

interface ServerListProps {
  servers: Server[];
  onAddServer: () => void;
  onEditServer: (server: Server) => void;
  onDeleteServer: (id: string) => void;
  onSelectServer: (server: Server) => void;
  selectedServerId?: string | null;
  loading?: boolean;
  error?: string | null;
}

export const ServerList: React.FC<ServerListProps> = ({
  servers,
  onAddServer,
  onEditServer,
  onDeleteServer,
  onSelectServer,
  selectedServerId,
  loading = false,
  error = null,
}) => {
  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-blue-500"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 border-l-4 border-red-400 p-4">
        <div className="flex">
          <div className="flex-shrink-0">
            <svg
              className="h-5 w-5 text-red-400"
              xmlns="http://www.w3.org/2000/svg"
              viewBox="0 0 20 20"
              fill="currentColor"
            >
              <path
                fillRule="evenodd"
                d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z"
                clipRule="evenodd"
              />
            </svg>
          </div>
          <div className="ml-3">
            <p className="text-sm text-red-700">{error}</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex justify-between items-center">
        <h2 className="text-lg font-medium text-gray-900 dark:text-white">MCP Servers</h2>
        <Button
          variant="primary"
          size="sm"
          onClick={onAddServer}
          leftIcon={<PlusIcon className="h-4 w-4" />}
        >
          Add Server
        </Button>
      </div>

      {servers.length === 0 ? (
        <div className="text-center py-12 bg-white dark:bg-gray-800 rounded-lg shadow">
          <svg
            className="mx-auto h-12 w-12 text-gray-400"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={1}
              d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10"
            />
          </svg>
          <h3 className="mt-2 text-sm font-medium text-gray-900 dark:text-white">No servers</h3>
          <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
            Get started by adding a new MCP server.
          </p>
          <div className="mt-6">
            <Button
              variant="primary"
              onClick={onAddServer}
              leftIcon={<PlusIcon className="h-4 w-4" />}
            >
              Add Server
            </Button>
          </div>
        </div>
      ) : (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {servers.map((server) => (
            <ServerCard
              key={server.id}
              server={server}
              isSelected={server.id === selectedServerId}
              onSelect={() => onSelectServer(server)}
              onEdit={() => onEditServer(server)}
              onDelete={() => onDeleteServer(server.id)}
            />
          ))}
        </div>
      )}
    </div>
  );
};
