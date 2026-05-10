#!/bin/bash
# Run this once to register the 6 AM daily cron job.
# Usage: bash setup_cron.sh

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CRON_CMD="0 6 * * * /bin/bash $REPO_DIR/run_daily.sh"

# Make run_daily.sh executable
chmod +x "$REPO_DIR/run_daily.sh"

# Install cron job (idempotent — removes old entry first)
(crontab -l 2>/dev/null | grep -v "run_daily.sh"; echo "$CRON_CMD") | crontab -

echo "Cron job installed:"
crontab -l | grep "run_daily"
echo ""
echo "The routine will run every day at 6:00 AM."
echo "Logs will be written to: $REPO_DIR/logs/run_<date>.log"
echo ""
echo "Before the first run, create a .env file at:"
echo "  $REPO_DIR/.env"
echo ""
echo "with these variables:"
echo "  IMAGE_API_KEY=<your image API key>"
echo "  IMAGE_API_URL=<your image API endpoint>"
echo "  ZAPIER_WEBHOOK_URL=<your Zapier catch webhook URL>"
