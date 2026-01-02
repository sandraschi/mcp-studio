import React, { createContext, useContext, ReactNode } from 'react';
import { apiService } from '../services/api/api.service';

interface ApiContextType {
  api: typeof apiService;
}

const ApiContext = createContext<ApiContextType | undefined>(undefined);

interface ApiProviderProps {
  children: ReactNode;
  apiInstance?: typeof apiService;
}

export const ApiProvider: React.FC<ApiProviderProps> = ({
  children,
  apiInstance = apiService,
}) => {
  return (
    <ApiContext.Provider value={{ api: apiInstance }}>
      {children}
    </ApiContext.Provider>
  );
};

export const useApi = (): ApiContextType => {
  const context = useContext(ApiContext);
  if (context === undefined) {
    throw new Error('useApi must be used within an ApiProvider');
  }
  return context;
};

// Convenience hook for direct API access
export const useApiService = () => {
  const { api } = useApi();
  return api;
};

// Export the context for testing or other advanced use cases
export default ApiContext;
