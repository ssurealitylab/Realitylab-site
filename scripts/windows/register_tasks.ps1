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

    Two things here are load-bearing, both learned the hard way:

      * The action runs powershell.exe by ABSOLUTE path. Task Scheduler does not
        resolve the executable against PATH; a bare 'powershell.exe' fails the
        task with 0x80070002 (file not found).

      * The action runs the .ps1 directly, NOT `cmd /c foo.bat`. Wrapping them in
        cmd gave the backends a console, and at logon that console was torn down
        under them: both died with 0xC000013A (STATUS_CONTROL_C_EXIT) seconds
        after starting, while their tunnels stayed up pointing at nothing. The
        public site then showed its "GPU is busy" fallback on a machine that was
        perfectly awake.
#>
[CmdletBinding()]
param(
    [string] $RepoRoot,
    [string] $Cloudflared = "$env:USERPROFILE\Desktop\RS\bin\cloudflared.exe"
)

$ErrorActionPreference = 'Stop'
if (-not $RepoRoot) { $RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path }

$win = Join-Path $RepoRoot 'scripts\windows'
$ps  = "$env:SystemRoot\System32\WindowsPowerShell\v1.0\powershell.exe"
$user = "$env:USERDOMAIN\$env:USERNAME"

$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries -StartWhenAvailable `
    -RestartCount 3 -RestartInterval (New-TimeSpan -Minutes 1) `
    -ExecutionTimeLimit ([TimeSpan]::Zero)

# Interactive: the tasks need the user's profile (conda env, git credentials).
$principal = New-ScheduledTaskPrincipal -UserId $user -LogonType Interactive -RunLevel Limited
$trigger   = New-ScheduledTaskTrigger -AtLogOn -User $user

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
