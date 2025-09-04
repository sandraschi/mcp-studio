import React, { useState } from 'react';
import { Server } from '../../types';
import { useServers } from '../../hooks/useServers';
import { ServerList } from './ServerList';
import { ServerForm } from './ServerForm';
import { Modal } from '../common/Modal';
import { Button } from '../common/Button';
import { PlusIcon } from '../common/Icons';

export const ServerManager: React.FC = () => {
  const [isFormOpen, setIsFormOpen] = useState(false);
  const [editingServer, setEditingServer] = useState<Server | null>(null);
  const [deletingServer, setDeletingServer] = useState<Server | null>(null);
  
  const {
    servers,
    loading,
    error,
    addServer,
    updateServer,
    deleteServer,
    refreshServers,
  } = useServers();

  const handleAddServer = async (serverData: Omit<Server, 'id' | 'status'>) => {
    try {
      await addServer(serverData);
      setIsFormOpen(false);
      setEditingServer(null);
      refreshServers();
    } catch (error) {
      console.error('Failed to add server:', error);
      throw error;
    }
  };

  const handleUpdateServer = async (serverData: Omit<Server, 'id' | 'status'>) => {
    if (!editingServer) return;
    
    try {
      await updateServer(editingServer.id, serverData);
      setIsFormOpen(false);
      setEditingServer(null);
      refreshServers();
    } catch (error) {
      console.error('Failed to update server:', error);
      throw error;
    }
  };

  const handleDeleteServer = async () => {
    if (!deletingServer) return;
    
    try {
      await deleteServer(deletingServer.id);
      setDeletingServer(null);
      refreshServers();
    } catch (error) {
      console.error('Failed to delete server:', error);
    }
  };

  const handleEditServer = (server: Server) => {
    setEditingServer(server);
    setIsFormOpen(true);
  };

  const handleFormSubmit = editingServer
    ? handleUpdateServer
    : handleAddServer;

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white">MCP Servers</h1>
        <Button
          variant="primary"
          onClick={() => {
            setEditingServer(null);
            setIsFormOpen(true);
          }}
          leftIcon={<PlusIcon className="h-4 w-4" />}
        >
          Add Server
        </Button>
      </div>

      <ServerList
        servers={servers}
        loading={loading}
        error={error?.message || null}
        onAddServer={() => {
          setEditingServer(null);
          setIsFormOpen(true);
        }}
        onEditServer={handleEditServer}
        onDeleteServer={(id) => {
          const server = servers.find(s => s.id === id);
          if (server) setDeletingServer(server);
        }}
        onSelectServer={(server) => {
          // Handle server selection (e.g., navigate to server details)
          console.log('Selected server:', server);
        }}
      />

      {/* Add/Edit Server Modal */}
      <Modal
        isOpen={isFormOpen}
        onClose={() => {
          setIsFormOpen(false);
          setEditingServer(null);
        }}
        title={editingServer ? 'Edit Server' : 'Add New Server'}
      >
        <ServerForm
          server={editingServer}
          onSubmit={handleFormSubmit}
          onCancel={() => {
            setIsFormOpen(false);
            setEditingServer(null);
          }}
          loading={loading}
          error={error?.message || null}
        />
      </Modal>

      {/* Delete Confirmation Modal */}
      <Modal
        isOpen={!!deletingServer}
        onClose={() => setDeletingServer(null)}
        title="Delete Server"
      >
        <div className="space-y-4">
          <p className="text-gray-700 dark:text-gray-300">
            Are you sure you want to delete the server "{deletingServer?.name}"? This action cannot be undone.
          </p>
          <div className="flex justify-end space-x-3 pt-2">
            <Button
              variant="secondary"
              onClick={() => setDeletingServer(null)}
              disabled={loading}
            >
              Cancel
            </Button>
            <Button
              variant="danger"
              onClick={handleDeleteServer}
              loading={loading}
            >
              Delete
            </Button>
          </div>
        </div>
      </Modal>
    </div>
  );
};
