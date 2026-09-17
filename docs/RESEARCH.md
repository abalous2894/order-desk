# Research notes (verified against industry + engineering sources)

## Domain: dry cleaning intake

**Verified patterns** (OS For Your Business, ERPLax, ERPNext laundry modules):

- Each **physical garment** is tracked individually with type and status.
- **Customer lookup** at the counter is usually by phone; inline customer creation without leaving the POS flow.
- Typical **status pipeline**: Received → In Process (cleaning/pressing) → Ready for Pickup → Completed/Collected.
- **Invoice/ticket number** ties a drop-off batch together; one customer visit can include many garments.
- **Audit trail** on status changes is common in production systems; for this assessment we enforce valid lifecycle transitions in a dedicated module.

## Data model (assessment mapping)

| Requirement | Design choice |
|-------------|---------------|
| Customer name + phone | `customers` table; composite unique `(name, phone)`; phone-first search |
| One customer → many garments | `garments.customer_id` FK with index |
| One customer → many invoices | `invoices.customer_id` FK |
| Invoice number unique | `invoices.invoice_number` UNIQUE |
| Garment linked to customer | Direct FK + must match parent invoice's customer |
| ~1,000 rows | PostgreSQL with indexes on `phone`, `invoice_number`, `customer_id` |

**Normalization:** 3NF: no repeated customer fields on garments except FK; invoice header separate from garment lines (matches separate Invoice + Garment modules in spec).

## Backend modularity (expert pattern)

Sources: FastAPI layered/DDD examples (router → service → repository), DEV "Baseline" starter:

- **Router:** HTTP only, no business rules
- **Service:** domain rules, orchestration, cross-module calls
- **Repository:** SQL only
- **Schemas:** Pydantic request/response separate from ORM

Four bounded modules: `customers`, `invoices`, `garments`, `status_lifecycle`.

## Operator UX (high-volume entry)

Sources: Microsoft Business Central Quick Entry, UX Stack Exchange power-user forms, VASUYASHII data-entry guide:

- **Phone-first search** with immediate customer select
- **Enter** submits/adds row; **Tab** predictable order
- **Inline validation** (duplicate invoice, invalid status) without clearing the form
- **Sticky customer context** while adding multiple garments/invoices
- **Defaults** (status = Received) to reduce keystrokes
- Desktop-first layout; minimal navigation during intake

## Testing (assessment)

- Integration tests on PostgreSQL (or SQLite for CI speed with same schema)
- Verify FK integrity, unique phone, unique invoice_number
- Verify status lifecycle rejects invalid transitions
- Verify one-to-many: one customer, multiple garments and invoices
