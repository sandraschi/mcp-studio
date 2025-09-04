import React, { useState, useEffect } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { 
  ArrowLeftIcon,
  PlayIcon,
  StopIcon,
  PencilIcon,
  TrashIcon,
  Cog6ToothIcon,
  InformationCircleIcon,
  ClockIcon,
  CodeBracketIcon,
  WrenchScrewdriverIcon,
  ArrowPathIcon,
  ExclamationTriangleIcon
} from '@heroicons/react/24/outline';
import { useServers, useToaster } from '../hooks';
import { Button, Card, Tabs, Tab, Badge, Tooltip, Modal, Input, Label } from '../components/ui';

export const ServerDetails: React.FC = () => {
  const { serverId } = useParams<{ serverId: string }>();
  const navigate = useNavigate();
  const { getServer, startServer, stopServer, executeTool, updateServer, deleteServer } = useServers();
  const { success, error } = useToaster();
  const [activeTab, setActiveTab] = useState('overview');
  const [isEditing, setIsEditing] = useState(false);
  const [isDeleteModalOpen, setIsDeleteModalOpen] = useState(false);
  const [isRestarting, setIsRestarting] = useState(false);
  const [serverData, setServerData] = useState({
    name: '',
    command: '',
    args: '',
    cwd: '',
    env: '{}',
    autoStart: false,
  });

  const server = getServer(serverId || '');

  useEffect(() => {
    if (server) {
      setServerData({
        name: server.name,
        command: server.command,
        args: server.args.join(' '),
        cwd: server.cwd || '',
        env: JSON.stringify(server.env || {}, null, 2),
        autoStart: server.autoStart || false,
      });
    }
  }, [server]);

  if (!server) {
    return (
      <div className="flex flex-col items-center justify-center h-64">
        <ExclamationTriangleIcon className="h-12 w-12 text-yellow-500 mb-4" />
        <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">Server not found</h3>
        <p className="text-gray-500 dark:text-gray-400 mb-6">The requested server could not be found or no longer exists.</p>
        <Button onClick={() => navigate('/')}>
          <ArrowLeftIcon className="h-4 w-4 mr-2" />
          Back to Dashboard
        </Button>
      </div>
    );
  }

  const handleStart = async () => {
    try {
      await startServer(server.id);
      success('Server started successfully');
    } catch (err) {
      console.error('Error starting server:', err);
      error('Failed to start server');
    }
  };

  const handleStop = async () => {
    try {
      await stopServer(server.id);
      success('Server stopped successfully');
    } catch (err) {
      console.error('Error stopping server:', err);
      error('Failed to stop server');
    }
  };

  const handleRestart = async () => {
    try {
      setIsRestarting(true);
      await stopServer(server.id);
      await startServer(server.id);
      success('Server restarted successfully');
    } catch (err) {
      console.error('Error restarting server:', err);
      error('Failed to restart server');
    } finally {
      setIsRestarting(false);
    }
  };

  const handleSave = async () => {
    try {
      await updateServer(server.id, {
        ...serverData,
        args: serverData.args.split(' ').filter(arg => arg.trim() !== ''),
        env: JSON.parse(serverData.env)
      });
      setIsEditing(false);
      success('Server updated successfully');
    } catch (err) {
      console.error('Error updating server:', err);
      error('Failed to update server');
    }
  };

  const handleDelete = async () => {
    try {
      await deleteServer(server.id);
      success('Server deleted successfully');
      navigate('/');
    } catch (err) {
      console.error('Error deleting server:', err);
      error('Failed to delete server');
    } finally {
      setIsDeleteModalOpen(false);
    }
  };

  const renderStatusBadge = () => {
    const statusMap = {
      online: { color: 'green', label: 'Online' },
      offline: { color: 'gray', label: 'Offline' },
      starting: { color: 'yellow', label: 'Starting' },
      stopping: { color: 'yellow', label: 'Stopping' },
      error: { color: 'red', label: 'Error' },
    };

    const status = statusMap[server.status] || { color: 'gray', label: 'Unknown' };
    return <Badge color={status.color}>{status.label}</Badge>;
  };

  const renderActionButtons = () => {
    if (isEditing) {
      return (
        <div className="flex space-x-2">
          <Button variant="secondary" onClick={() => setIsEditing(false)}>
            Cancel
          </Button>
          <Button onClick={handleSave}>
            Save Changes
          </Button>
        </div>
      );
    }

    return (
      <div className="flex space-x-2">
        {server.status === 'online' ? (
          <Button variant="danger" onClick={handleStop}>
            <StopIcon className="h-4 w-4 mr-2" />
            Stop
          </Button>
        ) : (
          <Button onClick={handleStart}>
            <PlayIcon className="h-4 w-4 mr-2" />
            Start
          </Button>
        )}
        <Button variant="secondary" onClick={() => setIsEditing(true)}>
          <PencilIcon className="h-4 w-4 mr-2" />
          Edit
        </Button>
        <Button variant="danger" outline onClick={() => setIsDeleteModalOpen(true)}>
          <TrashIcon className="h-4 w-4 mr-2" />
          Delete
        </Button>
      </div>
    );
  };

  return (
    <div className="space-y-6">
      <div className="md:flex md:items-center md:justify-between">
        <div className="flex items-center">
          <Button variant="ghost" size="sm" onClick={() => navigate(-1)} className="mr-4">
            <ArrowLeftIcon className="h-5 w-5" />
          </Button>
          <div>
            <div className="flex items-center">
              <h2 className="text-2xl font-bold text-gray-900 dark:text-white">
                {isEditing ? (
                  <Input
                    value={serverData.name}
                    onChange={(e) => setServerData({ ...serverData, name: e.target.value })}
                    className="text-2xl font-bold p-0 border-0 focus:ring-0 focus:ring-offset-0"
                  />
                ) : (
                  server.name
                )}
              </h2>
              <div className="ml-3">
                {renderStatusBadge()}
              </div>
            </div>
            <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
              {server.id}
            </p>
          </div>
        </div>
        <div className="mt-4 flex md:mt-0">
          {renderActionButtons()}
        </div>
      </div>

      <Tabs value={activeTab} onChange={setActiveTab}>
        <Tab value="overview" icon={<InformationCircleIcon className="h-5 w-5" />}>
          Overview
        </Tab>
        <Tab value="tools" icon={<WrenchScrewdriverIcon className="h-5 w-5" />}>
          Tools
        </Tab>
        <Tab value="logs" icon={<CodeBracketIcon className="h-5 w-5" />}>
          Logs
        </Tab>
        <Tab value="settings" icon={<Cog6ToothIcon className="h-5 w-5" />}>
          Settings
        </Tab>
      </Tabs>

      <div className="mt-6">
        {activeTab === 'overview' && (
          <Card>
            <div className="grid grid-cols-1 gap-6 md:grid-cols-2">
              <div>
                <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-4">Server Information</h3>
                <div className="space-y-4">
                  <div>
                    <Label>Status</Label>
                    <div className="mt-1">{renderStatusBadge()}</div>
                  </div>
                  <div>
                    <Label>Command</Label>
                    <div className="mt-1 font-mono text-sm bg-gray-100 dark:bg-gray-800 p-2 rounded">
                      {isEditing ? (
                        <Input
                          value={serverData.command}
                          onChange={(e) => setServerData({ ...serverData, command: e.target.value })}
                          className="font-mono text-sm"
                        />
                      ) : (
                        server.command
                      )}
                    </div>
                  </div>
                  <div>
                    <Label>Arguments</Label>
                    <div className="mt-1">
                      {isEditing ? (
                        <Input
                          value={serverData.args}
                          onChange={(e) => setServerData({ ...serverData, args: e.target.value })}
                          placeholder="arg1 arg2 --flag value"
                        />
                      ) : (
                        <div className="font-mono text-sm bg-gray-100 dark:bg-gray-800 p-2 rounded">
                          {server.args.join(' ')}
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              </div>
              <div>
                <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-4">Details</h3>
                <div className="space-y-4">
                  <div>
                    <Label>Working Directory</Label>
                    <div className="mt-1">
                      {isEditing ? (
                        <Input
                          value={serverData.cwd}
                          onChange={(e) => setServerData({ ...serverData, cwd: e.target.value })}
                        />
                      ) : (
                        <div className="font-mono text-sm bg-gray-100 dark:bg-gray-800 p-2 rounded">
                          {server.cwd || 'Not specified'}
                        </div>
                      )}
                    </div>
                  </div>
                  <div>
                    <Label>Environment Variables</Label>
                    <div className="mt-1">
                      {isEditing ? (
                        <textarea
                          value={serverData.env}
                          onChange={(e) => setServerData({ ...serverData, env: e.target.value })}
                          className="w-full h-40 font-mono text-sm bg-gray-100 dark:bg-gray-800 p-2 rounded border border-gray-300 dark:border-gray-700"
                        />
                      ) : (
                        <pre className="text-xs p-2 bg-gray-100 dark:bg-gray-800 rounded overflow-auto max-h-40">
                          {JSON.stringify(server.env || {}, null, 2)}
                        </pre>
                      )}
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </Card>
        )}

        {activeTab === 'tools' && (
          <Card>
            <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-4">Available Tools</h3>
            {server.tools && server.tools.length > 0 ? (
              <div className="overflow-hidden border border-gray-200 dark:border-gray-700 rounded-lg">
                <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
                  <thead className="bg-gray-50 dark:bg-gray-800">
                    <tr>
                      <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                        Name
                      </th>
                      <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                        Description
                      </th>
                      <th scope="col" className="px-6 py-3 text-right text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                        Actions
                      </th>
                    </tr>
                  </thead>
                  <tbody className="bg-white dark:bg-gray-800 divide-y divide-gray-200 dark:divide-gray-700">
                    {server.tools.map((tool) => (
                      <tr key={tool.name} className="hover:bg-gray-50 dark:hover:bg-gray-700">
                        <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900 dark:text-white">
                          {tool.name}
                        </td>
                        <td className="px-6 py-4 text-sm text-gray-500 dark:text-gray-400">
                          {tool.description || 'No description available'}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                          <Link
                            to={`/servers/${server.id}/tools/${tool.name}`}
                            className="text-blue-600 hover:text-blue-900 dark:text-blue-400 dark:hover:text-blue-300"
                          >
                            Execute
                          </Link>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <div className="text-center py-12">
                <WrenchScrewdriverIcon className="mx-auto h-12 w-12 text-gray-400" />
                <h3 className="mt-2 text-sm font-medium text-gray-900 dark:text-white">No tools available</h3>
                <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
                  This server doesn't expose any tools or is currently offline.
                </p>
              </div>
            )}
          </Card>
        )}

        {activeTab === 'logs' && (
          <Card>
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-medium text-gray-900 dark:text-white">Server Logs</h3>
              <Button size="sm" variant="secondary" onClick={() => {}}>
                <ArrowPathIcon className="h-4 w-4 mr-2" />
                Refresh
              </Button>
            </div>
            <div className="bg-black text-green-400 font-mono text-xs p-4 rounded h-96 overflow-auto">
              {server.status === 'offline' ? (
                <div className="text-gray-500 italic">Server is currently offline. Start the server to view logs.</div>
              ) : (
                <div>
                  <div className="text-gray-500">Connecting to server logs...</div>
                  <div className="mt-2">
                    <div className="text-gray-400">$ {server.command} {server.args.join(' ')}</div>
                    <div className="mt-2 text-green-300">Server started successfully</div>
                    <div className="mt-1">Listening on port 8000</div>
                    <div className="mt-1">Ready for connections</div>
                  </div>
                </div>
              )}
            </div>
          </Card>
        )}

        {activeTab === 'settings' && (
          <Card>
            <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-6">Server Settings</h3>
            <div className="space-y-6">
              <div>
                <div className="flex items-center justify-between">
                  <div>
                    <h4 className="font-medium text-gray-900 dark:text-white">Auto-start on boot</h4>
                    <p className="text-sm text-gray-500 dark:text-gray-400">
                      Automatically start this server when the application launches.
                    </p>
                  </div>
                  <div className="flex items-center">
                    <label className="relative inline-flex items-center cursor-pointer">
                      <input
                        type="checkbox"
                        className="sr-only peer"
                        checked={serverData.autoStart}
                        onChange={(e) => setServerData({ ...serverData, autoStart: e.target.checked })}
                      />
                      <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 dark:peer-focus:ring-blue-800 rounded-full peer dark:bg-gray-700 peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all dark:border-gray-600 peer-checked:bg-blue-600"></div>
                    </label>
                  </div>
                </div>
              </div>

              <div className="pt-5 border-t border-gray-200 dark:border-gray-700">
                <h4 className="text-red-600 dark:text-red-400 font-medium mb-2">Danger Zone</h4>
                <div className="bg-red-50 dark:bg-red-900/10 p-4 rounded-lg">
                  <div className="flex items-center justify-between">
                    <div>
                      <h5 className="font-medium text-red-700 dark:text-red-300">Delete this server</h5>
                      <p className="text-sm text-red-600 dark:text-red-400">
                        Once you delete a server, there is no going back. Please be certain.
                      </p>
                    </div>
                    <Button variant="danger" onClick={() => setIsDeleteModalOpen(true)}>
                      <TrashIcon className="h-4 w-4 mr-2" />
                      Delete Server
                    </Button>
                  </div>
                </div>
              </div>
            </div>
          </Card>
        )}
      </div>

      {/* Delete Confirmation Modal */}
      <Modal
        isOpen={isDeleteModalOpen}
        onClose={() => setIsDeleteModalOpen(false)}
        title="Delete Server"
        description={`Are you sure you want to delete "${server.name}"? This action cannot be undone.`}
        buttons={[
          {
            label: 'Cancel',
            onClick: () => setIsDeleteModalOpen(false),
            variant: 'secondary',
          },
          {
            label: 'Delete',
            onClick: handleDelete,
            variant: 'danger',
          },
        ]}
      />
    </div>
  );
};
