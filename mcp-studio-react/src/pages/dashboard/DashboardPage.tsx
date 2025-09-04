import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { styled } from '@mui/material/styles';
import { useApiCall } from '../../hooks/useApiCall';

// MUI Icons
import RefreshIcon from '@mui/icons-material/Refresh';
import ErrorOutlineIcon from '@mui/icons-material/ErrorOutline';
import CheckCircleOutlineIcon from '@mui/icons-material/CheckCircleOutline';
import WarningAmberIcon from '@mui/icons-material/WarningAmber';
import InfoIcon from '@mui/icons-material/Info';

// MUI Components
import {
  Box,
  Button,
  Card,
  CardContent,
  CardHeader,
  CircularProgress,
  Divider,
  Grid,
  IconButton,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Paper,
  Skeleton,
  Tooltip,
  Typography,
  LinearProgress,
} from '@mui/material';

// Types
type StatusType = 'online' | 'offline' | 'error';
type ActivityType = 'tool_run' | 'server_connect' | 'template_created' | 'error';

interface ServerStatusResponse {
  id: string;
  name: string;
  status: StatusType;
  lastSeen: string;
  toolCount?: number;
  cpuUsage?: number;
  memoryUsage?: number;
}

interface UsageStats {
  dailyExecutions: number;
  serverLoad: number;
  resourceUsage: {
    cpu: number;
    memory: number;
    storage: number;
  };
  toolUsage: Array<{
    name: string;
    count: number;
  }>;
  lastUpdated?: string;
}

interface RecentActivity {
  id: string;
  type: ActivityType;
  message: string;
  timestamp: string;
  user?: string;
}

// Styled Components
const DashboardContainer = styled(Box)(({ theme }) => ({
  padding: theme.spacing(3),
  width: '100%',
  maxWidth: '100%',
  margin: '0 auto',
  [theme.breakpoints.up('lg')]: {
    maxWidth: 1920,
  },
}));

// Helper Components
const LoadingSkeleton: React.FC = () => (
  <Paper sx={{ p: 3 }}>
    <Skeleton variant="rectangular" height={118} />
    <Skeleton variant="text" />
    <Skeleton variant="text" width="60%" />
  </Paper>
);

const ErrorMessage: React.FC<{ message: string }> = ({ message }) => (
  <Box
    display="flex"
    flexDirection="column"
    alignItems="center"
    justifyContent="center"
    minHeight="200px"
    color="error.main"
  >
    <ErrorOutlineIcon fontSize="large" />
    <Typography variant="subtitle1" color="textSecondary" align="center">
      {message}
    </Typography>
  </Box>
);

// Helper functions
const getActivityIcon = (type: ActivityType): React.ReactElement => {
  switch (type) {
    case 'tool_run':
      return <CheckCircleOutlineIcon color="primary" />;
    case 'server_connect':
      return <CheckCircleOutlineIcon color="success" />;
    case 'template_created':
      return <CheckCircleOutlineIcon color="info" />;
    case 'error':
      return <ErrorOutlineIcon color="error" />;
    default:
      return <InfoIcon color="info" />;
  }
};

const getStatusIcon = (status: StatusType): React.ReactElement => {
  switch (status) {
    case 'online':
      return <CheckCircleOutlineIcon color="success" />;
    case 'offline':
      return <ErrorOutlineIcon color="error" />;
    case 'error':
      return <WarningAmberIcon color="warning" />;
    default:
      return <InfoIcon color="info" />;
  }
};

const getProgressColor = (value: number): 'success' | 'warning' | 'error' => {
  if (value < 50) return 'success';
  if (value < 80) return 'warning';
  return 'error';
};

