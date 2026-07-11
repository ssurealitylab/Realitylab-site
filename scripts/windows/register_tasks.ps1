<#
.SYNOPSIS
    Register the four at-logon scheduled tasks that keep the live chatbot and
    Admin CMS running on this machine.

.DESCRIPTION
    Run once (after a fresh clone, or to repair the tasks):

        powershell -ExecutionPolicy Bypass -File scripts\windows\register_tasks.ps1

    Creates, at logon:
      RealityLab-Chatbot      chatbot backend      127.0.0.1:4105
      RealityLab-Admin        Admin CMS            127.0.0.1:4100
      RealityLab-Tunnel       tunnel + chatbot.html / bug-report.html URL sync
      RealityLab-AdminTunnel  tunnel + admin.html URL sync

    Several things here are load-bearing, all learned the hard way. Each one, on
    its own, produced the same visible symptom: the backends dead, their tunnels
    still up and pointing at nothing, and the public site showing its "the GPU is
    busy training" fallback on a machine that was wide awake.

      * The action runs powershell.exe by ABSOLUTE path. Task Scheduler does not
        resolve the executable against PATH; a bare 'powershell.exe' fails the
        task with 0x80070002 (file not found).

      * The action runs the .ps1 directly, NOT `cmd /c foo.bat`. Through cmd the
        backends got a console, and at logon that console was torn down under
        them -- they died with 0xC000013A (STATUS_CONTROL_C_EXIT) seconds after
        starting.

      * RestartCount is high, so a task that dies comes back a minute later
        rather than staying dead until someone notices the site is broken.

    KNOWN LIMITATION: these run as Interactive, so they live in the user's
    desktop session and logging off kills them (0xC000013A again). Locking the
    screen is fine; signing out is not. Fixing it properly means -LogonType S4U
    and an -AtStartup trigger, which need an elevated PowerShell -- run this
    script as administrator and swap those in if you want that.
#>
[CmdletBinding()]
param(
    [string] $RepoRoot,
    [string] $Cloudflared = "$env:USERPROFILE\Desktop\RS\bin\cloudflared.exe"
)

$ErrorActionPreference = 'Stop'
if (-not $RepoRoot) { $RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path }

# Check before touching anything. Each task is unregistered before it is
# re-registered, so failing halfway through leaves tasks *deleted* -- which is
# how RealityLab-Chatbot once vanished while the site was live.
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()
           ).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $isAdmin) {
    Write-Host 'This script needs an elevated PowerShell.' -ForegroundColor Red
    Write-Host 'S4U and the at-startup trigger cannot be registered as a normal user;'
    Write-Host 'without them the backends die whenever you sign out.'
    Write-Host ''
    Write-Host 'Right-click PowerShell -> Run as administrator, then:'
    Write-Host "  powershell -ExecutionPolicy Bypass -File `"$PSCommandPath`""
    exit 1
}

$win = Join-Path $RepoRoot 'scripts\windows'
$ps  = "$env:SystemRoot\System32\WindowsPowerShell\v1.0\powershell.exe"
$user = "$env:USERDOMAIN\$env:USERNAME"

$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries -StartWhenAvailable `
    -RestartCount 999 -RestartInterval (New-TimeSpan -Minutes 1) `
    -ExecutionTimeLimit ([TimeSpan]::Zero)

# S4U, not Interactive: an Interactive task lives inside the user's desktop
# session, so signing out tears the backends down with 0xC000013A while their
# tunnels stay up, and the site sits on its "GPU is busy" fallback. S4U runs
# detached from any session, still as this user -- so the conda env and the git
# credentials in Credential Manager stay reachable -- and stores no password.
#
# Needs an elevated PowerShell. Without it Register-ScheduledTask fails with
# "Access is denied", and this script deliberately says so rather than silently
# falling back to Interactive, which is what left the machine broken before.
$principal = New-ScheduledTaskPrincipal -UserId $user -LogonType S4U -RunLevel Limited

# At startup as well as at logon, so a reboot brings the site back whether or not
# anyone signs in.
$trigger = @(
    New-ScheduledTaskTrigger -AtStartup
    New-ScheduledTaskTrigger -AtLogOn -User $user
)

$tasks = @(
    @{ Name = 'RealityLab-Chatbot';     Script = "$win\run_backend.ps1";     Extra = @('-Service', 'chatbot'); Desc = 'Reality Lab chatbot backend (127.0.0.1:4105)' },
    @{ Name = 'RealityLab-Admin';       Script = "$win\run_backend.ps1";     Extra = @('-Service', 'admin');   Desc = 'Reality Lab Admin CMS (127.0.0.1:4100)' },
    @{ Name = 'RealityLab-Tunnel';      Script = "$win\tunnel_watchdog.ps1"; Extra = @('-Service', 'chatbot', '-Cloudflared', $Cloudflared); Desc = 'Cloudflare tunnel + chatbot.html URL watchdog' },
    @{ Name = 'RealityLab-AdminTunnel'; Script = "$win\tunnel_watchdog.ps1"; Extra = @('-Service', 'admin',   '-Cloudflared', $Cloudflared); Desc = 'Cloudflare tunnel + admin.html URL watchdog' }
)

foreach ($t in $tasks) {
    $argList = @('-NoProfile', '-ExecutionPolicy', 'Bypass', '-WindowStyle', 'Hidden',
                 '-File', "`"$($t.Script)`"") + $t.Extra
    $action = New-ScheduledTaskAction -Execute $ps -Argument ($argList -join ' ') -WorkingDirectory $RepoRoot

    if (Get-ScheduledTask -TaskName $t.Name -ErrorAction SilentlyContinue) {
        Unregister-ScheduledTask -TaskName $t.Name -Confirm:$false
    }
    Register-ScheduledTask -TaskName $t.Name -Action $action -Trigger $trigger `
        -Principal $principal -Settings $settings -Description $t.Desc | Out-Null
    Write-Host "registered: $($t.Name)"
}

Write-Host ''
Write-Host 'Start them now without logging out:'
Write-Host "  Get-ScheduledTask -TaskName 'RealityLab-*' | Start-ScheduledTask"
Get-ScheduledTask -TaskName 'RealityLab-*' | Select-Object TaskName, State |
    Format-Table -AutoSize | Out-String | Write-Host
