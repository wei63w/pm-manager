param(
    [Parameter(Mandatory = $true)]
    [string]$TargetProject
)

$ErrorActionPreference = "Stop"
$pack = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
$srcDir = Join-Path $pack "adapters\claude-code\commands"
$dest = Join-Path (Resolve-Path $TargetProject) ".claude\commands"

if (-not (Test-Path $srcDir)) {
    throw "Missing $srcDir — run adapter generator first"
}

New-Item -ItemType Directory -Force -Path $dest | Out-Null
Copy-Item -Force (Join-Path $srcDir "*.md") $dest
# Also drop a pointer to pack for templates
$pointer = Join-Path (Resolve-Path $TargetProject) ".claude\pm-manager-pack.path"
Set-Content -Path $pointer -Value $pack -Encoding utf8
Write-Host "Installed Claude commands -> $dest"
Write-Host "Pack path written to $pointer"
