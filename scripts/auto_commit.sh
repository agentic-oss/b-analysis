#!/usr/bin/env bash
set -e

DATE=${1:-$(date +%Y-%m-%d)}

echo "=== Auto Commit Daily Market Analysis Outputs for $DATE ==="

# Check git status
if [ -z "$(git status --porcelain)" ]; then
    echo "No file changes detected. Nothing to commit."
    exit 0
fi

# Stage generated data and reports
git add data/ reports/ config/

if git diff --cached --quiet; then
    echo "No staged changes to commit."
    exit 0
fi

COMMIT_MSG="data: daily Indian market analysis $DATE"
echo "Committing with message: $COMMIT_MSG"
git commit -m "$COMMIT_MSG"

if [ "$PUSH_ENABLED" = "true" ]; then
    echo "Pushing changes to remote branch..."
    git push origin HEAD
else
    echo "PUSH_ENABLED is not set to 'true'. Skipping git push."
fi
