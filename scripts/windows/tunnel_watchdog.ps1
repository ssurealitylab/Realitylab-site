<#
.SYNOPSIS
    Windows port of ai_server/restart_tunnel.sh + monitor_tunnel.sh.

.DESCRIPTION
    Owns a Cloudflare quick tunnel in front of the local chatbot, and keeps the
    hostname baked into the site in sync with it.

    A quick tunnel gets a fresh random *.trycloudflare.com hostname every time
    it starts, and the live site hardcodes that hostname in _includes/chatbot.html
    and _includes/bug-report.html. So whenever the tunnel rotates, the new URL has
    to be written into both files and pushed, or GitHub Pages keeps serving the
    stale hostname and the site's chatbot 502s even though the tunnel is healthy.

    Guards carried over from the shell scripts, all of which exist because
    Cloudflare rate-limits quick-tunnel creation:
      - lock file            one watchdog at a time
      - 429 detection        1 hour cooldown, persisted across runs
      - daily attempt cap    stop hammering after 20 tunnel creations in a day
      - exponential backoff  120s doubling to 30 min between retries

.NOTES
    The chatbot itself is not managed here; start it first (run-chatbot.bat).
#>
[CmdletBinding()]
param(
    # $PSScriptRoot is not yet bound while param defaults are evaluated, so the
    # repo root is resolved below rather than here.
    [string] $RepoRoot,
    [string] $Cloudflared = "$env:USERPROFILE\Desktop\RS\bin\cloudflared.exe",
    [int]    $Port       = 4105,
    [string] $Branch     = 'main',
    [int]    $CheckIntervalSec = 600,
    [switch] $Once
)

$ErrorActionPreference = 'Stop'

if (-not $RepoRoot) { $RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path }

$AiServer      = Join-Path $RepoRoot 'ai_server'
$ChatbotFile   = Join-Path $RepoRoot '_includes\chatbot.html'
$BugReportFile = Join-Path $RepoRoot '_includes\bug-report.html'
$LogFile       = Join-Path $AiServer 'tunnel_watchdog.log'
$TempLog       = Join-Path $AiServer 'tunnel_temp.log'
$LockFile      = Join-Path $AiServer 'restart_tunnel.lock'
$RateLimitFile = Join-Path $AiServer 'rate_limit_until.txt'
$DailyFile     = Join-Path $AiServer 'daily_attempts.txt'

$MAX_RETRIES         = 10
$INITIAL_DELAY       = 120
$MAX_DELAY           = 1800
$RATE_LIMIT_COOLDOWN = 3600
$DAILY_MAX_ATTEMPTS  = 20
$URL_RE              = 'https://[a-z0-9-]+\.trycloudflare\.com'

function Invoke-Git {
    # git writes ordinary progress to stderr. Under $ErrorActionPreference='Stop'
    # PowerShell 5.1 turns those lines into a terminating NativeCommandError, so
    # a *successful* push would abort this script. Run git with the preference
    # relaxed and judge it by its exit code instead.
    param([Parameter(ValueFromRemainingArguments)] [string[]] $GitArgs)
    $prev = $ErrorActionPreference
    $ErrorActionPreference = 'Continue'
    try {
        $output = & git @GitArgs 2>&1 | Out-String
        return [pscustomobject]@{ Code = $LASTEXITCODE; Output = $output.Trim() }
    } finally { $ErrorActionPreference = $prev }
}

function Write-Log {
    param([string] $Message)
    $line = "[{0}] {1}" -f (Get-Date -Format 'yyyy-MM-dd HH:mm:ss'), $Message
    Write-Host $line
    Add-Content -Path $LogFile -Value $line -Encoding utf8
}

function Get-SiteUrl {
    $m = Select-String -Path $ChatbotFile -Pattern "DIRECT_AI_SERVER_URL = '($URL_RE)'" | Select-Object -First 1
    if ($m) { return $m.Matches[0].Groups[1].Value }
    return $null
}

function Test-TunnelHealthy {
    param([string] $Url)
    try {
        $r = Invoke-WebRequest "$Url/health" -UseBasicParsing -TimeoutSec 20
        return $r.Content -match '"status"\s*:\s*"healthy"'
    } catch { return $false }
}

