"""
Helper script to commit generated data and reports automatically to git.
Prevents committing untracked secret files or credentials.
"""
import datetime
import logging
import os
import subprocess
import sys

logger = logging.getLogger("GitCommit")


def run_cmd(cmd: str) -> str:
    res = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if res.returncode != 0:
        logger.warning(f"Command '{cmd}' failed: {res.stderr.strip()}")
    return res.stdout.strip()


def main():
    date_str = datetime.date.today().strftime("%Y-%m-%d")
    if len(sys.argv) > 1:
        date_str = sys.argv[1]

    # Staging generated outputs only
    paths_to_stage = ["data/", "reports/"]
    for path in paths_to_stage:
        if os.path.exists(path):
            run_cmd(f"git add {path}")

    status = run_cmd("git status --porcelain")
    if not status:
        logger.info("No changes to commit.")
        return

    commit_msg = f"data: daily Indian market analysis {date_str}"
    logger.info(f"Committing changes with message: {commit_msg}")
    run_cmd(f'git commit -m "{commit_msg}"')


if __name__ == "__main__":
    main()
