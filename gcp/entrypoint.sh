#!/bin/sh
set -e

BUCKET="${LITESTREAM_BUCKET}"
DB_PATH="/pb/pb_data/data.db"

# Restore database from GCS if replica exists
if [ -n "$BUCKET" ]; then
    echo "Restoring database from GCS..."
    litestream restore -if-replica-exists -o "$DB_PATH" "$BUCKET"
fi

# Start nginx in background
echo "Starting nginx..."
nginx

# Start Pocketbase with Litestream replication
echo "Starting Pocketbase with Litestream..."
exec litestream replicate \
    -exec "/usr/local/bin/pocketbase serve --http=0.0.0.0:8090" \
    "$BUCKET"