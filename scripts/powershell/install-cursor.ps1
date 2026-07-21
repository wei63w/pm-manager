param(
    [Parameter(Mandatory = $true)]
    [string]$TargetProject
)

$ErrorActionPreference = "Stop"
$pack = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
$dest = Join-Path (Resolve-Path $TargetProject) ".cursor\skills\pm-manager"

New-Item -ItemType Directory -Force -Path $dest | Out-Null
# Copy whole pack so templates/scripts resolve relative to SKILL.md
$items = @("SKILL.md", "AGENTS.md", "README.md", "templates", "scripts", "memory")
foreach ($i in $items) {
    $src = Join-Path $pack $i
    $dst = Join-Path $dest $i
    if (Test-Path $src -PathType Container) {
        if (Test-Path $dst) { Remove-Item -Recurse -Force $dst }
        Copy-Item -Recurse -Force $src $dst
    } elseif (Test-Path $src) {
        Copy-Item -Force $src $dst
    }
}
Write-Host "Installed Cursor skill pack -> $dest"
Write-Host "Optional: also copy adapters\cursor\skills\pm-* for per-command skills."
