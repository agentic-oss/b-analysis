"""
Automated Git Commit script for generated market analysis artifacts.
Stages data/, reports/, config/ changes while ignoring secrets, and commits cleanly.
"""

import os
import sys
import subprocess
from datetime import datetime


def run_cmd(cmd: list) -> tuple:
    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    return result.returncode, result.stdout.strip(), result.stderr.strip()


def auto_commit(date_str: str = None):
    if not date_str:
        date_str = datetime.today().strftime("%Y-%m-%d")

    _dir = os.path.dirname(os.path.abspath(__file__))
    repo_root = os.path.abspath(os.path.join(_dir, "../.."))
    os.chdir(repo_root)

    # Ensure git user config exists if not set
    code, out, _ = run_cmd(["git", "config", "user.name"])
    if not out:
        run_cmd(["git", "config", "user.name", "github-actions[bot]"])
        run_cmd(["git", "config", "user.email", "github-actions[bot]@users.noreply.github.com"])

    # Check status
    code, out, _ = run_cmd(["git", "status", "--porcelain"])
    if not out:
        print("No changes to commit.")
        return

    # Stage data and reports
    run_cmd(["git", "add", "data/", "reports/", "config/"])

    # Verify staged files
    code, staged, _ = run_cmd(["git", "diff", "--cached", "--name-only"])
    if not staged:
        print("No staged changes found to commit.")
        return

    commit_msg = f"data: daily Indian market analysis {date_str}"
    code, out, err = run_cmd(["git", "commit", "-m", commit_msg])

    if code == 0:
        print(f"Successfully committed changes: {commit_msg}")
        # Try pushing if permitted
        push_code, push_out, push_err = run_cmd(["git", "push"])
        if push_code == 0:
            print("Successfully pushed commit to remote branch.")
        else:
            print("Push omitted or skipped (no remote permission or branch unset):", push_err)
    else:
        print("Git commit failed:", err)


if __name__ == "__main__":
    date_arg = sys.argv[1] if len(sys.argv) > 1 else None
    auto_commit(date_arg)
