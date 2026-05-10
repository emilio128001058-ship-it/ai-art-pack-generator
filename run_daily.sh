#!/bin/bash
# Daily runner for the AI art pack generator.
# Called by cron at 6 AM: 0 6 * * * /bin/bash /home/user/ai-art-pack-generator/run_daily.sh

set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_DIR="$REPO_DIR/logs"
LOG_FILE="$LOG_DIR/run_$(date +%Y-%m-%d).log"

mkdir -p "$LOG_DIR"

# Redirect all output to date-stamped log file
exec >> "$LOG_FILE" 2>&1

echo ""
echo "=== Starting at $(date) ==="

# Load env vars from .env if present
if [ -f "$REPO_DIR/.env" ]; then
    set -a
    # shellcheck disable=SC1091
    source "$REPO_DIR/.env"
    set +a
    echo "Loaded .env"
fi

# Pull latest code from the main branch
echo "Pulling latest code..."
git -C "$REPO_DIR" pull origin main

# Run the orchestrator
echo "Running daily generation..."
python3 "$REPO_DIR/run_daily.py"

echo "=== Finished at $(date) ==="
