# MCP Studio Web Dashboard Dockerfile
# Containerizes the web dashboard (NOT the MCP server mode)

FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create directories for logs and data
RUN mkdir -p /app/logs /app/data

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PORT=8001 \
    REPOS_DIR=/app/repos \
    OLLAMA_URL=http://host.docker.internal:11434 \
    LOG_DIR=/app/logs

# Expose port
EXPOSE 8001

# Health check - simple check that server is responding
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8001/', timeout=5)" || exit 1

# Run the dashboard (web mode only, not MCP server mode)
# The script handles uvicorn startup internally
CMD ["python", "-u", "studio_dashboard.py"]
