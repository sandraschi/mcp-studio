import { useEffect, useRef, useCallback } from 'react';

export const useWebSocket = (
  url: string,
  onMessage: (data: any) => void,
  reconnect = true,
  reconnectInterval = 5000,
  reconnectAttempts = 5
) => {
  const ws = useRef<WebSocket | null>(null);
  const reconnectTimeout = useRef<number>();
  const reconnectCount = useRef(0);
  const isMounted = useRef(true);

  const connect = useCallback(() => {
    if (!isMounted.current) return;

    // Close existing connection if any
    if (ws.current) {
      ws.current.close();
    }

    try {
      ws.current = new WebSocket(url);

      ws.current.onopen = () => {
        reconnectCount.current = 0;
        console.log('WebSocket connected');
      };

      ws.current.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          onMessage(data);
        } catch (error) {
          console.error('Error parsing WebSocket message:', error);
        }
      };

      ws.current.onclose = () => {
        console.log('WebSocket disconnected');
        if (!isMounted.current) return;

        // Attempt to reconnect
        if (reconnect && reconnectCount.current < reconnectAttempts) {
          reconnectCount.current += 1;
          console.log(`Attempting to reconnect (${reconnectCount.current}/${reconnectAttempts})...`);
          
          reconnectTimeout.current = window.setTimeout(() => {
            if (isMounted.current) {
              connect();
            }
          }, reconnectInterval);
        }
      };

      ws.current.onerror = (error) => {
        console.error('WebSocket error:', error);
      };
    } catch (error) {
      console.error('Failed to create WebSocket:', error);
      
      // Try to reconnect if initial connection fails
      if (reconnect && reconnectCount.current < reconnectAttempts) {
        reconnectCount.current += 1;
        reconnectTimeout.current = window.setTimeout(() => {
          if (isMounted.current) {
            connect();
          }
        }, reconnectInterval);
      }
    }
  }, [url, onMessage, reconnect, reconnectInterval, reconnectAttempts]);

  // Initialize WebSocket connection
  useEffect(() => {
    isMounted.current = true;
    connect();

    // Cleanup function
    return () => {
      isMounted.current = false;
      
      // Clear any pending reconnection attempts
      if (reconnectTimeout.current) {
        clearTimeout(reconnectTimeout.current);
      }
      
      // Close WebSocket connection
      if (ws.current) {
        ws.current.close();
      }
    };
  }, [connect]);

  // Function to send messages through WebSocket
  const sendMessage = useCallback((message: any) => {
    if (ws.current && ws.current.readyState === WebSocket.OPEN) {
      try {
        const messageString = typeof message === 'string' 
          ? message 
          : JSON.stringify(message);
        ws.current.send(messageString);
        return true;
      } catch (error) {
        console.error('Error sending WebSocket message:', error);
        return false;
      }
    } else {
      console.warn('WebSocket is not connected');
      return false;
    }
  }, []);

  return { sendMessage };
};

export default useWebSocket;
