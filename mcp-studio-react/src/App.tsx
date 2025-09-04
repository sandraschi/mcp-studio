import React, { Suspense, useState, useEffect } from 'react';
import { 
  BrowserRouter as Router, 
  Routes, 
  Route, 
  Navigate, 
  useLocation 
} from 'react-router-dom';
import { ThemeProvider, createTheme, CssBaseline } from '@mui/material';
import { WebSocketProvider } from './contexts/WebSocketContext';
import { AuthProvider, useAuth } from './contexts/AuthContext';
import { ToastContainer } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';

// Lazy load pages for better performance
const LoginPage = React.lazy(() => import('./pages/auth/LoginPage'));
const RegisterPage = React.lazy(() => import('./pages/auth/RegisterPage'));
const DashboardPage = React.lazy(() => import('./pages/dashboard/DashboardPage'));
const HomePage = React.lazy(() => import('./pages/home/HomePage'));
const AppLayout = React.lazy(() => import('./components/layout/AppLayout'));

// Create a theme instance
const theme = createTheme({
  palette: {
    primary: {
      main: '#1976d2',
    },
    secondary: {
      main: '#dc004e',
    },
    background: {
      default: '#f5f5f5',
    },
  },
  typography: {
    fontFamily: '"Roboto", "Helvetica", "Arial", sans-serif',
    h1: {
      fontWeight: 500,
    },
    h2: {
      fontWeight: 500,
    },
    h3: {
      fontWeight: 500,
    },
  },
  components: {
    MuiButton: {
      styleOverrides: {
        root: {
          textTransform: 'none',
        },
      },
    },
    MuiCard: {
      styleOverrides: {
        root: {
          borderRadius: 8,
          boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
        },
      },
    },
  },
});

// Loading component for Suspense fallback
const LoadingFallback = () => (
  <div style={{
    display: 'flex',
    justifyContent: 'center',
    alignItems: 'center',
    height: '100vh',
    width: '100vw',
    backgroundColor: theme.palette.background.default,
  }}>
    <div style={{ textAlign: 'center' }}>
      <div style={{ marginBottom: 16 }}>Loading MCP Studio...</div>
      <div className="spinner"></div>
    </div>
  </div>
);

// Online status indicator component
const OnlineStatusIndicator = () => {
  const [isOnline, setIsOnline] = useState(navigator.onLine);

  useEffect(() => {
    const handleOnline = () => setIsOnline(true);
    const handleOffline = () => setIsOnline(false);

    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);

    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
    };
  }, []);

  if (isOnline) return null;
  
  return (
    <div style={{
      position: 'fixed',
      bottom: 0,
      left: 0,
      right: 0,
      backgroundColor: '#ff9800',
      color: 'white',
      textAlign: 'center',
      padding: '8px',
      zIndex: 1400,
      boxShadow: '0 -2px 4px rgba(0,0,0,0.1)',
    }}>
      You are currently offline. Some features may be limited.
    </div>
  );
};

// Protected route wrapper
const ProtectedRoute = ({ children }: { children: React.ReactNode }) => {
  const { isAuthenticated, isLoading } = useAuth();
  const location = useLocation();
  
  if (isLoading) {
    return <LoadingFallback />;
  }
  
  if (!isAuthenticated) {
    // Redirect them to the /login page, but save the current location they were trying to go to
    return <Navigate to="/login" state={{ from: location }} replace />;
  }
  
  return <>{children}</>;
};

// Define routes
const AppRoutes = () => {
  const { isAuthenticated, isLoading } = useAuth();

  if (isLoading) {
    return <LoadingFallback />;
  }

  return (
    <Routes>
      {/* Public routes */}
      <Route 
        path="/" 
        element={isAuthenticated ? <Navigate to="/dashboard" replace /> : <HomePage />} 
      />
      <Route 
        path="/login" 
        element={isAuthenticated ? <Navigate to="/dashboard" replace /> : <LoginPage />} 
      />
      <Route 
        path="/register" 
        element={isAuthenticated ? <Navigate to="/dashboard" replace /> : <RegisterPage />} 
      />
      
      {/* Protected routes */}
      <Route element={
        <ProtectedRoute>
          <AppLayout />
        </ProtectedRoute>
      }>
        <Route path="/dashboard" element={<DashboardPage />} />
        
        {/* Add more protected routes here */}
        
        {/* Default dashboard redirect for authenticated users */}
        <Route path="/" element={<Navigate to="/dashboard" replace />} />
      </Route>
      
      {/* 404 route */}
      <Route 
        path="*" 
        element={
          <Navigate to={isAuthenticated ? "/dashboard" : "/login"} replace />
        } 
      />
    </Routes>
  );
};

// Main App component - ROUTER MOVED OUTSIDE AuthProvider
function App() {
  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <Router>
        <Suspense fallback={<LoadingFallback />}>
          <AuthProvider>
            <WebSocketProvider>
              <AppRoutes />
              <OnlineStatusIndicator />
              <ToastContainer
                position="bottom-right"
                autoClose={5000}
                hideProgressBar={false}
                newestOnTop={false}
                closeOnClick
                rtl={false}
                pauseOnFocusLoss
                draggable
                pauseOnHover
                theme="light"
              />
            </WebSocketProvider>
          </AuthProvider>
        </Suspense>
      </Router>
    </ThemeProvider>
  );
}

export default App;