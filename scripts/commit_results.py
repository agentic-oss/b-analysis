#!/usr/bin/env python3
"""Automated Git Commit Script for Generated Daily Artifacts."""

import argparse
import datetime
import os
import subprocess
import sys


def run_command(cmd: str) -> subprocess.CompletedProcess:
    """Execute bash command and return result."""
    return subprocess.run(cmd, shell=True, text=True, capture_output=True)


def check_secrets():
    """Safety check: verify git status does not contain sensitive key/secret files."""
    status = run_command("git status --porcelain").stdout
    forbidden_extensions = [".env", ".pem", ".key", ".secret"]
    for line in status.splitlines():
        filename = line.strip().split()[-1]
        for ext in forbidden_extensions:
            if filename.endswith(ext):
                print(f"SECURITY ERROR: Unsafe secret file detected in git status: {filename}")
                sys.exit(1)


def commit_and_push(date_str: str):
    """Stage generated artifacts, create commit, and push if permitted."""
    check_secrets()

    # Stage generated paths
    paths_to_stage = ["data/", "reports/"]
    for p in paths_to_stage:
        if os.path.exists(p):
            run_command(f"git add {p}")

    status = run_command("git status --porcelain").stdout
    if not status.strip():
        print("No generated file changes to commit.")
        return

    commit_msg = f"data: daily Indian market analysis {date_str}"
    commit_res = run_command(f'git commit -m "{commit_msg}"')
    if commit_res.returncode == 0:
        print(f"Successfully committed generated daily artifacts: '{commit_msg}'")
    else:
        print(f"Git commit failed or nothing to commit: {commit_res.stderr}")
        return

    # Try push
    push_res = run_command("git push")
    if push_res.returncode == 0:
        print("Successfully pushed committed changes to remote repository.")
    else:
        print(f"Git push skipped or non-zero return (environment permissions): {push_res.stderr}")


def main():
    parser = argparse.ArgumentParser(description="Git Commit Automated Pipeline Artifacts")
    parser.add_argument("--date", type=str, default=None, help="Trading date YYYY-MM-DD")
    args = parser.parse_args()

    date_str = args.date or datetime.date.today().strftime("%Y-%m-%d")
    commit_and_push(date_str)


if __name__ == "__main__":
    main()