function Test-LocalChatbot {
    try {
        $r = Invoke-WebRequest "http://127.0.0.1:$Port/health" -UseBasicParsing -TimeoutSec 10
        return $r.Content -match 'healthy'
    } catch { return $false }
}

function Stop-Tunnel {
    # Match on the command line rather than the image name: other cloudflared
    # instances (e.g. the admin tunnel) must survive.
    Get-CimInstance Win32_Process -Filter "Name = 'cloudflared.exe'" -ErrorAction SilentlyContinue |
        Where-Object { $_.CommandLine -like "*--url http://127.0.0.1:$Port*" } |
        ForEach-Object {
            Write-Log "killing cloudflared pid $($_.ProcessId)"
            Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue
        }
}

function Test-RateLimited {
    if (-not (Test-Path $RateLimitFile)) { return $false }
    $until = [int64](Get-Content $RateLimitFile -Raw).Trim()
    $now = [DateTimeOffset]::UtcNow.ToUnixTimeSeconds()
    if ($now -lt $until) {
        Write-Log ("rate-limit cooldown active, {0} min remaining" -f [math]::Ceiling(($until - $now) / 60))
        return $true
    }
    Remove-Item $RateLimitFile -Force -ErrorAction SilentlyContinue
    return $false
}

function Set-RateLimitCooldown {
    $until = [DateTimeOffset]::UtcNow.ToUnixTimeSeconds() + $RATE_LIMIT_COOLDOWN
    Set-Content -Path $RateLimitFile -Value $until -Encoding ascii
    Write-Log "rate limit hit; cooling down $($RATE_LIMIT_COOLDOWN / 60) min"
}

function Step-DailyCount {
    $today = Get-Date -Format 'yyyy-MM-dd'
    $count = 0
    if (Test-Path $DailyFile) {
        $lines = @(Get-Content $DailyFile)
        if ($lines.Count -ge 2 -and $lines[0].Trim() -eq $today) { $count = [int]$lines[1].Trim() }
    }
    if ($count -ge $DAILY_MAX_ATTEMPTS) {
        Write-Log "daily tunnel-creation cap ($DAILY_MAX_ATTEMPTS) reached"
        return $false
    }
    Set-Content -Path $DailyFile -Value @($today, ($count + 1)) -Encoding ascii
    Write-Log "tunnel creation attempt $($count + 1)/$DAILY_MAX_ATTEMPTS today"
    return $true
}

function Reset-DailyCount {
    Set-Content -Path $DailyFile -Value @((Get-Date -Format 'yyyy-MM-dd'), 0) -Encoding ascii
}

function Publish-Url {
    param([string] $NewUrl)

    $oldUrl = Get-SiteUrl
    if ($oldUrl -eq $NewUrl) { Write-Log "site already points at $NewUrl"; return }

    Write-Log "updating site URL: $oldUrl -> $NewUrl"
    foreach ($f in @($ChatbotFile, $BugReportFile)) {
        if (-not (Test-Path $f)) { continue }
        $text = [IO.File]::ReadAllText($f)
        $updated = [regex]::Replace($text, "DIRECT_AI_SERVER_URL = '$URL_RE'", "DIRECT_AI_SERVER_URL = '$NewUrl'")
        if ($updated -ne $text) { [IO.File]::WriteAllText($f, $updated); Write-Log "  rewrote $(Split-Path $f -Leaf)" }
    }

    Push-Location $RepoRoot
    try {
        # Stage only the two files: `git add -A` would sweep whatever else the
        # working tree happens to be carrying on this machine.
        Invoke-Git add -- '_includes/chatbot.html' '_includes/bug-report.html' | Out-Null
        if ((Invoke-Git commit -m 'Auto-update Cloudflare Tunnel URL').Code -ne 0) {
            Write-Log 'nothing to commit'; return
        }

        for ($i = 1; $i -le 3; $i++) {
            if ((Invoke-Git push origin $Branch).Code -eq 0) { Write-Log "pushed (attempt $i)"; return }
            Write-Log "push attempt $i failed; pull --rebase"
            Invoke-Git rebase --abort | Out-Null
            if ((Invoke-Git pull --rebase origin $Branch).Code -ne 0) {
                Invoke-Git rebase --abort | Out-Null
                Write-Log 'rebase conflict; giving up'; return
            }
        }
        Write-Log 'WARNING: exhausted push attempts; GitHub Pages will serve the stale URL'
    } finally { Pop-Location }
}

