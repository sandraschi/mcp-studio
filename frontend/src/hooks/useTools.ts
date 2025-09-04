import { useState, useCallback } from 'react';
import { Tool, ToolExecutionResult } from '../types';
import { api } from '../services/api';
import { useApp } from '../contexts/AppContext';

interface UseToolsProps {
  serverId: string;
}

export const useTools = ({ serverId }: UseToolsProps) => {
  const [tools, setTools] = useState<Tool[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [executing, setExecuting] = useState<boolean>(false);
  const [executionResult, setExecutionResult] = useState<ToolExecutionResult | null>(null);
  const { addNotification } = useApp();

  const fetchTools = useCallback(async () => {
    if (!serverId) return;
    
    setLoading(true);
    setError(null);
    
    try {
      const { data, error } = await api.getTools(serverId);
      if (error) throw new Error(error);
      if (data) setTools(data);
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to fetch tools';
      setError(message);
      addNotification({
        type: 'error',
        title: 'Error',
        message,
      });
    } finally {
      setLoading(false);
    }
  }, [serverId, addNotification]);

  const getToolById = useCallback((toolId: string): Tool | undefined => {
    return tools.find(tool => tool.id === toolId);
  }, [tools]);

  const executeTool = useCallback(async (toolId: string, parameters: Record<string, any>) => {
    if (!serverId) return;
    
    setExecuting(true);
    setExecutionResult(null);
    
    try {
      const { data, error } = await api.executeTool(serverId, toolId, parameters);
      
      if (error) throw new Error(error);
      if (data) {
        setExecutionResult(data);
        return data;
      }
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to execute tool';
      addNotification({
        type: 'error',
        title: 'Execution Error',
        message,
      });
      throw err;
    } finally {
      setExecuting(false);
    }
  }, [serverId, addNotification]);

  return {
    tools,
    loading,
    error,
    executing,
    executionResult,
    fetchTools,
    getToolById,
    executeTool,
    clearExecutionResult: () => setExecutionResult(null),
  };
};
