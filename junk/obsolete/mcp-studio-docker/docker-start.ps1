# MCP Studio Docker Build and Start Script

Write-Host "🐳 Building and Starting MCP Studio Docker Container" -ForegroundColor Cyan
Write-Host ""

# Set repos directory if not already set
if (-not $env:REPOS_DIR) {
    $env:REPOS_DIR = "D:/Dev/repos"
    Write-Host "📂 Using default REPOS_DIR: $env:REPOS_DIR" -ForegroundColor Yellow
}
else {
    Write-Host "📂 Using REPOS_DIR: $env:REPOS_DIR" -ForegroundColor Green
}

# Set APPDATA and HOME for MCP client config discovery (if not set)
if (-not $env:APPDATA) {
    $env:APPDATA = "$env:USERPROFILE\AppData\Roaming"
}
if (-not $env:HOME) {
    $env:HOME = $env:USERPROFILE
}
Write-Host "   📁 APPDATA: $env:APPDATA" -ForegroundColor Gray
Write-Host "   📁 HOME: $env:HOME" -ForegroundColor Gray

# Verify the repos directory exists
if (-not (Test-Path $env:REPOS_DIR)) {
    Write-Host "❌ ERROR: Repos directory does not exist: $env:REPOS_DIR" -ForegroundColor Red
    Write-Host "   Please set REPOS_DIR to a valid path" -ForegroundColor Yellow
    exit 1
}
Write-Host "   ✅ Repos directory exists: $env:REPOS_DIR" -ForegroundColor Green

# Clean up any existing containers
Write-Host ""
Write-Host "🧹 Cleaning up existing containers..." -ForegroundColor Yellow
docker compose down 2>&1 | Out-Null
if ($LASTEXITCODE -eq 0) {
    Write-Host "   ✅ Stopped and removed existing containers" -ForegroundColor Green
}
else {
    Write-Host "   ℹ️  No existing containers to clean up" -ForegroundColor Gray
}

# Build the image
Write-Host ""
Write-Host "🔨 Building Docker image..." -ForegroundColor Yellow
docker compose build

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Build failed!" -ForegroundColor Red
    exit 1
}

Write-Host "✅ Build completed" -ForegroundColor Green

# Start the container
Write-Host ""
Write-Host "🚀 Starting container..." -ForegroundColor Yellow
docker compose up -d

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Failed to start container!" -ForegroundColor Red
    exit 1
}

# Wait a moment for container to start
Start-Sleep -Seconds 3

# Verify volume mount
Write-Host ""
Write-Host "🔍 Verifying volume mount..." -ForegroundColor Yellow
$mountCheck = docker compose exec -T mcp-studio sh -c "test -d /app/repos && ls -d /app/repos/*/ 2>/dev/null | wc -l" 2>&1
if ($mountCheck -match "^\d+$" -and [int]$mountCheck -gt 0) {
    Write-Host "   ✅ Volume mount working - found $mountCheck repository directories" -ForegroundColor Green
} else {
    Write-Host "   ⚠️  WARNING: Volume mount may not be working correctly" -ForegroundColor Yellow
    Write-Host "   Expected: $env:REPOS_DIR -> /app/repos" -ForegroundColor Gray
    Write-Host "   Run: .\docker-verify-mount.ps1 to diagnose" -ForegroundColor Gray
}

# Check status
Write-Host ""
Write-Host "📊 Container Status:" -ForegroundColor Cyan
docker compose ps

# Show logs
Write-Host ""
Write-Host "📋 Recent Logs:" -ForegroundColor Cyan
docker compose logs --tail 15 mcp-studio

Write-Host ""
Write-Host "✅ MCP Studio should be running!" -ForegroundColor Green
Write-Host ""
Write-Host "🌐 Access the dashboard at: http://localhost:8001" -ForegroundColor Cyan
Write-Host ""
Write-Host "Useful commands:" -ForegroundColor Yellow
Write-Host "  View logs:    docker compose logs -f mcp-studio" -ForegroundColor White
Write-Host "  Stop:         docker compose down" -ForegroundColor White
Write-Host "  Restart:      docker compose restart" -ForegroundColor White
Write-Host ""
