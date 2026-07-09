#!/bin/bash
# Start chatbot server + tunnels after rest time (08:00 KST)
#
# NOTE: llama-server / GPT-OSS-120B startup was removed when the chatbot
# switched to the OpenAI API. See ai_chatbot_server.py.
# The legacy script is preserved as start_server_and_tunnel.legacy.sh for
# rollback in case the OpenAI backend is reverted.

set -u

WORK_DIR="${REALITY_HOME:-$HOME/Realitylab-site}"
LOG_FILE="$WORK_DIR/ai_server/rest_time.log"
CHATBOT_SERVER="$WORK_DIR/ai_server/ai_chatbot_server.py"
ADMIN_CMS_DIR="$WORK_DIR/admin_cms"

echo "$(date): === REST TIME END ===" >> "$LOG_FILE"

# === 1. Start ai_chatbot_server.py ===
if pgrep -f "ai_chatbot_server.py" > /dev/null; then
    echo "$(date): ai_chatbot_server already running, skipping" >> "$LOG_FILE"
else
    echo "$(date): Starting ai_chatbot_server.py (port 4005)..." >> "$LOG_FILE"
    cd "$WORK_DIR/ai_server" || exit 1
    nohup python3 "$CHATBOT_SERVER" --port 4005 > /tmp/chatbot_server.log 2>&1 &
    echo "$(date): ai_chatbot_server starting (PID: $!)" >> "$LOG_FILE"

    for i in {1..10}; do
        sleep 2
        if curl -s --max-time 3 http://localhost:4005/health | grep -q "healthy"; then
            echo "$(date): ai_chatbot_server is ready!" >> "$LOG_FILE"
            break
        fi
        echo "$(date): Waiting for chatbot server... ($i/10)" >> "$LOG_FILE"
    done
fi

# === 2. Start chatbot tunnel ===
echo "$(date): Starting chatbot tunnel..." >> "$LOG_FILE"
"$WORK_DIR/ai_server/restart_tunnel.sh" >> "$LOG_FILE" 2>&1

# === 3. Start admin CMS server (port 4010) ===
if pgrep -f "admin_server.py" > /dev/null; then
    echo "$(date): admin_server already running, skipping" >> "$LOG_FILE"
else
    echo "$(date): Starting admin_server.py (port 4010)..." >> "$LOG_FILE"
    cd "$ADMIN_CMS_DIR" || exit 1
    nohup python3 admin_server.py --port 4010 > /tmp/admin_cms.log 2>&1 &
    echo "$(date): admin_server starting (PID: $!)" >> "$LOG_FILE"
    sleep 5
fi

# === 4. Start admin tunnel ===
echo "$(date): Starting admin tunnel..." >> "$LOG_FILE"
"$WORK_DIR/ai_server/restart_admin_tunnel.sh" >> "$LOG_FILE" 2>&1

echo "$(date): All services started" >> "$LOG_FILE"
