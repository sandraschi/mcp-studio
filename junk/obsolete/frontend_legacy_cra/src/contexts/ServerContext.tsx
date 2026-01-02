import React, { createContext, useContext, useEffect, useState, useCallback } from 'react';
import { Server } from '../types';
import { useApi } from '../hooks/useApi';
import { useWebSocket } from '../hooks/useWebSocket';

type ServerContextType = {
  servers: Server[];
  loading: boolean;
  error: string | null;
  refreshServers: () => Promise<void>;
  startServer: (serverId: string) => Promise<void>;
  stopServer: (serverId: string) => Promise<void>;
  executeTool: (serverId: string, toolName: string, parameters: any) => Promise<any>;
  getServer: (serverId: string) => Server | undefined;
};

const ServerContext = createContext<ServerContextType | undefined>(undefined);

export const ServerProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [servers, setServers] = useState<Server[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const { get, post } = useApi();

  // Fetch servers from the API
  const fetchServers = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await get<Server[]>('/api/mcp/servers');
      setServers(data);
    } catch (err) {
      console.error('Failed to fetch servers:', err);
      setError('Failed to load servers. Please try again later.');
    } finally {
      setLoading(false);
    }
  }, [get]);

  // Set up WebSocket for real-time updates
  useWebSocket(
    `ws://${window.location.host}/api/mcp/servers/ws`,
    (data) => {
      if (data.type === 'update') {
        setServers(data.data);
      }
    },
    true, // Enable reconnection
    5000, // 5s reconnect interval
    10 // Max 10 reconnection attempts
  );

  // Initial fetch
  useEffect(() => {
    fetchServers();
  }, [fetchServers]);

  // Start a server
  const startServer = async (serverId: string) => {
    try {
      await post(`/api/mcp/servers/${serverId}/start`, {});
      // The WebSocket will update the UI when the server status changes
    } catch (err) {
      console.error('Failed to start server:', err);
      throw new Error('Failed to start server');
    }
  };

  // Stop a server
  const stopServer = async (serverId: string) => {
    try {
      await post(`/api/mcp/servers/${serverId}/stop`, {});
      // The WebSocket will update the UI when the server status changes
    } catch (err) {
      console.error('Failed to stop server:', err);
      throw new Error('Failed to stop server');
    }
  };

  // Execute a tool on a server
  const executeTool = async (serverId: string, toolName: string, parameters: any) => {
    try {
      const result = await post(`/api/mcp/servers/${serverId}/tools/${toolName}`, parameters);
      return result;
    } catch (err) {
      console.error('Failed to execute tool:', err);
      throw new Error('Failed to execute tool');
    }
  };

  // Get a server by ID
  const getServer = (serverId: string) => {
    return servers.find(server => server.id === serverId);
  };

  return (
    <ServerContext.Provider
      value={{
        servers,
        loading,
        error,
        refreshServers: fetchServers,
        startServer,
        stopServer,
        executeTool,
        getServer,
      }}
    >
      {children}
    </ServerContext.Provider>
  );
};

export const useServers = (): ServerContextType => {
  const context = useContext(ServerContext);
  if (context === undefined) {
    throw new Error('useServers must be used within a ServerProvider');
  }
  return context;
};
