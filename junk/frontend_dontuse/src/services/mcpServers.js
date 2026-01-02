import { apiClient } from '../api/client';

export const mcpServersService = {
    getServers: async () => {
        return await apiClient.get('/v1/mcp/servers/');
    },

    startServer: async (serverId) => {
        return await apiClient.post(`/v1/mcp/servers/${serverId}/start`);
    },

    stopServer: async (serverId) => {
        return await apiClient.post(`/v1/mcp/servers/${serverId}/stop`);
    },

    getServerTools: async (serverId) => {
        return await apiClient.get(`/v1/mcp/servers/${serverId}/tools`);
    }
};
