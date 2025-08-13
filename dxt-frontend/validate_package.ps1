# DXT Package Validation Script for MCP Studio Frontend
# This script validates the DXT package structure and contents

# Exit on error
$ErrorActionPreference = "Stop"

# Colors for output
$successColor = "Green"
$errorColor = "Red"
$infoColor = "Cyan"
$warningColor = "Yellow"

function Write-Info {
    param([string]$message)
    Write-Host "[INFO] $message" -ForegroundColor $infoColor
}

function Write-Success {
    param([string]$message)
    Write-Host "[SUCCESS] $message" -ForegroundColor $successColor
}

function Write-Error {
    param([string]$message)
    Write-Host "[ERROR] $message" -ForegroundColor $errorColor
}

function Write-Warning {
    param([string]$message)
    Write-Host "[WARNING] $message" -ForegroundColor $warningColor
}

function Test-CommandExists {
    param([string]$command)
    try {
        $null = Get-Command $command -ErrorAction Stop
        return $true
    } catch {
        return $false
    }
}

# Check DXT CLI
if (-not (Test-CommandExists "dxt")) {
    Write-Error "DXT CLI is not installed. Please install it with 'npm install -g @dxt/cli'"
    exit 1
}

# Check required files
$requiredFiles = @(
    "manifest.json",
    "prompts/system.md",
    "prompts/user.md",
    "package/build/index.html"
)

$allFilesExist = $true
Write-Info "Validating package structure..."

foreach ($file in $requiredFiles) {
    $filePath = Join-Path -Path $PSScriptRoot -ChildPath $file
    if (-not (Test-Path $filePath)) {
        Write-Error "Missing required file: $file"
        $allFilesExist = $false
    } else {
        Write-Success "Found: $file"
    }
}

if (-not $allFilesExist) {
    Write-Error "Package validation failed due to missing files"
    exit 1
}

# Validate manifest.json
Write-Info "Validating manifest.json..."
$manifestPath = Join-Path -Path $PSScriptRoot -ChildPath "manifest.json"
$manifest = Get-Content -Path $manifestPath -Raw | ConvertFrom-Json

# Check required manifest fields
$requiredManifestFields = @(
    "dxt_version",
    "name",
    "version",
    "description",
    "author",
    "server"
)

$manifestValid = $true
foreach ($field in $requiredManifestFields) {
    if (-not $manifest.PSObject.Properties.Name -contains $field) {
        Write-Error "Missing required manifest field: $field"
        $manifestValid = $false
    }
}

# Check server configuration
if ($manifest.server) {
    $requiredServerFields = @("type", "entry_point", "mcp_config")
    foreach ($field in $requiredServerFields) {
        if (-not $manifest.server.PSObject.Properties.Name -contains $field) {
            Write-Error "Missing required server field: $field"
            $manifestValid = $false
        }
    }
    
    # Check mcp_config
    if ($manifest.server.mcp_config) {
        $requiredMcpConfig = @("command", "args", "cwd")
        foreach ($field in $requiredMcpConfig) {
            if (-not $manifest.server.mcp_config.PSObject.Properties.Name -contains $field) {
                Write-Error "Missing required mcp_config field: $field"
                $manifestValid = $false
            }
        }
    }
}

# Check user_config
if (-not $manifest.user_config) {
    Write-Warning "No user_config section found in manifest. Consider adding configuration options."
}

if (-not $manifestValid) {
    Write-Error "Manifest validation failed"
    exit 1
}

# Validate prompts
$systemPromptPath = Join-Path -Path $PSScriptRoot -ChildPath "prompts/system.md"
$userPromptPath = Join-Path -Path $PSScriptRoot -ChildPath "prompts/user.md"

$systemPrompt = Get-Content -Path $systemPromptPath -Raw
$userPrompt = Get-Content -Path $userPromptPath -Raw

if ([string]::IsNullOrWhiteSpace($systemPrompt)) {
    Write-Warning "System prompt is empty. Consider adding guidance for the AI."
}

if ([string]::IsNullOrWhiteSpace($userPrompt)) {
    Write-Warning "User prompt is empty. Consider adding usage instructions."
}

# Check build directory
$buildDir = Join-Path -Path $PSScriptRoot -ChildPath "package/build"
if (-not (Test-Path $buildDir)) {
    Write-Error "Build directory not found. Please build the React application first."
    exit 1
}

# Run DXT validation
Write-Info "Running DXT validation..."
try {
    $validationOutput = dxt validate $manifestPath 2>&1 | Out-String
    
    if ($LASTEXITCODE -eq 0) {
        Write-Success "DXT validation passed successfully"
        Write-Output $validationOutput
    } else {
        Write-Error "DXT validation failed"
        Write-Output $validationOutput
        exit 1
    }
} catch {
    Write-Error "Error running DXT validation: $_"
    exit 1
}

Write-Success "Package validation completed successfully!"
Write-Info "You can now proceed with packaging using: .\package_dxt.ps1"
