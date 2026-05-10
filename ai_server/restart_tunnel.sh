#!/bin/bash

# Cloudflare Tunnel Auto-Restart Script with Smart Retry Logic
# - Exponential backoff to avoid rate limits
# - Rate limit detection with long cooldown
# - Lock file to prevent duplicate runs
# - Daily attempt limit

WORK_DIR="/home/i0179/Realitylab-site"
LOG_FILE="$WORK_DIR/ai_server/tunnel_cron.log"
CHATBOT_FILE="$WORK_DIR/_includes/chatbot.html"
BUGREPORT_FILE="$WORK_DIR/_includes/bug-report.html"
PID_FILE="$WORK_DIR/ai_server/cloudflared.pid"
TEMP_LOG="$WORK_DIR/ai_server/tunnel_temp.log"
CLOUDFLARED="$WORK_DIR/ai_server/cloudflared.new"
LOCK_FILE="$WORK_DIR/ai_server/restart_tunnel.lock"
RATE_LIMIT_FILE="$WORK_DIR/ai_server/rate_limit_until.txt"
DAILY_COUNT_FILE="$WORK_DIR/ai_server/daily_attempts.txt"

# Port for ai_chatbot_server.py
AI_SERVER_PORT=4005

# Retry settings - Exponential backoff
MAX_RETRIES=10              # Fewer retries with longer waits
INITIAL_DELAY=120           # Start with 2 minutes
MAX_DELAY=1800              # Max 30 minutes between retries
RATE_LIMIT_COOLDOWN=3600    # 1 hour cooldown on rate limit
DAILY_MAX_ATTEMPTS=20       # Max 20 attempts per day

cd "$WORK_DIR"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" >> "$LOG_FILE"
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

# shellcheck source=/home/i0179/Realitylab-site/ai_server/git_push_helper.sh
source "$WORK_DIR/ai_server/git_push_helper.sh"

cleanup_lock() {
    rm -f "$LOCK_FILE"
}

# Check for existing lock (prevent duplicate runs)
if [ -f "$LOCK_FILE" ]; then
    LOCK_PID=$(cat "$LOCK_FILE" 2>/dev/null)
    if ps -p "$LOCK_PID" > /dev/null 2>&1; then
        log "Another restart_tunnel.sh is already running (PID: $LOCK_PID). Exiting."
        exit 0
    else
        log "Stale lock file found. Removing..."
        rm -f "$LOCK_FILE"
    fi
fi

# Create lock file
echo $$ > "$LOCK_FILE"
trap cleanup_lock EXIT

# Check rate limit cooldown
if [ -f "$RATE_LIMIT_FILE" ]; then
    RATE_LIMIT_UNTIL=$(cat "$RATE_LIMIT_FILE" 2>/dev/null)
    CURRENT_TIME=$(date +%s)
    if [ "$CURRENT_TIME" -lt "$RATE_LIMIT_UNTIL" ]; then
        WAIT_MINS=$(( (RATE_LIMIT_UNTIL - CURRENT_TIME) / 60 ))
        log "Rate limit cooldown active. Wait ${WAIT_MINS} more minutes. Exiting."
        exit 0
    else
        rm -f "$RATE_LIMIT_FILE"
    fi
fi

# Check daily attempt limit
TODAY=$(date +%Y-%m-%d)
if [ -f "$DAILY_COUNT_FILE" ]; then
    SAVED_DATE=$(head -1 "$DAILY_COUNT_FILE" 2>/dev/null)
    SAVED_COUNT=$(tail -1 "$DAILY_COUNT_FILE" 2>/dev/null)
    if [ "$SAVED_DATE" == "$TODAY" ]; then
        if [ "$SAVED_COUNT" -ge "$DAILY_MAX_ATTEMPTS" ]; then
            log "Daily attempt limit reached ($DAILY_MAX_ATTEMPTS). Try again tomorrow."
            exit 0
        fi
        DAILY_COUNT=$SAVED_COUNT
    else
        DAILY_COUNT=0
    fi
else
    DAILY_COUNT=0
fi

# Increment daily count
DAILY_COUNT=$((DAILY_COUNT + 1))
echo -e "$TODAY\n$DAILY_COUNT" > "$DAILY_COUNT_FILE"

log "========================================"
log "Starting Cloudflare Tunnel restart (Attempt $DAILY_COUNT/$DAILY_MAX_ATTEMPTS today)..."

# Kill existing cloudflared processes
if [ -f "$PID_FILE" ]; then
    OLD_PID=$(cat "$PID_FILE")
    if ps -p $OLD_PID > /dev/null 2>&1; then
        log "Killing old cloudflared process (PID: $OLD_PID)"
        kill $OLD_PID 2>/dev/null
        sleep 2
    fi
fi
pkill -f "cloudflared.*url http://localhost:4005" 2>/dev/null
sleep 2

# Retry loop with exponential backoff
RETRY_COUNT=0
CURRENT_DELAY=$INITIAL_DELAY

