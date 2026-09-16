import subprocess
import logging
from typing import List, Optional

logger = logging.getLogger(__name__)


def auto_commit_and_push(
    commit_message: str,
    paths_to_add: Optional[List[str]] = None
) -> bool:
    """
    Checks for git changes in data/ and reports/, stages changed files, and commits with provided message.
    Pushes changes if remote branch permission is available.
    """
    if paths_to_add is None:
        paths_to_add = ["data/", "reports/"]

    try:
        # Check git status
        status_out = subprocess.check_output(["git", "status", "--porcelain"]).decode("utf-8")
        if not status_out.strip():
            logger.info("No modified files or new artifacts to commit.")
            return False

        # Add specified paths
        for path in paths_to_add:
            subprocess.run(["git", "add", path], check=False)

        # Commit changes
        commit_res = subprocess.run(["git", "commit", "-m", commit_message], capture_output=True, text=True)
        if commit_res.returncode == 0:
            logger.info(f"Successfully committed artifacts: {commit_message}")
        else:
            logger.info(f"Git commit output: {commit_res.stdout} {commit_res.stderr}")

        # Attempt push (optional / graceful if remote configured)
        push_res = subprocess.run(["git", "push"], capture_output=True, text=True)
        if push_res.returncode == 0:
            logger.info("Successfully pushed committed changes to remote repository.")
        else:
            logger.info(f"Git push skipped or not permitted in current environment: {push_res.stderr.strip()}")

        return True
    except Exception as e:
        logger.warning(f"Error during automated git commit process: {e}")
        return False
