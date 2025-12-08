# MCP Studio Docker Build and Test Script

Write-Host "🐳 Testing MCP Studio Docker Setup" -ForegroundColor Cyan
Write-Host ""

# Check Docker is available
Write-Host "1. Checking Docker..." -ForegroundColor Yellow
try {
    $dockerVersion = docker --version 2>&1
    Write-Host "   ✅ Docker found: $dockerVersion" -ForegroundColor Green
} catch {
    Write-Host "   ❌ Docker not found. Please install Docker Desktop." -ForegroundColor Red
    exit 1
}

# Check docker-compose
Write-Host "2. Checking Docker Compose..." -ForegroundColor Yellow
try {
    $composeVersion = docker compose version 2>&1
    Write-Host "   ✅ Docker Compose found: $composeVersion" -ForegroundColor Green
} catch {
    Write-Host "   ❌ Docker Compose not found." -ForegroundColor Red
    exit 1
}

# Check required files
Write-Host "3. Checking required files..." -ForegroundColor Yellow
$requiredFiles = @("Dockerfile", "docker-compose.yml", "requirements.txt", "studio_dashboard.py")
$allExist = $true
foreach ($file in $requiredFiles) {
    if (Test-Path $file) {
        Write-Host "   ✅ $file exists" -ForegroundColor Green
    } else {
        Write-Host "   ❌ $file missing" -ForegroundColor Red
        $allExist = $false
    }
}

if (-not $allExist) {
    Write-Host "   ❌ Missing required files. Cannot build." -ForegroundColor Red
    exit 1
}

# Validate docker-compose.yml
Write-Host "4. Validating docker-compose.yml..." -ForegroundColor Yellow
try {
    docker compose config > $null 2>&1
    Write-Host "   ✅ docker-compose.yml is valid" -ForegroundColor Green
} catch {
    Write-Host "   ❌ docker-compose.yml has errors" -ForegroundColor Red
    docker compose config
    exit 1
}

# Build image
Write-Host "5. Building Docker image..." -ForegroundColor Yellow
Write-Host "   This may take a few minutes..." -ForegroundColor Gray
try {
    docker build -t mcp-studio:test . 2>&1 | ForEach-Object {
        if ($_ -match "ERROR|error|Error") {
            Write-Host "   $_" -ForegroundColor Red
        } elseif ($_ -match "Step|RUN|COPY|CMD") {
            Write-Host "   $_" -ForegroundColor Cyan
        } else {
            Write-Host "   $_" -ForegroundColor Gray
        }
    }
    Write-Host "   ✅ Build completed successfully" -ForegroundColor Green
} catch {
    Write-Host "   ❌ Build failed" -ForegroundColor Red
    exit 1
}

# Check if image was created
Write-Host "6. Verifying image..." -ForegroundColor Yellow
$imageExists = docker images mcp-studio:test --format "{{.Repository}}:{{.Tag}}" 2>&1
if ($imageExists -match "mcp-studio:test") {
    Write-Host "   ✅ Image created: mcp-studio:test" -ForegroundColor Green
} else {
    Write-Host "   ❌ Image not found" -ForegroundColor Red
    exit 1
}

# Test container startup (dry run)
Write-Host "7. Testing container configuration..." -ForegroundColor Yellow
try {
    # Set default REPOS_DIR if not set
    if (-not $env:REPOS_DIR) {
        $env:REPOS_DIR = "D:/Dev/repos"
        Write-Host "   ℹ️  Using default REPOS_DIR: $env:REPOS_DIR" -ForegroundColor Gray
    } else {
        Write-Host "   ℹ️  Using REPOS_DIR: $env:REPOS_DIR" -ForegroundColor Gray
    }
    
    # Validate compose config with environment
    docker compose config > $null 2>&1
    Write-Host "   ✅ Container configuration valid" -ForegroundColor Green
} catch {
    Write-Host "   ❌ Container configuration error" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "✅ All tests passed!" -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Cyan
Write-Host "  1. Set your repos directory: `$env:REPOS_DIR = 'D:/Dev/repos'" -ForegroundColor White
Write-Host "  2. Start the dashboard: docker compose up -d" -ForegroundColor White
Write-Host "  3. Access at: http://localhost:8001" -ForegroundColor White
Write-Host "  4. View logs: docker compose logs -f mcp-studio" -ForegroundColor White
Write-Host ""
