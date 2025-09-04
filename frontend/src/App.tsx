import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { ThemeProvider } from './contexts/ThemeContext';
import { AuthProvider, useAuth, ProtectedRoute } from './contexts/AuthContext';
import { ServerProvider } from './contexts/ServerContext';
import { ToasterProvider } from './components/ui/Toast';
import { Layout } from './components/layout/Layout';
import { AuthLayout } from './components/layout/AuthLayout';
import { Dashboard } from './pages/Dashboard';
import { ServerDetails } from './pages/ServerDetails';
import { ToolExecution } from './pages/ToolExecution';
import { ToolConsolePage } from './pages/ToolConsolePage';
import { Settings } from './pages/Settings';
import { Login } from './pages/auth/Login';
import { Register } from './pages/auth/Register';
import { ForgotPassword } from './pages/auth/ForgotPassword';
import { ResetPassword } from './pages/auth/ResetPassword';
import { NotFound } from './pages/NotFound';

// Wrapper component for protected routes
const ProtectedLayout: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { isAuthenticated, isLoading } = useAuth();

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-blue-500"></div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  return <Layout>{children}</Layout>;
};

// Wrapper for auth pages (login, register, etc.)
const AuthPages: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { isAuthenticated, isLoading } = useAuth();

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-blue-500"></div>
      </div>
    );
  }

  if (isAuthenticated) {
    return <Navigate to="/" replace />;
  }

  return <>{children}</>;
};

const App: React.FC = () => {
  return (
    <ThemeProvider>
      <ToasterProvider>
        <AuthProvider>
          <ServerProvider>
            <Router>
              <Routes>
                {/* Public routes */}
                <Route path="/login" element={
                  <AuthPages>
                    <Login />
                  </AuthPages>
                } />
                <Route path="/register" element={
                  <AuthPages>
                    <Register />
                  </AuthPages>
                } />
                <Route path="/forgot-password" element={
                  <AuthPages>
                    <ForgotPassword />
                  </AuthPages>
                } />
                <Route path="/reset-password" element={
                  <AuthPages>
                    <ResetPassword />
                  </AuthPages>
                } />

                {/* Protected routes */}
                <Route path="/" element={
                  <ProtectedLayout>
                    <Dashboard />
                  </ProtectedLayout>
                } />
                <Route path="/servers/:id" element={
                  <ProtectedLayout>
                    <ServerDetails />
                  </ProtectedLayout>
                } />
                <Route path="/tools" element={
                  <ProtectedLayout>
                    <ToolConsolePage />
                  </ProtectedLayout>
                } />
                <Route path="/tools/execute/:toolName" element={
                  <ProtectedLayout>
                    <ToolExecution />
                  </ProtectedLayout>
                } />
                <Route path="/settings" element={
                  <ProtectedLayout>
                    <Settings />
                  </ProtectedLayout>
                } />

                {/* 404 - Not Found */}
                <Route path="*" element={<NotFound />} />
              </Routes>
            </Router>
          </ServerProvider>
        </AuthProvider>
      </ToasterProvider>
    </ThemeProvider>
  );
};

export default App;
