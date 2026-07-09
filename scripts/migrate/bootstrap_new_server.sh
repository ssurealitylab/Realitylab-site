#!/bin/bash
# Reality Lab — new server bootstrap.
#
# Run on the FRESH server after `git clone`ing the repo.
# Idempotent: safe to run repeatedly (skips steps that are already done).
#
# Usage:
#   cd ~/Realitylab-site
#   ./scripts/migrate/bootstrap_new_server.sh
#
# After this finishes with all green, the only remaining action is to
# start the tunnel (cron will keep it running).

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$REPO_ROOT"

step() { printf '\n\033[1;34m== %s\033[0m\n' "$*"; }
warn() { printf '\033[1;33m!! %s\033[0m\n' "$*" >&2; }
ok()   { printf '\033[1;32mOK\033[0m %s\n' "$*"; }
ask()  { local prompt="$1"; local reply; read -r -p "$prompt " reply; echo "$reply"; }

# ---- 1/8 system packages ---------------------------------------------------
step "1/8 System packages"
NEED_APT=0
for pkg in ruby ruby-dev python3 python3-venv python3-pip git curl default-jre; do
    dpkg -s "$pkg" >/dev/null 2>&1 || NEED_APT=1
done
if [ "$NEED_APT" = 1 ]; then
    sudo apt update
    sudo apt install -y ruby-full ruby-dev build-essential \
                        python3 python3-venv python3-pip \
                        git curl default-jre
fi
if ! command -v cloudflared >/dev/null; then
    step "Installing cloudflared"
    curl -fsSL https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64 \
        -o /tmp/cloudflared
    sudo install -m 0755 /tmp/cloudflared /usr/local/bin/cloudflared
    rm /tmp/cloudflared
fi
ok "system packages present"

# ---- 2/8 Ruby / Jekyll -----------------------------------------------------
step "2/8 Bundler + Jekyll"
if ! command -v bundle >/dev/null; then
    sudo gem install bundler
fi
bundle config set --local path 'vendor/bundle'
bundle install
ok "jekyll ready (bundle exec jekyll serve to test)"

# ---- 3/8 Python venv + chatbot deps ---------------------------------------
step "3/8 Python virtualenv + chatbot deps"
if [ ! -d "$REPO_ROOT/.venv" ]; then
    python3 -m venv "$REPO_ROOT/.venv"
fi
# shellcheck disable=SC1091
source "$REPO_ROOT/.venv/bin/activate"
pip install --upgrade pip
pip install -r ai_server/requirements.txt
pip install bcrypt   # required by admin_cms
ok "chatbot dependencies installed in .venv"

# ---- 4/8 .env --------------------------------------------------------------
step "4/8 .env (OpenAI credentials)"
if [ ! -f "$REPO_ROOT/.env" ]; then
    cp "$REPO_ROOT/.env.example" "$REPO_ROOT/.env"
    chmod 600 "$REPO_ROOT/.env"
    warn "Created $REPO_ROOT/.env from template. Edit it now to fill in OPENAI_API_KEY."
    warn "You can continue this script; the chatbot just won't answer until the key is set."
else
    if grep -q '^OPENAI_API_KEY=sk-\.\.\.\.$\|^OPENAI_API_KEY=$\|^OPENAI_API_KEY=sk-\.\.\.' "$REPO_ROOT/.env"; then
        warn ".env exists but OPENAI_API_KEY still looks like a placeholder. Edit it."
    else
        ok ".env present"
    fi
fi

# ---- 5/8 Admin password ---------------------------------------------------
step "5/8 Admin CMS password"
if [ -f "$REPO_ROOT/admin_cms/admin_config.json" ] \
   && python3 -c "import json,sys; sys.exit(0 if 'password_hash' in json.load(open('$REPO_ROOT/admin_cms/admin_config.json')) else 1)" 2>/dev/null; then
    ok "admin_config.json already has password_hash"
