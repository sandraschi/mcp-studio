import React, { useState, useEffect } from 'react';
import { GlobeAltIcon, CodeBracketIcon, BookOpenIcon, InformationCircleIcon } from '@heroicons/react/24/outline';
import ClientInfoModal from '../components/ClientInfoModal';

interface Client {
  id: string;
  name: string;
  short_description: string;
  homepage?: string;
  github?: string;
  documentation?: string;
  platform: string;
  client_type: string;
  status: string;
  features: string[];
}

export const Clients: React.FC = () => {
  const [clients, setClients] = useState<Client[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedClient, setSelectedClient] = useState<string | null>(null);
  const [filterType, setFilterType] = useState<string>('all');

  useEffect(() => {
    fetchClients();
  }, []);

  const fetchClients = async () => {
    try {
      setLoading(true);
      const response = await fetch('/api/v1/clients');
      const data = await response.json();
      setClients(data.clients || []);
    } catch (error) {
      console.error('Error fetching clients:', error);
    } finally {
      setLoading(false);
    }
  };

  const filteredClients = filterType === 'all' 
    ? clients 
    : clients.filter(c => c.client_type === filterType);

  const clientTypes = Array.from(new Set(clients.map(c => c.client_type)));

  const getClientTypeIcon = (type: string) => {
    switch (type) {
      case 'Desktop':
        return '🖥️';
      case 'IDE':
        return '💻';
      case 'Extension':
        return '🔌';
      default:
        return '📦';
    }
  };

  const getStatusBadge = (status: string) => {
    const colors = {
      Active: 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200',
      Beta: 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200',
      Deprecated: 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200',
    };
    return colors[status as keyof typeof colors] || colors.Active;
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-blue-500"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="md:flex md:items-center md:justify-between">
        <div className="min-w-0 flex-1">
          <h2 className="text-2xl font-bold leading-7 text-gray-900 dark:text-white sm:truncate sm:text-3xl sm:tracking-tight">
            MCP Client Zoo
          </h2>
          <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
            All supported MCP clients with links to documentation and resources
          </p>
        </div>
      </div>

      {/* Filter */}
      <div className="flex flex-wrap gap-2">
        <button
          onClick={() => setFilterType('all')}
          className={`px-3 py-1 text-sm rounded-full ${
            filterType === 'all'
              ? 'bg-blue-600 text-white'
              : 'bg-gray-200 dark:bg-gray-700 text-gray-800 dark:text-gray-200 hover:bg-gray-300 dark:hover:bg-gray-600'
          }`}
        >
          All ({clients.length})
        </button>
        {clientTypes.map(type => (
          <button
            key={type}
            onClick={() => setFilterType(type)}
            className={`px-3 py-1 text-sm rounded-full ${
              filterType === type
                ? 'bg-blue-600 text-white'
                : 'bg-gray-200 dark:bg-gray-700 text-gray-800 dark:text-gray-200 hover:bg-gray-300 dark:hover:bg-gray-600'
            }`}
          >
            {getClientTypeIcon(type)} {type}s ({clients.filter(c => c.client_type === type).length})
          </button>
        ))}
      </div>

      {/* Client Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {filteredClients.map(client => (
          <div
            key={client.id}
            className="bg-white dark:bg-gray-800 rounded-lg shadow-lg overflow-hidden hover:shadow-xl transition-shadow duration-300"
          >
            <div className="p-6">
              {/* Title & Status */}
              <div className="flex items-start justify-between mb-3">
                <div className="flex items-center">
                  <span className="text-2xl mr-2">{getClientTypeIcon(client.client_type)}</span>
                  <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
                    {client.name}
                  </h3>
                </div>
                <span className={`px-2 py-1 text-xs font-medium rounded ${getStatusBadge(client.status)}`}>
                  {client.status}
                </span>
              </div>

              {/* Description */}
              <p className="text-sm text-gray-600 dark:text-gray-400 mb-4 line-clamp-2">
                {client.short_description}
              </p>

              {/* Platform & Type */}
              <div className="flex items-center text-xs text-gray-500 dark:text-gray-400 mb-4">
                <span>{client.platform}</span>
                <span className="mx-2">•</span>
                <span>{client.client_type}</span>
              </div>

              {/* Features */}
              {client.features && client.features.length > 0 && (
                <div className="mb-4">
                  <div className="flex flex-wrap gap-1">
                    {client.features.slice(0, 3).map((feature, idx) => (
                      <span
                        key={idx}
                        className="inline-block px-2 py-1 text-xs bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded"
                      >
                        {feature}
                      </span>
                    ))}
                    {client.features.length > 3 && (
                      <span className="inline-block px-2 py-1 text-xs text-gray-500 dark:text-gray-400">
                        +{client.features.length - 3} more
                      </span>
                    )}
                  </div>
                </div>
              )}

              {/* Links */}
              <div className="flex flex-wrap gap-2">
                {client.homepage && (
                  <a
                    href={client.homepage}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-flex items-center text-xs text-blue-600 hover:text-blue-700 dark:text-blue-400"
                  >
                    <GlobeAltIcon className="h-4 w-4 mr-1" />
                    Website
                  </a>
                )}
                {client.github && (
                  <a
                    href={client.github}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-flex items-center text-xs text-blue-600 hover:text-blue-700 dark:text-blue-400"
                  >
                    <CodeBracketIcon className="h-4 w-4 mr-1" />
                    GitHub
                  </a>
                )}
                {client.documentation && (
                  <a
                    href={client.documentation}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-flex items-center text-xs text-blue-600 hover:text-blue-700 dark:text-blue-400"
                  >
                    <BookOpenIcon className="h-4 w-4 mr-1" />
                    Docs
                  </a>
                )}
                <button
                  onClick={() => setSelectedClient(client.id)}
                  className="inline-flex items-center text-xs text-gray-600 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-300"
                >
                  <InformationCircleIcon className="h-4 w-4 mr-1" />
                  Details
                </button>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Info Banner */}
      <div className="rounded-lg bg-blue-50 dark:bg-blue-900/30 p-6">
        <div className="flex">
          <div className="flex-shrink-0">
            <InformationCircleIcon className="h-6 w-6 text-blue-400" />
          </div>
          <div className="ml-3">
            <h3 className="text-sm font-medium text-blue-800 dark:text-blue-200">
              Universal MCP Support
            </h3>
            <div className="mt-2 text-sm text-blue-700 dark:text-blue-300">
              <p>
                MCP Studio automatically discovers and connects to MCP servers from <strong>all {clients.length} supported clients</strong>.
                Configure your MCP servers in any of these clients, and they'll appear in MCP Studio's unified dashboard!
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Client Info Modal */}
      <ClientInfoModal
        isOpen={selectedClient !== null}
        onClose={() => setSelectedClient(null)}
        clientId={selectedClient || undefined}
      />
    </div>
  );
};

export default Clients;

