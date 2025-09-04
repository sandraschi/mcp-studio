import React, { useState, useEffect } from 'react';
import { useApp } from '../../contexts/AppContext';
import { XMarkIcon, CheckCircleIcon, ExclamationCircleIcon, InformationCircleIcon, ExclamationTriangleIcon } from './Icons';

const Notifications: React.FC = () => {
  const { state, removeNotification, markNotificationRead } = useApp();
  const [expanded, setExpanded] = useState<string | null>(null);
  const { notifications } = state;

  // Auto-close notifications after 5 seconds
  useEffect(() => {
    const timer = setTimeout(() => {
      notifications
        .filter(n => !n.read)
        .slice(0, -3) // Keep the 3 most recent notifications
        .forEach(n => markNotificationRead(n.id));
    }, 5000);

    return () => clearTimeout(timer);
  }, [notifications, markNotificationRead]);

  if (notifications.length === 0) return null;

  const getIcon = (type: string) => {
    const iconClass = 'h-5 w-5';
    switch (type) {
      case 'success':
        return <CheckCircleIcon className={`${iconClass} text-green-500`} />;
      case 'error':
        return <ExclamationCircleIcon className={`${iconClass} text-red-500`} />;
      case 'warning':
        return <ExclamationTriangleIcon className={`${iconClass} text-yellow-500`} />;
      default:
        return <InformationCircleIcon className={`${iconClass} text-blue-500`} />;
    }
  };

  return (
    <div className="fixed bottom-0 right-0 z-50 w-full max-w-sm p-4 space-y-2">
      {notifications.map((notification) => (
        <div
          key={notification.id}
          className={`relative p-4 pr-10 rounded-lg shadow-lg ${
            notification.type === 'success'
              ? 'bg-green-50 dark:bg-green-900/30 border border-green-200 dark:border-green-800'
              : notification.type === 'error'
              ? 'bg-red-50 dark:bg-red-900/30 border border-red-200 dark:border-red-800'
              : notification.type === 'warning'
              ? 'bg-yellow-50 dark:bg-yellow-900/30 border border-yellow-200 dark:border-yellow-800'
              : 'bg-blue-50 dark:bg-blue-900/30 border border-blue-200 dark:border-blue-800'
          } ${notification.read ? 'opacity-80' : 'opacity-100'}`}
          onClick={() => setExpanded(expanded === notification.id ? null : notification.id)}
        >
          <div className="flex items-start">
            <div className="flex-shrink-0 pt-0.5">
              {getIcon(notification.type)}
            </div>
            <div className="ml-3 w-0 flex-1">
              <p className="text-sm font-medium text-gray-900 dark:text-white">
                {notification.title}
              </p>
              <p 
                className={`mt-1 text-sm ${
                  notification.type === 'success'
                    ? 'text-green-700 dark:text-green-300'
                    : notification.type === 'error'
                    ? 'text-red-700 dark:text-red-300'
                    : notification.type === 'warning'
                    ? 'text-yellow-700 dark:text-yellow-300'
                    : 'text-blue-700 dark:text-blue-300'
                } ${expanded === notification.id ? 'whitespace-pre-wrap' : 'truncate'}`}
              >
                {notification.message}
              </p>
              {notification.action && (
                <div className="mt-2">
                  <button
                    type="button"
                    className={`inline-flex items-center text-sm font-medium ${
                      notification.type === 'success'
                        ? 'text-green-700 hover:text-green-900 dark:text-green-400 dark:hover:text-green-300'
                        : notification.type === 'error'
                        ? 'text-red-700 hover:text-red-900 dark:text-red-400 dark:hover:text-red-300'
                        : notification.type === 'warning'
                        ? 'text-yellow-700 hover:text-yellow-900 dark:text-yellow-400 dark:hover:text-yellow-300'
                        : 'text-blue-700 hover:text-blue-900 dark:text-blue-400 dark:hover:text-blue-300'
                    }`}
                    onClick={(e) => {
                      e.stopPropagation();
                      notification.action?.onClick();
                      markNotificationRead(notification.id);
                    }}
                  >
                    {notification.action.label}
                  </button>
                </div>
              )}
            </div>
            <div className="ml-4 flex-shrink-0 flex">
              <button
                className="bg-white dark:bg-gray-800 rounded-md inline-flex text-gray-400 hover:text-gray-500 dark:hover:text-gray-300 focus:outline-none"
                onClick={(e) => {
                  e.stopPropagation();
                  removeNotification(notification.id);
                }}
              >
                <span className="sr-only">Close</span>
                <XMarkIcon className="h-5 w-5" />
              </button>
            </div>
          </div>
        </div>
      ))}
    </div>
  );
};

export default Notifications;
