# MCP Studio Start (reservoir ports 10724 backend, 10725 frontend per WEBAPP_PORTS.md)
$BackendPort = 10724
$FrontendPort = 10725
$Root = $PSScriptRoot

try {
    Push-Location (Join-Path $Root "frontend")
    npx --yes kill-port $BackendPort $FrontendPort 2>$null
} finally {
    Pop-Location
}

Write-Host "Starting MCP Studio..." -ForegroundColor Cyan
Write-Host "Backend: http://localhost:$BackendPort  Frontend: http://localhost:$FrontendPort" -ForegroundColor Gray

# Start backend (src.mcp_studio when run from repo root)
$backendCmd = "Set-Location '$Root'; `$env:PYTHONPATH='$Root'; `$env:PORT='$BackendPort'; python -m uvicorn src.mcp_studio.main:app --reload --host 0.0.0.0 --port $BackendPort"
Start-Process powershell -ArgumentList "-NoExit", "-Command", $backendCmd

Start-Sleep -Seconds 2

# Start frontend (react-scripts uses PORT env)
$frontendDir = Join-Path $Root "frontend"
$frontendCmd = "Set-Location '$frontendDir'; `$env:PORT='$FrontendPort'; `$env:BROWSER='none'; npm run start"
Start-Process powershell -ArgumentList "-NoExit", "-Command", $frontendCmd

Write-Host "Backend and frontend started. Close their windows to stop." -ForegroundColor Green
Write-Host "Webapp: http://localhost:$FrontendPort" -ForegroundColor Cyan
