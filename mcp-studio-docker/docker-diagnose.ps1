# Docker Diagnostic Script

Write-Host "🔍 Diagnosing Docker Setup..." -ForegroundColor Cyan
Write-Host ""

# Check Docker
Write-Host "1. Docker Status:" -ForegroundColor Yellow
try {
    $dockerVersion = docker --version 2>&1
    Write-Host "   $dockerVersion" -ForegroundColor Green
} catch {
    Write-Host "   ❌ Docker not found" -ForegroundColor Red
    exit 1
}

# Check Docker Compose
Write-Host ""
Write-Host "2. Docker Compose:" -ForegroundColor Yellow
try {
    $composeVersion = docker compose version 2>&1
    Write-Host "   $composeVersion" -ForegroundColor Green
} catch {
    Write-Host "   ❌ Docker Compose not found" -ForegroundColor Red
    exit 1
}

# Check Docker daemon
Write-Host ""
Write-Host "3. Docker Daemon:" -ForegroundColor Yellow
try {
    $dockerInfo = docker info 2>&1 | Select-Object -First 1
    if ($dockerInfo -match "Server Version" -or $dockerInfo -match "ERROR") {
        if ($dockerInfo -match "ERROR") {
            Write-Host "   ❌ Docker daemon not running: $dockerInfo" -ForegroundColor Red
            Write-Host "   💡 Start Docker Desktop" -ForegroundColor Yellow
            exit 1
        } else {
            Write-Host "   ✅ Docker daemon is running" -ForegroundColor Green
        }
    }
} catch {
    Write-Host "   ❌ Cannot connect to Docker daemon" -ForegroundColor Red
    exit 1
}

# Check files
Write-Host ""
Write-Host "4. Required Files:" -ForegroundColor Yellow
$files = @("Dockerfile", "docker-compose.yml", "requirements.txt", "studio_dashboard.py")
foreach ($file in $files) {
    if (Test-Path $file) {
        Write-Host "   ✅ $file" -ForegroundColor Green
    } else {
        Write-Host "   ❌ $file missing" -ForegroundColor Red
    }
}

# Check docker-compose config
Write-Host ""
Write-Host "5. Docker Compose Config:" -ForegroundColor Yellow
try {
    $config = docker compose config 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "   ✅ Configuration is valid" -ForegroundColor Green
        $services = docker compose config --services 2>&1
        Write-Host "   Services: $services" -ForegroundColor Gray
    } else {
        Write-Host "   ❌ Configuration error:" -ForegroundColor Red
        Write-Host "   $config" -ForegroundColor Red
    }
} catch {
    Write-Host "   ❌ Failed to validate config" -ForegroundColor Red
}

# Check existing containers
Write-Host ""
Write-Host "6. Existing Containers:" -ForegroundColor Yellow
$containers = docker ps -a --filter "name=mcp-studio" --format "{{.Names}} - {{.Status}}" 2>&1
if ($containers) {
    Write-Host "   Found:" -ForegroundColor Yellow
    $containers | ForEach-Object { Write-Host "   $_" -ForegroundColor Gray }
} else {
    Write-Host "   ℹ️  No existing mcp-studio containers" -ForegroundColor Gray
}

# Check images
Write-Host ""
Write-Host "7. Docker Images:" -ForegroundColor Yellow
$images = docker images mcp-studio --format "{{.Repository}}:{{.Tag}} - {{.Size}}" 2>&1
if ($images) {
    Write-Host "   Found:" -ForegroundColor Yellow
    $images | ForEach-Object { Write-Host "   $_" -ForegroundColor Gray }
} else {
    Write-Host "   ℹ️  No mcp-studio images built yet" -ForegroundColor Gray
}

Write-Host ""
Write-Host "✅ Diagnosis complete!" -ForegroundColor Green
Write-Host ""
Write-Host "To build and start:" -ForegroundColor Cyan
Write-Host "  .\mcp-studio-docker\docker-start.ps1" -ForegroundColor White
Write-Host ""
