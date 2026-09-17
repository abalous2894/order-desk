# Order Desk — Control Matrix (SOC 1 Type 1)

**Assessment type:** Design suitability at a point in time  
**Legend:** ✅ Designed · ⚠️ Partial · ❌ Not designed

---

## CC1 — Control environment

| ID | Control objective | Control activity | Status | Evidence |
|----|-------------------|------------------|--------|----------|
| CC1.1 | System documented | Architecture README + this system description | ✅ | `README.md`, `docs/SOC1_SYSTEM_DESCRIPTION.md` |
| CC1.2 | Change control | Git + CI on PR/push | ✅ | `.github/workflows/test.yml` |
| CC1.3 | Segregation of duties | Single operator role; no admin/clerk split | ⚠️ | By design for assessment scope |

---

## CC2 — Risk assessment

| ID | Control objective | Control activity | Status | Evidence |
|----|-------------------|------------------|--------|----------|
| CC2.1 | Application input risks | Validation + security tests | ✅ | `tests/test_edge_cases.py`, `tests/test_security.py` |
| CC2.2 | Dependency risks | bandit, pip-audit, npm audit in CI | ✅ | `scripts/run-audits.sh`, CI workflow |

---

## PI — Processing integrity (order data)

| ID | Control objective | Control activity | Status | Evidence |
|----|-------------------|------------------|--------|----------|
| PI-01 | Valid customer master | Name/phone validation | ✅ | `util/text.py`, edge tests |
| PI-02 | Unique invoices | DB unique + normalization + 409 | ✅ | `invoices/service.py`, integration tests |
| PI-02b | Sequential tickets | Cannot create 0006 before 0001–0005 | ✅ | `invoices/repository.py`, sequence tests |
| PI-03 | Garment-invoice linkage | FK + service checks | ✅ | `garments/service.py` |
| PI-04 | Valid garment types | Backend whitelist | ✅ | `garments/constants.py` |
| PI-05 | Status lifecycle | Forward-only transitions | ✅ | `status_lifecycle/service.py` |
| PI-06 | No post-completion intake | Block garments on completed invoice | ✅ | Integration test |
| PI-07 | SQL injection mitigation | Parameterized queries + LIKE escape | ✅ | `test_security.py` |

---

## AC — Logical access

| ID | Control objective | Control activity | Status | Evidence |
|----|-------------------|------------------|--------|----------|
| AC-01 | Authenticate operators | Bearer token on POST/PATCH | ✅ | `auth/operator.py`, `tests/test_auth.py` |
| AC-02 | Identify actor | `X-Operator-Id` required | ✅ | Auth dependency + audit log |
| AC-03 | TLS in transit | nginx TLS overlay | ✅ | `docker-compose.tls.yml`, `nginx.tls.conf` |
| AC-04 | CORS restriction | Allowlist origins | ✅ | `main.py` |

---

## AT — Audit trail and logging

| ID | Control objective | Control activity | Status | Evidence |
|----|-------------------|------------------|--------|----------|
| AT-01 | Status change history | Append-only `garment_status_events` | ✅ | `audit_models.py`, `tests/test_audit_log.py` |
| AT-02 | Request traceability | JSON logs: request_id, operator, outcome | ✅ | `middleware/request_logging.py` |
| AT-03 | Correlation ID | `X-Request-Id` response header | ✅ | Request logging middleware |

---

## IT — IT general controls

| ID | Control objective | Control activity | Status | Evidence |
|----|-------------------|------------------|--------|----------|
| IT-01 | Secrets management | `.env` + Docker secrets overlay | ✅ | `.env.example`, `docker-compose.secrets.yml` |
| IT-02 | Schema versioning | Alembic + `alembic_version` | ✅ | `alembic/`, `tests/test_migrations.py` |
| IT-03 | Backup | Manual script + optional sidecar | ✅ | `scripts/backup-db.sh`, `docs/BACKUP_RESTORE.md` |
| IT-04 | Restore tested | Documented restore runbook | ✅ | `scripts/restore-db.sh`, BACKUP_RESTORE |
| IT-05 | Health check | `/health` endpoint | ✅ | `main.py` |

---

## Summary readiness (Type 1 design)

| Domain | Ready |
|--------|-------|
| Processing integrity | Yes |
| Logical access | Yes (single shared token model) |
| Audit trail | Yes |
| ITGC (backup, TLS, migrations) | Yes (operational effectiveness = Type 2) |

**Remaining Type 2 items:** periodic access reviews, backup restore drills with evidence, 6–12 months of operating effectiveness testing.
