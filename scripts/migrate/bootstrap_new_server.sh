#!/bin/bash
# Reality Lab — new server bootstrap.
#
# Run on the FRESH server after `git clone`ing the repo.
# Assumes Ubuntu 22.04+ and a user that already has sudo.
#
# Usage:
#   cd ~/Realitylab-site
#   ./scripts/migrate/bootstrap_new_server.sh
#
# What it does:
#   1. Install system packages (ruby, python, cloudflared)
#   2. bundle install (Jekyll)
#   3. pip install chatbot requirements
#   4. Prompt you to create .env
#   5. Prompt you to drop secret files (admin_config.json, name_mapping.json, RAG)
#   6. Print next steps (cron install, systemd, cloudflared login)

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$REPO_ROOT"

step() { printf '\n\033[1;34m== %s\033[0m\n' "$*"; }
warn() { printf '\033[1;33m!! %s\033[0m\n' "$*" >&2; }
ok()   { printf '\033[1;32mOK\033[0m %s\n' "$*"; }

step "1/6 System packages"
if ! command -v ruby >/dev/null || ! command -v python3 >/dev/null || ! command -v git >/dev/null; then
    sudo apt update
    sudo apt install -y ruby-full ruby-dev build-essential \
                        python3 python3-venv python3-pip \
                        git curl default-jre
fi

if ! command -v cloudflared >/dev/null; then
    step "Installing cloudflared to /usr/local/bin"
    curl -fsSL https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64 \
        -o /tmp/cloudflared
    sudo install -m 0755 /tmp/cloudflared /usr/local/bin/cloudflared
    rm /tmp/cloudflared
fi
ok "system packages present"

step "2/6 Bundler + Jekyll"
if ! command -v bundle >/dev/null; then
    sudo gem install bundler
fi
bundle config set --local path 'vendor/bundle'
bundle install
ok "jekyll ready (bundle exec jekyll serve to test)"

step "3/6 Python virtualenv + chatbot deps"
if [ ! -d "$REPO_ROOT/.venv" ]; then
    python3 -m venv "$REPO_ROOT/.venv"
fi
# shellcheck disable=SC1091
source "$REPO_ROOT/.venv/bin/activate"
pip install --upgrade pip
pip install -r ai_server/requirements.txt
ok "chatbot dependencies installed in .venv"

step "4/6 .env"
if [ ! -f "$REPO_ROOT/.env" ]; then
    cp "$REPO_ROOT/.env.example" "$REPO_ROOT/.env"
    warn "Edit $REPO_ROOT/.env and fill in OPENAI_API_KEY, then re-run this script (or move on)."
else
    ok ".env already exists"
fi

step "5/6 Secrets that must be SCP-ed from the old server"
missing=0
check_missing() {
    if [ ! -f "$1" ] && [ ! -d "$1" ]; then
        warn "MISSING: $1"
        missing=$((missing+1))
    else
        ok "found: $1"
    fi
}
check_missing "$REPO_ROOT/admin_cms/admin_config.json"
check_missing "$REPO_ROOT/ai_server/name_mapping.json"
check_missing "$REPO_ROOT/ai_server/knowledge_base.json"
check_missing "$REPO_ROOT/ai_server/hierarchical_rag"
if [ $missing -gt 0 ]; then
    warn "$missing secret(s) missing. From the OLD server run:"
    echo "  scp admin_cms/admin_config.json <new-host>:$REPO_ROOT/admin_cms/"
    echo "  scp ai_server/name_mapping.json ai_server/knowledge_base.json <new-host>:$REPO_ROOT/ai_server/"
    echo "  scp -r ai_server/hierarchical_rag <new-host>:$REPO_ROOT/ai_server/"
fi

step "6/6 Next steps (manual)"
cat <<EOF

  a. Cloudflare Tunnel (one-time login on this box)
       cloudflared tunnel login
     (Or copy ~/.cloudflared from the old server to reuse existing cert.)

  b. Install cron:
       crontab scripts/migrate/crontab.new-server.txt
       crontab -l

  c. (Optional) systemd units for admin + chatbot:
       sudo cp scripts/migrate/systemd/*.service /etc/systemd/system/
       sudo systemctl daemon-reload
       sudo systemctl enable --now reality-chatbot reality-admin
     Edit the unit files if REPO_ROOT differs from \$HOME/Realitylab-site.

  d. Smoke test:
       source .venv/bin/activate
       python3 ai_server/ai_chatbot_server.py --port 4005 &
       curl -s http://localhost:4005/health | jq
       curl -s -X POST http://localhost:4005/chat \\
            -H 'content-type: application/json' \\
            -d '{"question":"Reality Lab이 뭐야?","mode":"deep"}' | jq

  e. Point Cloudflare tunnel at localhost:4005 (chatbot) and :4010 (admin)
     — either via 'cloudflared --url http://localhost:4005' (matches old setup)
     or by configuring a named tunnel in ~/.cloudflared/config.yml.

  f. Once tunnels + git push are verified end-to-end, disable the OLD server's
     crontab (comment lines, don't delete) and monitor for 24h before shutdown.

EOF
ok "bootstrap complete"
