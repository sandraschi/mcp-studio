import React, { useState, useCallback, useEffect } from 'react';
import type { Server } from '../../types';
import { ToolExplorer } from './ToolExplorer';
import { ServerManager } from '../servers/ServerManager';
import { useToast } from '../ui/Toast/ToastProvider';
import { useServers } from '../../contexts/ServerContext';

type TabType = 'explorer' | 'servers';

// Simple icon components with className support
const ServerIcon = ({ className = '' }: { className?: string }) => (
  <span className={className}>🖥️</span>
);

const CogIcon = ({ className = '' }: { className?: string }) => (
  <span className={className}>⚙️</span>
);

const BoltIcon = ({ className = '' }: { className?: string }) => (
  <span className={className}>⚡</span>
);

interface ToolExecutionResult {
  success: boolean;
  data?: unknown;
  error?: string;
  executionTime: number;
  timestamp: string;
}

interface ToolExplorerProps {
  server: Server | null;
  tools: any[]; // Replace 'any' with the actual Tool type if available
  loading?: boolean;
  error?: string | null;
  onExecuteTool: (toolId: string, parameters: Record<string, unknown>) => Promise<unknown>;
  className?: string;
}

export const ToolConsole: React.FC = () => {
  const { 
    servers, 
    loading: serversLoading, 
    error: serversError, 
    refreshServers, 
    executeTool 
  } = useServers();
  
  const { toast } = useToast();
  const [activeTab, setActiveTab] = useState<TabType>('explorer');
  const [selectedServerId, setSelectedServerId] = useState<string | null>(null);
  const [isExecuting, setIsExecuting] = useState(false);
  const [executionResult, setExecutionResult] = useState<ToolExecutionResult | null>(null);

  // Set the first server as selected when servers are loaded
  useEffect(() => {
    if (servers.length > 0 && !selectedServerId) {
      setSelectedServerId(servers[0].id);
    }
  }, [servers, selectedServerId]);

  const handleServerSelect = useCallback((serverId: string) => {
    setSelectedServerId(serverId);
    setExecutionResult(null); // Clear previous execution result when changing servers
  }, []);

  const handleRefresh = useCallback(async () => {
    try {
      await refreshServers();
      toast({
        title: 'Success',
        description: 'Server list refreshed',
        variant: 'success'
      });
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to refresh servers',
        variant: 'destructive'
      });
    }
  }, [refreshServers, toast]);

  const handleExecuteTool = useCallback(async (toolId: string, parameters: Record<string, unknown>) => {
    if (!selectedServerId) {
      toast({
        title: 'Error',
        description: 'No server selected',
        variant: 'destructive'
      });
      return;
    }

    setIsExecuting(true);
    setExecutionResult(null);

    try {
      const startTime = Date.now();
      const result = await executeTool(selectedServerId, toolId, parameters);
      const executionTime = Date.now() - startTime;
      
      const executionResult: ToolExecutionResult = {
        success: true,
        data: result,
        executionTime,
        timestamp: new Date().toISOString()
      };
      
      setExecutionResult(executionResult);
      return executionResult;
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to execute tool';
      const errorResult: ToolExecutionResult = {
        success: false,
        error: errorMessage,
        executionTime: 0,
        timestamp: new Date().toISOString()
      };
      
      setExecutionResult(errorResult);
      throw error;
    } finally {
      setIsExecuting(false);
    }
  }, [selectedServerId, executeTool, toast]);

  const selectedServer = selectedServerId 
    ? servers.find(server => server.id === selectedServerId) || null 
    : null;

  return (
    <div className="h-full flex flex-col bg-gray-50 dark:bg-gray-900">
      <div className="border-b border-gray-200 dark:border-gray-700">
        <div className="flex items-center justify-between px-4">
          <div className="flex space-x-2">
            <button
              type="button"
              className={`px-4 py-2 text-sm font-medium rounded-t-md ${
                activeTab === 'explorer'
                  ? 'bg-white text-blue-600 dark:bg-gray-800 dark:text-blue-400'
                  : 'text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200'
              }`}
              onClick={() => setActiveTab('explorer')}
            >
              <div className="flex items-center">
                <BoltIcon className="w-4 h-4 mr-2" />
                Tool Explorer
              </div>
            </button>
            <button
              type="button"
              className={`px-4 py-2 text-sm font-medium rounded-t-md ${
                activeTab === 'servers'
                  ? 'bg-white text-blue-600 dark:bg-gray-800 dark:text-blue-400'
                  : 'text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200'
              }`}
              onClick={() => setActiveTab('servers')}
            >
              <div className="flex items-center">
                <ServerIcon className="w-4 h-4 mr-2" />
                Server Manager
              </div>
            </button>
          </div>
          
          <div className="flex items-center space-x-2">
            <select
              value={selectedServerId || ''}
              onChange={(e) => handleServerSelect(e.target.value)}
              className="block w-48 px-3 py-2 text-sm border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:border-gray-600 dark:text-white"
              disabled={serversLoading || isExecuting}
            >
              <option value="">Select a server</option>
              {servers.map((server) => (
                <option key={server.id} value={server.id}>
                  {server.name}
                </option>
              ))}
            </select>
            
            <button
              type="button"
              onClick={handleRefresh}
              disabled={serversLoading || isExecuting}
              className="p-2 text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200 disabled:opacity-50"
              title="Refresh servers"
            >
              <CogIcon className={`w-5 h-5 ${serversLoading ? 'animate-spin' : ''}`} />
            </button>
          </div>
        </div>
      </div>

      <div className="flex-1 overflow-auto">
        {activeTab === 'explorer' ? (
          <div className="p-4">
            <ToolExplorer 
              server={selectedServer}
              tools={[]} // TODO: Pass actual tools from context or props
              loading={serversLoading || isExecuting}
              error={serversError}
              onExecuteTool={handleExecuteTool}
              className="flex-1"
            />
          </div>
        ) : (
          <div className="p-4">
            <ServerManager />
          </div>
        )}
      </div>
    </div>
  );
};