function New-Tunnel {
    # Returns the tunnel URL, or $null.
    if (Test-RateLimited) { return $null }
    if (-not (Step-DailyCount)) { return $null }

    Stop-Tunnel
    Remove-Item $TempLog -Force -ErrorAction SilentlyContinue

    Start-Process -FilePath $Cloudflared `
        -ArgumentList @('tunnel', '--no-autoupdate', '--url', "http://127.0.0.1:$Port") `
        -RedirectStandardOutput "$TempLog.out" -RedirectStandardError "$TempLog" `
        -WindowStyle Hidden | Out-Null

    for ($w = 0; $w -lt 45; $w++) {
        Start-Sleep -Seconds 1
        if (-not (Test-Path $TempLog)) { continue }
        $log = Get-Content $TempLog -Raw -ErrorAction SilentlyContinue
        if (-not $log) { continue }

        $m = [regex]::Match($log, $URL_RE)
        if ($m.Success) { return $m.Value }

        if ($log -match '429 Too Many Requests') { Set-RateLimitCooldown; Stop-Tunnel; return $null }
        if ($log -match 'Error unmarshaling QuickTunnel|failed to unmarshal quick Tunnel') {
            Write-Log 'Cloudflare quick-tunnel API error'; Stop-Tunnel; return $null
        }
    }
    Write-Log 'timed out waiting for tunnel URL'
    Stop-Tunnel
    return $null
}

function Restart-TunnelWithBackoff {
    $delay = $INITIAL_DELAY
    for ($attempt = 1; $attempt -le $MAX_RETRIES; $attempt++) {
        Write-Log "tunnel create attempt $attempt/$MAX_RETRIES"
        $url = New-Tunnel
        if ($url) {
            Write-Log "tunnel URL: $url"
            Start-Sleep -Seconds 5   # let the edge finish registering the hostname
            if (Test-TunnelHealthy $url) {
                Write-Log 'tunnel health check passed'
                Publish-Url $url
                Reset-DailyCount
                return $url
            }
            Write-Log 'tunnel health check failed'
            Stop-Tunnel
        }
        if (Test-Path $RateLimitFile) { return $null }   # cooling down, do not spin
        if ($attempt -lt $MAX_RETRIES) {
            Write-Log "backing off ${delay}s"
            Start-Sleep -Seconds $delay
            $delay = [math]::Min($delay * 2, $MAX_DELAY)
        }
    }
    Write-Log "ERROR: could not establish a tunnel after $MAX_RETRIES attempts"
    return $null
}

# ---- lock ----------------------------------------------------------------
if (Test-Path $LockFile) {
    $lockPid = (Get-Content $LockFile -Raw).Trim()
    if ($lockPid -and (Get-Process -Id $lockPid -ErrorAction SilentlyContinue)) {
        Write-Log "another watchdog is running (pid $lockPid); exiting"
        exit 0
    }
    Write-Log 'stale lock file; removing'
    Remove-Item $LockFile -Force
}
Set-Content -Path $LockFile -Value $PID -Encoding ascii

try {
    if (-not (Test-Path $Cloudflared)) { throw "cloudflared not found at $Cloudflared" }
    if (-not (Test-LocalChatbot)) { throw "local chatbot is not answering on 127.0.0.1:$Port - start run-chatbot.bat first" }

    Write-Log '=== tunnel watchdog starting ==='
    $url = Get-SiteUrl
    if ($url -and (Test-TunnelHealthy $url)) {
        Write-Log "existing tunnel already healthy: $url"
    } else {
        $url = Restart-TunnelWithBackoff
        if (-not $url) { Write-Log 'giving up for now'; exit 1 }
    }

    if ($Once) { Write-Log 'once mode; exiting'; exit 0 }

    while ($true) {
        Start-Sleep -Seconds $CheckIntervalSec
        if (-not (Test-LocalChatbot)) { Write-Log 'local chatbot down; skipping check'; continue }
        $url = Get-SiteUrl
        if ($url -and (Test-TunnelHealthy $url)) { Write-Log "OK: $url"; continue }
        Write-Log "tunnel unhealthy ($url); rebuilding"
        Restart-TunnelWithBackoff | Out-Null
    }
} finally {
    Remove-Item $LockFile -Force -ErrorAction SilentlyContinue
}
