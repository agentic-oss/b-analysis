import os
import subprocess
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

def run_cmd(cmd):
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    return result.returncode, result.stdout.strip(), result.stderr.strip()

def auto_commit():
    """
    Checks git status for modified/untracked files in data/ and reports/,
    commits with standardized message, and pushes if remote permission exists.
    """
    # Configure git bot user if needed
    run_cmd('git config user.name "github-actions[bot]"')
    run_cmd('git config user.email "41898282+github-actions[bot]@users.noreply.github.com"')

    code, out, _ = run_cmd("git status --porcelain data/ reports/")
    if not out:
        logger.info("No data or report changes to commit.")
        return

    date_str = datetime.now().strftime("%Y-%m-%d")
    commit_msg = f"data: daily Indian market analysis {date_str}"

    run_cmd("git add data/ reports/")
    code, out, err = run_cmd(f'git commit -m "{commit_msg}"')
    if code == 0:
        logger.info(f"Successfully committed changes: {commit_msg}")
        push_code, push_out, push_err = run_cmd("git push")
        if push_code == 0:
            logger.info("Successfully pushed committed changes to remote repository.")
        else:
            logger.warning(f"Push skipped or failed (may require workflow permission): {push_err}")
    else:
        logger.warning(f"Git commit returned code {code}: {err}")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    auto_commit()