while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
    RETRY_COUNT=$((RETRY_COUNT + 1))
    log "Attempt $RETRY_COUNT/$MAX_RETRIES - Creating tunnel..."

    rm -f "$TEMP_LOG"

    # Start tunnel
    nohup $CLOUDFLARED tunnel --url http://localhost:$AI_SERVER_PORT > "$TEMP_LOG" 2>&1 &
    NEW_PID=$!
    echo $NEW_PID > "$PID_FILE"

    # Wait for URL (max 45 seconds)
    MAX_WAIT=45
    WAIT_COUNT=0
    NEW_URL=""
    RATE_LIMITED=false

    while [ $WAIT_COUNT -lt $MAX_WAIT ]; do
        sleep 1
        WAIT_COUNT=$((WAIT_COUNT + 1))

        if [ -f "$TEMP_LOG" ]; then
            # Check for successful URL
            NEW_URL=$(grep -oE 'https://[a-z0-9-]+\.trycloudflare\.com' "$TEMP_LOG" | head -1)
            if [ -n "$NEW_URL" ]; then
                break
            fi

            # Check for RATE LIMIT error (429)
            if grep -q "429 Too Many Requests" "$TEMP_LOG" 2>/dev/null; then
                log "RATE LIMIT detected (429)! Entering cooldown..."
                RATE_LIMITED=true
                pkill -f "cloudflared.*url http://localhost:4005" 2>/dev/null
                break
            fi

            # Check for Cloudflare API error (service outage)
            if grep -q "Error unmarshaling QuickTunnel" "$TEMP_LOG" 2>/dev/null; then
                log "Cloudflare API error detected"
                pkill -f "cloudflared.*url http://localhost:4005" 2>/dev/null
                break
            fi

            if grep -q "failed to unmarshal quick Tunnel" "$TEMP_LOG" 2>/dev/null; then
                log "Cloudflare API error detected"
                pkill -f "cloudflared.*url http://localhost:4005" 2>/dev/null
                break
            fi
        fi
    done

    # If rate limited, set cooldown and exit
    if [ "$RATE_LIMITED" = true ]; then
        COOLDOWN_UNTIL=$(($(date +%s) + RATE_LIMIT_COOLDOWN))
        echo "$COOLDOWN_UNTIL" > "$RATE_LIMIT_FILE"
        log "Rate limit cooldown set for $((RATE_LIMIT_COOLDOWN / 60)) minutes."
        log "========================================"
        exit 1
    fi

    # If we got a URL, verify and update
    if [ -n "$NEW_URL" ]; then
        log "Tunnel URL obtained: $NEW_URL"

        # Wait for tunnel to stabilize
        sleep 5

        # Verify tunnel works
        HEALTH_CHECK=$(curl -s --connect-timeout 10 "$NEW_URL/health" 2>/dev/null)
        if echo "$HEALTH_CHECK" | grep -q "healthy"; then
            log "Tunnel health check PASSED!"

            # Get old URL
            OLD_URL=$(grep -oE "DIRECT_AI_SERVER_URL = 'https://[a-z0-9-]+\.trycloudflare\.com'" "$CHATBOT_FILE" | grep -oE 'https://[a-z0-9-]+\.trycloudflare\.com')

            if [ "$OLD_URL" == "$NEW_URL" ]; then
                log "URL unchanged, no update needed"
            else
                log "Updating URLs: $OLD_URL -> $NEW_URL"

                # Update chatbot.html
                sed -i "s|DIRECT_AI_SERVER_URL = '$OLD_URL'|DIRECT_AI_SERVER_URL = '$NEW_URL'|g" "$CHATBOT_FILE"

                # Update bug-report.html
                if [ -f "$BUGREPORT_FILE" ]; then
                    sed -i "s|DIRECT_AI_SERVER_URL = '$OLD_URL'|DIRECT_AI_SERVER_URL = '$NEW_URL'|g" "$BUGREPORT_FILE"
                fi

                # Git commit and push (with auto pull --rebase + retry on conflict)
                git add -A
                git commit -m "Auto-update Cloudflare Tunnel URL" >> "$LOG_FILE" 2>&1
                if safe_git_push main "$LOG_FILE"; then
                    log "Successfully pushed to GitHub!"
                else
                    log "WARNING: Failed to push to GitHub after retries"
                fi
            fi

            # Reset daily count on success (optional - encourages healthy behavior)
            echo -e "$TODAY\n0" > "$DAILY_COUNT_FILE"

            log "Tunnel restart completed successfully!"
            log "========================================"
            exit 0
        else
            log "Health check FAILED, will retry..."
            pkill -f "cloudflared.*url http://localhost:4005" 2>/dev/null
        fi
    fi

    # Wait before retry (exponential backoff)
    if [ $RETRY_COUNT -lt $MAX_RETRIES ]; then
        log "Waiting ${CURRENT_DELAY}s before next attempt (exponential backoff)..."
        sleep $CURRENT_DELAY

        # Double the delay for next time, up to max
        CURRENT_DELAY=$((CURRENT_DELAY * 2))
        if [ $CURRENT_DELAY -gt $MAX_DELAY ]; then
            CURRENT_DELAY=$MAX_DELAY
        fi
    fi
done

log "ERROR: Failed to create tunnel after $MAX_RETRIES attempts!"
log "========================================"
exit 1
