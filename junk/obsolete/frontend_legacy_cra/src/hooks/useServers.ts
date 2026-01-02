import { useState, useEffect, useCallback } from 'react';
import { Server } from '../types';
import { api } from '../services/api';
import { useApp } from '../contexts/AppContext';

export const useServers = () => {
  const [servers, setServers] = useState<Server[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const { addNotification } = useApp();

  const fetchServers = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const { data, error } = await api.getServers();
      if (error) throw new Error(error);
      if (data) setServers(data);
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to fetch servers';
      setError(message);
      addNotification({
        type: 'error',
        title: 'Error',
        message,
      });
    } finally {
      setLoading(false);
    }
  }, [addNotification]);

  const addServer = async (serverData: Omit<Server, 'id' | 'status'>) => {
    try {
      const { data, error } = await api.createServer(serverData);
      if (error) throw new Error(error);
      if (data) {
        setServers(prev => [...prev, data]);
        addNotification({
          type: 'success',
          title: 'Success',
          message: 'Server added successfully',
        });
        return data;
      }
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to add server';
      addNotification({
        type: 'error',
        title: 'Error',
        message,
      });
      throw err;
    }
  };

  const updateServer = async (id: string, updates: Partial<Server>) => {
    try {
      const { data, error } = await api.updateServer(id, updates);
      if (error) throw new Error(error);
      if (data) {
        setServers(prev => prev.map(s => s.id === id ? { ...s, ...data } : s));
        addNotification({
          type: 'success',
          title: 'Success',
          message: 'Server updated successfully',
        });
        return data;
      }
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to update server';
      addNotification({
        type: 'error',
        title: 'Error',
        message,
      });
      throw err;
    }
  };

  const deleteServer = async (id: string) => {
    try {
      const { error } = await api.deleteServer(id);
      if (error) throw new Error(error);
      setServers(prev => prev.filter(s => s.id !== id));
      addNotification({
        type: 'success',
        title: 'Success',
        message: 'Server deleted successfully',
      });
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to delete server';
      addNotification({
        type: 'error',
        title: 'Error',
        message,
      });
      throw err;
    }
  };

  useEffect(() => {
    fetchServers();
  }, [fetchServers]);

  return {
    servers,
    loading,
    error,
    addServer,
    updateServer,
    deleteServer,
    refreshServers: fetchServers,
  };
};