// Main Component
const DashboardPage: React.FC = () => {
  const [lastUpdated, setLastUpdated] = useState<Date>(new Date());
  const [isRefreshing, setIsRefreshing] = useState(false);

  // Default data structures
  const defaultUsageStats: UsageStats = {
    dailyExecutions: 0,
    serverLoad: 0,
    resourceUsage: { cpu: 0, memory: 0, storage: 0 },
    toolUsage: []
  };

  // API Calls with proper error handling
  const {
    data: serverStatus = [],
    isLoading: isLoadingServers,
    error: serverError,
    execute: fetchServers
  } = useApiCall<ServerStatusResponse[], []>(
    async () => {
      const response = await fetch('/api/servers/status');
      if (!response.ok) throw new Error('Failed to fetch server status');
      return response.json();
    },
    { initialData: [] as ServerStatusResponse[] }
  );

  const {
    data: usageStats = defaultUsageStats,
    isLoading: isLoadingStats,
    error: statsError,
    execute: fetchStats
  } = useApiCall<UsageStats, []>(
    async () => {
      const response = await fetch('/api/usage/stats');
      if (!response.ok) throw new Error('Failed to fetch usage stats');
      return response.json();
    },
    { initialData: defaultUsageStats }
  );

  const {
    data: recentActivity = [],
    isLoading: isLoadingActivity,
    error: activityError,
    execute: fetchActivity
  } = useApiCall<RecentActivity[], []>(
    async () => {
      const response = await fetch('/api/activity/recent');
      if (!response.ok) throw new Error('Failed to fetch recent activity');
      return response.json();
    },
    { initialData: [] as RecentActivity[] }
  );

  // Derived state with safe defaults
  const isLoading = isLoadingServers || isLoadingActivity || isLoadingStats;
  const hasError = Boolean(serverError || activityError || statsError);

  const safeRecentActivity = Array.isArray(recentActivity) ? recentActivity : [];
  const safeServerStatus = Array.isArray(serverStatus) ? serverStatus : [];
  const safeUsageStats = usageStats || defaultUsageStats;

  // Calculate server statistics
  const serverStats = useMemo(() => {
    const stats = {
      online: 0,
      offline: 0,
      error: 0,
    };

    safeServerStatus.forEach(server => {
      if (server?.status === 'online') stats.online++;
      else if (server?.status === 'offline') stats.offline++;
      else if (server?.status === 'error') stats.error++;
    });

    return stats;
  }, [safeServerStatus]);

  // Refresh all data
  const refreshData = useCallback(async () => {
    setIsRefreshing(true);
    try {
      await Promise.all([
        fetchServers(),
        fetchActivity(),
        fetchStats()
      ].map(p => p.catch(e => {
        console.error('Error in refresh:', e);
        return null;
      })));
      setLastUpdated(new Date());
    } catch (error) {
      console.error('Error refreshing data:', error);
    } finally {
      setIsRefreshing(false);
    }
  }, [fetchServers, fetchActivity, fetchStats]);

  // Initial data load and auto-refresh
  useEffect(() => {
    refreshData();

    const interval = setInterval(refreshData, 30000);
    return () => clearInterval(interval);
  }, [refreshData]);

  // Loading state
  if (isLoading && !isRefreshing) {
    return (
      <DashboardContainer>
        <Grid container spacing={3}>
          {[1, 2, 3, 4].map((item) => (
            <Grid item xs={12} sm={6} lg={3} key={item}>
              <LoadingSkeleton />
            </Grid>
          ))}
        </Grid>
      </DashboardContainer>
    );
  }

  // Error state
  if (hasError) {
    const errorMessage =
      serverError?.message ||
      activityError?.message ||
      statsError?.message ||
      'An unknown error occurred';

    return (
      <DashboardContainer>
        <ErrorMessage message={errorMessage} />
        <Button
          variant="contained"
          color="primary"
          onClick={refreshData}
          disabled={isRefreshing}
          startIcon={<RefreshIcon />}
        >
          {isRefreshing ? 'Refreshing...' : 'Retry'}
        </Button>
      </DashboardContainer>
    );
  }

  // Render functions
  const renderRecentActivity = (): React.ReactElement => {
    if (isLoadingActivity) {
      return <Skeleton variant="rectangular" height={200} />;
    }

    if (activityError) {
      return <ErrorMessage message="Failed to load recent activity" />;
    }

    if (!safeRecentActivity.length) {
      return <Typography>No recent activity</Typography>;
    }

    return (
      <List>
        {safeRecentActivity.map((activity) => (
          <ListItem key={activity.id} divider>
            <ListItemIcon>
              {getActivityIcon(activity.type)}
            </ListItemIcon>
            <ListItemText
              primary={activity.message}
              secondary={`${new Date(activity.timestamp).toLocaleString()} • ${activity.user || 'System'}`}
            />
          </ListItem>
        ))}
      </List>
    );
  };

  const renderServerStatus = (): React.ReactElement => {
    if (isLoadingServers) {
      return <Skeleton variant="rectangular" height={200} />;
    }

    if (serverError) {
      return <ErrorMessage message="Failed to load server status" />;
    }

    if (!safeServerStatus.length) {
      return <Typography>No servers found</Typography>;
    }

    return (
      <List>
        {safeServerStatus.map((server) => (
          <ListItem key={server.id} divider>
            <ListItemIcon>
              {getStatusIcon(server.status)}
            </ListItemIcon>
            <ListItemText
              primary={server.name}
              secondary={
                <Box component="span">
                  <Typography component="span" variant="body2" display="block">
                    Status: {server.status}
                  </Typography>
                  <Typography component="span" variant="body2" display="block">
                    Last seen: {new Date(server.lastSeen).toLocaleString()}
                  </Typography>
                  {server.toolCount !== undefined && (
                    <Typography component="span" variant="body2">
                      • {server.toolCount} tools
                    </Typography>
                  )}
                </Box>
              }
            />
          </ListItem>
        ))}
      </List>
    );
  };

  return (
    <DashboardContainer>
      {/* Header */}
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h4" component="h1">
          Dashboard
        </Typography>
        <Box display="flex" alignItems="center" gap={2}>
          {isRefreshing && <CircularProgress size={24} />}
          <Tooltip title="Refresh data">
            <IconButton onClick={refreshData} disabled={isRefreshing}>
              <RefreshIcon />
            </IconButton>
          </Tooltip>
          <Typography variant="caption" color="textSecondary">
            Last updated: {lastUpdated.toLocaleTimeString()}
          </Typography>
        </Box>
      </Box>

      <Grid container spacing={3}>
        {/* Server Status Summary */}
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                Online Servers
              </Typography>
              <Typography variant="h4">
                {serverStats.online}
                <Typography component="span" color="textSecondary">
                  /{safeServerStatus.length || 0}
                </Typography>
              </Typography>
              <LinearProgress
                variant="determinate"
                value={safeServerStatus.length ? (serverStats.online / safeServerStatus.length) * 100 : 0}
                color={getProgressColor(safeServerStatus.length ? (serverStats.online / safeServerStatus.length) * 100 : 0)}
                sx={{ mt: 1 }}
              />
            </CardContent>
          </Card>
        </Grid>

        {/* Daily Executions */}
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                Daily Executions
              </Typography>
              <Typography variant="h4">{safeUsageStats.dailyExecutions || 0}</Typography>
              <LinearProgress
                variant="determinate"
                value={Math.min(100, safeUsageStats.dailyExecutions || 0)}
                color={getProgressColor(safeUsageStats.dailyExecutions || 0)}
                sx={{ mt: 1 }}
              />
            </CardContent>
          </Card>
        </Grid>

        {/* CPU Usage */}
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                CPU Usage
              </Typography>
              <Typography variant="h4">{safeUsageStats.resourceUsage?.cpu || 0}%</Typography>
              <LinearProgress
                variant="determinate"
                value={safeUsageStats.resourceUsage?.cpu || 0}
                color={getProgressColor(safeUsageStats.resourceUsage?.cpu || 0)}
                sx={{ mt: 1 }}
              />
            </CardContent>
          </Card>
        </Grid>

        {/* Memory Usage */}
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                Memory Usage
              </Typography>
              <Typography variant="h4">{safeUsageStats.resourceUsage?.memory || 0}%</Typography>
              <LinearProgress
                variant="determinate"
                value={safeUsageStats.resourceUsage?.memory || 0}
                color={getProgressColor(safeUsageStats.resourceUsage?.memory || 0)}
                sx={{ mt: 1 }}
              />
            </CardContent>
          </Card>
        </Grid>

        {/* Recent Activity */}
        <Grid item xs={12} lg={8}>
          <Card sx={{ mb: 3 }}>
            <CardHeader
              title="Recent Activity"
              action={
                <Button
                  size="small"
                  onClick={refreshData}
                  disabled={isRefreshing}
                  startIcon={<RefreshIcon />}
                >
                  Refresh
                </Button>
              }
            />
            <Divider />
            <CardContent>
              {renderRecentActivity()}
            </CardContent>
          </Card>
        </Grid>

        {/* Server Status */}
        <Grid item xs={12} lg={4}>
          <Card>
            <CardHeader
              title="Server Status"
              subheader={`${serverStats.online} online, ${serverStats.offline + serverStats.error} with issues`}
            />
            <Divider />
            <CardContent>
              {renderServerStatus()}
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </DashboardContainer>
  );
};

export default DashboardPage;