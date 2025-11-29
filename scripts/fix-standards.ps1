#!/usr/bin/env pwsh
# Auto-generated fix script for mcp-studio
# Generated: 2025-10-26_00-42-41
# Issues to fix: 8

param([switch]$DryRun = $false)

Write-Host '🔧 Fixing Repository Standards...' -ForegroundColor Cyan
if ($DryRun) { Write-Host '🔍 DRY RUN MODE' -ForegroundColor Yellow }

$centralDocs = 'D:\Dev\repos\mcp-central-docs'

# Fix: Create assets/icon.svg

# Fix: Create requirements.txt

# Fix: Create assets/prompts/system.md

# Fix: Create .github/workflows/release.yml from central docs template
if (-not (Test-Path '.github/workflows/release.yml')) {
    if (Test-Path "$centralDocs/templates/.github/workflows/release.yml") {
        Copy-Item "$centralDocs/templates/.github/workflows/release.yml" '.github/workflows/release.yml' -Force
        Write-Host '  ✅ Copied: .github/workflows/release.yml' -ForegroundColor Green
    }
}

# Fix: Create .github/workflows/ci.yml from central docs template
if (-not (Test-Path '.github/workflows/ci.yml')) {
    if (Test-Path "$centralDocs/templates/.github/workflows/ci.yml") {
        Copy-Item "$centralDocs/templates/.github/workflows/ci.yml" '.github/workflows/ci.yml' -Force
        Write-Host '  ✅ Copied: .github/workflows/ci.yml' -ForegroundColor Green
    }
}

# Fix: Create CONTRIBUTING.md from central docs template
if (-not (Test-Path 'CONTRIBUTING.md')) {
    if (Test-Path "$centralDocs/templates/CONTRIBUTING.md") {
        Copy-Item "$centralDocs/templates/CONTRIBUTING.md" 'CONTRIBUTING.md' -Force
        Write-Host '  ✅ Copied: CONTRIBUTING.md' -ForegroundColor Green
    }
}

# Fix: Create .cursorrules from central docs template
if (-not (Test-Path '.cursorrules')) {
    if (Test-Path "$centralDocs/templates/.cursorrules") {
        Copy-Item "$centralDocs/templates/.cursorrules" '.cursorrules' -Force
        Write-Host '  ✅ Copied: .cursorrules' -ForegroundColor Green
    }
}

# Fix: Add ruff configuration to pyproject.toml

Write-Host '✅ Fix script complete!' -ForegroundColor Green
