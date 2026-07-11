<#
.SYNOPSIS
    Launch the chatbot or Admin CMS backend as a scheduled task would.

.DESCRIPTION
    The .bat launchers exist for a human at a terminal. Driving them from Task
    Scheduler via `cmd /c` gave both backends a console, and at logon that
    console was torn down under them -- they died with 0xC000013A (STATUS_
    CONTROL_C_EXIT) seconds after starting, leaving the tunnels alive and
    pointing at nothing. The site then showed its "GPU is busy" fallback even
    though the machine was up.

    This starts python directly, with no console to lose, and blocks so Task
    Scheduler sees the task as still running.
#>
[CmdletBinding()]
param(
    [ValidateSet('chatbot', 'admin')]
    [string] $Service = 'chatbot',

    [string] $RepoRoot,
    [string] $Python = "$env:USERPROFILE\anaconda3\envs\RS\python.exe",
    [int]    $Port
)

$ErrorActionPreference = 'Stop'
if (-not $RepoRoot) { $RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path }

$SERVICES = @{
    chatbot = @{ DefaultPort = 4105; Dir = 'ai_server'; Script = 'ai_chatbot_server.py' }
    admin   = @{ DefaultPort = 4100; Dir = 'admin_cms'; Script = 'admin_server.py' }
}
$CFG = $SERVICES[$Service]
if (-not $Port) { $Port = $CFG.DefaultPort }

$workDir = Join-Path $RepoRoot $CFG.Dir
$logFile = Join-Path $RepoRoot "ai_server\$Service.service.log"

# The Korean console codepage is cp949 and both servers print emoji while
# loading. Without UTF-8 those prints raise, and for the chatbot the exception
# takes load_rag() down with it: a server that starts fine and then answers
# with no RAG context.
$env:PYTHONUTF8       = '1'
$env:PYTHONIOENCODING = 'utf-8'
$env:PYTHONUNBUFFERED = '1'

if ($Service -eq 'chatbot') {
    if (-not (Test-Path (Join-Path $RepoRoot '.env'))) { throw "$RepoRoot\.env missing (OPENAI_API_KEY)" }
    # This account carries an OPENAI_API_KEY for other projects, and
    # load_dotenv() will not override an already-set variable.
    $env:OPENAI_API_KEY = ''
} elseif (-not (Test-Path (Join-Path $RepoRoot 'admin_cms\admin_config.json'))) {
    throw 'admin_cms\admin_config.json missing - run admin_cms/set_admin_password.py'
}

# Bind to loopback only: the apps default to 0.0.0.0, and the tunnel is the
# intended way in. Timestamp header so restarts are visible in the log.
Add-Content -Path $logFile -Value "`n[$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')] starting $Service on 127.0.0.1:$Port" -Encoding utf8

# Start-Process rather than `& python ... *>> log`: with $ErrorActionPreference
# 'Stop', PowerShell 5.1 turns each stderr line from a native command into a
# terminating error, and Flask greets us on stderr ("WARNING: This is a
# development server"). Redirecting that way killed the server on startup.
# Let the child write its own streams to disk, and block until it exits so
# Task Scheduler keeps the task marked running.
$proc = Start-Process -FilePath $Python `
    -ArgumentList @($CFG.Script, '--host', '127.0.0.1', '--port', "$Port") `
    -WorkingDirectory $workDir `
    -RedirectStandardOutput $logFile -RedirectStandardError "$logFile.err" `
    -NoNewWindow -PassThru
$proc.WaitForExit()
exit $proc.ExitCode
