import { useState, useCallback, useRef, useEffect } from 'react';

type ApiCallFunction<T, P extends any[]> = (...args: P) => Promise<T>;

interface UseApiCallOptions<T> {
  onSuccess?: (data: T) => void;
  onError?: (error: Error) => void;
  initialData?: T | null;
  enabled?: boolean;
}

export function useApiCall<T, P extends any[] = []>(
  apiCall: ApiCallFunction<T, P>,
  options: UseApiCallOptions<T> = {}
) {
  const {
    onSuccess,
    onError,
    initialData = null,
    enabled = true,
  } = options;

  const [data, setData] = useState<T | null>(initialData);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [error, setError] = useState<Error | null>(null);
  const isMounted = useRef<boolean>(true);

  // Set isMounted to false when the component unmounts
  useEffect(() => {
    return () => {
      isMounted.current = false;
    };
  }, []);

  // Reset the state
  const reset = useCallback(() => {
    if (isMounted.current) {
      setData(initialData);
      setError(null);
      setIsLoading(false);
    }
  }, [initialData]);

  // The main function that executes the API call
  const execute = useCallback(async (...args: P): Promise<T | null> => {
    if (!enabled) return null;
    
    if (isMounted.current) {
      setIsLoading(true);
      setError(null);
    }

    try {
      const result = await apiCall(...args);
      
      if (isMounted.current) {
        setData(result);
        setIsLoading(false);
        onSuccess?.(result);
      }
      
      return result;
    } catch (err) {
      const error = err instanceof Error ? err : new Error('An unknown error occurred');
      
      if (isMounted.current) {
        setError(error);
        setIsLoading(false);
        onError?.(error);
      }
      
      throw error;
    }
  }, [apiCall, enabled, onError, onSuccess]);

  // Auto-execute the API call if enabled is true
  useEffect(() => {
    if (enabled) {
      execute(...[] as unknown as P).catch(() => {});
    }
  }, [enabled, execute]);

  return {
    data,
    isLoading,
    error,
    execute,
    reset,
  };
}
