# 🐳 MCP Studio Docker Deployment Guide

**Important**: This Docker setup is for the **web dashboard only**. The MCP server mode should **NEVER** be containerized (see [Containerization Guidelines](docs/mcp-technical/CONTAINERIZATION_GUIDELINES.md)).

---

## Quick Start

### Prerequisites

- Docker and Docker Compose installed
- Ollama running (optional, for AI features)
- Repos directory accessible

### Basic Usage

**Recommended: Use the automated script** (handles cleanup automatically):
```powershell
cd d:\Dev\repos\mcp-studio
.\mcp-studio-docker\docker-start.ps1
```

**Or manually**:

1. **Set your repos directory** (Windows example):
   ```powershell
   # IMPORTANT: Set REPOS_DIR BEFORE running docker compose
   $env:REPOS_DIR = "D:/Dev/repos"
   
   # Verify the path exists
   Test-Path $env:REPOS_DIR
   
   # Always clean up first!
   docker compose down
   
   # Build and start
   docker compose build
   docker compose up -d
   
   # Verify the mount worked
   docker compose exec mcp-studio ls /app/repos
   ```
   
   **⚠️ Critical**: The `REPOS_DIR` environment variable must be set **before** running `docker compose up`, otherwise the volume mount will use the default path or fail.

2. **Or use .env file**:
   ```env
   REPOS_DIR=D:/Dev/repos
   PORT=8001
   OLLAMA_URL=http://host.docker.internal:11434
   ```
   Then:
   ```powershell
   docker compose down
   docker compose build
   docker compose up -d
   ```

3. **Access the dashboard**:
   ```
   http://localhost:8001
   ```

**⚠️ Important**: Always run `docker compose down` before rebuilding to avoid stale containers and port conflicts!

---

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `REPOS_DIR` | `D:/Dev/repos` | Path to your MCP repositories directory |
| `PORT` | `8001` | Port for the web dashboard |
| `OLLAMA_URL` | `http://host.docker.internal:11434` | Ollama API URL (optional) |

### Volume Mounts

The `docker-compose.yml` mounts:

1. **Repos Directory** (`${REPOS_DIR}:/app/repos:rw`)
   - **Full read-write access** required for:
     - Scanning repository structure
     - Reading files for analysis
     - Executing MCP tools from repos
     - Accessing configuration files
   - **Windows paths**: Use forward slashes (`D:/Dev/repos`) or escaped backslashes
   - **Linux/Mac paths**: Use standard paths (`/home/user/repos`)

2. **Logs Directory** (`./logs:/app/logs`)
   - Persistent log storage

3. **Data Directory** (`./data:/app/data`)
   - Preprompts database
   - Persistent application data

---

## Ollama Integration (Tricky Part)

The local LLM interface can be configured in several ways:

### Option 1: Ollama on Host (Recommended for Windows/Mac)

**Default configuration** - Ollama runs on your host machine:

```yaml
environment:
  - OLLAMA_URL=http://host.docker.internal:11434
```

**Requirements**:
- Ollama must be running on host: `ollama serve`
- Docker Desktop must support `host.docker.internal` (default on Windows/Mac)
- On Linux, may need `--network=host` or `extra_hosts` configuration

### Option 2: Ollama in Docker

Uncomment the Ollama service in `docker-compose.yml`:

```yaml
services:
  ollama:
    image: ollama/ollama:latest
    container_name: ollama
    ports:
      - "11434:11434"
    volumes:
      - ollama_data:/root/.ollama
    networks:
      - mcp-studio-network

  mcp-studio:
    environment:
      - OLLAMA_URL=http://ollama:11434
```

**Note**: This requires significant disk space for models and may be slower than host Ollama.

### Option 3: Ollama on Network

If Ollama runs on another machine:

```yaml
environment:
  - OLLAMA_URL=http://192.168.1.100:11434
```

### Option 4: No Ollama (Disable AI Features)

Set empty URL to disable AI features:

```yaml
environment:
  - OLLAMA_URL=
```

The dashboard will work but AI assistant features will be unavailable.

---

## Windows-Specific Notes

### Path Format

**Use forward slashes** in docker-compose.yml:
```yaml
volumes:
  - "D:/Dev/repos:/app/repos:rw"  # ✅ Correct
  - "D:\Dev\repos:/app/repos:rw"  # ❌ May not work
```

### Drive Access

Docker Desktop on Windows can access all drives by default. If you have issues:

1. **Docker Desktop Settings** → **Resources** → **File Sharing**
2. Ensure your drive (e.g., `D:`) is shared
3. Restart Docker Desktop

### PowerShell Environment Variables

```powershell
# Set for current session
$env:REPOS_DIR = "D:/Dev/repos"
docker-compose up -d

# Or use .env file (recommended)
```

---

## Linux-Specific Notes

### Host Network Mode (Alternative)

If `host.docker.internal` doesn't work, use host network:

```yaml
services:
  mcp-studio:
    network_mode: "host"
    # Remove ports mapping when using host network
    # ports:
    #   - "8001:8001"
    environment:
      - OLLAMA_URL=http://localhost:11434
```

**Warning**: This removes network isolation but simplifies Ollama access.

---

## Troubleshooting

### Stale Containers / Port Conflicts

**Problem**: Port already in use or stale containers running

**Solution**:
```powershell
# Stop and remove all containers
docker compose down

# Verify nothing is using the port
netstat -ano | findstr :8001

# Start fresh
docker compose up -d
```

