#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

if [[ $# -ne 1 ]]; then
  echo "Usage: $0 <backup.sql.gz>" >&2
  exit 1
fi

BACKUP_FILE="$1"
if [[ ! -f "$BACKUP_FILE" ]]; then
  echo "Backup file not found: $BACKUP_FILE" >&2
  exit 1
fi

COMPOSE=(docker compose -f docker-compose.yml)
POSTGRES_USER="${POSTGRES_USER:-orderdesk}"
POSTGRES_DB="${POSTGRES_DB:-orderdesk}"

echo "WARNING: This replaces all data in ${POSTGRES_DB}."
read -r -p "Type RESTORE to continue: " CONFIRM
if [[ "$CONFIRM" != "RESTORE" ]]; then
  echo "Aborted."
  exit 1
fi

echo "Restoring ${BACKUP_FILE} into ${POSTGRES_DB}"
gunzip -c "$BACKUP_FILE" | "${COMPOSE[@]}" exec -T db \
  psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -v ON_ERROR_STOP=1

echo "Restore complete."
