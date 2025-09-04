import React, { useState, useEffect } from 'react';
import { Server } from '../../types';
import { Button } from '../common/Button';
import { Input, Select } from '../common/Form';

interface ServerFormProps {
  server?: Server | null;
  onSubmit: (serverData: Omit<Server, 'id' | 'status'>) => Promise<void>;
  onCancel: () => void;
  loading?: boolean;
  error?: string | null;
}

type ServerType = 'http' | 'https' | 'ws' | 'wss';

const defaultServer: Omit<Server, 'id' | 'status'> = {
  name: '',
  description: '',
  url: '',
  type: 'http',
  auth: {
    type: 'none',
    username: '',
    password: '',
    token: '',
  },
  metadata: {},
};

export const ServerForm: React.FC<ServerFormProps> = ({
  server,
  onSubmit,
  onCancel,
  loading = false,
  error = null,
}) => {
  const [formData, setFormData] = useState<Omit<Server, 'id' | 'status'>>(
    server || defaultServer
  );
  const [validationErrors, setValidationErrors] = useState<Record<string, string>>({});

  useEffect(() => {
    if (server) {
      setFormData(server);
    } else {
      setFormData(defaultServer);
    }
  }, [server]);

  const validate = (): boolean => {
    const errors: Record<string, string> = {};
    
    if (!formData.name.trim()) {
      errors.name = 'Server name is required';
    }
    
    if (!formData.url.trim()) {
      errors.url = 'Server URL is required';
    } else {
      try {
        new URL(formData.url);
      } catch (e) {
        errors.url = 'Please enter a valid URL';
      }
    }

    if (formData.auth.type === 'basic' && !formData.auth.username) {
      errors['auth.username'] = 'Username is required for basic auth';
    }

    if (formData.auth.type === 'token' && !formData.auth.token) {
      errors['auth.token'] = 'Token is required';
    }

    setValidationErrors(errors);
    return Object.keys(errors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!validate()) {
      return;
    }

    try {
      await onSubmit(formData);
    } catch (err) {
      // Error handling is done by the parent component
      console.error('Form submission error:', err);
    }
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) => {
    const { name, value } = e.target;
    
    // Handle nested properties (e.g., auth.username)
    if (name.startsWith('auth.')) {
      const authField = name.split('.')[1] as keyof typeof formData.auth;
      setFormData(prev => ({
        ...prev,
        auth: {
          ...prev.auth,
          [authField]: value,
        },
      }));
    } else {
      setFormData(prev => ({
        ...prev,
        [name]: value,
      }));
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      {error && (
        <div className="rounded-md bg-red-50 dark:bg-red-900/30 p-4 mb-4">
          <div className="flex">
            <div className="ml-3">
              <h3 className="text-sm font-medium text-red-800 dark:text-red-200">
                Error
              </h3>
              <div className="mt-2 text-sm text-red-700 dark:text-red-300">
                {error}
              </div>
            </div>
          </div>
        </div>
      )}

      <div className="space-y-4">
        <Input
          label="Server Name"
          name="name"
          value={formData.name}
          onChange={handleChange}
          placeholder="My MCP Server"
          required
          error={validationErrors.name}
        />

        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          <Select
            label="Protocol"
            name="type"
            value={formData.type}
            onChange={handleChange}
            options={[
              { value: 'http', label: 'HTTP' },
              { value: 'https', label: 'HTTPS' },
              { value: 'ws', label: 'WebSocket' },
              { value: 'wss', label: 'WebSocket Secure' },
            ]}
            required
          />

          <Input
            label="Server URL"
            name="url"
            value={formData.url}
            onChange={handleChange}
            placeholder="https://example.com/api"
            required
            error={validationErrors.url}
          />
        </div>

        <div className="border-t border-gray-200 dark:border-gray-700 pt-4">
          <h3 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">
            Authentication
          </h3>
          
          <Select
            label="Authentication Type"
            name="auth.type"
            value={formData.auth.type}
            onChange={handleChange}
            options={[
              { value: 'none', label: 'None' },
              { value: 'basic', label: 'Basic Auth' },
              { value: 'token', label: 'Bearer Token' },
              { value: 'api-key', label: 'API Key' },
            ]}
            className="mb-4"
          />

          {formData.auth.type === 'basic' && (
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
              <Input
                label="Username"
                name="auth.username"
                value={formData.auth.username || ''}
                onChange={handleChange}
                placeholder="username"
                error={validationErrors['auth.username']}
                required
              />
              <Input
                label="Password"
                name="auth.password"
                type="password"
                value={formData.auth.password || ''}
                onChange={handleChange}
                placeholder="••••••••"
                autoComplete="new-password"
              />
            </div>
          )}

          {formData.auth.type === 'token' && (
            <Input
              label="Bearer Token"
              name="auth.token"
              type="password"
              value={formData.auth.token || ''}
              onChange={handleChange}
              placeholder="Enter your token"
              error={validationErrors['auth.token']}
              required
            />
          )}

          {formData.auth.type === 'api-key' && (
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
              <Input
                label="Header Name"
                name="auth.headerName"
                value={formData.auth.headerName || 'X-API-Key'}
                onChange={handleChange}
                placeholder="X-API-Key"
              />
              <Input
                label="API Key"
                name="auth.apiKey"
                type="password"
                value={formData.auth.apiKey || ''}
                onChange={handleChange}
                placeholder="Enter your API key"
                required
              />
            </div>
          )}
        </div>

        <div>
          <label
            htmlFor="description"
            className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1"
          >
            Description (Optional)
          </label>
          <textarea
            id="description"
            name="description"
            rows={3}
            className="shadow-sm focus:ring-blue-500 focus:border-blue-500 block w-full sm:text-sm border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white rounded-md"
            placeholder="A brief description of this server"
            value={formData.description}
            onChange={handleChange}
          />
        </div>
      </div>

      <div className="flex justify-end space-x-3 pt-2">
        <Button
          type="button"
          variant="secondary"
          onClick={onCancel}
          disabled={loading}
        >
          Cancel
        </Button>
        <Button
          type="submit"
          variant="primary"
          loading={loading}
        >
          {server ? 'Update Server' : 'Add Server'}
        </Button>
      </div>
    </form>
  );
};
