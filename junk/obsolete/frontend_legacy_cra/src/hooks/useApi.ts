import { useState, useCallback } from 'react';

type HttpMethod = 'GET' | 'POST' | 'PUT' | 'DELETE' | 'PATCH';

interface ApiResponse<T> {
  data: T | null;
  error: Error | null;
  isLoading: boolean;
}

interface ApiRequestOptions extends RequestInit {
  method?: HttpMethod;
  headers?: Record<string, string>;
  body?: any;
}

export const useApi = () => {
  const [state, setState] = useState<{
    loading: boolean;
    error: Error | null;
  }>({
    loading: false,
    error: null,
  });

  const request = useCallback(
    async <T>(
      url: string,
      options: ApiRequestOptions = {}
    ): Promise<{ data: T | null; error: Error | null }> => {
      setState({ loading: true, error: null });

      try {
        const { method = 'GET', headers = {}, body, ...restOptions } = options;

        const config: RequestInit = {
          method,
          headers: {
            'Content-Type': 'application/json',
            ...headers,
          },
          credentials: 'include',
          ...restOptions,
        };

        if (body && method !== 'GET' && method !== 'HEAD') {
          config.body = JSON.stringify(body);
        }

        const response = await fetch(url, config);

        if (!response.ok) {
          const errorData = await response.json().catch(() => ({}));
          throw new Error(
            errorData.message || `HTTP error! status: ${response.status}`
          );
        }

        // For 204 No Content responses
        if (response.status === 204) {
          return { data: null, error: null };
        }

        const data = await response.json();
        return { data, error: null };
      } catch (error) {
        const err = error as Error;
        console.error('API request failed:', err);
        return { data: null, error: err };
      } finally {
        setState((prev) => ({ ...prev, loading: false }));
      }
    },
    []
  );

  const get = useCallback(
    async <T>(url: string, options: Omit<ApiRequestOptions, 'method'> = {}) => {
      const { data, error } = await request<T>(url, { ...options, method: 'GET' });
      if (error) throw error;
      return data as T;
    },
    [request]
  );

  const post = useCallback(
    async <T>(
      url: string,
      body: any,
      options: Omit<ApiRequestOptions, 'method' | 'body'> = {}
    ) => {
      const { data, error } = await request<T>(url, {
        ...options,
        method: 'POST',
        body,
      });
      if (error) throw error;
      return data as T;
    },
    [request]
  );

  const put = useCallback(
    async <T>(
      url: string,
      body: any,
      options: Omit<ApiRequestOptions, 'method' | 'body'> = {}
    ) => {
      const { data, error } = await request<T>(url, {
        ...options,
        method: 'PUT',
        body,
      });
      if (error) throw error;
      return data as T;
    },
    [request]
  );

  const del = useCallback(
    async <T>(url: string, options: Omit<ApiRequestOptions, 'method'> = {}) => {
      const { data, error } = await request<T>(url, { ...options, method: 'DELETE' });
      if (error) throw error;
      return data as T;
    },
    [request]
  );

  return {
    get,
    post,
    put,
    delete: del,
    isLoading: state.loading,
    error: state.error,
  };
};

export default useApi;
