param(
    [switch]$Force
)

$ErrorActionPreference = "Stop"
$RepoRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$SourceDir = Join-Path $RepoRoot "minecraft-mod-dev"
$CodexHome = if ($env:CODEX_HOME) { $env:CODEX_HOME } else { Join-Path $HOME ".codex" }
$SkillsDir = Join-Path $CodexHome "skills"
$TargetDir = Join-Path $SkillsDir "minecraft-mod-dev"

if (-not (Test-Path (Join-Path $SourceDir "SKILL.md")) -or
    -not (Test-Path (Join-Path $SourceDir "agents/openai.yaml"))) {
    throw "Invalid package: required skill files are missing."
}

New-Item -ItemType Directory -Force -Path $SkillsDir | Out-Null

if (Test-Path $TargetDir) {
    if (-not $Force) {
        throw "Target already exists: $TargetDir. Re-run with -Force to replace it and retain a backup."
    }

    $Timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
    $BackupDir = "$TargetDir.backup-$Timestamp"
    Move-Item -Path $TargetDir -Destination $BackupDir
    Write-Host "Existing installation moved to $BackupDir"
}

Copy-Item -Recurse -Path $SourceDir -Destination $TargetDir
Write-Host "Installed minecraft-mod-dev to $TargetDir"
Write-Host "The skill will be available from the next Codex turn."
