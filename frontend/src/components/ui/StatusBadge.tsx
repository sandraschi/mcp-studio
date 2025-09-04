import React from 'react';
import classNames from 'classnames';

export type Status = 'online' | 'offline' | 'error' | 'starting' | 'stopping' | 'warning' | 'unknown';

interface StatusBadgeProps {
  status: Status;
  className?: string;
}

export const StatusBadge: React.FC<StatusBadgeProps> = ({ status, className = '' }) => {
  const statusConfig = {
    online: {
      text: 'Online',
      bg: 'bg-green-100 dark:bg-green-900/30',
      textColor: 'text-green-800 dark:text-green-400',
      dot: 'bg-green-400',
    },
    offline: {
      text: 'Offline',
      bg: 'bg-gray-100 dark:bg-gray-800',
      textColor: 'text-gray-800 dark:text-gray-300',
      dot: 'bg-gray-400',
    },
    error: {
      text: 'Error',
      bg: 'bg-red-100 dark:bg-red-900/30',
      textColor: 'text-red-800 dark:text-red-400',
      dot: 'bg-red-400',
    },
    starting: {
      text: 'Starting',
      bg: 'bg-blue-100 dark:bg-blue-900/30',
      textColor: 'text-blue-800 dark:text-blue-400',
      dot: 'bg-blue-400',
    },
    stopping: {
      text: 'Stopping',
      bg: 'bg-yellow-100 dark:bg-yellow-900/30',
      textColor: 'text-yellow-800 dark:text-yellow-400',
      dot: 'bg-yellow-400',
    },
    unknown: {
      text: 'Unknown',
      bg: 'bg-gray-100 dark:bg-gray-800',
      textColor: 'text-gray-800 dark:text-gray-300',
      dot: 'bg-gray-400',
    },
    warning: {
      text: 'Warning',
      bg: 'bg-yellow-100 dark:bg-yellow-900/30',
      textColor: 'text-yellow-800 dark:text-yellow-400',
      dot: 'bg-yellow-400',
    },
  };

  const config = statusConfig[status] || statusConfig.unknown;

  return (
    <span
      className={classNames(
        'inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium',
        config.bg,
        config.textColor,
        className
      )}
    >
      <span className={`w-2 h-2 mr-1.5 rounded-full ${config.dot}`}></span>
      {config.text}
    </span>
  );
};
