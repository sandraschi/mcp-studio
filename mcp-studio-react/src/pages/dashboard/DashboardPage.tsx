import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';
import { useApiCall } from '../../hooks/useApiCall';
import { apiService } from '../../services/api/api.service';
import type { 
  ServerStatus, 
  RecentActivity, 
  UsageStats,
  ActivityType,
  StatusType,
  ResourceUsage
} from '../../types/dashboard';

// Import MUI components
import {
  Box, 
  Button,
  Card, 
  CardContent, 
  CardHeader,
  Chip,
  CircularProgress, 
  Divider,
  Grid, 
  IconButton,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Paper,
  Typography, 
  useTheme,
} from '@mui/material';

// Import MUI Icons
import { 
  PlayArrow as PlayArrowIcon,
  Stop as StopIcon,
  Refresh as RefreshIcon,
  Info as InfoIcon,
  Warning as WarningIcon,
  Error as ErrorIcon,
  CheckCircle as SuccessIcon,
  Code as TemplateIcon,
  History as HistoryIcon,
  Dns as ServerIcon,
  Settings as SettingsIcon,
  Build as ToolIcon,
} from '@mui/icons-material';

// Import Chart.js components
import { Bar, Line } from 'react-chartjs-2';
import { 
  Chart as ChartJS, 
  CategoryScale, 
  LinearScale, 
  BarElement, 
  LineElement, 
  PointElement, 
  Title, 
  Tooltip as ChartTooltip, 
  TimeScale,
  ChartData,
  ChartOptions,
  registerables 
} from 'chart.js';
import 'chartjs-adapter-date-fns';
import { formatDistanceToNow } from 'date-fns';

// Register Chart.js components
ChartJS.register(
  CategoryScale,
  LinearScale,
  BarElement,
  LineElement,
  PointElement,
  Title,
  ChartTooltip,
  Legend,
  TimeScale,
  ...registerables
);

// Fix for Tooltip component conflict
declare module 'chart.js' {
  interface TooltipPositionerMap {
    myCustomPositioner: any;
  }
}

// Types
interface ServerStatus {
  status: 'ONLINE' | 'OFFLINE' | 'ERROR';
  lastActive: string;
  cpuLoad?: number;
  memoryUsage?: number;
  toolCount?: number;
}

interface Server {
  id: string;
  name: string;
  status: ServerStatus;
  lastActive: Date;
  toolCount: number;
}

