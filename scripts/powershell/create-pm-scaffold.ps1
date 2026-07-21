# Create .pm governance scaffold (Windows helper, mirrors scripts/python/create_pm_scaffold.py)
param(
    [Parameter(Mandatory = $false)]
    [string]$ProjectRoot = "."
)

$ErrorActionPreference = "Stop"
$root = (Resolve-Path $ProjectRoot).Path
$packRoot = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
$py = Join-Path $packRoot "scripts\python\create_pm_scaffold.py"

if (Get-Command python -ErrorAction SilentlyContinue) {
    python $py $root
    exit $LASTEXITCODE
}

Write-Host "Python not found; creating minimal .pm tree manually..."
$pm = Join-Path $root ".pm"
@(
    "config", "state", "charter", "outline", "inbox\stacks", "evidence\scans",
    "bugs\incidents", "architecture", "engineering", "environments", "integration",
    "testing", "release", "database", "operations", "cost"
) | ForEach-Object {
    New-Item -ItemType Directory -Force -Path (Join-Path $pm $_) | Out-Null
}

$gitExclude = Join-Path $root ".git\info\exclude"
if (Test-Path (Join-Path $root ".git")) {
    $dir = Split-Path $gitExclude -Parent
    New-Item -ItemType Directory -Force -Path $dir | Out-Null
    $content = if (Test-Path $gitExclude) { Get-Content $gitExclude -Raw } else { "" }
    if ($content -notmatch '(?m)^\s*\.pm/\s*$') {
        Add-Content -Path $gitExclude -Value "`n# PM governance workbench (local only)`n.pm/"
    }
}

Write-Host "scaffolded $pm (minimal). Prefer Python script for full templates."
