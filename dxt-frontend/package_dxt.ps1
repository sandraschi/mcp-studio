# DXT Package Script for MCP Studio Frontend
# This script automates the process of creating a DXT package for the MCP Studio Frontend

# Exit on error
$ErrorActionPreference = "Stop"

# Configuration
$packageName = "mcp-studio-frontend"
$version = "1.0.0"
$outputDir = "./dist"
$dxtPackageName = "$packageName-$version.dxt"

# Colors for output
$successColor = "Green"
$errorColor = "Red"
$infoColor = "Cyan"

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

function Test-CommandExists {
    param([string]$command)
    try {
        $null = Get-Command $command -ErrorAction Stop
        return $true
    } catch {
        return $false
    }
}

# Check prerequisites
Write-Info "Checking prerequisites..."

# Check if DXT CLI is installed
if (-not (Test-CommandExists "dxt")) {
    Write-Error "DXT CLI is not installed. Please install it with 'npm install -g @dxt/cli'"
    exit 1
}

# Check Node.js version
$nodeVersion = (node --version) -replace '^v|\r\n|\n|\r', ''
if ([version]$nodeVersion -lt [version]"16.0.0") {
    Write-Error "Node.js 16.0.0 or later is required. Current version: $nodeVersion"
    exit 1
}

# Check npm version
$npmVersion = (npm --version) -replace '\r\n|\n|\r', ''
if ([version]$npmVersion -lt [version]"8.0.0") {
    Write-Error "npm 8.0.0 or later is required. Current version: $npmVersion"
    exit 1
}

# Create output directory
if (-not (Test-Path $outputDir)) {
    New-Item -ItemType Directory -Path $outputDir | Out-Null
    Write-Info "Created output directory: $outputDir"
}

# Build the React application
Write-Info "Building the React application..."
Set-Location "../mcp-studio-react"

# Install dependencies
Write-Info "Installing npm dependencies..."
npm ci --silent
if ($LASTEXITCODE -ne 0) {
    Write-Error "Failed to install npm dependencies"
    exit 1
}

# Build the application
Write-Info "Building the application..."
npm run build --silent
if ($LASTEXITCODE -ne 0) {
    Write-Error "Failed to build the application"
    exit 1
}

Set-Location "../dxt-frontend"

# Copy build files to package directory
$buildDir = "package/build"
if (Test-Path $buildDir) {
    Remove-Item -Path $buildDir -Recurse -Force
}
New-Item -ItemType Directory -Path $buildDir | Out-Null
Copy-Item -Path "../mcp-studio-react/build/*" -Destination $buildDir -Recurse -Force

# Validate the manifest
Write-Info "Validating the manifest..."
dxt validate manifest.json
if ($LASTEXITCODE -ne 0) {
    Write-Error "Manifest validation failed"
    exit 1
}

# Create the DXT package
Write-Info "Creating DXT package..."
dxt pack -o "$outputDir/$dxtPackageName"
if ($LASTEXITCODE -ne 0) {
    Write-Error "Failed to create DXT package"
    exit 1
}

# Verify the package was created
if (-not (Test-Path "$outputDir/$dxtPackageName")) {
    Write-Error "Failed to create DXT package: $outputDir/$dxtPackageName not found"
    exit 1
}

# Sign the package (optional)
$signKey = $env:DXT_SIGN_KEY
if ($signKey) {
    Write-Info "Signing the DXT package..."
    dxt sign "$outputDir/$dxtPackageName" --key $signKey
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Failed to sign DXT package"
        exit 1
    }
    $signedPackage = "$outputDir/$packageName-$version-signed.dxt"
    if (Test-Path $signedPackage) {
        Write-Success "Created signed DXT package: $signedPackage"
    } else {
        Write-Error "Failed to create signed DXT package"
        exit 1
    }
} else {
    Write-Info "Skipping package signing (DXT_SIGN_KEY environment variable not set)"
    Write-Success "Created unsigned DXT package: $outputDir/$dxtPackageName"
}

# Create a checksum file
$checksumFile = "$outputDir/$packageName-$version-sha256.txt"
$packagePath = if ($signKey) { $signedPackage } else { "$outputDir/$dxtPackageName" }
$checksum = (Get-FileHash -Path $packagePath -Algorithm SHA256).Hash
"$checksum  $($packagePath | Split-Path -Leaf)" | Out-File -FilePath $checksumFile -Encoding UTF8

Write-Success "DXT package creation completed successfully!"
Write-Info "Package: $packagePath"
Write-Info "Checksum: $checksumFile"
Write-Info ""
Write-Info "To install the package:"
Write-Info "1. Copy the .dxt file to your DXT packages directory"
Write-Info "2. Run: dxt install $packagePath"
Write-Info "3. Configure the package using the DXT CLI or configuration file"
Write-Info "4. Start the frontend: dxt start $packageName"
