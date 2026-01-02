import React from 'react';
import { Server } from '../../types';
import { Button } from '../common/Button';
import { PencilIcon, TrashIcon, ServerIcon } from '../common/Icons';

interface ServerCardProps {
  server: Server;
  isSelected?: boolean;
  onSelect: () => void;
  onEdit: () => void;
  onDelete: () => void;
}

export const ServerCard: React.FC<ServerCardProps> = ({
  server,
  isSelected = false,
  onSelect,
  onEdit,
  onDelete,
}) => {
  const getStatusColor = () => {
    switch (server.status) {
      case 'online':
        return 'bg-green-500';
      case 'offline':
        return 'bg-red-500';
      case 'error':
        return 'bg-red-700';
      case 'starting':
      case 'stopping':
        return 'bg-yellow-500';
      case 'warning':
        return 'bg-yellow-300';
      default:
        return 'bg-gray-400';
    }
  };

  return (
    <div
      className={`relative rounded-lg border ${
        isSelected
          ? 'border-blue-500 ring-2 ring-blue-500 ring-opacity-50'
          : 'border-gray-200 dark:border-gray-700 hover:border-blue-300 dark:hover:border-blue-700'
      } bg-white dark:bg-gray-800 shadow-sm overflow-hidden transition-all duration-200`}
      onClick={onSelect}
    >
      <div className="p-4">
        <div className="flex items-start justify-between">
          <div className="flex-1 min-w-0">
            <div className="flex items-center">
              <ServerIcon className="h-5 w-5 text-gray-400 mr-2" />
              <h3 className="text-lg font-medium text-gray-900 dark:text-white truncate">
                {server.name}
              </h3>
            </div>
            <p className="mt-1 text-sm text-gray-500 dark:text-gray-400 truncate">
              {server.description || 'No description provided'}
            </p>
          </div>
          <div className="ml-4 flex items-center">
            <div className={`h-3 w-3 rounded-full ${getStatusColor()} mr-2`}></div>
            <span className="text-xs font-medium text-gray-500 dark:text-gray-400">
              {server.status?.toUpperCase()}
            </span>
          </div>
        </div>

        <div className="mt-4 flex flex-wrap gap-2">
          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200">
            {server.tools?.length || 0} tools
          </span>
          {server.latency !== undefined && (
            <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200">
              {server.latency}ms
            </span>
          )}
          {server.version && (
            <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-200">
              v{server.version}
            </span>
          )}
        </div>

        <div className="mt-4 flex justify-between items-center">
          <div className="flex space-x-2">
            <Button
              variant="secondary"
              size="xs"
              onClick={(e) => {
                e.stopPropagation();
                onEdit();
              }}
              leftIcon={<PencilIcon className="h-3 w-3" />}
            >
              Edit
            </Button>
            <Button
              variant="danger"
              size="xs"
              onClick={(e) => {
                e.stopPropagation();
                onDelete();
              }}
              leftIcon={<TrashIcon className="h-3 w-3" />}
            >
              Delete
            </Button>
          </div>
          <Button
            variant="primary"
            size="xs"
            onClick={(e) => {
              e.stopPropagation();
              onSelect();
            }}
          >
            Connect
          </Button>
        </div>
      </div>
    </div>
  );
};
