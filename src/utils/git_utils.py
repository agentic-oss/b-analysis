import subprocess
import logging
import os

logger = logging.getLogger("utils.git_utils")

def git_commit_and_push(commit_message: str, push: bool = False) -> bool:
    """
    Stages generated data files, checks for changes, and commits them.
    Pushes if requested and permitted.
    """
    try:
        # Check status
        status = subprocess.check_output(["git", "status", "--porcelain"], text=True)
        if not status.strip():
            logger.info("No untracked or modified files to commit.")
            return True

        # Stage specific generated data/report directories
        subprocess.run(["git", "add", "data/", "reports/"], check=True)

        # Check staged diff
        staged = subprocess.check_output(["git", "diff", "--cached", "--name-only"], text=True)
        if not staged.strip():
            logger.info("No staged files for git commit.")
            return True

        # Commit
        subprocess.run(["git", "commit", "-m", commit_message], check=True)
        logger.info(f"Git commit created: {commit_message}")

        if push:
            try:
                subprocess.run(["git", "push"], check=True)
                logger.info("Successfully pushed changes to remote repository.")
            except Exception as pe:
                logger.warning(f"Git push failed (permission or branch upstream issue): {pe}")

        return True
    except Exception as e:
        logger.error(f"Error executing git workflow: {e}")
        return False
