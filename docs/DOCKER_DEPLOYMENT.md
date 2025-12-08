# 🐳 MCP Studio Docker Deployment Guide

**Containerizing the Web Dashboard** (NOT the MCP server mode)

---

## ⚠️ Important: What Gets Containerized

### ✅ **Containerized: Web Dashboard**
- FastAPI web interface
- Dashboard UI
- Tool discovery and execution console
- AI assistant (if Ollama available)

### ❌ **NOT Containerized: MCP Server Mode**
- MCP server mode runs natively (STDIO communication)
- Direct integration with Claude Desktop
- Simple `pip install` deployment

---

## 🚀 Quick Start

### **Prerequisites**
- Docker and Docker Compose installed
- Repos directory accessible (default: `D:\Dev\repos` on Windows)
- Ollama running (optional, for AI features)

### **1. Build and Run**

```powershell
# Windows PowerShell
cd D:\Dev\repos\mcp-studio
docker compose up -d
```

```bash
# Linux/Mac
cd /path/to/mcp-studio
docker compose up -d
```

### **2. Access Dashboard**

Open browser: http://localhost:8001

---

## 📁 Volume Mounts

### **Repos Directory (Required)**

The dashboard **must** have access to your repos directory to scan MCP servers.

**Windows:**
```yaml
volumes:
  - "D:/Dev/repos:/app/repos:ro"
```

**Linux/Mac:**
```yaml
volumes:
  - "/path/to/repos:/app/repos:ro"
```

**Custom Location:**
```powershell
# Set environment variable
$env:REPOS_DIR = "C:\MyRepos"
docker compose up -d
```

---

## 🤖 Ollama Integration (Tricky!)

The local LLM interface can be configured in several ways:

### **Option 1: Ollama on Host Machine** (Recommended for Windows/Mac)

Ollama runs on your host, container accesses it via `host.docker.internal`:

```yaml
environment:
  - OLLAMA_URL=http://host.docker.internal:11434
```

**Works on:**
- ✅ Windows (Docker Desktop)
- ✅ Mac (Docker Desktop)
- ⚠️ Linux (may need `--network=host`)

### **Option 2: Ollama in Docker** (Recommended for Linux)

Run Ollama as a separate container:

```yaml
services:
  ollama:
    image: ollama/ollama:latest
    ports:
      - "11434:11434"
    volumes:
      - ollama_data:/root/.ollama

  mcp-studio:
    environment:
      - OLLAMA_URL=http://ollama:11434
```

### **Option 3: Ollama on Network**

If Ollama runs on another machine:

```yaml
environment:
  - OLLAMA_URL=http://192.168.1.100:11434
```

### **Option 4: No Ollama** (Dashboard Still Works!)

If you don't need AI features:

```yaml
environment:
  - OLLAMA_URL=
```

The dashboard will work, but AI assistant features will be disabled.

---

## 🔧 Configuration

### **Environment Variables**

Create `.env` file or set in `docker-compose.yml`:

```env
# Port for web dashboard
PORT=8001

# Repos directory (Windows format)
REPOS_DIR=D:/Dev/repos

# Ollama URL (see options above)
OLLAMA_URL=http://host.docker.internal:11434
```

### **Custom Port**

```yaml
ports:
  - "9000:8001"  # Access on port 9000
```

---

## 🐛 Troubleshooting

### **Repos Not Scanning**

**Problem:** Dashboard shows no repos

**Solution:**
1. Check volume mount path is correct
2. Verify repos directory exists
3. Check container logs: `docker compose logs mcp-studio`

```powershell
# Verify mount
docker compose exec mcp-studio ls -la /app/repos
```

### **Ollama Connection Failed**

**Problem:** AI features not working

**Solution:**

**Windows/Mac:**
```yaml
# Ensure extra_hosts is set
extra_hosts:
  - "host.docker.internal:host-gateway"
```

**Linux:**
```yaml
# Use host network mode
network_mode: "host"
environment:
  - OLLAMA_URL=http://localhost:11434
```

**Or run Ollama in Docker:**
```yaml
# Add ollama service to docker-compose.yml
```

### **Permission Denied**

**Problem:** Can't read repos directory

**Solution:**
```powershell
# Windows: Check folder permissions
# Linux: May need to adjust user/group
docker compose exec mcp-studio whoami
```

---

## 📊 Production Deployment

### **Multi-Stage Build** (Optional)

For smaller images:

```dockerfile
# Build stage
FROM python:3.11-slim as builder
WORKDIR /app
COPY requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

# Runtime stage
FROM python:3.11-slim
WORKDIR /app
COPY --from=builder /root/.local /root/.local
COPY . .
ENV PATH=/root/.local/bin:$PATH
CMD ["python", "studio_dashboard.py"]
```

### **Health Checks**

Already included in Dockerfile:

```dockerfile
HEALTHCHECK --interval=30s --timeout=10s \
    CMD python -c "import httpx; httpx.get('http://localhost:8001/api/health')"
```

### **Resource Limits**

Add to `docker-compose.yml`:

```yaml
services:
  mcp-studio:
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 2G
        reservations:
          cpus: '0.5'
          memory: 512M
```

---

## 🔒 Security Considerations

### **Read-Only Repos Mount**

Repos are mounted read-only (`:ro`) to prevent accidental modifications:

```yaml
volumes:
  - "${REPOS_DIR}:/app/repos:ro"
```

### **Network Isolation**

Dashboard runs in isolated network:

```yaml
networks:
  mcp-studio-network:
    driver: bridge
```

### **Environment Variables**

Never commit secrets in `docker-compose.yml`. Use `.env` file (gitignored).

---

## 📝 Example Configurations

### **Windows Development**

```yaml
version: '3.8'
services:
  mcp-studio:
    build: .
    ports:
      - "8001:8001"
    volumes:
      - "D:/Dev/repos:/app/repos:ro"
    environment:
      - REPOS_DIR=/app/repos
      - OLLAMA_URL=http://host.docker.internal:11434
    extra_hosts:
      - "host.docker.internal:host-gateway"
```

### **Linux Production**

```yaml
version: '3.8'
services:
  ollama:
    image: ollama/ollama:latest
    ports:
      - "11434:11434"
    volumes:
      - ollama_data:/root/.ollama

  mcp-studio:
    build: .
    ports:
      - "8001:8001"
    volumes:
      - "/opt/repos:/app/repos:ro"
    environment:
      - REPOS_DIR=/app/repos
      - OLLAMA_URL=http://ollama:11434
    depends_on:
      - ollama

volumes:
  ollama_data:
```

---

## ✅ Verification

### **Check Container Status**

```powershell
docker compose ps
```

### **View Logs**

```powershell
docker compose logs -f mcp-studio
```

### **Test Repos Access**

```powershell
docker compose exec mcp-studio ls /app/repos
```

### **Test Ollama Connection**

```powershell
docker compose exec mcp-studio curl http://host.docker.internal:11434/api/tags
```

---

## 🎯 Key Points

1. ✅ **Repos directory MUST be mounted** - Dashboard needs full access to scan
2. ⚠️ **Ollama is optional** - Dashboard works without it (no AI features)
3. 🔒 **Repos are read-only** - Prevents accidental modifications
4. 🐳 **Only web dashboard is containerized** - MCP server mode stays native
5. 🌐 **Ollama connection is configurable** - Multiple deployment options

---

**Remember:** MCP servers themselves should NEVER be containerized (STDIO communication). Only the web dashboard gets containerized! 🐳
