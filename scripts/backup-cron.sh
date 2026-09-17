#!/bin/sh
set -eu

INTERVAL="${BACKUP_INTERVAL_SECONDS:-86400}"
mkdir -p /backups

while true; do
  TS="$(date -u +%Y%m%dT%H%M%SZ)"
  OUT="/backups/orderdesk_${TS}.sql.gz"
  echo "Starting backup to ${OUT}"
  pg_dump --clean --if-exists | gzip > "$OUT"
  echo "Backup complete: ${OUT}"
  find /backups -name 'orderdesk_*.sql.gz' -mtime +14 -delete
  sleep "$INTERVAL"
done
