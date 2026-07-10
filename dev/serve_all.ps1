<#
.SYNOPSIS
    Windows counterpart of dev/serve_all.sh — Jekyll + chatbot + Admin CMS.

.DESCRIPTION
    Ports deliberately differ from the Linux script's 4000/4005/4010:

      - 4005 and 4010 are forwarded elsewhere by VS Code on this machine, so
        binding them fails with WSAEACCES.
      - On the box that hosts the live chatbot, 4105 is the *production*
        instance. A dev chatbot on 4105 would take the public site down.

    Everything is overridable, so a machine without those constraints can pass
    -ChatbotPort 4005 and match the shell script exactly.

.EXAMPLE
    powershell -ExecutionPolicy Bypass -File dev\serve_all.ps1
    powershell -ExecutionPolicy Bypass -File dev\serve_all.ps1 chatbot
#>
[CmdletBinding()]
param(
    [ValidateSet('all', 'jekyll', 'chatbot', 'admin')]
    [string] $What = 'all',

    [string] $RepoRoot,
    [string] $Python     = "$env:USERPROFILE\anaconda3\envs\RS\python.exe",
    [string] $RubyBin    = 'C:\Ruby33-x64\bin',
    [string] $BundlePath = "$env:USERPROFILE\Desktop\RS\gems-win",

    [int] $JekyllPort  = 4001,
    [int] $ChatbotPort = 4205,
    [int] $AdminPort   = 4210
)

$ErrorActionPreference = 'Stop'
if (-not $RepoRoot) { $RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path }

$LogDir = Join-Path $env:TEMP 'reality-dev'
New-Item -ItemType Directory -Force -Path $LogDir | Out-Null

# cp949 consoles make the servers' emoji prints throw, and that exception takes
# load_rag() down with it -- a chatbot that starts but answers with no context.
$env:PYTHONUTF8       = '1'
$env:PYTHONIOENCODING = 'utf-8'
$env:PYTHONUNBUFFERED = '1'
$env:BUNDLE_PATH      = $BundlePath

function Test-PortBusy {
    param([int] $Port)
    [bool](Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue)
}

function Start-DevService {
    param(
        [string] $Name, [int] $Port, [string] $Exe,
        [string[]] $ArgList, [string] $WorkDir, [string] $Url
    )
    if (Test-PortBusy $Port) { Write-Host "[$Name] port $Port already in use - skipping"; return }

    $out = Join-Path $LogDir "$Name.log"
    $p = Start-Process -FilePath $Exe -ArgumentList $ArgList -WorkingDirectory $WorkDir `
        -RedirectStandardOutput $out -RedirectStandardError "$out.err" `
        -WindowStyle Hidden -PassThru
    Set-Content -Path (Join-Path $LogDir "$Name.pid") -Value $p.Id -Encoding ascii
    Write-Host "[$Name] PID $($p.Id) - $Url"
}

function Start-Jekyll {
    if (-not (Test-Path "$RubyBin\bundle.bat")) {
        Write-Host "[jekyll] bundle.bat not found under $RubyBin. Install RubyInstaller with MSYS2."
        return
    }
    Start-DevService -Name 'jekyll' -Port $JekyllPort -Exe "$RubyBin\bundle.bat" `
        -ArgList @('exec', 'jekyll', 'serve', '--host', '127.0.0.1', '--port', "$JekyllPort", '--livereload') `
        -WorkDir $RepoRoot -Url "http://localhost:$JekyllPort"
}

function Start-Chatbot {
    if (-not (Test-Path $Python)) { Write-Host "[chatbot] python not found at $Python"; return }
    if (-not (Test-Path (Join-Path $RepoRoot '.env'))) {
        Write-Host '[chatbot] WARN: .env missing - /chat will 503 (health still works)'
    }
    # This account carries an OPENAI_API_KEY for other projects, and
    # load_dotenv() will not override an already-set variable.
    $env:OPENAI_API_KEY = ''
    Start-DevService -Name 'chatbot' -Port $ChatbotPort -Exe $Python `
        -ArgList @('ai_chatbot_server.py', '--host', '127.0.0.1', '--port', "$ChatbotPort") `
        -WorkDir (Join-Path $RepoRoot 'ai_server') -Url "http://localhost:$ChatbotPort/health"
}

function Start-Admin {
    if (-not (Test-Path $Python)) { Write-Host "[admin] python not found at $Python"; return }
    if (-not (Test-Path (Join-Path $RepoRoot 'admin_cms\admin_config.json'))) {
        Write-Host '[admin] WARN: admin_config.json missing - run admin_cms/set_admin_password.py first'
    }
    Start-DevService -Name 'admin' -Port $AdminPort -Exe $Python `
        -ArgList @('admin_server.py', '--host', '127.0.0.1', '--port', "$AdminPort") `
        -WorkDir (Join-Path $RepoRoot 'admin_cms') -Url "http://localhost:$AdminPort"
}

switch ($What) {
    'all'     { Start-Jekyll; Start-Chatbot; Start-Admin }
    'jekyll'  { Start-Jekyll }
    'chatbot' { Start-Chatbot }
    'admin'   { Start-Admin }
}

Write-Host ''
Write-Host "logs: $LogDir"
Write-Host "stop: powershell -ExecutionPolicy Bypass -File dev\stop_all.ps1"
