#!/usr/bin/env bash
# Unpack portable session files from a sync archive.
# Extracts portable-sync.tar.gz into the project root, overwriting existing files.
#
# Usage: bash scripts/unpack-portable.sh [project-root]
#   project-root defaults to current directory

set -euo pipefail

PROJECT_ROOT="${1:-.}"
ARCHIVE="$PROJECT_ROOT/portable-sync.tar.gz"

if [ ! -f "$ARCHIVE" ]; then
    echo '{"status": "error", "message": "No portable-sync.tar.gz found in project root."}'
    exit 1
fi

# List contents before extracting
FILE_COUNT=$(tar tzf "$ARCHIVE" | wc -l)

# Extract into project root
cd "$PROJECT_ROOT"
tar xzf portable-sync.tar.gz

echo "{\"status\": \"success\", \"files_unpacked\": $FILE_COUNT}"
echo "Unpacked $FILE_COUNT files from portable-sync.tar.gz" >&2

# Optionally remove the archive after unpacking
# rm portable-sync.tar.gz
