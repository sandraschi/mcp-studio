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
  ResourceUsage,
  ToolExecutionStats,
  ServerMetrics
} from '../../types/dashboard';

// Material-UI Components
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
  alpha
} from '@mui/material';

// Icons
import {
  PlayArrow as PlayArrowIcon,
  Refresh as RefreshIcon,
  Info as InfoIcon,
  Warning as WarningIcon,
  Error as ErrorIcon,
  CheckCircle as SuccessIcon,
  Dns as ServerIcon,
  Memory as MemoryIcon,
  Storage as StorageIcon,
  Cpu as CpuIcon,
  Timeline as TimelineIcon
} from '@mui/icons-material';

// Chart.js
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  LineElement,
  PointElement,
  Title,
  Tooltip as ChartTooltip,
  Legend,
  TimeScale,
  registerables
} from 'chart.js';
import { Line, Bar } from 'react-chartjs-2';
import 'chartjs-adapter-date-fns';
import { format, subDays } from 'date-fns';

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

// Types
type DashboardStats = {
  serverStatus: ServerStatus[];
  recentActivity: RecentActivity[];
  usageStats: UsageStats | null;
  toolStats: ToolExecutionStats | null;
};

// Utility functions
const getStatusColor = (status: StatusType) => {
  switch (status) {
    case 'online': return 'success';
    case 'error': return 'error';
    case 'offline':
    default: return 'default';
  }
};

const getActivityIcon = (type: ActivityType) => {
  switch (type) {
    case 'tool_run': return <PlayArrowIcon fontSize="small" />;
    case 'server_connect': return <ServerIcon fontSize="small" />;
    case 'template_created': return <InfoIcon fontSize="small" />;
    case 'error': return <ErrorIcon color="error" fontSize="small" />;
    default: return <InfoIcon fontSize="small" />;
  }
};

