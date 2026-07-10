#!/bin/bash
# dev/serve_all.sh — 로컬에서 Jekyll + 챗봇 + Admin CMS 한 방에 백그라운드 기동
#
# 사용:
#   ./dev/serve_all.sh              # 3개 다 띄움
#   ./dev/serve_all.sh jekyll       # Jekyll만
#   ./dev/serve_all.sh chatbot      # 챗봇만
#   ./dev/serve_all.sh admin        # Admin만
#
# 로그: /tmp/reality-dev/*.log
# 중지: ./dev/stop_all.sh

set -u

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
LOG_DIR="/tmp/reality-dev"
mkdir -p "$LOG_DIR"

WANT="${1:-all}"

start_jekyll() {
    if lsof -i :4000 >/dev/null 2>&1; then
        echo "[jekyll] port 4000 already in use — skipping"
        return
    fi
    echo "[jekyll] starting on :4000 (livereload)"
    cd "$REPO_ROOT"
    nohup bundle exec jekyll serve --port 4000 --livereload \
        > "$LOG_DIR/jekyll.log" 2>&1 &
    echo $! > "$LOG_DIR/jekyll.pid"
    echo "[jekyll] PID $(cat $LOG_DIR/jekyll.pid) — http://localhost:4000"
}

start_chatbot() {
    if lsof -i :4005 >/dev/null 2>&1; then
        echo "[chatbot] port 4005 already in use — skipping"
        return
    fi
    if [ ! -f "$REPO_ROOT/.venv/bin/python3" ]; then
        echo "[chatbot] .venv not found. Run scripts/migrate/bootstrap_new_server.sh first."
        return
    fi
    if [ ! -f "$REPO_ROOT/.env" ]; then
        echo "[chatbot] WARN: .env missing — /chat will 503 (health/tunnel still works)"
    fi
    echo "[chatbot] starting on :4005"
    cd "$REPO_ROOT/ai_server"
    nohup "$REPO_ROOT/.venv/bin/python3" ai_chatbot_server.py --port 4005 \
        > "$LOG_DIR/chatbot.log" 2>&1 &
    echo $! > "$LOG_DIR/chatbot.pid"
    echo "[chatbot] PID $(cat $LOG_DIR/chatbot.pid) — http://localhost:4005/health"
}

start_admin() {
    if lsof -i :4010 >/dev/null 2>&1; then
        echo "[admin] port 4010 already in use — skipping"
        return
    fi
    if [ ! -f "$REPO_ROOT/.venv/bin/python3" ]; then
        echo "[admin] .venv not found. Run scripts/migrate/bootstrap_new_server.sh first."
        return
    fi
    if [ ! -f "$REPO_ROOT/admin_cms/admin_config.json" ]; then
        echo "[admin] WARN: admin_config.json missing — run admin_cms/set_admin_password.py first"
    fi
    echo "[admin] starting on :4010"
    cd "$REPO_ROOT/admin_cms"
    nohup "$REPO_ROOT/.venv/bin/python3" admin_server.py --port 4010 \
        > "$LOG_DIR/admin.log" 2>&1 &
    echo $! > "$LOG_DIR/admin.pid"
    echo "[admin] PID $(cat $LOG_DIR/admin.pid) — http://localhost:4010"
}

case "$WANT" in
    all)     start_jekyll; start_chatbot; start_admin ;;
    jekyll)  start_jekyll ;;
    chatbot) start_chatbot ;;
    admin)   start_admin ;;
    *)       echo "usage: $0 [all|jekyll|chatbot|admin]"; exit 1 ;;
esac

echo ""
echo "logs: tail -f $LOG_DIR/*.log"
echo "stop: $REPO_ROOT/dev/stop_all.sh"
