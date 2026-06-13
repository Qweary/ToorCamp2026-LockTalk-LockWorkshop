# lock.ps1 — the attendee's one CLI command on Windows. Run it from ANYWHERE in
# the cloned repo and it drives the whole no-hardware workshop flow.
#
#     .\lock.ps1 read --all
#     .\lock.ps1 write --code 420420 --slot 32 --role elevated
#     .\lock.ps1 recover
#     .\lock.ps1 build mydump.bin myinjected.bin
#
# What it does: a thin, cwd-robust dispatcher over the bundled Python tools, so
# the handout's one set of commands is correct everywhere. (The live-chip path
# is Linux-only; Windows is the no-hardware lane — see start.ps1.)
#
# PATH-RELATIVE BY DESIGN: the install root is resolved from this script's own
# location ($PSScriptRoot), so the repo can be cloned anywhere.

$ErrorActionPreference = 'Continue'

# ---------------------------------------------------------------------------
# Resolve the install root from this script's own location. lock.ps1 lives at
# the repo root, so $PSScriptRoot IS the root in the cloned-repo layout.
# ---------------------------------------------------------------------------
$Root = $PSScriptRoot

# ---------------------------------------------------------------------------
# Dual-layout tools-dir probe (mirrors bin/lock). Tools live under
# workshop\kit\tools in the cloned repo, and under tools\ (a sibling of this
# script) in an extracted kit / installed tree. Use whichever has lock-tool.py.
# ---------------------------------------------------------------------------
$ToolsDir = $null
foreach ($cand in @((Join-Path $Root 'workshop\kit\tools'), (Join-Path $Root 'tools'))) {
    if (Test-Path -LiteralPath (Join-Path $cand 'lock-tool.py')) {
        $ToolsDir = $cand
        break
    }
}

if (-not $ToolsDir) {
    Write-Host '==> Could not locate the workshop tools directory.'
    Write-Host "    Looked for lock-tool.py under:"
    Write-Host "      $(Join-Path $Root 'workshop\kit\tools')   (cloned-repo layout)"
    Write-Host "      $(Join-Path $Root 'tools')                (extracted-kit layout)"
    Write-Host '    The clone or kit looks incomplete — re-clone or re-extract.'
    exit 1
}

$LockTool = Join-Path $ToolsDir 'lock-tool.py'
$Recover  = Join-Path $ToolsDir 'recover-baseline.py'
$Build    = Join-Path $ToolsDir 'build-injected.py'

# No MINIPRO_HOME here by design — the bundled minipro binary is a Linux ELF and
# the live path never runs on Windows (same rationale as start.ps1).

# ---------------------------------------------------------------------------
# Find a Python launcher. Prefer 'python'; fall back to the 'py' launcher.
# ---------------------------------------------------------------------------
$PyExe = $null
if (Get-Command python -ErrorAction SilentlyContinue) {
    $PyExe = 'python'
} elseif (Get-Command py -ErrorAction SilentlyContinue) {
    $PyExe = 'py'
}
if (-not $PyExe) {
    Write-Host '==> Python was not found on your PATH.'
    Write-Host '    The lock tools need Python 3. Install it from https://www.python.org/downloads/'
    Write-Host '    (check "Add python.exe to PATH"), then re-run .\lock.ps1'
    exit 127
}

function Write-Usage {
    Write-Host 'lock.ps1 — cwd-robust CLI for the Dead Bytes Tell No Lies workshop.'
    Write-Host ''
    Write-Host 'Usage:'
    Write-Host '    .\lock.ps1 read    [--dump PATH] [--all]'
    Write-Host '    .\lock.ps1 write    --code DIGITS [--slot N] [--role ROLE]'
    Write-Host '    .\lock.ps1 recover  [--baseline PATH] [--yes] [--skip-verify]'
    Write-Host '    .\lock.ps1 build    SRC.bin DST.bin'
    Write-Host ''
    Write-Host '    (The --live path is Linux-only; Windows is the no-hardware lane.)'
    Write-Host "    Tools dir in use: $ToolsDir"
}

# ---------------------------------------------------------------------------
# Dispatch. Pass remaining args through verbatim; preserve the python exit code.
# ---------------------------------------------------------------------------
if ($args.Count -eq 0) {
    Write-Usage
    exit 2
}

$Sub = $args[0]
$Rest = @()
if ($args.Count -gt 1) { $Rest = $args[1..($args.Count - 1)] }

switch ($Sub) {
    { $_ -in @('read', 'write') } {
        & $PyExe $LockTool $Sub @Rest
        exit $LASTEXITCODE
    }
    'recover' {
        & $PyExe $Recover @Rest
        exit $LASTEXITCODE
    }
    'build' {
        & $PyExe $Build @Rest
        exit $LASTEXITCODE
    }
    { $_ -in @('-h', '--help', 'help') } {
        Write-Usage
        exit 0
    }
    default {
        Write-Host "==> Unknown subcommand: $Sub"
        Write-Host ''
        Write-Usage
        exit 2
    }
}
