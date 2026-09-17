# Order Desk — System Description (SOC 1 Type 1)

**Service organization:** Order Desk (internal dry-cleaning intake application)  
**Version:** 0.1.0  
**Last updated:** September 2026  
**Intended use:** Capture customer profiles, invoice/ticket numbers, garment line items, and garment status for dry-cleaning counter operations.

---

## 1. Services provided

Order Desk provides a web-based operator console and JSON API for:

- Customer lookup and creation (phone-first search)
- Invoice (ticket) creation with globally unique numbers
- Garment intake linked to customer and invoice
- Forward-only garment status lifecycle with append-only audit events

The system is **not** a general ledger. It supports **processing integrity** of order data that may inform operational or revenue reporting.

---

## 2. System components

| Component | Technology | Role |
|-----------|------------|------|
| Web UI | React + Vite + nginx | Operator data entry |
| API | FastAPI (Python 3.12) | Business rules, validation, auth |
| Database | PostgreSQL 16 | Persistent storage, constraints |
| Migrations | Alembic | Versioned schema (`alembic_version`) |
| Reverse proxy | nginx | Static UI, API proxy, optional TLS |

**Deployment:** Docker Compose (default). Database volume `orderdesk_pgdata` is not exposed on the host network.

---

## 3. Data entities

| Entity | Key controls |
|--------|----------------|
| `customers` | Composite unique `(name, phone)`; validated name and phone |
| `invoices` | Globally unique `invoice_number`; canonical numeric normalization |
| `garments` | FK to customer + invoice; garment type whitelist |
| `garment_status_events` | Append-only; actor + timestamp on status changes |
| `alembic_version` | Schema change control |

---

## 4. Boundaries and interfaces

**Inbound:** Operator browser (HTTP/HTTPS) → nginx → API  
**Outbound:** None to external financial systems in this assessment build  
**Authentication:** Shared bearer token + per-request operator ID header on mutating calls

---

## 5. Complementary user entity controls (CUECs)

User entities (shop operators) should:

1. Protect `OPERATOR_TOKEN` and rotate on staff turnover
2. Issue unique operator IDs per clerk
3. Restrict network access to the Order Desk host
4. Review backup success and perform periodic restore tests (see [BACKUP_RESTORE.md](BACKUP_RESTORE.md))
5. Use TLS in production (`docker-compose.tls.yml` or upstream load balancer)

---

## 6. Infrastructure controls implemented

| Area | Implementation |
|------|----------------|
| Logical access | Operator token + `X-Operator-Id` on POST/PATCH |
| Audit trail | `garment_status_events` table |
| Schema control | Alembic migrations at API startup |
| Secrets | `.env` / Docker secret files |
| Transport | Optional TLS via nginx overlay |
| Backups | Manual script + optional daily sidecar |
| Monitoring | Structured JSON request logs with `request_id` |
| CI assurance | pytest, bandit, pip-audit, npm audit |

---

## 7. Change management

- Application source in git
- CI runs on push/PR (`.github/workflows/test.yml`)
- Schema changes require new Alembic revision
- Production deploy: rebuild API image, `alembic upgrade head` on startup

---

## 8. Exclusions

Not in scope for this system description:

- Payroll, GL posting, or tax reporting
- Multi-tenant SaaS isolation
- Formal SOC attestation or CPA sign-off
