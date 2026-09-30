#!/usr/bin/env bash
set -euo pipefail

SRC="${1:-./data/app.db}"
DEST="${2:-./backups/app-$(date +%Y%m%d-%H%M%S).db}"

mkdir -p "$(dirname "$DEST")"
sqlite3 "$SRC" ".backup '$DEST'"
echo "Backup written to $DEST"
