#!/bin/bash
# Stop chatbot server + chatbot tunnel for rest time (04:00-08:00 KST)
#
# NOTE: llama-server shutdown was removed when the chatbot switched to
# the OpenAI API. See ai_chatbot_server.py.

set -u

WORK_DIR="${REALITY_HOME:-$HOME/Realitylab-site}"
LOG_FILE="$WORK_DIR/ai_server/rest_time.log"

echo "$(date): === REST TIME START ===" >> "$LOG_FILE"

# Stop ai_chatbot_server.py
echo "$(date): Stopping ai_chatbot_server..." >> "$LOG_FILE"
pkill -f "ai_chatbot_server.py"
sleep 1

# Stop chatbot cloudflared tunnel only (port 4005). Keep admin tunnel running.
echo "$(date): Stopping chatbot cloudflared tunnel..." >> "$LOG_FILE"
pkill -f "cloudflared.*url http://localhost:4005"
sleep 1

echo "$(date): Chatbot services stopped" >> "$LOG_FILE"
echo "$(date): Rest time active until 8 AM KST" >> "$LOG_FILE"
