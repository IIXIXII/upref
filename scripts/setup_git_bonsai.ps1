<#
.SYNOPSIS
Installs the pinned Windows x64 Git Bonsai release for this checkout.

.DESCRIPTION
Downloads the official archive, checks its SHA-256 hash, and installs the
executable and upstream license under .tools. Registers a repository-local
git bonsai alias and protects master. Does not run branch maintenance.

.EXAMPLE
.\scripts\setup_git_bonsai.ps1
#>
[CmdletBinding()]
param()

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$ProjectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$Version = "0.3.0"
$ArchiveName = "git-bonsai-$Version-x86_64-windows.tar.bz2"
$ArchiveUrl = "https://github.com/agateau/git-bonsai/releases/download/$Version/$ArchiveName"
$ArchiveSha256 = "fa365a7ff1e569fdf772508daa24baff999be5172df58aaf49afa5b2aaeee019"
$InstallDirectory = Join-Path $ProjectRoot ".tools\git-bonsai"
$ArchivePath = Join-Path $InstallDirectory $ArchiveName
$Executable = Join-Path $InstallDirectory "git-bonsai.exe"
$AliasValue = "!.tools/git-bonsai/git-bonsai.exe"

try {
    if ($env:OS -ne "Windows_NT" -or
        [System.Runtime.InteropServices.RuntimeInformation]::OSArchitecture.ToString() -ne "X64") {
        throw "This installer requires Windows x64. See docs/development.rst for other platforms."
    }
    $Git = (Get-Command git -CommandType Application -ErrorAction Stop).Source
    $Tar = (Get-Command tar -CommandType Application -ErrorAction Stop).Source

    & $Git -C $ProjectRoot rev-parse --git-dir | Out-Null
    if ($LASTEXITCODE -ne 0) { throw "Run this installer from an Upref Git checkout." }

    $ExistingAlias = & $Git -C $ProjectRoot config --local --get alias.bonsai
    if ($LASTEXITCODE -gt 1) { throw "Cannot read the local Git configuration." }
    if ($ExistingAlias -and $ExistingAlias -ne $AliasValue) {
        throw "A different local alias.bonsai already exists; keep or remove it before setup."
    }

    New-Item -ItemType Directory -Path $InstallDirectory -Force | Out-Null
    if (-not (Test-Path -LiteralPath $ArchivePath -PathType Leaf)) {
        Write-Host "Downloading Git Bonsai $Version from its official release..."
        Invoke-WebRequest -UseBasicParsing -Uri $ArchiveUrl -OutFile $ArchivePath
    }
    if ((Get-FileHash -LiteralPath $ArchivePath -Algorithm SHA256).Hash -ne $ArchiveSha256) {
        throw "Archive checksum mismatch. Remove '$ArchivePath' and run setup again."
    }

    & $Tar -xjf $ArchivePath -C $InstallDirectory --strip-components 1 `
        "git-bonsai-$Version/git-bonsai.exe" "git-bonsai-$Version/LICENSE"
    if ($LASTEXITCODE -ne 0) { throw "Could not extract Git Bonsai." }

    & $Executable --version
    if ($LASTEXITCODE -ne 0) { throw "The installed Git Bonsai executable could not run." }

    & $Git -C $ProjectRoot config --local alias.bonsai $AliasValue
    if ($LASTEXITCODE -ne 0) { throw "Could not register the local git bonsai alias." }
    & $Git -C $ProjectRoot config --local git-bonsai.default-branch master
    if ($LASTEXITCODE -ne 0) { throw "Could not configure the default branch." }

    $ProtectedBranches = @(& $Git -C $ProjectRoot config --local --get-all git-bonsai.protected-branches)
    if ($LASTEXITCODE -gt 1) { throw "Cannot read protected branches." }
    if ($ProtectedBranches -cnotcontains "master") {
        & $Git -C $ProjectRoot config --local --add git-bonsai.protected-branches master
        if ($LASTEXITCODE -ne 0) { throw "Could not protect master." }
    }

    Write-Host "Git Bonsai is ready. Run 'git bonsai' or '.\make.bat bonsai' from this checkout."
}
catch {
    Write-Error $_
    exit 1
}
