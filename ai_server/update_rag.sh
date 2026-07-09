#!/bin/bash

# Reality Lab RAG Auto-Update Script
# Builds knowledge base from local YAML/MD files and rebuilds hierarchical RAG index.
#
# Portable: honors REALITY_HOME, falls back to the script's own location.

set -u

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SITE_ROOT="${REALITY_HOME:-$(cd "$SCRIPT_DIR/.." && pwd)}"
PYTHON="${PYTHON_BIN:-python3}"
if [ -x "$SITE_ROOT/.venv/bin/python3" ]; then
    PYTHON="$SITE_ROOT/.venv/bin/python3"
fi
export CUDA_VISIBLE_DEVICES=""

RESTART_CHATBOT="${RESTART_CHATBOT:-1}"

echo ""
echo "========================================"
echo "[$(date)] Starting RAG Update..."
echo "========================================"

# Step 1: Build knowledge base from local data files
echo "[$(date)] Step 1/3: Building knowledge base from local files..."
cd "$SCRIPT_DIR" || exit 1
$PYTHON build_knowledge_base.py
if [ $? -ne 0 ]; then
    echo "[$(date)] ERROR: Knowledge base build failed!"
    exit 1
fi
echo "[$(date)] Knowledge base built successfully"

# Step 2: Build hierarchical RAG index
echo "[$(date)] Step 2/3: Building hierarchical RAG index..."
$PYTHON build_hierarchical_rag.py
if [ $? -ne 0 ]; then
    echo "[$(date)] ERROR: Hierarchical RAG build failed!"
    exit 1
fi
echo "[$(date)] Hierarchical RAG index built successfully"

# Step 3: Restart chatbot server (unless caller opted out)
if [ "$RESTART_CHATBOT" = "1" ]; then
    echo "[$(date)] Step 3/3: Restarting chatbot server..."
    pkill -f "ai_chatbot_server.py" || true
    sleep 3

    nohup $PYTHON ai_chatbot_server.py --port 4005 >> /tmp/chatbot_server.log 2>&1 &
    CHATBOT_PID=$!
    sleep 5

    if ps -p $CHATBOT_PID > /dev/null 2>&1; then
        echo "[$(date)] Chatbot server restarted (PID: $CHATBOT_PID)"
    else
        echo "[$(date)] WARNING: Chatbot server may not have started. Monitor will auto-restart it."
    fi
else
    echo "[$(date)] Step 3/3: SKIP chatbot restart (RESTART_CHATBOT=$RESTART_CHATBOT)"
fi

# Summary
KB_FILE="$SCRIPT_DIR/knowledge_base.json"
if [ -f "$KB_FILE" ]; then
    DOCS_COUNT=$($PYTHON -c "import json; f=open('$KB_FILE'); data=json.load(f); print(len(data)); f.close()")
    echo ""
    echo "Summary:"
    echo "  Knowledge base documents: $DOCS_COUNT"
fi

echo ""
echo "========================================"
echo "[$(date)] RAG Update Completed!"
echo "========================================"
