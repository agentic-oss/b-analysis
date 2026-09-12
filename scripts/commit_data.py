#!/usr/bin/env python3
import os
import sys
import subprocess
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

def commit_daily_data():
    """
    Automated git commit utility for daily analysis artifacts.
    Checks for sensitive files before committing.
    """
    status_proc = subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True)
    if not status_proc.stdout.strip():
        logger.info("No modified or untracked files to commit.")
        return

    # Security check: Ensure no .env or sensitive credentials are standard files
    untracked = status_proc.stdout.strip().split("\n")
    for line in untracked:
        filename = line[3:].strip()
        if filename.endswith(".env") or "secret" in filename.lower() or "key" in filename.lower():
            logger.error(f"SECURITY ALERT: Refusing to commit potentially sensitive file: {filename}")
            sys.exit(1)

    # Stage data, reports, and quality outputs
    stage_cmd = ["git", "add", "data/", "reports/", "docs/"]
    subprocess.run(stage_cmd, check=True)

    date_str = os.popen("date +%Y-%m-%d").read().strip()
    commit_msg = f"data: daily Indian market analysis {date_str}"

    commit_cmd = ["git", "commit", "-m", commit_msg]
    res = subprocess.run(commit_cmd, capture_output=True, text=True)
    if res.returncode == 0:
        logger.info(f"Successfully committed daily outputs: {commit_msg}")
    else:
        logger.info(f"Git commit output: {res.stdout} {res.stderr}")

if __name__ == "__main__":
    commit_daily_data()
