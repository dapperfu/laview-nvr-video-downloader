#!/bin/bash

# Script to sync improvements from upstream hikvision-downloader
# This script fetches the latest changes and shows what improvements are available

set -e

echo "🔄 Syncing with upstream hikvision-downloader..."

# Fetch latest upstream changes
echo "📥 Fetching latest upstream changes..."
git fetch upstream

# Show what's new
echo ""
echo "📋 New commits available from upstream:"
git log --oneline upstream/master --not master | head -20

echo ""
echo "🔍 To see detailed changes for a specific commit:"
echo "   git show <commit-hash>"
echo ""
echo "📝 To incorporate specific improvements:"
echo "   1. Review the changes: git show <commit-hash>"
echo "   2. Manually apply the improvements to our code"
echo "   3. Test the changes"
echo "   4. Commit with: git commit -m 'Sync: <description of improvement>'"
echo ""
echo "⚠️  Remember: Maintain our Laview-specific structure and functionality!"
echo "   - Keep the laview_dl/ package structure"
echo "   - Preserve the --camera argument functionality"
echo "   - Maintain video-only focus"
echo "   - Keep our custom CLI interface"

