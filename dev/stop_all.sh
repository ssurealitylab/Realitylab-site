#!/bin/bash
# dev/stop_all.sh — serve_all.sh로 띄운 로컬 서비스 종료

set -u

LOG_DIR="/tmp/reality-dev"

WANT="${1:-all}"

stop_by_name() {
    local NAME="$1"
    local PIDFILE="$LOG_DIR/$NAME.pid"
    if [ ! -f "$PIDFILE" ]; then
        echo "[$NAME] no pidfile — nothing to stop"
        return
    fi
    local PID
    PID=$(cat "$PIDFILE")
    if kill -0 "$PID" 2>/dev/null; then
        kill "$PID" && echo "[$NAME] SIGTERM sent to $PID"
        sleep 2
        if kill -0 "$PID" 2>/dev/null; then
            kill -9 "$PID" && echo "[$NAME] SIGKILL (survived TERM)"
        fi
    else
        echo "[$NAME] PID $PID no longer running"
    fi
    rm -f "$PIDFILE"
}

case "$WANT" in
    all)
        stop_by_name jekyll
        stop_by_name chatbot
        stop_by_name admin
        # jekyll spawns a child ruby too — clean up if orphaned
        pkill -f "jekyll serve" 2>/dev/null || true
        ;;
    jekyll)  stop_by_name jekyll; pkill -f "jekyll serve" 2>/dev/null || true ;;
    chatbot) stop_by_name chatbot ;;
    admin)   stop_by_name admin ;;
    *) echo "usage: $0 [all|jekyll|chatbot|admin]"; exit 1 ;;
esac
