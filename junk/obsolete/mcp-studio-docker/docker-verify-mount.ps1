# Verify Docker Volume Mount

Write-Host "🔍 Verifying Docker Volume Mount" -ForegroundColor Cyan
Write-Host ""

# Check if container is running
$container = docker ps --filter "name=mcp-studio" --format "{{.Names}}" 2>&1
if (-not $container -or $container -notmatch "mcp-studio") {
    Write-Host "❌ Container mcp-studio is not running" -ForegroundColor Red
    Write-Host "   Start it first: docker compose up -d" -ForegroundColor Yellow
    exit 1
}

Write-Host "✅ Container is running: $container" -ForegroundColor Green
Write-Host ""

# Check mounts
Write-Host "📦 Volume Mounts:" -ForegroundColor Yellow
$mounts = docker inspect mcp-studio --format='{{range .Mounts}}{{.Type}} {{.Source}} -> {{.Destination}}{{"\n"}}{{end}}' 2>&1
$mounts | ForEach-Object {
    if ($_ -match "repos") {
        Write-Host "   $_" -ForegroundColor Cyan
    } else {
        Write-Host "   $_" -ForegroundColor Gray
    }
}

Write-Host ""
Write-Host "📂 Checking /app/repos inside container:" -ForegroundColor Yellow

# Check if directory exists
$dirCheck = docker compose exec -T mcp-studio sh -c "test -d /app/repos && echo 'EXISTS' || echo 'MISSING'" 2>&1
Write-Host "   Directory status: $dirCheck" -ForegroundColor $(if ($dirCheck -match "EXISTS") { "Green" } else { "Red" })

# List contents
Write-Host ""
Write-Host "   Contents:" -ForegroundColor Yellow
$contents = docker compose exec -T mcp-studio sh -c "ls -la /app/repos 2>&1 | head -10" 2>&1
if ($contents) {
    $contents | ForEach-Object { Write-Host "   $_" -ForegroundColor Gray }
} else {
    Write-Host "   (empty or cannot access)" -ForegroundColor Red
}

# Check if it's the actual repos or empty
Write-Host ""
Write-Host "🔍 Checking for repo directories:" -ForegroundColor Yellow
$repoCount = docker compose exec -T mcp-studio sh -c "ls -d /app/repos/*/ 2>/dev/null | wc -l" 2>&1
if ($repoCount -match "^\d+$" -and [int]$repoCount -gt 0) {
    Write-Host "   ✅ Found $repoCount repository directories" -ForegroundColor Green
} else {
    Write-Host "   ❌ No repository directories found" -ForegroundColor Red
    Write-Host ""
    Write-Host "   💡 Troubleshooting:" -ForegroundColor Yellow
    Write-Host "   1. Check REPOS_DIR environment variable is set correctly" -ForegroundColor White
    Write-Host "   2. Verify the path exists on host: $env:REPOS_DIR" -ForegroundColor White
    Write-Host "   3. Check Docker Desktop file sharing settings" -ForegroundColor White
    Write-Host "   4. Restart container: docker compose down && docker compose up -d" -ForegroundColor White
}

Write-Host ""
