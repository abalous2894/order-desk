#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

echo "== pytest =="
pytest -q

echo "== bandit =="
python -m bandit -r src/order_desk -ll -q

echo "== pip-audit =="
python -m pip_audit

echo "== npm audit (web) =="
cd apps/web
npm audit --audit-level=high
cd "$ROOT"

echo "All audits passed."
