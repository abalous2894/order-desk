#!/usr/bin/env bash
set -euo pipefail
cd /app
python -c "from order_desk.db.migrate import upgrade_to_head; upgrade_to_head()"
exec uvicorn order_desk.main:app --host 0.0.0.0 --port 8000
