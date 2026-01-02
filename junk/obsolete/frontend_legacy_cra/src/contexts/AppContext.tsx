import React, { createContext, useContext, useReducer, ReactNode, useEffect } from 'react';
import { UiState, Server, Tool, Notification } from '../types';

// Initial state
const initialState: UiState = {
  darkMode: window.matchMedia('(prefers-color-scheme: dark)').matches,
  sidebarOpen: true,
  currentView: 'dashboard',
  selectedServerId: null,
  selectedTool: null,
  theme: {
    primaryColor: '#3b82f6',
    secondaryColor: '#8b5cf6',
    fontFamily: 'Inter, system-ui, sans-serif',
    borderRadius: '0.375rem',
  },
  layout: {
    cardView: 'grid',
    density: 'normal',
    showToolIcons: true,
  },
  notifications: [],
};

type Action =
  | { type: 'TOGGLE_DARK_MODE' }
  | { type: 'TOGGLE_SIDEBAR' }
  | { type: 'SET_CURRENT_VIEW'; payload: UiState['currentView'] }
  | { type: 'SELECT_SERVER'; payload: string | null }
  | { type: 'SELECT_TOOL'; payload: { serverId: string; toolId: string; tab?: string } | null }
  | { type: 'ADD_NOTIFICATION'; payload: Omit<Notification, 'id' | 'timestamp' | 'read'> }
  | { type: 'REMOVE_NOTIFICATION'; payload: string }
  | { type: 'MARK_NOTIFICATION_READ'; payload: string };

function appReducer(state: UiState, action: Action): UiState {
  switch (action.type) {
    case 'TOGGLE_DARK_MODE':
      return {
        ...state,
        darkMode: !state.darkMode,
      };
    
    case 'TOGGLE_SIDEBAR':
      return {
        ...state,
        sidebarOpen: !state.sidebarOpen,
      };
    
    case 'SET_CURRENT_VIEW':
      return {
        ...state,
        currentView: action.payload,
      };
    
    case 'SELECT_SERVER':
      return {
        ...state,
        selectedServerId: action.payload,
        selectedTool: action.payload ? state.selectedTool : null,
      };
    
    case 'SELECT_TOOL':
      return {
        ...state,
        selectedTool: action.payload,
        selectedServerId: action.payload?.serverId || state.selectedServerId,
      };
    
    case 'ADD_NOTIFICATION':
      const newNotification: Notification = {
        ...action.payload,
        id: crypto.randomUUID(),
        timestamp: new Date().toISOString(),
        read: false,
      };
      return {
        ...state,
        notifications: [newNotification, ...state.notifications].slice(0, 50), // Limit to 50 notifications
      };
    
    case 'REMOVE_NOTIFICATION':
      return {
        ...state,
        notifications: state.notifications.filter(n => n.id !== action.payload),
      };
    
    case 'MARK_NOTIFICATION_READ':
      return {
        ...state,
        notifications: state.notifications.map(n => 
          n.id === action.payload ? { ...n, read: true } : n
        ),
      };
    
    default:
      return state;
  }
}

// Create context
type AppContextType = {
  state: UiState;
  dispatch: React.Dispatch<Action>;
  addNotification: (notification: Omit<Notification, 'id' | 'timestamp' | 'read'>) => void;
  removeNotification: (id: string) => void;
  markNotificationRead: (id: string) => void;
  toggleDarkMode: () => void;
  toggleSidebar: () => void;
  setCurrentView: (view: UiState['currentView']) => void;
  selectServer: (serverId: string | null) => void;
  selectTool: (tool: { serverId: string; toolId: string; tab?: string } | null) => void;
};

const AppContext = createContext<AppContextType | undefined>(undefined);

// Provider component
export const AppProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [state, dispatch] = useReducer(appReducer, initialState);

  // Load saved preferences from localStorage
  useEffect(() => {
    try {
      const savedState = localStorage.getItem('appState');
      if (savedState) {
        const parsed = JSON.parse(savedState);
        // Only load safe preferences
        if (parsed.darkMode !== undefined) {
          dispatch({ type: 'TOGGLE_DARK_MODE' });
        }
        if (parsed.theme) {
          // Apply theme to document
          const root = document.documentElement;
          root.style.setProperty('--primary', parsed.theme.primaryColor);
          root.style.setProperty('--secondary', parsed.theme.secondaryColor);
          root.style.setProperty('--font-sans', parsed.theme.fontFamily);
          root.style.setProperty('--radius', parsed.theme.borderRadius);
        }
      }
    } catch (e) {
      console.error('Failed to load app state:', e);
    }
  }, []);

  // Save preferences to localStorage when they change
  useEffect(() => {
    const { notifications, ...preferences } = state;
    try {
      localStorage.setItem('appState', JSON.stringify(preferences));
    } catch (e) {
      console.error('Failed to save app state:', e);
    }
  }, [state.darkMode, state.theme, state.layout]);

  // Apply dark mode class to document
  useEffect(() => {
    if (state.darkMode) {
      document.documentElement.classList.add('dark');
    } else {
      document.documentElement.classList.remove('dark');
    }
  }, [state.darkMode]);

  const value = {
    state,
    dispatch,
    addNotification: (notification: Omit<Notification, 'id' | 'timestamp' | 'read'>) => 
      dispatch({ type: 'ADD_NOTIFICATION', payload: notification }),
    removeNotification: (id: string) => 
      dispatch({ type: 'REMOVE_NOTIFICATION', payload: id }),
    markNotificationRead: (id: string) => 
      dispatch({ type: 'MARK_NOTIFICATION_READ', payload: id }),
    toggleDarkMode: () => dispatch({ type: 'TOGGLE_DARK_MODE' }),
    toggleSidebar: () => dispatch({ type: 'TOGGLE_SIDEBAR' }),
    setCurrentView: (view: UiState['currentView']) => 
      dispatch({ type: 'SET_CURRENT_VIEW', payload: view }),
    selectServer: (serverId: string | null) => 
      dispatch({ type: 'SELECT_SERVER', payload: serverId }),
    selectTool: (tool: { serverId: string; toolId: string; tab?: string } | null) => 
      dispatch({ type: 'SELECT_TOOL', payload: tool }),
  };

  return <AppContext.Provider value={value}>{children}</AppContext.Provider>;
};

// Custom hook to use the app context
export const useApp = () => {
  const context = useContext(AppContext);
  if (context === undefined) {
    throw new Error('useApp must be used within an AppProvider');
  }
  return context;
};
