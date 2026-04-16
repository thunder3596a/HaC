param(
    [string]$OutputDir = "",
    [switch]$Clean
)

$ErrorActionPreference = "Stop"

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$repoRoot = Split-Path -Parent $scriptDir

if (-not $OutputDir) {
    $OutputDir = Join-Path $repoRoot "development/rag/pilot-corpus"
}

$filesDir = Join-Path $OutputDir "files"
$manifestPath = Join-Path $OutputDir "manifest.json"

$includePatterns = @(
    "README.md",
    "GETTING_STARTED.md",
    ".github/copilot-instructions.md",
    "Docker-Critical/**/*.yml",
    "Docker-Critical/**/*.yaml",
    "Docker-Critical/**/README.md",
    "Docker-NonCritical/**/*.yml",
    "Docker-NonCritical/**/*.yaml",
    "Docker-NonCritical/**/README.md",
    ".forgejo/workflows/deploy-*.yml",
    ".forgejo/workflows/check-updates-*.yml",
    ".forgejo/workflows/apply-updates-*.yml",
    ".forgejo/issue_template/*.md",
    "scripts/*.ps1",
    "scripts/*.sh",
    "scripts/generate-container-sensors.py"
)

$excludePatterns = @(
    "**/.env",
    "**/.env.*",
    "scripts/required-secrets.txt",
    "**/*secret*",
    "**/*token*",
    "**/*password*",
    "**/*private*",
    "**/acme.json",
    ".git/**",
    ".venv/**",
    "node_modules/**",
    "**/*.log",
    "**/*.sqlite*",
    "**/*checksum*",
    "Docker-Critical/Home/HomeAssistant/config/**",
    ".ai/**"
)

function Convert-GlobToRegex {
    param([string]$Pattern)

    $normalized = $Pattern.Replace('\', '/')
    $builder = New-Object System.Text.StringBuilder

    for ($i = 0; $i -lt $normalized.Length; $i++) {
        $ch = $normalized[$i]

        if ($ch -eq '*') {
            $nextIsStar = ($i + 1 -lt $normalized.Length) -and ($normalized[$i + 1] -eq '*')
            if ($nextIsStar) {
                [void]$builder.Append('.*')
                $i++
            }
            else {
                [void]$builder.Append('[^/]*')
            }
            continue
        }

        if ($ch -eq '?') {
            [void]$builder.Append('[^/]')
            continue
        }

        [void]$builder.Append([regex]::Escape([string]$ch))
    }

    return '^' + $builder.ToString() + '$'
}

$includeMatchers = $includePatterns | ForEach-Object { [regex]::new((Convert-GlobToRegex -Pattern $_), [System.Text.RegularExpressions.RegexOptions]::IgnoreCase) }
$excludeMatchers = $excludePatterns | ForEach-Object { [regex]::new((Convert-GlobToRegex -Pattern $_), [System.Text.RegularExpressions.RegexOptions]::IgnoreCase) }

function Test-MatchesAny {
    param(
        [string]$Path,
        [System.Text.RegularExpressions.Regex[]]$Matchers
    )

    foreach ($matcher in $Matchers) {
        if ($matcher.IsMatch($Path)) {
            return $true
        }
    }

    return $false
}

if ($Clean -and (Test-Path $OutputDir)) {
    Remove-Item -Path $OutputDir -Recurse -Force
}

if (-not (Test-Path $OutputDir)) {
    New-Item -Path $OutputDir -ItemType Directory -Force | Out-Null
}

if (-not (Test-Path $filesDir)) {
    New-Item -Path $filesDir -ItemType Directory -Force | Out-Null
}

$allFiles = Get-ChildItem -Path $repoRoot -File -Recurse
$selected = New-Object System.Collections.Generic.List[object]

foreach ($file in $allFiles) {
    $relPath = [System.IO.Path]::GetRelativePath($repoRoot, $file.FullName).Replace('\', '/')

    if (-not (Test-MatchesAny -Path $relPath -Matchers $includeMatchers)) {
        continue
    }

    if (Test-MatchesAny -Path $relPath -Matchers $excludeMatchers) {
        continue
    }

    $selected.Add([pscustomobject]@{
        path = $relPath
        bytes = $file.Length
        modifiedUtc = $file.LastWriteTimeUtc.ToString('o')
    })
}

foreach ($item in $selected) {
    $sourcePath = Join-Path $repoRoot $item.path
    $destPath = Join-Path $filesDir $item.path
    $destDir = Split-Path -Parent $destPath

    if (-not (Test-Path $destDir)) {
        New-Item -Path $destDir -ItemType Directory -Force | Out-Null
    }

    Copy-Item -Path $sourcePath -Destination $destPath -Force
}

$manifest = [pscustomobject]@{
    generatedAtUtc = (Get-Date).ToUniversalTime().ToString('o')
    repoRoot = $repoRoot
    outputDir = $OutputDir
    policy = [pscustomobject]@{
        include = $includePatterns
        exclude = $excludePatterns
    }
    totals = [pscustomobject]@{
        files = $selected.Count
        bytes = ($selected | Measure-Object -Property bytes -Sum).Sum
    }
    files = $selected | Sort-Object -Property path
}

$manifest | ConvertTo-Json -Depth 8 | Set-Content -Path $manifestPath -Encoding UTF8

Write-Host "Exported $($selected.Count) files to $filesDir"
Write-Host "Manifest: $manifestPath"
