#!/bin/bash

# Shared helper for restart_tunnel.sh / restart_admin_tunnel.sh.
#
# safe_git_push <branch> <log_file>
#
# Pushes HEAD to origin/<branch>. If the push is rejected because the remote
# advanced (this is the common cause of the chronic "Failed to push to GitHub"
# warning we saw across both auto-update scripts), it pulls with --rebase and
# retries up to 3 times. Returns 0 on success, 1 on failure.
#
# Why this matters for tunnel URL rotation:
#   The whole point of admin.html / chatbot.html living in git is that
#   reality.ssu.ac.kr/admin.html always redirects to the *current* tunnel.
#   If push silently fails, GitHub Pages keeps serving the stale URL and the
#   site appears broken even though the tunnel itself is healthy.

safe_git_push() {
    local BRANCH="${1:-main}"
    local LOG_FILE="${2:-/dev/stderr}"
    local MAX_ATTEMPTS=3

    _log() {
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] [safe_git_push] $1" >> "$LOG_FILE"
    }

    for attempt in $(seq 1 $MAX_ATTEMPTS); do
        if git push origin "$BRANCH" >> "$LOG_FILE" 2>&1; then
            _log "push succeeded on attempt $attempt"
            return 0
        fi

        _log "push attempt $attempt failed, attempting pull --rebase"

        # Abort any in-progress rebase from a prior failed attempt.
        if [ -d "$(git rev-parse --git-dir)/rebase-merge" ] || \
           [ -d "$(git rev-parse --git-dir)/rebase-apply" ]; then
            git rebase --abort >> "$LOG_FILE" 2>&1
            _log "aborted in-progress rebase"
        fi

        if ! git pull --rebase origin "$BRANCH" >> "$LOG_FILE" 2>&1; then
            _log "pull --rebase failed (likely conflict). Aborting and giving up."
            git rebase --abort >> "$LOG_FILE" 2>&1
            return 1
        fi

        _log "rebase clean, will retry push"
    done

    _log "exhausted $MAX_ATTEMPTS push attempts, giving up"
    return 1
}
