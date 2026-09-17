# Backup and restore runbook

## Scope

PostgreSQL database for Order Desk (`customers`, `invoices`, `garments`, `garment_status_events`, `alembic_version`).

## RTO / RPO (targets)

| Metric | Target |
|--------|--------|
| RPO (max data loss) | 24 hours with daily backup sidecar; lower if `backup-db.sh` is run more often |
| RTO (time to restore) | 15 minutes for single-shop Docker deployment |

## One-off backup (manual)

With the stack running:

```bash
./scripts/backup-db.sh
```

Output: `backups/orderdesk_<UTC-timestamp>.sql.gz`

Environment overrides:

- `BACKUP_DIR` — destination directory (default `./backups`)
- `POSTGRES_USER`, `POSTGRES_DB` — match `.env` / Compose

## Scheduled backups (Docker sidecar)

```bash
docker compose -f docker-compose.yml -f docker-compose.backup.yml up -d backup
```

The sidecar runs `pg_dump` on an interval (default 86400 seconds / daily) and deletes backups older than 14 days.

## Restore procedure

1. Stop API traffic (scale web/api to zero or take app offline).
2. Confirm backup file path: `ls -lh backups/`
3. Run restore:

```bash
./scripts/restore-db.sh backups/orderdesk_YYYYMMDDTHHMMSSZ.sql.gz
```

4. Type `RESTORE` when prompted.
5. Restart API and verify:

```bash
curl -s http://localhost:8082/health
curl -s -H "Authorization: Bearer $OPERATOR_TOKEN" -H "X-Operator-Id: OPS" \
  "http://localhost:8082/api/v1/customers/search?q=test"
```

## Restore test (recommended quarterly)

1. Copy production backup to a staging machine.
2. Run restore against a fresh Compose stack (`docker compose down -v` first on staging only).
3. Spot-check customer count, latest invoice, and a garment status audit trail.

## Failure handling

| Symptom | Action |
|---------|--------|
| `backup-db.sh` fails with "container not running" | Start stack: `docker compose up -d db` |
| Restore fails mid-script | Re-run on empty DB after `docker compose down -v` (staging only) |
| Corrupt gzip file | Use previous backup; verify with `gzip -t backup.sql.gz` |
