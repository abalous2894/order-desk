#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

BACKUP_DIR="${BACKUP_DIR:-$ROOT/backups}"
TIMESTAMP="$(date -u +%Y%m%dT%H%M%SZ)"
COMPOSE=(docker compose)
if [[ -f docker-compose.yml ]]; then
  COMPOSE+=( -f docker-compose.yml )
fi
if [[ -f docker-compose.secrets.yml ]] && [[ -f secrets/postgres_password ]]; then
  COMPOSE+=( -f docker-compose.secrets.yml )
fi

POSTGRES_USER="${POSTGRES_USER:-orderdesk}"
POSTGRES_DB="${POSTGRES_DB:-orderdesk}"

mkdir -p "$BACKUP_DIR"
OUTPUT="$BACKUP_DIR/orderdesk_${TIMESTAMP}.sql.gz"

echo "Backing up ${POSTGRES_DB} to ${OUTPUT}"
"${COMPOSE[@]}" exec -T db \
  pg_dump -U "$POSTGRES_USER" -d "$POSTGRES_DB" --clean --if-exists \
  | gzip > "$OUTPUT"

echo "Backup complete: $OUTPUT"
ls -lh "$OUTPUT"
