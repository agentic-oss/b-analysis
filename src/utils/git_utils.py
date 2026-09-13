import subprocess
import os
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class GitIntegrator:
    @staticmethod
    def commit_and_push(date_str: str, repo_dir: str = ".") -> bool:
        """
        Automatically stages and commits generated daily market data artifacts.
        Pushes to current branch if remote permission is available.
        """
        try:
            # Check for changes in data/ and reports/
            diff_check = subprocess.run(
                ["git", "status", "--porcelain", "data/", "reports/"],
                cwd=repo_dir,
                capture_output=True,
                text=True
            )

            if not diff_check.stdout.strip():
                logger.info("No generated market data changes to commit.")
                return False

            # Stage data and reports
            subprocess.run(["git", "add", "data/", "reports/"], cwd=repo_dir, check=True)

            commit_msg = f"data: daily Indian market analysis {date_str}"
            subprocess.run(["git", "commit", "-m", commit_msg], cwd=repo_dir, check=True)
            logger.info(f"Successfully committed artifacts: {commit_msg}")

            # Try pushing if git remote is set up
            push_res = subprocess.run(["git", "push"], cwd=repo_dir, capture_output=True, text=True)
            if push_res.returncode == 0:
                logger.info("Successfully pushed commits to remote repo.")
            else:
                logger.warning(f"Git push skipped or failed: {push_res.stderr.strip()}")

            return True

        except Exception as e:
            logger.error(f"Failed to complete Git commit/push: {str(e)}")
            return False
