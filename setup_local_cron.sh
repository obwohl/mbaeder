#!/bin/bash

# Setup script for local execution of SWM Scraper via crontab
# This script sets up a crontab entry to run the scraper every 30 minutes.

if [ "$#" -ne 1 ]; then
    echo "Usage: $0 <path_to_repository>"
    echo "Example: $0 /home/user/projects/swm-auslastung"
    exit 1
fi

REPO_PATH=$(realpath "$1")

if [ ! -d "$REPO_PATH/.git" ]; then
    echo "Error: $REPO_PATH is not a valid git repository."
    exit 1
fi

if [ ! -f "$REPO_PATH/swm_auslastung.py" ] || [ ! -f "$REPO_PATH/process_auslastung.py" ]; then
    echo "Error: Python scraper files not found in $REPO_PATH."
    exit 1
fi

CRON_CMD="cd $REPO_PATH && python3 swm_auslastung.py && python3 process_auslastung.py && git add auslastung_raw.csv auslastung_live.csv scraper.log && git commit -m \"chore: update auslastung data via local cron\" && git push"

# Create a temporary file for the new crontab
TMP_CRON=$(mktemp)

# Export the current crontab, ignore "no crontab" error
crontab -l > "$TMP_CRON" 2>/dev/null || true

# Check if the command is already in the crontab
if grep -q "swm_auslastung.py" "$TMP_CRON"; then
    echo "Crontab entry already exists. No changes made."
    rm "$TMP_CRON"
    exit 0
fi

# Append the new cron job (runs at minute 17 of every hour)
echo "17 * * * * $CRON_CMD >> $REPO_PATH/local_cron_execution.log 2>&1" >> "$TMP_CRON"

# Install the new crontab
crontab "$TMP_CRON"

# Cleanup
rm "$TMP_CRON"

echo "Successfully added crontab entry for $REPO_PATH."
echo "The scraper will now run locally at minute 17 of every hour."
