import React, { useEffect } from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';
import { CircularProgress, Box, Typography } from '@mui/material';

interface ProtectedRouteProps {
  children: React.ReactNode;
  requiredRoles?: string[];
  redirectTo?: string;
}

/**
 * A component that protects routes by checking authentication and optionally user roles.
 * If the user is not authenticated, they will be redirected to the login page.
 * If the user doesn't have the required roles, they will be redirected to the specified path.
 * 
 * @param children - The child components to render if authenticated and authorized
 * @param requiredRoles - Optional array of role names required to access the route
 * @param redirectTo - Optional path to redirect to if user is not authorized (default: '/unauthorized')
 */
const ProtectedRoute: React.FC<ProtectedRouteProps> = ({
  children,
  requiredRoles = [],
  redirectTo = '/unauthorized',
}) => {
  const { isAuthenticated, isLoading, user } = useAuth();
  const location = useLocation();

  // Check if user has required roles
  const hasRequiredRoles = requiredRoles.length === 0 || 
    (user && requiredRoles.some(role => user.roles?.includes(role)));

  // Show loading state while checking authentication
  if (isLoading) {
    return (
      <Box
        display="flex"
        flexDirection="column"
        justifyContent="center"
        alignItems="center"
        minHeight="100vh"
      >
        <CircularProgress size={60} thickness={4} />
        <Typography variant="h6" mt={2} color="textSecondary">
          Verifying your session...
        </Typography>
      </Box>
    );
  }

  // If not authenticated, redirect to login with the return location
  if (!isAuthenticated) {
    return (
      <Navigate
        to="/login"
        state={{ from: location }}
        replace
      />
    );
  }

  // If authenticated but doesn't have required roles, redirect to unauthorized
  if (!hasRequiredRoles) {
    return <Navigate to={redirectTo} replace />;
  }

  // User is authenticated and has required roles, render children
  return <>{children}</>;
};

export default ProtectedRoute;
