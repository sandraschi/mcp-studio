#!/usr/bin/env powershell
<#
.SYNOPSIS
    Build MCPB package for MCP Studio

.DESCRIPTION
    This script builds an MCPB (MCP Bundle) package for the MCP Studio MCP server.
    It validates prerequisites, builds the package, and performs integrity checks.

.PARAMETER OutputDir
    Output directory for the built package (default: "dist")

.PARAMETER NoSign
    Skip package signing (useful for development builds)

.PARAMETER Clean
    Clean the output directory before building

.EXAMPLE
    .\build-mcpb-package.ps1

.EXAMPLE
    .\build-mcpb-package.ps1 -OutputDir "C:\builds" -NoSign

.EXAMPLE
    .\build-mcpb-package.ps1 -Clean
#>

param(
    [string]$OutputDir = "dist",
    [switch]$NoSign,
    [switch]$Clean
)

# Script configuration
$ErrorActionPreference = "Stop"
$scriptName = $MyInvocation.MyCommand.Name
$packageName = "mcp-studio"

# Color output functions
function Write-ColorOutput {
    param(
        [string]$Message,
        [string]$Color = "White"
    )
    Write-Host $Message -ForegroundColor $Color
}

function Write-Success {
    param([string]$Message)
    Write-ColorOutput "✅ $Message" "Green"
}

function Write-Error {
    param([string]$Message)
    Write-ColorOutput "❌ $Message" "Red"
}

function Write-Info {
    param([string]$Message)
    Write-ColorOutput "ℹ️  $Message" "Cyan"
}

function Write-Warning {
    param([string]$Message)
    Write-ColorOutput "⚠️  $Message" "Yellow"
}

# Prerequisites check
function Test-Prerequisites {
    Write-Info "Checking prerequisites..."

    # Check Python
    try {
        $pythonVersion = python --version 2>$null
        if ($LASTEXITCODE -eq 0) {
            Write-Success "Python found: $pythonVersion"
        } else {
            throw "Python not found"
        }
    } catch {
        Write-Error "Python 3.10+ is required but not found"
        exit 1
    }

    # Check Node.js and MCPB CLI
    try {
        $nodeVersion = node --version 2>$null
        if ($LASTEXITCODE -eq 0) {
            Write-Success "Node.js found: $nodeVersion"
        } else {
            throw "Node.js not found"
        }
    } catch {
        Write-Error "Node.js is required for MCPB CLI"
        exit 1
    }

    # Check MCPB CLI
    try {
        $mcpbVersion = mcpb --version 2>$null
        if ($LASTEXITCODE -eq 0) {
            Write-Success "MCPB CLI found: $mcpbVersion"
        } else {
            throw "MCPB CLI not found"
        }
    } catch {
        Write-Error "MCPB CLI not found. Install with: npm install -g @anthropic-ai/mcpb"
        exit 1
    }

    # Check manifest.json
    if (-not (Test-Path "manifest.json")) {
        Write-Error "manifest.json not found in project root"
        exit 1
    }
    Write-Success "manifest.json found"

    # Check mcpb.json
    if (-not (Test-Path "mcpb.json")) {
        Write-Error "mcpb.json not found in project root"
        exit 1
    }
    Write-Success "mcpb.json found"
}

# Validate manifest
function Test-Manifest {
    Write-Info "Validating manifest.json..."

    try {
        $validation = mcpb validate manifest.json 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Success "Manifest validation passed"
            return $true
        } else {
            Write-Error "Manifest validation failed:"
            Write-ColorOutput $validation "Red"
            return $false
        }
    } catch {
        Write-Error "Manifest validation error: $_"
        return $false
    }
}

# Create output directory
function New-OutputDirectory {
    param([string]$Path)

    if ($Clean -and (Test-Path $Path)) {
        Write-Info "Cleaning output directory: $Path"
        Remove-Item $Path -Recurse -Force
    }

    if (-not (Test-Path $Path)) {
        New-Item -ItemType Directory -Path $Path -Force | Out-Null
        Write-Success "Created output directory: $Path"
    }
}

# Build MCPB package
function New-MCPBPackage {
    param([string]$OutputPath)

    Write-Info "Building MCPB package..."

    $outputFile = Join-Path $OutputPath "$packageName.mcpb"

    try {
        if ($NoSign) {
            Write-Info "Building without signing (development mode)..."
            $buildCommand = "mcpb pack . $OutputPath --no-sign"
        } else {
            Write-Info "Building with signing (production mode)..."
            $buildCommand = "mcpb pack . $OutputPath"
        }

        Write-Info "Executing: $buildCommand"
        $buildOutput = Invoke-Expression $buildCommand 2>&1

        if ($LASTEXITCODE -eq 0) {
            Write-Success "Package built successfully: $outputFile"
            return $outputFile
        } else {
            Write-Error "Package build failed"
            Write-ColorOutput $buildOutput "Red"
            return $null
        }
    } catch {
        Write-Error "Package build error: $_"
        return $null
    }
}

# Verify package
function Test-Package {
    param([string]$PackagePath)

    Write-Info "Verifying package integrity..."

    if (-not (Test-Path $PackagePath)) {
        Write-Error "Package file not found: $PackagePath"
        return $false
    }

    try {
        $packageInfo = mcpb info $PackagePath 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Success "Package verification passed"

            # Extract package size
            $fileSize = (Get-Item $PackagePath).Length
            $fileSizeMB = [math]::Round($fileSize / 1MB, 2)
            Write-Info "Package size: $fileSizeMB MB"

            return $true
        } else {
            Write-Error "Package verification failed"
            Write-ColorOutput $packageInfo "Red"
            return $false
        }
    } catch {
        Write-Error "Package verification error: $_"
        return $false
    }
}

# Main build process
function Start-Build {
    Write-ColorOutput "`n🚀 Starting MCPB Package Build for $packageName`n" "Magenta"

    # Prerequisites check
    Test-Prerequisites

    # Validate manifest
    if (-not (Test-Manifest)) {
        Write-Error "Build aborted due to manifest validation failure"
        exit 1
    }

    # Create output directory
    New-OutputDirectory $OutputDir

    # Build package
    $packagePath = New-MCPBPackage $OutputDir

    if (-not $packagePath) {
        Write-Error "Build failed - package not created"
        exit 1
    }

    # Verify package
    if (-not (Test-Package $packagePath)) {
        Write-Error "Build failed - package verification failed"
        exit 1
    }

    # Success
    Write-ColorOutput "`n🎉 MCPB Package Build Completed Successfully!`n" "Green"
    Write-Info "Package location: $packagePath"
    Write-Info "Ready for distribution or installation in Claude Desktop"

    # Next steps
    Write-ColorOutput "`n📋 Next Steps:" "Yellow"
    Write-Info "1. Test installation: Drag $packagePath to Claude Desktop"
    Write-Info "2. Configure user settings when prompted"
    Write-Info "3. Test MCP Studio tools in Claude Desktop"
    if (-not $NoSign) {
        Write-Info "4. Package is production-ready with signing"
    } else {
        Write-Info "4. For production: Rebuild without -NoSign flag"
    }
}

# Execute main build
try {
    Start-Build
} catch {
    Write-Error "Build script failed with error: $_"
    exit 1
}
