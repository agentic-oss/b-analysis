"""
Git Commit Utility for Data Pipeline Outputs.
Prevents committing API keys, tokens, or environment files.
"""

import os
import subprocess
import logging
import sys

logger = logging.getLogger("GitCommit")


def check_no_secrets():
    """Scans staging diff for potential secret keys."""
    try:
        diff_output = subprocess.check_output(["git", "diff", "--cached"], text=True)
        suspicious_terms = ["api_key", "secret_key", "password=", "token=", "bearer "]
        for line in diff_output.splitlines():
            if line.startswith("+"):
                for term in suspicious_terms:
                    if term in line.lower():
                        logger.error(f"Potential secret detected in diff line: {line.strip()}")
                        sys.exit(1)
    except Exception as e:
        logger.warning(f"Could not run secret check: {e}")


def commit_pipeline_outputs(date_str: str):
    """Stages generated data/ and reports/ files and commits if changes exist."""
    try:
        # Check git status
        status = subprocess.check_output(["git", "status", "--porcelain"], text=True)
        if not status:
            logger.info("No changes to commit.")
            return

        # Stage data and reports directories
        subprocess.run(["git", "add", "data/", "reports/"], check=True)

        # Verify secret safeguard
        check_no_secrets()

        commit_msg = f"data: daily Indian market analysis {date_str}"
        res = subprocess.run(["git", "commit", "-m", commit_msg], capture_output=True, text=True)
        if res.returncode == 0:
            logger.info(f"Committed daily analysis output: '{commit_msg}'")
        else:
            logger.info(f"Git commit output: {res.stdout.strip() or res.stderr.strip()}")

    except Exception as e:
        logger.error(f"Error executing git commit: {e}")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--date", type=str, required=True)
    args = parser.parse_args()
    commit_pipeline_outputs(args.date)
