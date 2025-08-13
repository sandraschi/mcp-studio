import React, { useState, useEffect } from 'react';
import { Server, Tool } from '../types';
import { ServerList } from '../components/server/ServerList';
import { ToolPanel } from '../components/tool/ToolPanel';
import { apiService } from '../services/api';

export const Dashboard: React.FC = () => {
  const [selectedServer, setSelectedServer] = useState<Server | null>(null);
  const [serverTools, setServerTools] = useState<Tool[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Load tools when a server is selected
  useEffect(() => {
    const loadTools = async () => {
      if (!selectedServer) {
        setServerTools([]);
        return;
      }

      try {
        setLoading(true);
        setError(null);
        const tools = await apiService.getTools(selectedServer.id);
        setServerTools(tools);
      } catch (err) {
        console.error('Failed to load tools:', err);
        setError('Failed to load tools. Please try again.');
        setServerTools([]);
      } finally {
        setLoading(false);
      }
    };

    loadTools();
  }, [selectedServer]);

  const handleServerSelect = (server: Server) => {
    setSelectedServer(server);
  };

  return (
    <div className="min-h-screen bg-gray-100">
      {/* Header */}
      <header className="bg-white shadow">
        <div className="max-w-7xl mx-auto px-4 py-4 sm:px-6 lg:px-8">
          <h1 className="text-2xl font-bold text-gray-900">MCP Studio</h1>
        </div>
      </header>

      {/* Main content */}
      <main className="max-w-7xl mx-auto px-4 py-6 sm:px-6 lg:px-8">
        <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
          {/* Server list */}
          <div className="lg:col-span-1">
            <div className="bg-white rounded-lg shadow overflow-hidden">
              <ServerList 
                onSelectServer={handleServerSelect} 
                selectedServerId={selectedServer?.id}
              />
            </div>
          </div>

          {/* Tool panel */}
          <div className="lg:col-span-3">
            {selectedServer ? (
              <>
                {error && (
                  <div className="mb-4 p-4 bg-red-50 border-l-4 border-red-400">
                    <div className="flex">
                      <div className="flex-shrink-0">
                        <svg className="h-5 w-5 text-red-400" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
                          <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                        </svg>
                      </div>
                      <div className="ml-3">
                        <p className="text-sm text-red-700">{error}</p>
                      </div>
                    </div>
                  </div>
                )}

                <div className="bg-white rounded-lg shadow overflow-hidden mb-6">
                  <div className="px-4 py-5 border-b border-gray-200 sm:px-6">
                    <h3 className="text-lg leading-6 font-medium text-gray-900">
                      {selectedServer.name}
                    </h3>
                    <p className="mt-1 max-w-2xl text-sm text-gray-500">
                      {selectedServer.type || 'MCP Server'}
                    </p>
                  </div>
                  <div className="px-4 py-5 sm:p-6">
                    <div className="grid grid-cols-1 gap-5 sm:grid-cols-2">
                      <div>
                        <dt className="text-sm font-medium text-gray-500 truncate">Status</dt>
                        <dd className="mt-1 flex items-center">
                          <span className={`h-3 w-3 rounded-full ${
                            selectedServer.status === 'ONLINE' ? 'bg-green-500' : 
                            selectedServer.status === 'OFFLINE' ? 'bg-gray-400' : 
                            selectedServer.status === 'STARTING' || selectedServer.status === 'STOPPING' ? 'bg-yellow-500' : 'bg-red-500'
                          } mr-2`}></span>
                          <span className="capitalize">
                            {selectedServer.status.toLowerCase()}
                          </span>
                        </dd>
                      </div>
                      <div>
                        <dt className="text-sm font-medium text-gray-500 truncate">Tools Available</dt>
                        <dd className="mt-1 text-gray-900">
                          {loading ? 'Loading...' : `${serverTools.length} tools`}
                        </dd>
                      </div>
                      {selectedServer.lastSeen && (
                        <div>
                          <dt className="text-sm font-medium text-gray-500 truncate">Last Seen</dt>
                          <dd className="mt-1 text-gray-900">
                            {new Date(selectedServer.lastSeen).toLocaleString()}
                          </dd>
                        </div>
                      )}
                    </div>
                  </div>
                </div>

                <ToolPanel 
                  serverId={selectedServer.id}
                  tools={serverTools}
                />
              </>
            ) : (
              <div className="bg-white rounded-lg shadow overflow-hidden p-8 text-center">
                <svg
                  className="mx-auto h-12 w-12 text-gray-400"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                  aria-hidden="true"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"
                  />
                </svg>
                <h3 className="mt-2 text-sm font-medium text-gray-900">No server selected</h3>
                <p className="mt-1 text-sm text-gray-500">
                  Select a server from the list to view and execute its tools.
                </p>
              </div>
            )}
          </div>
        </div>
      </main>
    </div>
  );
};
