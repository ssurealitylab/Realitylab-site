<#
.SYNOPSIS
    Windows counterpart of dev/stop_all.sh — stops what serve_all.ps1 started.

.DESCRIPTION
    Kills by recorded PID, then sweeps orphans by command line. bundle.bat is a
    shim that spawns ruby, so killing the recorded PID alone leaves the Jekyll
    server holding its port -- the same reason stop_all.sh follows up with
    `pkill -f "jekyll serve"`.

    Only processes matching this repo's dev ports are touched: the production
    chatbot (4105) and its tunnel must survive.
#>
[CmdletBinding()]
param(
    [ValidateSet('all', 'jekyll', 'chatbot', 'admin')]
    [string] $What = 'all',

    [int] $JekyllPort  = 4001,
    [int] $ChatbotPort = 4205,
    [int] $AdminPort   = 4210
)

$LogDir = Join-Path $env:TEMP 'reality-dev'

function Stop-ByPidFile {
    param([string] $Name)
    $pidFile = Join-Path $LogDir "$Name.pid"
    if (-not (Test-Path $pidFile)) { Write-Host "[$Name] no pidfile - nothing to stop"; return }
    $procId = (Get-Content $pidFile -Raw).Trim()
    if ($procId -and (Get-Process -Id $procId -ErrorAction SilentlyContinue)) {
        Stop-Process -Id $procId -Force -ErrorAction SilentlyContinue
        Write-Host "[$Name] killed PID $procId"
    } else {
        Write-Host "[$Name] PID $procId no longer running"
    }
    Remove-Item $pidFile -Force -ErrorAction SilentlyContinue
}

function Stop-ByPort {
    # Orphaned children keep the listener open after the shim dies.
    param([string] $Name, [int] $Port)
    Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue |
        Select-Object -ExpandProperty OwningProcess -Unique |
        ForEach-Object {
            Stop-Process -Id $_ -Force -ErrorAction SilentlyContinue
            Write-Host "[$Name] killed orphan PID $_ holding port $Port"
        }
}

if ($What -in @('all', 'jekyll'))  { Stop-ByPidFile 'jekyll';  Stop-ByPort 'jekyll'  $JekyllPort }
if ($What -in @('all', 'chatbot')) { Stop-ByPidFile 'chatbot'; Stop-ByPort 'chatbot' $ChatbotPort }
if ($What -in @('all', 'admin'))   { Stop-ByPidFile 'admin';   Stop-ByPort 'admin'   $AdminPort }
