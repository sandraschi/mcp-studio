# MCP Studio Watchfiles Crashproofing

This directory contains crashproofing implementation for MCP Studio using watchfiles. The crashproof runner automatically detects application crashes and restarts the service with exponential backoff.

## 🚀 Quick Start

### 1. Install Dependencies
```bash
# Install watchfiles dependencies
pip install -r requirements-watchfiles.txt

# Or use the PowerShell script (Windows)
.\install-watchfiles.ps1
```

### 2. Run with Crashproofing
```bash
# Instead of: python -m uvicorn mcp_studio.main:app --host 0.0.0.0 --port 7787 --reload
python watchfiles_runner.py
```

## 📋 Features

### Automatic Crash Detection & Recovery
- Monitors MCP Studio process health
- Automatically restarts on crashes with exponential backoff
- HTTP health check integration (`/api/health` endpoint)
- Detailed crash logging and reporting

### Configurable Restart Policy
- Maximum restart attempts (default: 10)
- Exponential backoff delays (1s, 1.5s, 2.25s, etc.)
- Health check intervals (default: 30s)
- Custom restart delays and multipliers

### Comprehensive Logging
- Structured logging to console and file
- Crash reports saved to `logs/` directory
- Process statistics and uptime tracking
- JSON-formatted crash reports

## ⚙️ Configuration

### Environment Variables

#### MCP Studio Settings
- `MCP_STUDIO_HOST`: Host to bind to (default: `0.0.0.0`)
- `MCP_STUDIO_PORT`: Port to bind to (default: `7787`)
- `MCP_STUDIO_DEBUG`: Enable debug mode (default: `true`)
- `MCP_STUDIO_WORKERS`: Number of workers (default: `1`)
- `MCP_STUDIO_LOG_LEVEL`: Log level (default: `INFO`)

#### Watchfiles Settings
- `WATCHFILES_MAX_RESTARTS`: Max restart attempts (default: `10`)
- `WATCHFILES_RESTART_DELAY`: Base restart delay in seconds (default: `1.0`)
- `WATCHFILES_BACKOFF_MULTIPLIER`: Exponential backoff multiplier (default: `1.5`)
- `WATCHFILES_HEALTH_CHECK_INTERVAL`: Health check interval in seconds (default: `30`)
- `WATCHFILES_NOTIFY_ON_CRASH`: Enable crash notifications (default: `true`)

### Example Configuration
```bash
export MCP_STUDIO_HOST=127.0.0.1
export MCP_STUDIO_PORT=8000
export WATCHFILES_MAX_RESTARTS=5
export WATCHFILES_RESTART_DELAY=2.0
export WATCHFILES_HEALTH_CHECK_INTERVAL=60
python watchfiles_runner.py
```

## 📊 Monitoring & Logs

### Log Files
- **Console Output**: Real-time monitoring information
- **File Log**: `logs/mcp-studio-watchfiles.log` - All events and crashes
- **Crash Reports**: `logs/mcp-studio-crash-report-{timestamp}.json` - Detailed crash analysis

### Health Checks
The runner monitors the `/api/health` endpoint every 30 seconds (configurable). If the health check fails, it initiates a restart.

### Process Statistics
- Total uptime tracking
- Crash count and frequency
- Restart success/failure rates
- Process resource usage

## 🛑 Graceful Shutdown

The runner handles system signals properly:
- `SIGINT` (Ctrl+C): Graceful shutdown with cleanup
- `SIGTERM`: Graceful shutdown for systemd integration

## 🐧 Production Deployment

### Systemd Service
Use the provided service file for production deployment:

```bash
# Copy service file
sudo cp mcp-studio-watchfiles.service /etc/systemd/system/

# Create dedicated user
sudo useradd -r -s /bin/false mcp-studio

# Set permissions
sudo chown -R mcp-studio:mcp-studio /opt/mcp-studio

# Enable and start service
sudo systemctl enable mcp-studio-watchfiles
sudo systemctl start mcp-studio-watchfiles

# Check status
sudo systemctl status mcp-studio-watchfiles
```

### Docker Integration
For Docker deployments, the watchfiles runner can be used as a health check:

```dockerfile
# Use watchfiles runner as entrypoint
COPY watchfiles_runner.py /app/
CMD ["python", "watchfiles_runner.py"]
```

## 🧪 Testing Crashproofing

### Manual Crash Testing
```bash
# Start the runner
python watchfiles_runner.py

# In another terminal, find and kill the process
ps aux | grep uvicorn
kill -9 <uvicorn-pid>

# Watch the runner automatically restart MCP Studio
```

### Health Check Testing
```bash
# Test health endpoint
curl http://localhost:7787/api/health

# Temporarily break the health check to test restart logic
# (Modify the health endpoint to return 500 temporarily)
```

## 📈 Benefits Over Standard Deployment

### Before Watchfiles:
- ❌ Manual intervention required on crashes
- ❌ No visibility into crash patterns
- ❌ Development downtime during debugging
- ❌ Production instability

### After Watchfiles:
- ✅ Zero-touch crash recovery
- ✅ Detailed crash analytics and reporting
- ✅ Improved development workflow
- ✅ Production-grade stability before dockerization

## 🔧 Troubleshooting

### Common Issues

#### "Module 'watchfiles' not found"
```bash
pip install -r requirements-watchfiles.txt
```

#### "Permission denied" on log files
```bash
mkdir -p logs
chmod 755 logs
```

#### Health checks failing
- Verify `/api/health` endpoint is working
- Check network connectivity
- Adjust `WATCHFILES_HEALTH_CHECK_INTERVAL`

#### Process not restarting
- Check system resource limits
- Verify uvicorn command is correct
- Check application logs for startup errors

### Debug Mode
Enable debug logging:
```bash
export MCP_STUDIO_LOG_LEVEL=DEBUG
python watchfiles_runner.py
```

## 📚 Related Files

- `watchfiles_runner.py` - Main crashproof runner implementation
- `requirements-watchfiles.txt` - Required dependencies
- `install-watchfiles.ps1` - Windows installation script
- `mcp-studio-watchfiles.service` - Systemd service template
- `logs/mcp-studio-watchfiles.log` - Runtime logs
- `logs/mcp-studio-crash-report-*.json` - Crash analysis reports

## 🔄 Migration to Docker

When ready to dockerize:

1. **Keep watchfiles logic** as container health check
2. **Use Docker restart policies** (`restart: unless-stopped`)
3. **Convert health checks** to Docker HEALTHCHECK
4. **Mount logs directory** for persistent crash reports

Example docker-compose.yml:
```yaml
version: '3.8'
services:
  mcp-studio:
    build: .
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:7787/api/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
    volumes:
      - ./logs:/app/logs
```

## 🤝 Contributing

When modifying the crashproof runner:

1. Test crash scenarios thoroughly
2. Update logging for new features
3. Document new configuration options
4. Add appropriate error handling
5. Update this README

## 📞 Support

For issues with crashproofing:

1. Check `logs/mcp-studio-watchfiles.log` for errors
2. Review crash reports in `logs/` directory
3. Verify environment variable configuration
4. Test health endpoint manually
5. Check system resource usage

---

**Note**: This crashproofing solution provides production-grade stability while maintaining development flexibility. It's designed as a stopgap before full containerization and can be easily migrated to Docker/Kubernetes deployments.
