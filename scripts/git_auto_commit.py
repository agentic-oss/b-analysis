import subprocess
import logging
import sys

logger = logging.getLogger("GitAutoCommit")

def auto_commit_and_push(date_str: str):
    """
    Checks for modified generated data/reports and commits them automatically.
    Never commits secrets or environment files.
    """
    try:
        # Check status
        status = subprocess.check_output(["git", "status", "--porcelain"], text=True)
        if not status.strip():
            logger.info("No changes detected in repository. Nothing to commit.")
            return

        # Stage specific safe directories
        paths_to_stage = ["data/", "reports/"]
        for p in paths_to_stage:
            subprocess.run(["git", "add", p], check=False)

        # Check staged changes
        staged = subprocess.check_output(["git", "diff", "--cached", "--name-only"], text=True)
        if not staged.strip():
            logger.info("No relevant generated data to commit.")
            return

        commit_msg = f"data: daily Indian market analysis {date_str}"
        subprocess.run(["git", "commit", "-m", commit_msg], check=True)
        logger.info(f"Successfully committed generated analysis for {date_str}")

        # Push if remote is configured and permission exists
        push_res = subprocess.run(["git", "push"], check=False)
        if push_res.returncode == 0:
            logger.info("Successfully pushed commits to remote repository.")
        else:
            logger.info("Git push not executed or not permitted in current context.")

    except Exception as e:
        logger.error(f"Git auto-commit failed: {e}")

if __name__ == "__main__":
    date_arg = sys.argv[1] if len(sys.argv) > 1 else "latest"
    auto_commit_and_push(date_arg)
