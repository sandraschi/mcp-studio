import { apiClient } from '../api/client';

export const reposService = {
    getRepos: async () => {
        return await apiClient.get('/v1/repos/');
    },

    runScan: async (path = null) => {
        const params = path ? `?scan_path=${encodeURIComponent(path)}` : '';
        return await apiClient.post(`/v1/repos/run_scan${params}`);
    },

    getScanProgress: async () => {
        return await apiClient.get('/v1/repos/progress');
    }
};
