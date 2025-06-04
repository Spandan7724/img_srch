import { useEffect, useRef, useState } from 'react';

export function useWebSocket(url, onMessage) {
  const ws = useRef(null);
  const [isConnected, setIsConnected] = useState(false);
  const [connectionError, setConnectionError] = useState(null);

  useEffect(() => {
    if (!url) return;

    const connect = () => {
      try {
        ws.current = new WebSocket(url);
        
        ws.current.onopen = () => {
          console.log('WebSocket connected');
          setIsConnected(true);
          setConnectionError(null);
        };

        ws.current.onmessage = (event) => {
          try {
            const data = JSON.parse(event.data);
            if (onMessage) {
              onMessage(data);
            }
          } catch (error) {
            console.error('Error parsing WebSocket message:', error);
          }
        };

        ws.current.onclose = (event) => {
          console.log('WebSocket disconnected:', event.code, event.reason);
          setIsConnected(false);
          
          // Attempt to reconnect after 3 seconds if not a manual close
          if (event.code !== 1000) {
            setTimeout(() => {
              console.log('Attempting to reconnect...');
              connect();
            }, 3000);
          }
        };

        ws.current.onerror = (error) => {
          console.error('WebSocket error:', error);
          setConnectionError('WebSocket connection failed');
          setIsConnected(false);
        };

      } catch (error) {
        console.error('Error creating WebSocket:', error);
        setConnectionError('Failed to create WebSocket connection');
      }
    };

    connect();

    return () => {
      if (ws.current) {
        ws.current.close(1000, 'Component unmounting');
      }
    };
  }, [url, onMessage]);

  return {
    isConnected,
    connectionError,
    sendMessage: (message) => {
      if (ws.current && ws.current.readyState === WebSocket.OPEN) {
        ws.current.send(JSON.stringify(message));
      }
    }
  };
} 