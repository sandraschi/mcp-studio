$ErrorActionPreference = "Stop"

$SitePath = "d:\Dev\tmp\test_sites\vortex-ai\www"
$RepoUrl = Read-Host "Enter your new GitHub Repository URL (e.g., https://github.com/user/repo.git)"
$Domain = "vortex-ai.org"

if (-not (Test-Path $SitePath)) {
    Write-Error "Site path $SitePath does not exist. Did you generate the site?"
}

Set-Location $SitePath

# Create CNAME file for GitHub Pages
$Domain | Out-File "CNAME" -Encoding ascii
Write-Host "Created CNAME file for $Domain"

# Git operations
if (-not (Test-Path ".git")) {
    git init
    Write-Host "Initialized git repository"
}

git add .
git commit -m "Deploying vortex-ai.org"
git branch -M main

try {
    git remote add origin $RepoUrl
}
catch {
    Write-Warning "Remote 'origin' might already exist. Ignoring."
    git remote set-url origin $RepoUrl
}

Write-Host "Pushing to GitHub..."
git push -u origin main

Write-Host "Done! Now go to GitHub Settings -> Pages and ensure things are set up (DNS check might take time)."
