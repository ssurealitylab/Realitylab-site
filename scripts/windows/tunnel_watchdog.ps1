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
    One instance per backend: -Service chatbot (4105, rewrites chatbot.html and
    bug-report.html) or -Service admin (4100, rewrites admin.html so that
    reality.ssu.ac.kr/admin.html keeps redirecting to the current tunnel).

    The backends themselves are not managed here; start them first
    (run-chatbot.bat / run-admin.bat).
#>
[CmdletBinding()]
param(
    # Which tunnel this instance owns. Two run side by side, one per backend.
    [ValidateSet('chatbot', 'admin')]
    [string] $Service = 'chatbot',

    # $PSScriptRoot is not yet bound while param defaults are evaluated, so the
    # repo root is resolved below rather than here.
    [string] $RepoRoot,
    [string] $Cloudflared = "$env:USERPROFILE\Desktop\RS\bin\cloudflared.exe",
    [int]    $Port,
    [string] $Branch     = 'main',
    [int]    $CheckIntervalSec = 600,
    [switch] $Once
)

# The chatbot moved to a Cloudflare Worker (reality-lab-chatbot.i0179.workers.dev),
# which has a fixed hostname and needs no PC. This watchdog must not run for it
# any more: it would start a quick tunnel and overwrite the Worker URL baked into
# chatbot.html / bug-report.html with a throwaway *.trycloudflare.com one.
# The admin CMS still runs locally, so -Service admin is untouched.
if ($Service -eq 'chatbot') {
    Write-Host "chatbot tunnel retired - served by Cloudflare Worker. Nothing to do."
    exit 0
}

$ErrorActionPreference = 'Stop'

if (-not $RepoRoot) { $RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path }

$AiServer = Join-Path $RepoRoot 'ai_server'

# Per-service wiring. The site files carry the tunnel hostname as a JS constant;
# rewriting them and pushing is what keeps reality.ssu.ac.kr/admin.html (and the
# chatbot widget) pointing at whatever random hostname the tunnel drew this time.
$SERVICES = @{
    chatbot = @{
        DefaultPort = 4105
        # Local readiness probe, and what a working tunnel must echo back.
        LocalPath   = '/health'
        HealthPath  = '/health'
        HealthMatch = '"status"\s*:\s*"healthy"'
        Constant    = 'DIRECT_AI_SERVER_URL'
        SiteFiles   = @('_includes\chatbot.html', '_includes\bug-report.html')
        CommitMsg   = 'Auto-update Cloudflare Tunnel URL'
        LogFile     = 'tunnel_watchdog.log'
        TempLog     = 'tunnel_temp.log'
        LockFile    = 'restart_tunnel.lock'
        DailyFile   = 'daily_attempts.txt'
        UrlFile     = $null
    }
    admin = @{
        DefaultPort = 4100
        # The CMS has no /health; an unauthenticated GET /login must render.
        LocalPath   = '/login'
        HealthPath  = '/login'
        HealthMatch = $null          # any 200 counts
        Constant    = 'ADMIN_URL'
        SiteFiles   = @('admin.html')
        CommitMsg   = 'Auto-update admin tunnel URL'
        LogFile     = 'admin_tunnel_watchdog.log'
        TempLog     = 'admin_tunnel_temp.log'
        LockFile    = 'restart_admin_tunnel.lock'
        DailyFile   = 'admin_daily_attempts.txt'
        UrlFile     = 'admin_url.txt'
    }
}
$CFG = $SERVICES[$Service]
if (-not $Port) { $Port = $CFG.DefaultPort }

# @() matters: admin has a single site file, and indexing a bare string would
# hand $PrimaryFile its first character instead of the path.
$SiteFiles     = @($CFG.SiteFiles | ForEach-Object { Join-Path $RepoRoot $_ })
$PrimaryFile   = $SiteFiles[0]
$LogFile       = Join-Path $AiServer $CFG.LogFile
$TempLog       = Join-Path $AiServer $CFG.TempLog
$LockFile      = Join-Path $AiServer $CFG.LockFile
$DailyFile     = Join-Path $AiServer $CFG.DailyFile
# Cloudflare rate-limits quick-tunnel creation per source IP, so both services
# share one cooldown: if the chatbot tunnel got 429'd, the admin one will too.
$RateLimitFile = Join-Path $AiServer 'rate_limit_until.txt'

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
    # If the stored credential expires, git otherwise tries to open an
    # interactive auth prompt. In this headless task that call blocks forever:
    # the push never returns, the retry/WARNING logic below never runs, and the
    # site keeps serving whatever stale URL was last pushed. Force git to fail
    # fast instead so the failure is logged and visible.
    $prevPrompt = $env:GIT_TERMINAL_PROMPT
    $env:GIT_TERMINAL_PROMPT = '0'
    try {
        $output = & git @GitArgs 2>&1 | Out-String
        return [pscustomobject]@{ Code = $LASTEXITCODE; Output = $output.Trim() }
    } finally {
        $ErrorActionPreference = $prev
        $env:GIT_TERMINAL_PROMPT = $prevPrompt
    }
}

