#!/bin/bash

# Check if a commit message was provided
if [ -z "$1" ]; then
  echo "Usage: $0 \"<commit_message>\""
  exit 1
fi

COMMIT_MESSAGE="$1"

echo "Staging all changes..."
git add .

echo "Committing with message: \"$COMMIT_MESSAGE\""
git commit -m "$COMMIT_MESSAGE"

echo "Pushing changes..."
git push

echo "Git operations completed."
