#!/bin/bash
# Apply BFG history cleanup to the real repo and push the rewritten history.
# You MUST run bfg_dry_run.sh first and be happy with the reported size.
#
# DESTRUCTIVE. Rewrites shared history. Coordinate with anyone else who
# has a clone before running this.

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
STAMP="$(date +%Y%m%d-%H%M%S)"
BACKUP_MIRROR="$HOME/reality-backup-$STAMP.git"
BFG_JAR="${BFG_JAR:-${TMPDIR:-/tmp}/bfg.jar}"
BFG_URL="https://repo1.maven.org/maven2/com/madgag/bfg/1.14.0/bfg-1.14.0.jar"
FILES_TO_DELETE='{admin_tunnel.log,admin_tunnel_temp.log,tunnel_monitor.log,tunnel_cron.log,tunnel_temp.log,tunnel_retry.log,rest_time.log,gpu_monitor.log,rag_update.log,daily_attempts.txt,cloudflared.pid,admin_cloudflared.pid,restart_tunnel.lock,jekyll.log,jekyll4001.log,jekyll4004.log,jekyll_server.log,cloudflare_tunnel.log,ai_server.log,ai_server.pid,ai_server_final.log,ai_server_fresh.log,ai_server_new.log,cu_crawler.log}'
SIZE_THRESHOLD='5M'

confirm() {
    read -r -p "$1 [y/N] " reply
    [[ "$reply" =~ ^[Yy]$ ]]
}

cd "$REPO_ROOT"

if [ -n "$(git status --porcelain)" ]; then
    echo "ERROR: working tree is dirty. Commit or stash first." >&2
    git status --short
    exit 1
fi

echo "== Full mirror backup → $BACKUP_MIRROR"
git clone --mirror "$REPO_ROOT" "$BACKUP_MIRROR"

if [ ! -f "$BFG_JAR" ]; then
    echo "== Downloading BFG"
    curl -fsSL "$BFG_URL" -o "$BFG_JAR"
fi

confirm "REWRITE history in $REPO_ROOT? This is destructive. Continue?" || {
    echo "Aborted. Backup preserved at $BACKUP_MIRROR."
    exit 1
}

echo "== BFG: delete auto-log files"
java -jar "$BFG_JAR" --delete-files "$FILES_TO_DELETE" "$REPO_ROOT" >/dev/null

echo "== BFG: strip blobs > $SIZE_THRESHOLD"
java -jar "$BFG_JAR" --strip-blobs-bigger-than "$SIZE_THRESHOLD" "$REPO_ROOT" >/dev/null

echo "== reflog + gc"
git reflog expire --expire=now --all
git gc --prune=now --aggressive >/dev/null

echo "== New .git size:"
du -sh .git

confirm "FORCE PUSH rewritten history to origin/main? Anyone with an existing clone will need to re-clone." || {
    echo "Skipping push. To finish later: git push --force origin main"
    exit 0
}

git push --force origin main
echo "== Done. Backup mirror: $BACKUP_MIRROR"
