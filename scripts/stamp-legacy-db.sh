#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

echo "Stamping existing schema as Alembic head (no DDL changes)."
docker compose run --rm api python -c "from order_desk.db.migrate import upgrade_to_head; upgrade_to_head()"
echo "Done. Restart API: docker compose up -d api"
