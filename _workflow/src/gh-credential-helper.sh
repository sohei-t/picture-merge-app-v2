#!/bin/bash
# GitHub CLI credential helper for M4 Mac
# This script acts as a Git credential helper using GitHub CLI
# Required for automatic push in M4 Mac environments

# Check if gh is available
GH_PATH=""
if [ -x "$HOME/bin/gh" ]; then
    GH_PATH="$HOME/bin/gh"
elif command -v gh &> /dev/null; then
    GH_PATH="gh"
else
    echo "Error: GitHub CLI (gh) not found" >&2
    echo "Please run: ./setup_github_cli_m4.sh" >&2
    exit 1
fi

# Execute gh auth git-credential with all arguments
exec "$GH_PATH" auth git-credential "$@"