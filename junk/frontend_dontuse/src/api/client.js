const API_BASE_URL = '/api';

export const apiClient = {
    get: async (endpoint) => {
        try {
            const response = await fetch(`${API_BASE_URL}${endpoint}`);
            if (!response.ok) {
                throw new Error(`API Error: ${response.statusText}`);
            }
            return await response.json();
        } catch (error) {
            console.error('API Request Failed:', error);
            throw error;
        }
    },
    post: async (endpoint, data) => {
        try {
            const response = await fetch(`${API_BASE_URL}${endpoint}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(data),
            });
            if (!response.ok) {
                throw new Error(`API Error: ${response.statusText}`);
            }
            return await response.json();
        } catch (error) {
            console.error('API Request Failed:', error);
            throw error;
        }
    }
};
