param(
    [string]$SourceRoot = "C:\Users\Nicho\Development",
    [string]$BackupRoot = "",
    [switch]$WhatIf
)

$ErrorActionPreference = "Stop"

if (-not $BackupRoot) {
    if ($env:OneDrive) {
        $BackupRoot = Join-Path $env:OneDrive "Backups\Dev-NonGit-AI"
    } else {
        $BackupRoot = "C:\Users\Nicho\OneDrive\Backups\Dev-NonGit-AI"
    }
}

$repoNames = @("Dealhound", "GardenPlanner", "HaC", "homeassistant", "UserBrowser")

$namePatterns = @(
    "AGENTS.md",
    "copilot-instructions.md",
    "*.instructions.md",
    "*.agent.md",
    "*.prompt.md",
    "SKILL.md"
)

$pathRegexes = @(
    "(^|\\)\.ai(\\|$)",
    "(^|\\)\.continue(\\|$)",
    "(^|\\)\.github\\agents(\\|$)",
    "(^|\\)\.github\\prompts(\\|$)",
    "(^|\\)\.github\\instructions(\\|$)"
)

function Test-Match {
    param([System.IO.FileInfo]$File)

    foreach ($pat in $namePatterns) {
        if ($File.Name -like $pat) { return $true }
    }

    foreach ($rx in $pathRegexes) {
        if ($File.FullName -match $rx) { return $true }
    }

    return $false
}

$timestamp = Get-Date -Format "yyyy-MM-dd_HH-mm-ss"
$manifest = @()

if (-not (Test-Path $BackupRoot)) {
    New-Item -ItemType Directory -Path $BackupRoot -Force | Out-Null
}

foreach ($repo in $repoNames) {
    $repoPath = Join-Path $SourceRoot $repo
    if (-not (Test-Path $repoPath)) { continue }

    $files = Get-ChildItem -Path $repoPath -Recurse -File -Force -ErrorAction SilentlyContinue |
        Where-Object {
            $_.FullName -notmatch "\\.git(\\|$)" -and
            $_.FullName -notmatch "\\node_modules(\\|$)" -and
            (Test-Match -File $_)
        }

    foreach ($file in $files) {
        $relativePath = $file.FullName.Substring($repoPath.Length).TrimStart("\\")
        $targetPath = Join-Path (Join-Path $BackupRoot $repo) $relativePath
        $targetDir = Split-Path -Parent $targetPath

        if (-not (Test-Path $targetDir)) {
            New-Item -ItemType Directory -Path $targetDir -Force | Out-Null
        }

        Copy-Item -Path $file.FullName -Destination $targetPath -Force -WhatIf:$WhatIf

        $manifest += [PSCustomObject]@{
            repo = $repo
            source = $file.FullName
            destination = $targetPath
            size = $file.Length
            modified = $file.LastWriteTimeUtc.ToString("o")
        }
    }
}

$manifestPath = Join-Path $BackupRoot ("manifest_" + $timestamp + ".json")
$manifest | ConvertTo-Json -Depth 4 | Set-Content -Path $manifestPath -Encoding UTF8

Write-Output "Backed up $($manifest.Count) AI-related files to $BackupRoot"
Write-Output "Manifest: $manifestPath"