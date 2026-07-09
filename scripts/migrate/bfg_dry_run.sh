#!/bin/bash
# BFG history-cleanup dry-run.
# Clones the current repo to a temp mirror, runs BFG against the mirror, and
# reports the size delta. The original working repo is not touched.
#
# Follow up with bfg_apply.sh if you're satisfied with the numbers.

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
STAMP="$(date +%Y%m%d-%H%M%S)"
WORK="${TMPDIR:-/tmp}/reality-bfg-$STAMP"
MIRROR="$WORK/reality.git"
BFG_JAR="$WORK/bfg.jar"
BFG_URL="https://repo1.maven.org/maven2/com/madgag/bfg/1.14.0/bfg-1.14.0.jar"

FILES_TO_DELETE='{admin_tunnel.log,admin_tunnel_temp.log,tunnel_monitor.log,tunnel_cron.log,tunnel_temp.log,tunnel_retry.log,rest_time.log,gpu_monitor.log,rag_update.log,daily_attempts.txt,cloudflared.pid,admin_cloudflared.pid,restart_tunnel.lock,jekyll.log,jekyll4001.log,jekyll4004.log,jekyll_server.log,cloudflare_tunnel.log,ai_server.log,ai_server.pid,ai_server_final.log,ai_server_fresh.log,ai_server_new.log,cu_crawler.log}'
SIZE_THRESHOLD='5M'

mkdir -p "$WORK"
echo "== Dry-run workspace: $WORK"

echo "== Cloning mirror from $REPO_ROOT"
git clone --mirror "$REPO_ROOT" "$MIRROR"

SIZE_BEFORE=$(du -sh "$MIRROR" | cut -f1)
echo "== Mirror size BEFORE: $SIZE_BEFORE"

if ! command -v java >/dev/null 2>&1; then
    echo "ERROR: java is required (sudo apt install default-jre)" >&2
    exit 1
fi

if [ ! -f "$BFG_JAR" ]; then
    echo "== Downloading BFG"
    curl -fsSL "$BFG_URL" -o "$BFG_JAR"
fi

echo "== Running BFG: delete auto-log files"
java -jar "$BFG_JAR" --delete-files "$FILES_TO_DELETE" "$MIRROR" >/dev/null

echo "== Running BFG: strip blobs larger than $SIZE_THRESHOLD"
java -jar "$BFG_JAR" --strip-blobs-bigger-than "$SIZE_THRESHOLD" "$MIRROR" >/dev/null

echo "== Expiring reflog and gc-ing"
git --git-dir="$MIRROR" reflog expire --expire=now --all
git --git-dir="$MIRROR" gc --prune=now --aggressive >/dev/null

SIZE_AFTER=$(du -sh "$MIRROR" | cut -f1)
echo ""
echo "======================================"
echo "  Mirror size BEFORE : $SIZE_BEFORE"
echo "  Mirror size AFTER  : $SIZE_AFTER"
echo "======================================"
echo ""
echo "Cleaned mirror is at: $MIRROR"
echo "If the numbers look good, run scripts/migrate/bfg_apply.sh to apply to the real repo."
echo "Rollback: the working repo was never modified. Delete $WORK when done."
