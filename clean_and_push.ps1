# Clean and Push Script for GitHub
$ErrorActionPreference = "Stop"

# Disable all pagers
$env:GIT_PAGER = ''
$env:LESS = ''
$env:PAGER = ''

Write-Host "Step 1: Removing large file from git history..." -ForegroundColor Yellow

# Remove Project Demo.mp4 from all commits
git filter-branch --force --index-filter 'git rm --cached --ignore-unmatch "Project Demo.mp4"' --prune-empty --tag-name-filter cat -- --all 2>&1 | Out-Null

Write-Host "Step 2: Cleaning up git references..." -ForegroundColor Yellow

# Clean up
git for-each-ref --format="delete %(refname)" refs/original | git update-ref --stdin 2>&1 | Out-Null
git reflog expire --expire=now --all 2>&1 | Out-Null
git gc --prune=now --aggressive 2>&1 | Out-Null

Write-Host "Step 3: Staging current changes..." -ForegroundColor Yellow
git add -A

Write-Host "Step 4: Checking for uncommitted changes..." -ForegroundColor Yellow
$status = git status --porcelain
if ($status) {
    Write-Host "Committing changes..." -ForegroundColor Yellow
    git commit -m "Remove large files and prepare for push"
}

Write-Host "Step 5: Pushing to GitHub..." -ForegroundColor Yellow
git push -u origin main --force

Write-Host "`nDone! Your project has been pushed to GitHub." -ForegroundColor Green