**Prevention**: Always run `docker compose down` before rebuilding, or use `mcp-studio-docker\docker-start.ps1` which handles cleanup automatically.

### Repos Not Accessible

**Problem**: Dashboard can't see repositories - shows `/app/repos` but it's empty

**Solutions**:
1. **Verify REPOS_DIR is set before starting**:
   ```powershell
   # Check if it's set
   echo $env:REPOS_DIR
   
   # Set it if missing
   $env:REPOS_DIR = "D:/Dev/repos"
   
   # Restart container
   docker compose down
   docker compose up -d
   ```

2. **Check volume mount is working**:
   ```powershell
   # Verify mount
   docker inspect mcp-studio --format='{{range .Mounts}}{{.Source}} -> {{.Destination}}{{"\n"}}{{end}}'
   
   # Check contents inside container
   docker compose exec mcp-studio ls -la /app/repos
   ```

3. **Use the verification script**:
   ```powershell
   .\mcp-studio-docker\docker-verify-mount.ps1
   ```

4. **Check volume mount path format** (use forward slashes: `D:/Dev/repos`)

5. **Verify Docker Desktop file sharing settings**:
   - Docker Desktop → Settings → Resources → File Sharing
   - Ensure your drive (D:) is shared
   - Restart Docker Desktop if needed

6. **Check container logs**: `docker compose logs mcp-studio`

### Ollama Connection Failed

**Problem**: AI features not working

**Solutions**:
1. **Check Ollama is running**: `ollama serve` on host
2. **Test connection**: `curl http://localhost:11434/api/tags`
3. **Verify OLLAMA_URL**: Check container environment: `docker exec mcp-studio env | grep OLLAMA`
4. **Try host.docker.internal**: `curl http://host.docker.internal:11434/api/tags` from container
5. **Check firewall**: Ensure port 11434 is accessible

### Permission Issues

**Problem**: Can't read/write to repos

**Solutions**:
1. Check volume mount permissions
2. Ensure repos directory is readable
3. On Linux, may need to adjust user/group IDs in Dockerfile

---

## Best Practices

### Always Clean Up Before Rebuilding

**Important**: Always stop and remove existing containers before rebuilding to avoid stale containers and port conflicts.

```powershell
# Clean up first (recommended)
docker compose down
docker compose build
docker compose up -d

# Or use the provided script
.\docker-start.ps1
```

**Why this matters**:
- Prevents port conflicts from stale containers
- Ensures fresh start with latest code changes
- Avoids confusion from multiple container instances
- Prevents resource leaks from orphaned containers

### Development Workflow

```powershell
# 1. Clean up existing containers
docker compose down

# 2. Rebuild with latest changes
docker compose build

# 3. Start fresh
docker compose up -d

# 4. Monitor logs
docker compose logs -f mcp-studio
```

**Or use the automated script**:
```powershell
.\mcp-studio-docker\docker-start.ps1
```

The script automatically:
- Cleans up existing containers
- Builds fresh image
- Starts new containers
- Shows status and logs

## Development vs Production

### Development

```bash
# Always clean up first!
docker compose down

# Build and run
docker compose build
docker compose up -d

# View logs
docker compose logs -f mcp-studio

# Stop
docker compose down
```

### Production

```bash
# Build optimized image
docker build -t mcp-studio:latest .

# Run with production settings
docker run -d \
  --name mcp-studio \
  -p 8001:8001 \
  -v "D:/Dev/repos:/app/repos:ro" \
  -v "./logs:/app/logs" \
  -v "./data:/app/data" \
  -e REPOS_DIR=/app/repos \
  -e OLLAMA_URL=http://host.docker.internal:11434 \
  --restart unless-stopped \
  mcp-studio:latest
```

**Note**: Production may use read-only (`:ro`) mount for repos if tool execution isn't needed.

---

## Security Considerations

1. **Repos Access**: Full read-write access means the container can modify your repos. Use read-only (`:ro`) if you only need scanning.

2. **Network**: The dashboard is exposed on port 8001. Consider:
   - Reverse proxy (nginx, traefik)
   - Authentication layer
   - Firewall rules

3. **Ollama**: If Ollama is exposed, ensure it's not publicly accessible.

---

## Why Not Containerize MCP Server Mode?

**MCP servers must NEVER be containerized** because:

- ❌ **STDIO complexity**: Claude Desktop needs direct process communication
- ❌ **Volume mounting**: Config files, credentials become complex
- ❌ **Debug overhead**: Harder to troubleshoot import/dependency issues
- ❌ **Resource waste**: Container overhead for simple Python script
- ❌ **Deployment complexity**: Docker adds steps without benefits

**Web dashboard CAN be containerized** because:

- ✅ **Web service**: Standard HTTP/WebSocket communication
- ✅ **Multi-component**: Benefits from container orchestration
- ✅ **Deployment**: Easier production deployment
- ✅ **Isolation**: Separates dashboard from host environment

---

## Next Steps

1. **Configure your repos directory** in `.env` or environment
2. **Set up Ollama** (optional but recommended)
3. **Start the dashboard**: `docker-compose up -d`
4. **Access**: `http://localhost:8001`
5. **Check logs**: `docker-compose logs -f`

For more details, see [Containerization Guidelines](docs/mcp-technical/CONTAINERIZATION_GUIDELINES.md).