const DashboardPage: React.FC = () => {
  const { user } = useAuth();
  const navigate = useNavigate();
  const theme = useTheme();
  
  // State with proper types
  const [lastUpdated, setLastUpdated] = useState<Date>(new Date());
  const [servers, setServers] = useState<Server[]>([]);
  const [usageStats, setUsageStats] = useState<UsageStats | null>(null);
  const [recentActivity, setRecentActivity] = useState<RecentActivity[] | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  
  // Fetch server status
  const {
    data: serverStatus = [],
    isLoading: isLoadingServers,
    error: serverError,
    execute: fetchServers,
  } = useApiCall<Server[]>(() => apiService.getServers(), {
    initialData: [],
    onSuccess: () => setLastUpdated(new Date()),
  });
  
  // Get recent activity with proper typing and null check
  const getRecentActivity = (): Array<RecentActivity & { icon: JSX.Element }> => {
    if (!recentActivity || !Array.isArray(recentActivity)) return [];
    return recentActivity.map((activity) => ({
      ...activity,
      icon: getActivityIcon(activity.type)
    }));
  };

  // Fetch recent activity
  const {
    data: recentActivity = [],
    isLoading: isLoadingActivity,
    error: activityError,
    execute: fetchActivity,
  } = useApiCall<RecentActivity[]>(() => 
    apiService.getRecentExecutions(10).then(executions => 
      executions.map(exec => ({
        id: exec.id,
        type: 'tool_run' as const,
        title: `Tool execution: ${exec.toolName}`,
        description: `Status: ${exec.status}`,
        timestamp: new Date(exec.startedAt).toISOString(),
        status: exec.status === 'completed' ? 'success' : 
                exec.status === 'failed' ? 'error' : 'info'
      }))
    ), {
    initialData: [],
  });
  
  // Fetch usage statistics
  const {
    data: fetchedStats,
    isLoading: isLoadingStats,
    error: statsError,
    execute: fetchStats,
  } = useApiCall<UsageStats>(async () => {
    // Mock data - replace with actual API call
    const serverStatus = await apiService.getServerStatus();
    const servers = Object.values(serverStatus);
    
    return {
      dailyExecutions: Array(7).fill(0).map(() => Math.floor(Math.random() * 100)),
      serverLoad: servers.map(s => s.cpuLoad || 0),
      resourceUsage: {
        cpu: servers.reduce((sum, s) => sum + (s.cpuLoad || 0), 0) / (servers.length || 1),
        memory: servers.reduce((sum, s) => sum + (s.memoryUsage || 0), 0) / (servers.length || 1),
        storage: 0 // Not available in server status
      }
    };
  }, {
  });
  
  // Refresh all data
  const refreshData = useCallback(async () => {
    setIsRefreshing(true);
    try {
      await Promise.all([fetchServers(), fetchActivity(), fetchStats()]);
      setLastUpdated(new Date());
    } catch (error) {
      console.error('Error refreshing data:', error);
    } finally {
      setIsRefreshing(false);
    }
  }, [fetchServers, fetchActivity, fetchStats]);
  
  // Initial data fetch
  useEffect(() => {
    refreshData();
    // Set up auto-refresh every 30 seconds
    const interval = setInterval(refreshData, 30000);
    return () => clearInterval(interval);
  }, [refreshData]);
  
  // Chart data for daily runs
  const dailyRunsData: ChartData<'line', number[], string> = {
    labels: Array.from({ length: 7 }, (_, i) => {
      const d = new Date();
      d.setDate(d.getDate() - (6 - i));
      return d.toLocaleDateString('en-US', { weekday: 'short' });
    }),
    datasets: [
      {
        label: 'Tool Executions',
        data: usageStats?.dailyExecutions?.length ? usageStats.dailyExecutions : [0, 0, 0, 0, 0, 0, 0],
        borderColor: theme.palette.primary.main,
        backgroundColor: 'rgba(75, 192, 192, 0.2)',
        tension: 0.3,
        fill: true,
      },
    ],
  };
  
  // Chart options for daily runs
  const dailyRunsOptions: ChartOptions<'line'> = {
    responsive: true,
    plugins: {
      legend: {
        display: false,
      },
      title: {
        display: true,
        text: 'Tool Executions (Last 7 Days)',
      },
    },
    scales: {
      y: {
        beginAtZero: true,
        ticks: {
          stepSize: 1,
        },
      },
    },
  };
  
  // Chart data for tool usage
  const toolUsageData = {
    labels: ['API Calls', 'Tool Executions', 'Server Requests'],
    datasets: [
      {
        label: 'Usage Count',
        data: [
          usageStats?.dailyExecutions?.reduce((a, b) => a + b, 0) || 0,
          usageStats?.serverLoad?.reduce((a, b) => a + b, 0) || 0,
          (usageStats?.resourceUsage?.cpu || 0) * 100
        ],
        backgroundColor: [
          'rgba(54, 162, 235, 0.5)',
          'rgba(75, 192, 192, 0.5)',
          'rgba(153, 102, 255, 0.5)'
        ],
        borderColor: [
          'rgba(54, 162, 235, 1)',
          'rgba(75, 192, 192, 1)',
          'rgba(153, 102, 255, 1)'
        ],
        borderWidth: 1,
      },
    ],
  };

  // Chart options for tool usage
  const toolUsageOptions: ChartOptions<'bar'> = {
    responsive: true,
    plugins: {
      legend: {
        display: false,
      },
      title: {
        display: true,
        text: 'Most Used Tools',
      },
    },
    scales: {
      y: {
        beginAtZero: true,
        ticks: {
          stepSize: 1,
        },
      },
    },
  };

  // Get status icon for activity item
  const getStatusIcon = (status?: string) => {
    switch (status) {
      case 'success':
        return <SuccessIcon color="success" fontSize="small" />;
      case 'error':
        return <ErrorIcon color="error" fontSize="small" />;
      case 'warning':
        return <WarningIcon color="warning" fontSize="small" />;
      case 'info':
      default:
        return <InfoIcon color="info" fontSize="small" />;
    }
  };

  // Get activity icon with proper type
  const getActivityIcon = (type: ActivityType) => {
    switch (type) {
      case 'tool_run':
        return <ToolIcon />;
      case 'server_connect':
        return <ServerIcon />;
      case 'template_created':
        return <TemplateIcon />;
      case 'error':
        return <ErrorIcon color="error" />;
      default:
        return <InfoIcon />;
    }
  };

  // Icons
  const RunIcon = PlayArrowIcon;

  // Handle refresh
  const handleRefresh = useCallback(() => {
    setIsRefreshing(true);
    Promise.all([
      fetchServers(),
      fetchActivity(),
      fetchStats()
    ]).finally(() => {
      setIsRefreshing(false);
      setLastUpdated(new Date());
    });
  }, [fetchServers, fetchActivity, fetchStats]);

  // Initial data load
  useEffect(() => {
    handleRefresh();
  }, [handleRefresh]);

  // Get status color with proper type
  const getStatusChip = (status: StatusType) => {
    switch (status) {
      case 'online':
        return <Chip label="Online" color="success" size="small" />;
      case 'offline':
        return <Chip label="Offline" color="default" size="small" />;
      case 'error':
        return <Chip label="Error" color="error" size="small" />;
      default:
        return <Chip label="Unknown" size="small" />;
    }
  };

  // Get resource usage data with proper typing
  const getResourceUsageData = (): ResourceUsage => {
    if (!usageStats?.resourceUsage) {
      return { cpu: 0, memory: 0, storage: 0 };
    }
    return {
      cpu: usageStats.resourceUsage.cpu || 0,
      memory: usageStats.resourceUsage.memory || 0,
      storage: usageStats.resourceUsage.storage || 0,
    };
  };
  
  // Get the current resource usage
  const resourceUsage = getResourceUsageData();
  
  // Get the server status data with null check
  const serverStatusData = serverStatus ? getServerStatus() : [];
  
  // Get the recent activity data with null check
  const recentActivityData = recentActivity ? getRecentActivity() : [];

  // Get server status with proper type and null check
  const getServerStatus = (): ServerStatus[] => {
    if (!serverStatus || !Array.isArray(serverStatus) || serverStatus.length === 0) {
      return [];
    }
    return serverStatus.map((server: any) => ({
      id: server.id || '',
      name: server.name || 'Unknown Server',
      status: (server.status as StatusType) || 'offline',
      lastSeen: new Date().toISOString(),
      toolCount: 0, // Will be populated from API
      cpuUsage: 0,  // Will be populated from API
      memoryUsage: 0, // Will be populated from API
    }));
  };

  // Calculate server statistics
  const totalServers = serverStatus?.length || 0;
  const onlineServers = serverStatus?.filter((s: ServerStatus) => s.status === 'online').length || 0;
  const offlineServers = totalServers - onlineServers;
  const totalTools = serverStatus?.reduce((sum: number, server: ServerStatus) => sum + (server.toolCount || 0), 0) || 0;

  
  return (
    <Box sx={{ flexGrow: 1 }}>
      {/* Header */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Box>
          <Typography variant="h4" component="h1" gutterBottom>
            Welcome back, {user?.firstName || user?.username || 'User'}!
          </Typography>
          <Typography variant="body1" color="text.secondary">
            Here's what's happening with your MCP Studio instance.
          </Typography>
        </Box>
        <Box>
          <Button
            variant="outlined"
            startIcon={<RefreshIcon />}
            onClick={refreshData}
            disabled={isRefreshing}
          >
            {isRefreshing ? 'Refreshing...' : 'Refresh'}
          </Button>
        </Box>
      </Box>
      
      {/* Stats Overview */}
      <Grid container spacing={3} sx={{ mb: 3 }}>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <Box>
                  <Typography color="text.secondary" gutterBottom>Total Servers</Typography>
                  <Typography variant="h4">{totalServers}</Typography>
                </Box>
                <ServerIcon color="primary" sx={{ fontSize: 40, opacity: 0.8 }} />
              </Box>
              <Box sx={{ mt: 2 }}>
                <Typography variant="body2" color="text.secondary">
                  {onlineServers} online, {offlineServers} offline
                </Typography>
              </Box>
            </CardContent>
          </Card>
        </Grid>
        
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <Box>
                  <Typography color="text.secondary" gutterBottom>Available Tools</Typography>
                  <Typography variant="h4">{totalTools}</Typography>
                </Box>
                <ToolIcon color="primary" sx={{ fontSize: 40, opacity: 0.8 }} />
              </Box>
              <Box sx={{ mt: 2 }}>
                <Button 
                  size="small" 
                  startIcon={<PlayArrowIcon />}
                  onClick={() => navigate('/tools')}
                >
                  Run Tool
                </Button>
              </Box>
            </CardContent>
          </Card>
        </Grid>
        
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <Box>
                  <Typography color="text.secondary" gutterBottom>Recent Activity</Typography>
                  <Typography variant="h4">
                    {recentActivity.length}
                  </Typography>
                </Box>
                <HistoryIcon color="primary" sx={{ fontSize: 40, opacity: 0.8 }} />
              </Box>
              <Box sx={{ mt: 2 }}>
                <Typography variant="body2" color="text.secondary">
                  Last updated {formatDistanceToNow(lastUpdated, { addSuffix: true })}
                </Typography>
              </Box>
            </CardContent>
          </Card>
        </Grid>
        
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <Box>
                  <Typography color="text.secondary" gutterBottom>System Status</Typography>
                  <Typography variant="h4">
                    {serverError ? 'Error' : 'Operational'}
                  </Typography>
                </Box>
                <SettingsIcon color={serverError ? 'error' : 'primary'} sx={{ fontSize: 40, opacity: 0.8 }} />
              </Box>
              <Box sx={{ mt: 2 }}>
                <Typography variant="body2" color={serverError ? 'error' : 'success.main'}>
                  {serverError ? 'Connection issues detected' : 'All systems normal'}
                </Typography>
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
      
      {/* Main Content */}
      <Grid container spacing={3}>
        {/* Left Column */}
        <Grid item xs={12} lg={8}>
          {/* Activity Chart */}
          <Card sx={{ mb: 3 }}>
            <CardHeader 
              title="Activity Overview" 
              action={
                <Button 
                  size="small" 
                  onClick={() => navigate('/activity')}
                  endIcon={<RefreshIcon />}
                  disabled={isRefreshing}
                >
                  View All
                </Button>
              } 
            />
            <CardContent sx={{ height: 300 }}>
              {isLoadingStats ? (
                <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100%' }}>
                  <CircularProgress />
                </Box>
              ) : (
                <Line data={dailyRunsData} options={dailyRunsOptions} />
              )}
            </CardContent>
          </Card>
          
          {/* Recent Activity */}
          <Card>
            <CardHeader 
              title="Recent Activity" 
              action={
                <Button 
                  size="small" 
                  onClick={() => navigate('/activity')}
                  endIcon={<RefreshIcon />}
                  disabled={isRefreshing}
                >
                  View All
                </Button>
              } 
            />
            <CardContent>
              {isLoadingActivity ? (
                <Box sx={{ display: 'flex', justifyContent: 'center', p: 3 }}>
                  <CircularProgress />
                </Box>
              ) : recentActivity.length > 0 ? (
                <List disablePadding>
                  {recentActivity.slice(0, 5).map((activity, index) => (
                    <React.Fragment key={activity.id}>
                      <Box 
                        sx={{ 
                          display: 'flex', 
                          alignItems: 'center',
                          py: 1.5,
                          px: 1,
                          '&:hover': {
                            backgroundColor: 'action.hover',
                            borderRadius: 1,
                          },
                        }}
                      >
                        <Box sx={{ mr: 2, display: 'flex', alignItems: 'center' }}>
                          {getStatusIcon(activity.status)}
                        </Box>
                        <Box sx={{ flexGrow: 1, minWidth: 0 }}>
                          <Typography variant="subtitle2" noWrap>
                            {activity.title}
                          </Typography>
                          <Typography variant="body2" color="text.secondary" noWrap>
                            {activity.description}
                          </Typography>
                        </Box>
                        <Box sx={{ ml: 2, textAlign: 'right' }}>
                          <Typography variant="caption" color="text.secondary">
                            {formatDistanceToNow(new Date(activity.timestamp), { addSuffix: true })}
                          </Typography>
                        </Box>
                      </Box>
                      {index < Math.min(4, recentActivity.length - 1) && <Divider />}
                    </React.Fragment>
                  ))}
                </List>
              ) : (
                <Box sx={{ textAlign: 'center', p: 3 }}>
                  <Typography variant="body2" color="text.secondary">
                    No recent activity found.
                  </Typography>
                </Box>
              )}
            </CardContent>
          </Card>
        </Grid>
        
        {/* Right Column */}
        <Grid item xs={12} lg={4}>
          {/* Server Status */}
          <Card sx={{ mb: 3 }}>
            <CardHeader 
              title="Server Status" 
              action={
                <IconButton 
                  size="small" 
                  onClick={() => fetchServers()} 
                  disabled={isRefreshing || isLoadingServers}
                >
                  <RefreshIcon fontSize="small" />
                </IconButton>
              } 
            />
            <CardContent>
              {isLoadingServers ? (
                <Box sx={{ display: 'flex', justifyContent: 'center', p: 3 }}>
                  <CircularProgress size={24} />
                </Box>
              ) : serverStatus.length > 0 ? (
                <List disablePadding>
                  {serverStatus.map((server, index) => (
                    <React.Fragment key={server.id}>
                      <Box 
                        sx={{ 
                          display: 'flex', 
                          alignItems: 'center',
                          justifyContent: 'space-between',
                          py: 1.5,
                          px: 1,
                          '&:hover': {
                            backgroundColor: 'action.hover',
                            borderRadius: 1,
                          },
                        }}
                      >
                        <Box sx={{ display: 'flex', alignItems: 'center', minWidth: 0 }}>
                          <ServerIcon 
                            sx={{ 
                              mr: 1.5, 
                              color: server.status === 'online' ? 'success.main' : 'text.secondary',
                            }} 
                          />
                          <Box sx={{ minWidth: 0 }}>
                            <Typography variant="subtitle2" noWrap>
                              {server.name}
                            </Typography>
                            <Box sx={{ display: 'flex', alignItems: 'center', mt: 0.5 }}>
                              <Typography variant="caption" color="text.secondary" noWrap>
                                {server.toolCount} tools • {formatDistanceToNow(new Date(server.lastSeen), { addSuffix: true })}
                              </Typography>
                            </Box>
                          </Box>
                        </Box>
                        <Box sx={{ ml: 1 }}>
                          {getStatusChip(server.status)}
                        </Box>
                      </Box>
                      {index < serverStatus.length - 1 && <Divider />}
                    </React.Fragment>
                  ))}
                </List>
              ) : (
                <Box sx={{ textAlign: 'center', p: 3 }}>
                  <Typography variant="body2" color="text.secondary">
                    No servers found. Add a server to get started.
                  </Typography>
                  <Button 
                    variant="outlined" 
                    size="small" 
                    sx={{ mt: 2 }}
                    onClick={() => navigate('/servers')}
                  >
                    Add Server
                  </Button>
                </Box>
              )}
            </CardContent>
          </Card>
          
          {/* Tool Usage */}
          <Card>
            <CardHeader 
              title="Tool Usage" 
              action={
                <Button 
                  size="small" 
                  onClick={() => navigate('/tools')}
                  endIcon={<RefreshIcon />}
                  disabled={isRefreshing}
                >
                  View All
                </Button>
              } 
            />
            <CardContent sx={{ height: 300 }}>
              {isLoadingStats ? (
                <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100%' }}>
                  <CircularProgress />
                </Box>
              ) : usageStats.toolUsage.length > 0 ? (
                <Bar data={toolUsageData} options={toolUsageOptions} />
              ) : (
                <Box sx={{ textAlign: 'center', p: 3 }}>
                  <Typography variant="body2" color="text.secondary">
                    No tool usage data available.
                  </Typography>
                  <Button 
                    variant="outlined" 
                    size="small" 
                    sx={{ mt: 2 }}
                    onClick={() => navigate('/tools')}
                  >
                    Explore Tools
                  </Button>
                </Box>
              )}
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
};

export default DashboardPage;
