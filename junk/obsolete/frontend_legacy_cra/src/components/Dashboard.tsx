import React, { useState, useEffect } from 'react';
import { Server } from '../types';
import { ServerCard } from './ServerCard';
import { Button } from './ui/Button';
import { Input } from './ui/Input';
import { useApi } from '../hooks/useApi';
import { useWebSocket } from '../hooks/useWebSocket';

export const Dashboard: React.FC = () => {
  const [servers, setServers] = useState<Server[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState('');
  const { get, post } = useApi();
  
  // Fetch initial server list
  useEffect(() => {
    const fetchServers = async () => {
      try {
        setIsLoading(true);
        const data = await get<Server[]>('/api/mcp/servers');
        setServers(data);
        setError(null);
      } catch (err) {
        console.error('Failed to fetch servers:', err);
        setError('Failed to load servers. Please try again later.');
      } finally {
        setIsLoading(false);
      }
    };

    fetchServers();
  }, [get]);

  // Set up WebSocket for real-time updates
  useWebSocket('ws://localhost:8000/api/mcp/servers/ws', (data) => {
    if (data.type === 'update') {
      setServers(data.data);
    }
  });

  const handleStartServer = async (serverId: string) => {
    try {
      await post(`/api/mcp/servers/${serverId}/start`, {});
      // The WebSocket will update the UI when the server status changes
    } catch (err) {
      console.error('Failed to start server:', err);
      setError('Failed to start server. Please check the console for details.');
    }
  };

  const handleStopServer = async (serverId: string) => {
    try {
      await post(`/api/mcp/servers/${serverId}/stop`, {});
      // The WebSocket will update the UI when the server status changes
    } catch (err) {
      console.error('Failed to stop server:', err);
      setError('Failed to stop server. Please check the console for details.');
    }
  };

  const handleExecuteTool = (serverId: string, toolName: string) => {
    // TODO: Implement tool execution modal
    console.log(`Execute tool ${toolName} on server ${serverId}`);
  };

  const filteredServers = servers.filter(server => 
    server.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    server.id.toLowerCase().includes(searchTerm.toLowerCase()) ||
    server.source.toLowerCase().includes(searchTerm.toLowerCase())
  );

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-blue-500"></div>
      </div>
    );
  }

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="flex flex-col md:flex-row md:items-center md:justify-between mb-8">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">MCP Servers</h1>
          <p className="text-gray-600 dark:text-gray-400">
            Manage your MCP servers and tools in one place
          </p>
        </div>
        <div className="mt-4 md:mt-0">
          <Button 
            variant="primary"
            onClick={() => {
              // TODO: Implement add server dialog
              console.log('Add server clicked');
            }}
          >
            Add Server
          </Button>
        </div>
      </div>

      {error && (
        <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 text-red-700 dark:text-red-400 px-4 py-3 rounded mb-6">
          {error}
        </div>
      )}

      <div className="mb-6">
        <Input
          type="text"
          placeholder="Search servers..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          className="w-full md:w-96"
          leftIcon={
            <svg className="w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
            </svg>
          }
        />
      </div>

      {filteredServers.length === 0 ? (
        <div className="text-center py-12">
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
              d="M9.172 16.172a4 4 0 015.656 0M9 10h.01M15 10h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
            />
          </svg>
          <h3 className="mt-2 text-sm font-medium text-gray-900 dark:text-white">No servers found</h3>
          <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
            {searchTerm ? 'Try a different search term.' : 'Get started by adding a new server.'}
          </p>
          <div className="mt-6">
            <Button
              variant="primary"
              onClick={() => {
                // TODO: Implement add server dialog
                console.log('Add server clicked');
              }}
            >
              <svg className="-ml-1 mr-2 h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
              </svg>
              Add Server
            </Button>
          </div>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {filteredServers.map((server) => (
            <ServerCard
              key={server.id}
              server={server}
              onStart={handleStartServer}
              onStop={handleStopServer}
              onExecuteTool={handleExecuteTool}
            />
          ))}
        </div>
      )}
    </div>
  );
};