function Write-Log {
    param([string] $Message)
    $line = "[{0}] {1}" -f (Get-Date -Format 'yyyy-MM-dd HH:mm:ss'), $Message
    Write-Host $line
    Add-Content -Path $LogFile -Value $line -Encoding utf8
}

function Get-SiteUrl {
    $m = Select-String -Path $PrimaryFile -Pattern "$($CFG.Constant) = '($URL_RE)'" | Select-Object -First 1
    if ($m) { return $m.Matches[0].Groups[1].Value }
    return $null
}

function Test-TunnelHealthy {
    param([string] $Url)
    try {
        $r = Invoke-WebRequest "$Url$($CFG.HealthPath)" -UseBasicParsing -TimeoutSec 20
        if (-not $CFG.HealthMatch) { return $r.StatusCode -eq 200 }
        return $r.Content -match $CFG.HealthMatch
    } catch { return $false }
}

function Test-LocalBackend {
    try {
        $r = Invoke-WebRequest "http://127.0.0.1:$Port$($CFG.LocalPath)" -UseBasicParsing -TimeoutSec 10
        return $r.StatusCode -eq 200
    } catch { return $false }
}

function Wait-LocalBackend {
    # At logon the backend and this script start together, and the chatbot spends
    # ~30s loading its embedding model. Don't lose the race.
    param([int] $TimeoutSec = 300)
    $deadline = (Get-Date).AddSeconds($TimeoutSec)
    while ((Get-Date) -lt $deadline) {
        if (Test-LocalBackend) { return $true }
        Write-Log "waiting for local $Service..."
        Start-Sleep -Seconds 10
    }
    return $false
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
    foreach ($f in $SiteFiles) {
        if (-not (Test-Path $f)) { continue }
        $text = [IO.File]::ReadAllText($f)
        $updated = [regex]::Replace($text, "$($CFG.Constant) = '$URL_RE'", "$($CFG.Constant) = '$NewUrl'")
        if ($updated -ne $text) { [IO.File]::WriteAllText($f, $updated); Write-Log "  rewrote $(Split-Path $f -Leaf)" }
    }
    if ($CFG.UrlFile) { Set-Content -Path (Join-Path $AiServer $CFG.UrlFile) -Value $NewUrl -Encoding ascii }

    Push-Location $RepoRoot
    try {
        # `commit -- <paths>` commits *only* those paths. Staging them and then
        # running a bare `git commit` would sweep in whatever else happened to be
        # sitting in the index -- this machine's working tree is not ours alone,
        # and an auto-push must never carry someone's half-finished work.
        $relative = @($CFG.SiteFiles | ForEach-Object { $_ -replace '\\', '/' })
        if ((Invoke-Git commit -m $CFG.CommitMsg -- @relative).Code -ne 0) {
            Write-Log 'nothing to commit'; return
        }

        for ($i = 1; $i -le 3; $i++) {
            $push = Invoke-Git push origin $Branch
            if ($push.Code -eq 0) { Write-Log "pushed (attempt $i)"; return }
            # Log the reason. Auth failure ("could not read Username",
            # "Authentication failed", "terminal prompts disabled") means the
            # stored credential expired and someone has to refresh it -- a pull
            # --rebase will not help, so bail out loudly rather than spinning.
            $reason = ($push.Output -split "`n" | Select-Object -Last 1).Trim()
            Write-Log "push attempt $i failed: $reason"
            if ($push.Output -match 'Authentication failed|could not read Username|terminal prompts disabled|Permission denied|fatal: could not read') {
                Write-Log 'AUTH FAILURE: git credential expired. Run `git push` once by hand to refresh it. GitHub Pages will serve the stale URL until then.'
                return
            }
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
            # Cloudflare's edge can take well over 5s to start serving a freshly
            # minted hostname. Give it several tries: discarding a live tunnel
            # here costs one of the 20 creations we get per day.
            $healthy = $false
            foreach ($probe in 1..5) {
                Start-Sleep -Seconds 5
                if (Test-TunnelHealthy $url) { $healthy = $true; break }
                Write-Log "  edge not serving yet (probe $probe/5)"
            }
            if ($healthy) {
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

    Write-Log "=== $Service tunnel watchdog starting ==="
    if (-not (Wait-LocalBackend)) { throw "local $Service never came up on 127.0.0.1:$Port" }
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
        if (-not (Test-LocalBackend)) { Write-Log "local $Service down; skipping check"; continue }
        $url = Get-SiteUrl
        if ($url -and (Test-TunnelHealthy $url)) { Write-Log "OK: $url"; continue }
        Write-Log "tunnel unhealthy ($url); rebuilding"
        Restart-TunnelWithBackoff | Out-Null
    }
} finally {
    Remove-Item $LockFile -Force -ErrorAction SilentlyContinue
}
