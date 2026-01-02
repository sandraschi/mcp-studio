import React from 'react';
import { Link } from 'react-router-dom';
import { Box, Button, Container, Typography, Grid, Paper, useTheme } from '@mui/material';
import { styled } from '@mui/material/styles';
import {
  Code as CodeIcon,
  Storage as ServerIcon,
  Settings as SettingsIcon,
  RocketLaunch as RocketIcon,
  Security as SecurityIcon,
  Api as ApiIcon,
} from '@mui/icons-material';

const FeatureCard = styled(Paper)(({ theme }) => ({
  padding: theme.spacing(3),
  height: '100%',
  display: 'flex',
  flexDirection: 'column',
  alignItems: 'center',
  textAlign: 'center',
  transition: 'transform 0.2s, box-shadow 0.2s',
  '&:hover': {
    transform: 'translateY(-4px)',
    boxShadow: theme.shadows[8],
  },
}));

const FeatureIcon = styled('div')(({ theme }) => ({
  width: 64,
  height: 64,
  borderRadius: '50%',
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'center',
  marginBottom: theme.spacing(2),
  color: theme.palette.primary.contrastText,
  backgroundColor: theme.palette.primary.main,
  '& svg': {
    fontSize: 32,
  },
}));

const features = [
  {
    icon: <ServerIcon />,
    title: 'MCP Server Management',
    description: 'Easily manage multiple MCP servers from a single interface with real-time status updates and health monitoring.',
  },
  {
    icon: <CodeIcon />,
    title: 'Tool Execution',
    description: 'Execute tools across your MCP servers with a user-friendly interface and monitor execution in real-time.',
  },
  {
    icon: <SettingsIcon />,
    title: 'Configuration',
    description: 'Centralized configuration management for all your MCP servers and tools.',
  },
  {
    icon: <RocketIcon />,
    title: 'High Performance',
    description: 'Optimized for speed and efficiency, even with a large number of tools and servers.',
  },
  {
    icon: <SecurityIcon />,
    title: 'Secure',
    description: 'Built with security in mind, featuring authentication and role-based access control.',
  },
  {
    icon: <ApiIcon />,
    title: 'Powerful API',
    description: 'RESTful API for programmatic access and integration with other tools and systems.',
  },
];

const HomePage: React.FC = () => {
  const theme = useTheme();

  return (
    <Box sx={{ flexGrow: 1 }}>
      {/* Hero Section */}
      <Box 
        sx={{
          bgcolor: theme.palette.primary.main,
          color: theme.palette.primary.contrastText,
          py: 12,
          mb: 8,
        }}
      >
        <Container maxWidth="lg">
          <Box sx={{ textAlign: 'center', maxWidth: 800, mx: 'auto' }}>
            <Typography 
              variant="h2" 
              component="h1" 
              gutterBottom 
              sx={{ 
                fontWeight: 700,
                mb: 3,
                [theme.breakpoints.down('sm')]: {
                  fontSize: '2.5rem',
                },
              }}
            >
              MCP Studio
            </Typography>
            <Typography 
              variant="h5" 
              component="p" 
              sx={{ 
                mb: 5,
                opacity: 0.9,
                [theme.breakpoints.down('sm')]: {
                  fontSize: '1.1rem',
                },
              }}
            >
              A powerful interface for managing and interacting with MCP servers and tools.
              Streamline your workflow and boost productivity with our intuitive platform.
            </Typography>
            <Box sx={{ display: 'flex', gap: 2, justifyContent: 'center', flexWrap: 'wrap' }}>
              <Button 
                component={Link} 
                to="/register" 
                variant="contained" 
                color="secondary" 
                size="large"
                sx={{ 
                  px: 4,
                  py: 1.5,
                  fontWeight: 600,
                }}
              >
                Get Started
              </Button>
              <Button 
                component={Link} 
                to="/login" 
                variant="outlined" 
                color="inherit"
                size="large"
                sx={{ 
                  px: 4,
                  py: 1.5,
                  fontWeight: 600,
                  borderColor: 'rgba(255, 255, 255, 0.5)',
                  '&:hover': {
                    borderColor: 'rgba(255, 255, 255, 0.75)',
                    backgroundColor: 'rgba(255, 255, 255, 0.08)',
                  },
                }}
              >
                Sign In
              </Button>
            </Box>
          </Box>
        </Container>
      </Box>

      {/* Features Section */}
      <Container maxWidth="lg" sx={{ mb: 12 }}>
        <Typography 
          variant="h3" 
          component="h2" 
          align="center" 
          gutterBottom
          sx={{ 
            fontWeight: 600,
            mb: 6,
            [theme.breakpoints.down('sm')]: {
              fontSize: '2rem',
              mb: 4,
            },
          }}
        >
          Powerful Features
        </Typography>
        
        <Grid container spacing={4}>
          {features.map((feature, index) => (
            <Grid item xs={12} sm={6} md={4} key={index}>
              <FeatureCard elevation={3}>
                <FeatureIcon>
                  {feature.icon}
                </FeatureIcon>
                <Typography variant="h5" component="h3" gutterBottom sx={{ fontWeight: 600 }}>
                  {feature.title}
                </Typography>
                <Typography variant="body1" color="text.secondary">
                  {feature.description}
                </Typography>
              </FeatureCard>
            </Grid>
          ))}
        </Grid>
      </Container>

      {/* CTA Section */}
      <Box 
        sx={{
          bgcolor: theme.palette.grey[100],
          py: 8,
        }}
      >
        <Container maxWidth="md" sx={{ textAlign: 'center' }}>
          <Typography 
            variant="h3" 
            component="h2" 
            gutterBottom
            sx={{ 
              fontWeight: 600,
              mb: 3,
              [theme.breakpoints.down('sm')]: {
                fontSize: '2rem',
              },
            }}
          >
            Ready to get started?
          </Typography>
          <Typography 
            variant="h6" 
            color="text.secondary" 
            sx={{ 
              mb: 4,
              maxWidth: 600,
              mx: 'auto',
              [theme.breakpoints.down('sm')]: {
                fontSize: '1.1rem',
              },
            }}
          >
            Join thousands of developers and teams who use MCP Studio to streamline their MCP server management.
          </Typography>
          <Button 
            component={Link} 
            to="/register" 
            variant="contained" 
            color="primary" 
            size="large"
            sx={{ 
              px: 5,
              py: 1.5,
              fontWeight: 600,
              fontSize: '1.1rem',
            }}
          >
            Create Free Account
          </Button>
        </Container>
      </Box>
    </Box>
  );
};

export default HomePage;