else
    reply=$(ask "Set a new admin password now? [Y/n]")
    if [ -z "$reply" ] || [[ "$reply" =~ ^[Yy] ]]; then
        python3 "$REPO_ROOT/admin_cms/set_admin_password.py"
    else
        warn "SKIPPED. Run later: python3 admin_cms/set_admin_password.py"
    fi
fi

# ---- 6/8 RAG index --------------------------------------------------------
step "6/8 RAG knowledge base + hierarchical index"
if [ -f "$REPO_ROOT/ai_server/hierarchical_rag/categories.json" ] \
   && [ -f "$REPO_ROOT/ai_server/knowledge_base.json" ]; then
    ok "RAG artifacts present (checked in via git)"
    reply=$(ask "Rebuild them now from current _data/? [y/N]")
    if [[ "$reply" =~ ^[Yy] ]]; then
        RESTART_CHATBOT=0 bash "$REPO_ROOT/ai_server/update_rag.sh"
    fi
else
    warn "RAG artifacts missing — building from _data/ now (needs sentence-transformers, first run downloads ~450MB)"
    RESTART_CHATBOT=0 bash "$REPO_ROOT/ai_server/update_rag.sh"
fi

# ---- 7/8 Smoke tests ------------------------------------------------------
step "7/8 Smoke tests"
python3 -c "import openai, flask, flask_cors, pytz, bcrypt, sentence_transformers; print('imports OK')" \
    && ok "python imports OK"

if [ -n "${OPENAI_API_KEY:-}" ] || grep -q '^OPENAI_API_KEY=sk-[A-Za-z0-9_-]\{20,\}' "$REPO_ROOT/.env" 2>/dev/null; then
    (
        cd "$REPO_ROOT/ai_server"
        nohup "$REPO_ROOT/.venv/bin/python3" ai_chatbot_server.py --port 4099 >/tmp/chatbot-smoke.log 2>&1 &
        echo $! > /tmp/chatbot-smoke.pid
    )
    sleep 3
    if curl -fs --max-time 5 http://localhost:4099/health | grep -q healthy; then
        ok "chatbot /health returns healthy on ephemeral port 4099"
    else
        warn "chatbot smoke test did not respond — check /tmp/chatbot-smoke.log"
    fi
    kill "$(cat /tmp/chatbot-smoke.pid 2>/dev/null)" 2>/dev/null || true
    rm -f /tmp/chatbot-smoke.pid
else
    warn "Skipping live chatbot smoke test (OPENAI_API_KEY is still a placeholder)"
fi

# ---- 8/8 Next steps -------------------------------------------------------
step "8/8 Next steps (manual)"
cat <<EOF

  a. systemd units for admin + chatbot:
       sudo cp scripts/migrate/systemd/reality-chatbot.service /etc/systemd/system/reality-chatbot@.service
       sudo cp scripts/migrate/systemd/reality-admin.service   /etc/systemd/system/reality-admin@.service
       sudo systemctl daemon-reload
       sudo systemctl enable --now reality-chatbot@\$USER reality-admin@\$USER

  b. crontab:
       crontab scripts/migrate/crontab.new-server.txt
       crontab -l

  c. Cloudflare tunnels (ephemeral --url mode, no login required):
       $REPO_ROOT/ai_server/restart_tunnel.sh          # chatbot on :4005
       $REPO_ROOT/ai_server/restart_admin_tunnel.sh    # admin on :4010
     These auto-commit the current tunnel URL to git so the site picks it up.

  d. Verify end-to-end:
       curl -s http://localhost:4005/health | jq
       curl -s http://localhost:4010/health | jq   (or admin.html in the browser)

  e. Cut over (once verified for 24h):
       On the OLD server: crontab -e  → comment every line
       Then stop old processes: pkill -f ai_chatbot_server; pkill -f admin_server; pkill cloudflared

EOF
ok "bootstrap complete"
