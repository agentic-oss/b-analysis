#!/usr/bin/env bash
set -e

DATE_STR=$(date +'%Y-%m-%d')
COMMIT_MSG="data: daily Indian market analysis ${DATE_STR}"

echo "Checking for uncommitted data changes..."

git add data/ reports/

if git diff --staged --quiet; then
    echo "No changes in market artifacts to commit."
else
    echo "Committing market artifacts for ${DATE_STR}..."
    git commit -m "${COMMIT_MSG}"
    echo "Successfully committed market data."
fi
