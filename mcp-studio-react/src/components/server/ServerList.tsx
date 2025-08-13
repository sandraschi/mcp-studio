import React, { useEffect, useState } from 'react';
import { Server } from '../../types';
import { apiService } from '../../services/api';
import { webSocketService } from '../../services/websocket';

interface ServerListProps {
  onSelectServer: (server: Server) => void;
  selectedServerId?: string;
}

export const ServerList: React.FC<ServerListProps> = ({ onSelectServer, selectedServerId }) => {
  const [servers, setServers] = useState<Server[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const loadServers = async () => {
      try {
        setLoading(true);
        const serverList = await apiService.getServers();
        setServers(serverList);
        setError(null);
      } catch (err) {
        console.error('Failed to load servers:', err);
        setError('Failed to load servers. Please try again.');
      } finally {
        setLoading(false);
      }
    };

    loadServers();

    // Subscribe to server status updates
    const unsubscribe = webSocketService.subscribe((message) => {
      if (message.type === 'STATUS_UPDATE') {
        setServers(prevServers => 
          prevServers.map(server => 
            server.id === message.data.serverId 
              ? { ...server, status: message.data.status } 
             : server
          )
        );
      }
    });

    return () => {
      unsubscribe();
    };
  }, []);

  const handleServerAction = async (serverId: string, action: 'start' | 'stop') => {
    try {
      if (action === 'start') {
        await apiService.startServer(serverId);
      } else {
        await apiService.stopServer(serverId);
      }
    } catch (err) {
      console.error(`Failed to ${action} server:`, err);
      setError(`Failed to ${action} server. Please try again.`);
    }
  };

  const handleRefresh = async () => {
    try {
      setLoading(true);
      await apiService.discoverServers();
      const serverList = await apiService.getServers();
      setServers(serverList);
      setError(null);
    } catch (err) {
      console.error('Failed to refresh servers:', err);
      setError('Failed to refresh servers. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'ONLINE':
        return 'bg-green-500';
      case 'OFFLINE':
        return 'bg-gray-500';
      case 'STARTING':
      case 'STOPPING':
        return 'bg-yellow-500';
      case 'ERROR':
        return 'bg-red-500';
      default:
        return 'bg-gray-300';
    }
  };

  if (loading) {
    return (
      <div className="p-4">
        <div className="animate-pulse space-y-2">
          {[1, 2, 3].map((i) => (
            <div key={i} className="h-16 bg-gray-200 rounded-md"></div>
          ))}
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-4 text-red-600">
        <p>{error}</p>
        <button 
          onClick={handleRefresh}
          className="mt-2 px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600"
        >
          Retry
        </button>
      </div>
    );
  }

  if (servers.length === 0) {
    return (
      <div className="p-4 text-center text-gray-500">
        <p>No servers found</p>
        <button 
          onClick={handleRefresh}
          className="mt-2 px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600"
        >
          Discover Servers
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-2 p-2">
      <div className="flex justify-between items-center mb-2">
        <h2 className="text-lg font-semibold">MCP Servers</h2>
        <button
          onClick={handleRefresh}
          className="p-1 text-gray-500 hover:text-gray-700"
          title="Refresh servers"
        >
          <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
            <path fillRule="evenodd" d="M4 2a1 1 0 011 1v2.101a7.002 7.002 0 0111.601 2.566 1 1 0 11-1.885.666A5.002 5.002 0 005.999 7H9a1 1 0 010 2H4a1 1 0 01-1-1V3a1 1 0 011-1zm.008 9.057a1 1 0 011.276.61A5.002 5.002 0 0014.001 13H11a1 1 0 110-2h5a1 1 0 011 1v5a1 1 0 11-2 0v-2.101a7.002 7.002 0 01-11.601-2.566 1 1 0 01.61-1.276z" clipRule="evenodd" />
          </svg>
        </button>
      </div>
      
      <div className="space-y-2">
        {servers.map((server) => (
          <div 
            key={server.id}
            onClick={() => onSelectServer(server)}
            className={`p-3 border rounded-md cursor-pointer transition-colors ${
              selectedServerId === server.id 
                ? 'border-blue-500 bg-blue-50' 
                : 'border-gray-200 hover:border-gray-300 hover:bg-gray-50'
            }`}
          >
            <div className="flex justify-between items-start">
              <div>
                <h3 className="font-medium text-gray-900">{server.name}</h3>
                <p className="text-sm text-gray-500">{server.type || 'Unknown Type'}</p>
              </div>
              <div className="flex items-center space-x-2">
                <span className={`h-3 w-3 rounded-full ${getStatusColor(server.status)}`} title={server.status}></span>
                {server.status === 'OFFLINE' ? (
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      handleServerAction(server.id, 'start');
                    }}
                    className="text-xs px-2 py-1 bg-green-500 text-white rounded hover:bg-green-600"
                    disabled={loading}
                  >
                    Start
                  </button>
                ) : (
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      handleServerAction(server.id, 'stop');
                    }}
                    className="text-xs px-2 py-1 bg-red-500 text-white rounded hover:bg-red-600"
                    disabled={loading || server.status === 'STOPPING'}
                  >
                    Stop
                  </button>
                )}
              </div>
            </div>
            {server.tools && (
              <div className="mt-2 text-xs text-gray-500">
                {server.tools.length} tools available
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
};
