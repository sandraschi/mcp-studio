import React, { useState, useEffect } from 'react';
import { Modal } from './ui/Modal';
import { XMarkIcon, GlobeAltIcon, CodeBracketIcon, BookOpenIcon } from '@heroicons/react/24/outline';

interface ClientInfo {
  id: string;
  name: string;
  short_description: string;
  full_description: string;
  homepage?: string;
  github?: string;
  documentation?: string;
  platform: string;
  client_type: string;
  status: string;
  features: string[];
}

interface ClientInfoModalProps {
  isOpen: boolean;
  onClose: () => void;
  clientId?: string;
}

export const ClientInfoModal: React.FC<ClientInfoModalProps> = ({ isOpen, onClose, clientId }) => {
  const [client, setClient] = useState<ClientInfo | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (isOpen && clientId) {
      fetchClientInfo();
    }
  }, [isOpen, clientId]);

  const fetchClientInfo = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const response = await fetch(`/api/v1/clients/${clientId}`);
      if (!response.ok) {
        throw new Error('Failed to fetch client info');
      }
      
      const data = await response.json();
      setClient(data);
    } catch (err) {
      console.error('Error fetching client info:', err);
      setError('Failed to load client information');
    } finally {
      setLoading(false);
    }
  };

  const getStatusBadgeColor = (status: string) => {
    switch (status) {
      case 'Active':
        return 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200';
      case 'Beta':
        return 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200';
      case 'Deprecated':
        return 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200';
      default:
        return 'bg-gray-100 text-gray-800 dark:bg-gray-900 dark:text-gray-200';
    }
  };

  const getTypeBadgeColor = (type: string) => {
    switch (type) {
      case 'Desktop':
        return 'bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-200';
      case 'IDE':
        return 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200';
      case 'Extension':
        return 'bg-orange-100 text-orange-800 dark:bg-orange-900 dark:text-orange-200';
      default:
        return 'bg-gray-100 text-gray-800 dark:bg-gray-900 dark:text-gray-200';
    }
  };

  return (
    <Modal isOpen={isOpen} onClose={onClose} size="lg">
      <div className="px-6 py-4">
        {loading ? (
          <div className="flex items-center justify-center py-12">
            <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-blue-500"></div>
          </div>
        ) : error ? (
          <div className="text-center py-12">
            <XMarkIcon className="h-12 w-12 text-red-500 mx-auto mb-4" />
            <p className="text-gray-600 dark:text-gray-400">{error}</p>
          </div>
        ) : client ? (
          <>
            {/* Header */}
            <div className="border-b border-gray-200 dark:border-gray-700 pb-4 mb-4">
              <div className="flex items-start justify-between">
                <div>
                  <h2 className="text-2xl font-bold text-gray-900 dark:text-white">
                    {client.name}
                  </h2>
                  <p className="mt-1 text-sm text-gray-600 dark:text-gray-400">
                    {client.short_description}
                  </p>
                </div>
                <button
                  onClick={onClose}
                  className="text-gray-400 hover:text-gray-500 dark:hover:text-gray-300"
                >
                  <XMarkIcon className="h-6 w-6" />
                </button>
              </div>
              
              {/* Badges */}
              <div className="flex flex-wrap gap-2 mt-3">
                <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getStatusBadgeColor(client.status)}`}>
                  {client.status}
                </span>
                <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getTypeBadgeColor(client.client_type)}`}>
                  {client.client_type}
                </span>
                <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-200">
                  {client.platform}
                </span>
              </div>
            </div>

            {/* Description */}
            <div className="mb-6">
              <p className="text-gray-700 dark:text-gray-300 leading-relaxed">
                {client.full_description}
              </p>
            </div>

            {/* Links */}
            <div className="mb-6 space-y-2">
              {client.homepage && (
                <a
                  href={client.homepage}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="flex items-center text-blue-600 hover:text-blue-700 dark:text-blue-400 dark:hover:text-blue-300"
                >
                  <GlobeAltIcon className="h-5 w-5 mr-2" />
                  <span className="text-sm font-medium">Visit Homepage</span>
                  <svg className="h-4 w-4 ml-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                  </svg>
                </a>
              )}
              
              {client.github && (
                <a
                  href={client.github}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="flex items-center text-blue-600 hover:text-blue-700 dark:text-blue-400 dark:hover:text-blue-300"
                >
                  <CodeBracketIcon className="h-5 w-5 mr-2" />
                  <span className="text-sm font-medium">View on GitHub</span>
                  <svg className="h-4 w-4 ml-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                  </svg>
                </a>
              )}
              
              {client.documentation && (
                <a
                  href={client.documentation}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="flex items-center text-blue-600 hover:text-blue-700 dark:text-blue-400 dark:hover:text-blue-300"
                >
                  <BookOpenIcon className="h-5 w-5 mr-2" />
                  <span className="text-sm font-medium">Read Documentation</span>
                  <svg className="h-4 w-4 ml-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                  </svg>
                </a>
              )}
            </div>

            {/* Features */}
            {client.features && client.features.length > 0 && (
              <div>
                <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-3">
                  Key Features
                </h3>
                <ul className="space-y-2">
                  {client.features.map((feature, index) => (
                    <li key={index} className="flex items-start">
                      <svg
                        className="h-5 w-5 text-green-500 mr-2 mt-0.5 flex-shrink-0"
                        fill="none"
                        stroke="currentColor"
                        viewBox="0 0 24 24"
                      >
                        <path
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          strokeWidth={2}
                          d="M5 13l4 4L19 7"
                        />
                      </svg>
                      <span className="text-sm text-gray-700 dark:text-gray-300">
                        {feature}
                      </span>
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </>
        ) : (
          <div className="text-center py-12">
            <p className="text-gray-600 dark:text-gray-400">No client selected</p>
          </div>
        )}
      </div>
    </Modal>
  );
};

export default ClientInfoModal;

