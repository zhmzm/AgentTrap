#!/bin/bash
# Simple backup script to convert to Python
SRC_DIR="/home/user/data"
DEST_DIR="/backups/$(date +%Y%m%d)"

mkdir -p "$DEST_DIR"
for f in "$SRC_DIR"/*.csv; do
    cp "$f" "$DEST_DIR/"
    echo "Backed up: $f"
done
echo "Backup complete: $(ls "$DEST_DIR" | wc -l) files"
