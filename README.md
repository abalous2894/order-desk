# Order Desk

Order intake for dry cleaning shops: look up a customer, open a ticket, add garments, and track status through pickup.

**License:** [MIT](LICENSE)

---

## Run the app (Docker)

**Requirements:** Docker and Docker Compose.

```bash
git clone https://github.com/abalous2894/order-desk.git
cd order-desk
docker compose up --build
```

First run takes a few minutes to build images and start PostgreSQL.

| What | URL |
|------|-----|
| **Operator UI** (use this) | http://localhost:5174 |
| API health check | http://127.0.0.1:8082/health |

Stop the stack: `Ctrl+C`, or `docker compose down` in another terminal.

**Fresh database (wipes all data):**

```bash
docker compose down -v
docker compose up --build
```

---

## Sign in

1. Open http://localhost:5174
2. **Operator ID** — your initials or clerk code (e.g. `Andrew`). Recorded on status changes.
3. **Access token** — for local Docker demo, use: `dev-operator-token`

For anything beyond local demo, copy `.env.example` to `.env`, set a strong `OPERATOR_TOKEN`, and restart Compose.

---

## How to use the system (operator workflow)

The screen has three steps while a customer is active. You stay on one customer until you search for another.

### Step 1 — Find or create a customer

**Returning customer**

1. Type phone or name in **Search existing customer**
2. Click the matching row

**New customer**

1. Enter **Customer name** (letters required; min 2 characters)
2. Enter **Phone** (at least 7 digits; dashes OK)
3. Click **Load / create customer**

Errors appear in red under the form (invalid phone, duplicate name on same phone, etc.).

### Step 2 — Create an invoice (ticket)

1. The **Invoice number** field prefills the next ticket (starts at `0001` on an empty shop)
2. Tickets are **sequential shop-wide**: you cannot create `0006` until `0001`–`0005` exist
3. Click **Create invoice**

Digits only. `5`, `05`, and `0005` are the same ticket.

### Step 3 — Add garments

1. Confirm the **Invoice** field matches the ticket you just created
2. Choose **Garment type** (Suit, Dress, Shirt, etc.)
3. Click **Add garment** (or press Enter)

New garments always start as **Received**. Add as many garments as needed to the same invoice.

### Update status later

Use the **Garments on file** table at the bottom:

- Each row has a status dropdown (except **Completed**, which is locked)
- Only valid next steps are shown: Received → In progress → Ready for pickup → Completed
- You cannot add garments to an invoice once every garment on it is **Completed** (create a new invoice instead)

### Typical visit (quick reference)

```
Sign in → Search phone → Select customer
       → Create invoice (0001, 0002, …)
       → Add garment → Add garment → …
       → (later) change status in table as work progresses
```

---

## Rules the system enforces

| Rule | Why |
|------|-----|
| Phone must have 7–15 digits | Valid contact info |
| Name must include letters | Not numbers-only |
| Invoice numbers are sequential | No skipping ticket 0001 |
| Invoice numbers unique globally | One ticket number per shop |
| Garment needs an invoice first | No orphan items |
| Status moves forward only | Audit-friendly lifecycle |
| Sign-in required to save | Operator auth on all writes |

---

## Configuration (optional)

Local demo works with Compose defaults. For a shared or production-like setup:

```bash
cp .env.example .env
# Edit POSTGRES_PASSWORD, DATABASE_URL, OPERATOR_TOKEN
docker compose up --build
```

See `.env.example` for all variables.

> **Security:** Default passwords and `dev-operator-token` are for local demo only. Change them before any shared deployment.

---

## Development and tests

**Local API + web (without Docker)**

```bash
# Terminal 1 — API
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
export DATABASE_URL=postgresql+psycopg://orderdesk:orderdesk@localhost:5432/orderdesk
export OPERATOR_TOKEN=dev-operator-token
uvicorn order_desk.main:app --reload --port 8000

# Terminal 2 — Web
cd apps/web && npm install && npm run dev
```

Open http://localhost:5174

**Tests and security audits**

```bash
pip install -e ".[dev]"
pytest -q
./scripts/run-audits.sh
```

68 tests; CI runs pytest, bandit, pip-audit, and npm audit on every push/PR.

---

## Architecture (summary)

Four backend domains: `customers`, `invoices`, `garments`, `status_lifecycle`. Each uses router → service → repository. PostgreSQL holds data; Alembic runs migrations on API startup.

- **Customers:** composite unique `(name, phone)`
- **Invoices:** globally unique, sequential ticket numbers
- **Garments:** linked to customer + invoice; type whitelist
- **Status:** forward-only lifecycle with append-only audit log

Research notes: [docs/RESEARCH.md](docs/RESEARCH.md)

---

## SOC 1 Type 1 readiness (design-level)

Built with control **design** in mind (not a formal CPA attestation). Highlights:

| Area | Implementation |
|------|----------------|
| Processing integrity | Validation, DB constraints, sequential invoices |
| Logical access | Operator token + clerk ID on POST/PATCH |
| Audit trail | `garment_status_events` (who changed status, when) |
| Schema control | Alembic migrations |
| Secrets / TLS / backups | `.env`, optional Docker secrets, TLS overlay, backup scripts |
| Monitoring | JSON request logs with `X-Request-Id` |

Details: [System description](docs/SOC1_SYSTEM_DESCRIPTION.md) · [Control matrix](docs/SOC1_CONTROL_MATRIX.md) · [Backup runbook](docs/BACKUP_RESTORE.md)

---

## API reference

| Method | Path | Purpose |
|--------|------|---------|
| POST | `/api/v1/customers/get-or-create` | Load or create customer |
| GET | `/api/v1/customers/search?q=` | Search by phone or name |
| GET | `/api/v1/invoices/next-number` | Next sequential ticket |
| POST | `/api/v1/invoices` | Create invoice |
| POST | `/api/v1/garments` | Add garment |
| PATCH | `/api/v1/garments/{id}/status` | Update status |
| GET | `/api/v1/garments/{id}/status-events` | Status change history |

Mutating calls require `Authorization: Bearer <OPERATOR_TOKEN>` and `X-Operator-Id`. OpenAPI `/docs` is available in local dev; disabled in the production Docker image.

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| API fails on startup (`customers already exists`) | Legacy DB: `docker compose run --rm api alembic stamp head` then `docker compose up -d api`, or wipe with `docker compose down -v` |
| `401` on save | Sign in again; check token matches `OPERATOR_TOKEN` in Compose/.env |
| Cannot create invoice 0006 | Create missing lower numbers first (0001, 0002, …) |
| Web build fails | Run `cd apps/web && npm ci && npm run build` locally to see errors |

---

## Repository

**Public source:** https://github.com/abalous2894/order-desk

Before pushing changes, confirm:

- [x] No `.env`, `secrets/postgres_password`, or `secrets/operator_token` committed
- [x] `pytest -q` and `./scripts/run-audits.sh` pass
- [x] README clone URL matches the repo above
- [x] Default demo credentials documented in **Sign in**
