#!/bin/bash

# Cloudflare Tunnel for Admin CMS (port 4010)
# - Starts tunnel
# - Updates admin.html with new URL
# - Pushes to GitHub so https://reality.ssu.ac.kr/admin.html always redirects to current URL

WORK_DIR="/home/i0179/Realitylab-site"
SITE_WORK_DIR="/data2/i0179/Realitylab-site"
LOG_FILE="$WORK_DIR/ai_server/admin_tunnel.log"
PID_FILE="$WORK_DIR/ai_server/admin_cloudflared.pid"
URL_FILE="$WORK_DIR/ai_server/admin_url.txt"
ADMIN_HTML="$SITE_WORK_DIR/admin.html"
CLOUDFLARED="$WORK_DIR/ai_server/cloudflared.new"
TEMP_LOG="$WORK_DIR/ai_server/admin_tunnel_temp.log"
ADMIN_PORT=4010

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" >> "$LOG_FILE"
}

# shellcheck source=/home/i0179/Realitylab-site/ai_server/git_push_helper.sh
source "$WORK_DIR/ai_server/git_push_helper.sh"

# Kill existing admin tunnel
if [ -f "$PID_FILE" ]; then
    OLD_PID=$(cat "$PID_FILE" 2>/dev/null)
    if [ -n "$OLD_PID" ] && ps -p "$OLD_PID" > /dev/null 2>&1; then
        kill "$OLD_PID" 2>/dev/null
        log "Killed old admin tunnel PID: $OLD_PID"
        sleep 2
    fi
fi
pkill -f "cloudflared.*url http://localhost:4010" 2>/dev/null
sleep 1

# Start new tunnel
log "Starting new admin tunnel..."
> "$TEMP_LOG"
nohup "$CLOUDFLARED" tunnel --url "http://localhost:${ADMIN_PORT}" > "$TEMP_LOG" 2>&1 &
NEW_PID=$!
echo "$NEW_PID" > "$PID_FILE"
log "Started cloudflared PID: $NEW_PID"

# Wait for URL
TUNNEL_URL=""
for i in {1..30}; do
    sleep 2
    TUNNEL_URL=$(grep -oE "https://[a-z0-9-]+\.trycloudflare\.com" "$TEMP_LOG" | head -1)
    if [ -n "$TUNNEL_URL" ]; then
        break
    fi
done

if [ -z "$TUNNEL_URL" ]; then
    log "ERROR: Failed to get tunnel URL"
    exit 1
fi

log "Admin tunnel URL: $TUNNEL_URL"
echo "$TUNNEL_URL" > "$URL_FILE"

# Verify
sleep 3
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" --max-time 10 "$TUNNEL_URL/login")
if [ "$HTTP_CODE" != "200" ]; then
    log "WARN: Admin tunnel returned $HTTP_CODE"
fi

# Update admin.html with new URL and push to GitHub
if [ -f "$ADMIN_HTML" ]; then
    OLD_URL=$(grep -oE "const ADMIN_URL = '[^']+'" "$ADMIN_HTML" | grep -oE "https://[^']+")
    if [ "$OLD_URL" != "$TUNNEL_URL" ]; then
        log "Updating admin.html: $OLD_URL -> $TUNNEL_URL"
        # Use # as sed delimiter to avoid escaping URL slashes
        sed -i "s#const ADMIN_URL = '[^']*'#const ADMIN_URL = '$TUNNEL_URL'#" "$ADMIN_HTML"

        # Git push (with auto pull --rebase + retry on conflict)
        cd "$SITE_WORK_DIR"
        git add admin.html
        git commit -m "Auto-update admin tunnel URL" >> "$LOG_FILE" 2>&1
        if safe_git_push main "$LOG_FILE"; then
            log "Successfully pushed admin URL to GitHub"
        else
            log "WARNING: Failed to push to GitHub after retries"
        fi
    else
        log "URL unchanged, skipping git push"
    fi
fi

cat "$TEMP_LOG" >> "$LOG_FILE"
rm -f "$TEMP_LOG"
echo "Admin URL: $TUNNEL_URL"
