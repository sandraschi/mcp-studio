# MCP Studio Frontend - User Guide

## Getting Started

### Prerequisites
- Node.js 16.0.0 or later
- npm 8.0.0 or later
- MCP Studio Backend service

### Installation
1. Install the DXT package using the DXT CLI
2. Configure the required settings in the DXT configuration
3. Start the frontend service

## Configuration

### Required Environment Variables
- `REACT_APP_API_URL`: URL of the MCP Studio API server
- `PORT`: Port to run the frontend server on (default: 3000)

### Optional Configuration
- `REACT_APP_THEME`: UI theme (light/dark)
- `REACT_APP_LOGGING_LEVEL`: Logging verbosity

## Usage

### Starting the Frontend
```bash
dxt start mcp-studio-frontend
```

### Accessing the Web Interface
1. Open a web browser
2. Navigate to `http://localhost:3000` (or your configured port)
3. Log in with your credentials

## Features

### Dashboard
- View server status and health metrics
- Monitor active connections
- View recent activity

### Server Management
- Add, edit, and remove MCP servers
- View server details and status
- Start/stop servers

### Tool Execution
- Browse available tools
- Execute tools with parameters
- View execution history and results

### User Management
- User authentication
- Role-based access control
- User preferences

## Troubleshooting

### Common Issues
1. **Connection Refused**
   - Ensure the backend server is running
   - Verify the API URL is correct
   - Check network connectivity

2. **Authentication Issues**
   - Verify your credentials
   - Check session expiration
   - Ensure your account has the necessary permissions

3. **UI Rendering Problems**
   - Clear browser cache
   - Check browser compatibility
   - Verify all dependencies are installed

## Support
For additional help, please contact support@mcp-studio.com