// Main component
const DashboardPage: React.FC = () => {
  const { user } = useAuth();
  const theme = useTheme();
  const navigate = useNavigate();
  
  // State
  const [lastUpdated, setLastUpdated] = useState<Date>(new Date());
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [dashboardData, setDashboardData] = useState<DashboardStats>({
    serverStatus: [],
    recentActivity: [],
    usageStats: null,
    toolStats: null
  });

  // Fetch dashboard data
  const fetchDashboardData = useCallback(async () => {
    try {
      setIsRefreshing(true);
      
      // Fetch data in parallel
      const [servers, activity, stats] = await Promise.all([
        apiService.getServers(),
        apiService.getRecentActivity(10),
        apiService.getUsageStats()
      ]);

      setDashboardData({
        serverStatus: servers,
        recentActivity: activity,
        usageStats: stats,
        toolStats: await apiService.getToolExecutionStats()
      });
      
      setLastUpdated(new Date());
    } catch (error) {
      console.error('Error fetching dashboard data:', error);
    } finally {
      setIsRefreshing(false);
    }
  }, []);

  // Initial data load
  useEffect(() => {
    fetchDashboardData();
  }, [fetchDashboardData]);

  // Refresh handler
  const handleRefresh = () => {
    fetchDashboardData();
  };

  // Chart data preparation
  const prepareChartData = () => {
    const { usageStats } = dashboardData;
    const days = 7;
    
    const labels = Array.from({ length: days }, (_, i) => 
      format(subDays(new Date(), days - i - 1), 'MMM dd')
    );

    return {
      executionData: {
        labels,
        datasets: [
          {
            label: 'Daily Executions',
            data: usageStats?.dailyExecutions || Array(days).fill(0),
            borderColor: theme.palette.primary.main,
            backgroundColor: alpha(theme.palette.primary.main, 0.1),
            tension: 0.3,
            fill: true
          }
        ]
      },
      resourceData: {
        labels: ['CPU', 'Memory', 'Storage'],
        datasets: [
          {
            label: 'Resource Usage %',
            data: [
              usageStats?.resourceUsage.cpu || 0,
              usageStats?.resourceUsage.memory || 0,
              usageStats?.resourceUsage.storage || 0
            ],
            backgroundColor: [
              theme.palette.primary.main,
              theme.palette.secondary.main,
              theme.palette.info.main
            ]
          }
        ]
      }
    };
  };

  const { executionData, resourceData } = prepareChartData();
  const { serverStatus, recentActivity, toolStats } = dashboardData;

  // Chart options
  const chartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: { display: false },
      tooltip: { mode: 'index', intersect: false }
    },
    scales: {
      y: { beginAtZero: true, max: 100 }
    }
  };

  // Render loading state
  if (isRefreshing && lastUpdated === null) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="60vh">
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Box sx={{ p: 3 }}>
      {/* Header */}
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h4" component="h1">
          Dashboard
        </Typography>
        <Button
          variant="outlined"
          startIcon={<RefreshIcon />}
          onClick={handleRefresh}
          disabled={isRefreshing}
        >
          {isRefreshing ? 'Refreshing...' : 'Refresh'}
        </Button>
      </Box>

      {/* Stats Grid */}
      <Grid container spacing={3} mb={3}>
        {/* Server Status */}
        <Grid item xs={12} md={4}>
          <Card>
            <CardHeader 
              title="Server Status" 
              avatar={<ServerIcon />}
              action={
                <Chip 
                  label={`${serverStatus.filter(s => s.status === 'online').length} Online`} 
                  color="success"
                  size="small"
                />
              }
            />
            <CardContent>
              <List dense>
                {serverStatus.map((server) => (
                  <ListItem key={server.id}>
                    <ListItemIcon>
                      <Chip
                        label={server.status}
                        color={getStatusColor(server.status)}
                        size="small"
                      />
                    </ListItemIcon>
                    <ListItemText 
                      primary={server.name} 
                      secondary={`${server.toolCount} tools`} 
                    />
                    <Chip 
                      label={`${Math.round(server.cpuUsage)}% CPU`} 
                      size="small" 
                      variant="outlined"
                      icon={<CpuIcon fontSize="small" />}
                    />
                  </ListItem>
                ))}
              </List>
            </CardContent>
          </Card>
        </Grid>

        {/* Resource Usage */}
        <Grid item xs={12} md={4}>
          <Card>
            <CardHeader 
              title="Resource Usage" 
              avatar={<MemoryIcon />}
            />
            <CardContent sx={{ height: 300 }}>
              <Bar 
                data={resourceData} 
                options={chartOptions} 
              />
            </CardContent>
          </Card>
        </Grid>

        {/* Tool Stats */}
        <Grid item xs={12} md={4}>
          <Card>
            <CardHeader 
              title="Tool Statistics" 
              avatar={<TimelineIcon />}
            />
            <CardContent>
              {toolStats ? (
                <Box>
                  <Box mb={2}>
                    <Typography variant="body2" color="text.secondary">Total Executions</Typography>
                    <Typography variant="h5">{toolStats.totalExecutions}</Typography>
                  </Box>
                  <Box mb={2}>
                    <Typography variant="body2" color="text.secondary">Success Rate</Typography>
                    <Typography variant="h5">
                      {Math.round(toolStats.successRate * 100)}%
                    </Typography>
                  </Box>
                  <Box>
                    <Typography variant="body2" color="text.secondary">Avg. Duration</Typography>
                    <Typography variant="h5">
                      {toolStats.averageDuration.toFixed(2)}s
                    </Typography>
                  </Box>
                </Box>
              ) : (
                <CircularProgress size={24} />
              )}
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Activity and Charts */}
      <Grid container spacing={3}>
        {/* Recent Activity */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardHeader 
              title="Recent Activity" 
              avatar={<TimelineIcon />}
            />
            <CardContent>
              <List dense>
                {recentActivity.map((activity) => (
                  <ListItem key={activity.id}>
                    <ListItemIcon>
                      {getActivityIcon(activity.type)}
                    </ListItemIcon>
                    <ListItemText
                      primary={activity.title}
                      secondary={`${format(new Date(activity.timestamp), 'PPpp')} • ${activity.description}`}
                      primaryTypographyProps={{
                        variant: 'body2',
                        color: activity.status === 'error' ? 'error' : 'text.primary'
                      }}
                    />
                  </ListItem>
                ))}
              </List>
            </CardContent>
          </Card>
        </Grid>

        {/* Execution Trend */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardHeader 
              title="Execution Trend" 
              subheader="Last 7 days"
              avatar={<TimelineIcon />}
            />
            <CardContent sx={{ height: 300 }}>
              <Line 
                data={executionData} 
                options={chartOptions} 
              />
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Last updated */}
      <Box mt={2} textAlign="right">
        <Typography variant="caption" color="text.secondary">
          Last updated: {lastUpdated ? format(lastUpdated, 'PPpp') : 'Never'}
        </Typography>
      </Box>
    </Box>
  );
};

export default DashboardPage;
