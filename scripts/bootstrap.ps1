<#
.SYNOPSIS
Creates or updates the repository-local Python development environment.

.DESCRIPTION
Discovers Python 3.10 or newer, creates .venv when needed, installs the
project with its development dependencies, and validates the installed
dependency set. An existing .venv is reused.

.PARAMETER Python
Optional path or command name for the base Python interpreter. When omitted,
the script checks UPREF_PYTHON and common Windows Python launchers.

.EXAMPLE
.\scripts\bootstrap.ps1

.EXAMPLE
.\scripts\bootstrap.ps1 -Python "C:\Python314\python.exe"

.OUTPUTS
None. Progress and errors are written to the host streams.
#>
[CmdletBinding()]
param(
    [Parameter()]
    [string] $Python
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$ProjectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$VenvPath = Join-Path $ProjectRoot ".venv"
$VenvPython = Join-Path $VenvPath "Scripts\python.exe"

function Resolve-PythonCandidate {
    <#
    .SYNOPSIS
    Resolves and validates one possible Python interpreter.

    .PARAMETER Label
    Human-readable candidate name used in diagnostics.

    .PARAMETER Executable
    Executable path or application name to resolve.

    .PARAMETER Arguments
    Arguments placed before Python's command-line options, such as -3 for py.

    .OUTPUTS
    A candidate object for Python 3.10 or newer, or $null when unavailable.
    #>
    param(
        [Parameter(Mandatory = $true)]
        [string] $Label,

        [Parameter(Mandatory = $true)]
        [string] $Executable,

        [Parameter()]
        [string[]] $Arguments = @()
    )

    try {
        if (Test-Path -LiteralPath $Executable -PathType Leaf) {
            $ResolvedExecutable = (Resolve-Path -LiteralPath $Executable).Path
        }
        else {
            $Command = Get-Command -Name $Executable -CommandType Application -ErrorAction Stop
            $ResolvedExecutable = $Command.Source
        }

        & $ResolvedExecutable @Arguments -c "import sys; raise SystemExit(0 if sys.version_info >= (3, 10) else 1)" *> $null
        if ($LASTEXITCODE -ne 0) {
            return $null
        }

        return [PSCustomObject]@{
            Label = $Label
            Executable = $ResolvedExecutable
            Arguments = $Arguments
        }
    }
    catch {
        Write-Verbose "Python candidate '$Label' is unavailable: $($_.Exception.Message)"
        return $null
    }
}

function Find-BasePython {
    <#
    .SYNOPSIS
    Selects the first available Python 3.10-or-newer interpreter.

    .DESCRIPTION
    Honors the -Python parameter first, then UPREF_PYTHON, a common local
    installation path, the py launcher, python, and python3.

    .OUTPUTS
    A validated candidate object containing its label, executable, and
    launcher arguments.

    .NOTES
    Throws when an explicit interpreter is invalid or no candidate is found.
    #>
    if ($Python) {
        $Explicit = Resolve-PythonCandidate -Label "-Python" -Executable $Python
        if ($null -eq $Explicit) {
            throw "The interpreter provided with -Python is unavailable or older than Python 3.10: $Python"
        }
        return $Explicit
    }

    $Candidates = @()

    if ($env:UPREF_PYTHON) {
        $Candidates += [PSCustomObject]@{
            Label = "UPREF_PYTHON"
            Executable = $env:UPREF_PYTHON
            Arguments = [string[]] @()
        }
    }

    if ($env:LOCALAPPDATA) {
        $Candidates += [PSCustomObject]@{
            Label = "LOCALAPPDATA"
            Executable = (Join-Path $env:LOCALAPPDATA "Python\bin\python.exe")
            Arguments = [string[]] @()
        }
    }

    $Candidates += [PSCustomObject]@{
        Label = "py -3"
        Executable = "py"
        Arguments = [string[]] @("-3")
    }
    $Candidates += [PSCustomObject]@{
        Label = "python"
        Executable = "python"
        Arguments = [string[]] @()
    }
    $Candidates += [PSCustomObject]@{
        Label = "python3"
        Executable = "python3"
        Arguments = [string[]] @()
    }

    foreach ($Candidate in $Candidates) {
        $Resolved = Resolve-PythonCandidate `
            -Label $Candidate.Label `
            -Executable $Candidate.Executable `
            -Arguments $Candidate.Arguments
        if ($null -ne $Resolved) {
            return $Resolved
        }
    }

    throw "Python 3.10 or newer was not found. Use -Python or set UPREF_PYTHON."
}

try {
    if (-not (Test-Path -LiteralPath $VenvPython -PathType Leaf)) {
        $BasePython = Find-BasePython
        Write-Host "Creating .venv with Python from $($BasePython.Label)..."
        & $BasePython.Executable @($BasePython.Arguments) -m venv $VenvPath
        if ($LASTEXITCODE -ne 0) {
            throw "Python failed to create the virtual environment (exit code $LASTEXITCODE)."
        }
    }
    else {
        Write-Host "Using existing environment: $VenvPath"
    }

    if (-not (Test-Path -LiteralPath $VenvPython -PathType Leaf)) {
        throw "The virtual environment does not contain Scripts\python.exe: $VenvPath"
    }

    & $VenvPython -c "import sys; raise SystemExit(0 if sys.version_info >= (3, 10) else 1)"
    if ($LASTEXITCODE -ne 0) {
        throw "The virtual environment must use Python 3.10 or newer."
    }

    Push-Location $ProjectRoot
    try {
        & $VenvPython -m pip install --upgrade pip
        if ($LASTEXITCODE -ne 0) {
            throw "pip upgrade failed (exit code $LASTEXITCODE)."
        }

        & $VenvPython -m pip install -e ".[dev]"
        if ($LASTEXITCODE -ne 0) {
            throw "Development dependency installation failed (exit code $LASTEXITCODE)."
        }

        & $VenvPython -m pip check
        if ($LASTEXITCODE -ne 0) {
            throw "pip check reported incompatible dependencies (exit code $LASTEXITCODE)."
        }
    }
    finally {
        Pop-Location
    }

    Write-Host "Development environment ready: $VenvPython"
    exit 0
}
catch {
    Write-Error $_
    exit 1
}
