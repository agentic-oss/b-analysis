"""Automated Git Integration Module."""

import subprocess
import logging
from typing import Optional

logger = logging.getLogger(__name__)

class GitIntegration:
    """Handles automatic staging, committing, and pushing generated pipeline artifacts without committing secrets."""

    @staticmethod
    def commit_daily_results(date_str: str, repo_path: str = ".") -> bool:
        """Stages data and reports directories and commits if changes exist."""
        try:
            # Check status
            status_cmd = subprocess.run(["git", "status", "--porcelain", "data/", "reports/"], cwd=repo_path, capture_output=True, text=True)
            if not status_cmd.stdout.strip():
                logger.info("No new changes in data/ or reports/ to commit.")
                return False

            # Stage data and reports
            subprocess.run(["git", "add", "data/", "reports/"], cwd=repo_path, check=True)

            # Commit with standard message format
            commit_msg = f"data: daily Indian market analysis {date_str}"
            subprocess.run(["git", "commit", "-m", commit_msg], cwd=repo_path, check=True)
            logger.info(f"Successfully committed generated market analysis for {date_str}")
            return True

        except subprocess.CalledProcessError as e:
            logger.warning(f"Git commit failed or skipped: {e}")
            return False

    @staticmethod
    def push_changes(repo_path: str = ".") -> bool:
        """Pushes local commits to remote if credentials/permissions allow."""
        try:
            subprocess.run(["git", "push"], cwd=repo_path, check=True)
            logger.info("Successfully pushed committed changes to remote repository.")
            return True
        except subprocess.CalledProcessError as e:
            logger.warning(f"Git push skipped or failed (likely running without write permission): {e}")
            return False
