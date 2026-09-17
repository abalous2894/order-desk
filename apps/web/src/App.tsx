import { FormEvent, useCallback, useEffect, useMemo, useRef, useState } from "react";
import {
  clearOperatorSession,
  getOperatorSession,
  saveOperatorSession,
  type OperatorSession,
} from "./auth";
import {
  createGarment,
  createInvoice,
  formatStatus,
  getNextInvoiceNumber,
  getOrCreateCustomer,
  isInvoiceComplete,
  Garment,
  Invoice,
  listGarments,
  listInvoices,
  listStatusTransitionRules,
  normalizeInvoiceNumber,
  searchCustomers,
  updateGarmentStatus,
  validateCustomerName,
  validatePhone,
  Customer,
} from "./api";

const GARMENT_TYPES = ["Suit", "Dress", "Shirt", "Pants", "Coat", "Skirt", "Other"];
const INTAKE_STATUS = "received";
const STATUS_ORDER = ["received", "in_progress", "ready_for_pickup", "completed"];

export default function App() {
  const [operatorSession, setOperatorSession] = useState<OperatorSession | null>(() =>
    getOperatorSession(),
  );
  const [operatorId, setOperatorId] = useState("");
  const [operatorToken, setOperatorToken] = useState("");
  const [loginError, setLoginError] = useState<string | null>(null);

  const [search, setSearch] = useState("");
  const [results, setResults] = useState<Customer[]>([]);
  const [active, setActive] = useState<Customer | null>(null);
  const [invoices, setInvoices] = useState<Invoice[]>([]);
  const [garments, setGarments] = useState<Garment[]>([]);
  const [statusRules, setStatusRules] = useState<Record<string, string[]>>({});
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [customerError, setCustomerError] = useState<string | null>(null);
  const [invoiceError, setInvoiceError] = useState<string | null>(null);
  const [garmentError, setGarmentError] = useState<string | null>(null);

  const [name, setName] = useState("");
  const [phone, setPhone] = useState("");
  const [invoiceNumber, setInvoiceNumber] = useState("");
  const [garmentType, setGarmentType] = useState("Suit");

  const phoneRef = useRef<HTMLInputElement>(null);
  const garmentRef = useRef<HTMLSelectElement>(null);

  useEffect(() => {
    if (!operatorSession) return;
    void listStatusTransitionRules().then(setStatusRules).catch(() => undefined);
    phoneRef.current?.focus();
  }, [operatorSession]);

  function handleSignIn(e: FormEvent) {
    e.preventDefault();
    setLoginError(null);
    const id = operatorId.trim();
    const token = operatorToken.trim();
    if (id.length < 2) {
      setLoginError("Operator ID must be at least 2 characters");
      return;
    }
    if (!token) {
      setLoginError("Access token is required");
      return;
    }
    const session = { operatorId: id, operatorToken: token };
    saveOperatorSession(session);
    setOperatorSession(session);
    setOperatorToken("");
  }

  function handleSignOut() {
    clearOperatorSession();
    setOperatorSession(null);
    setActive(null);
    setResults([]);
    setMessage(null);
    setError(null);
  }

  const statusOptions = useCallback(
    (current: string): string[] => {
      const next = statusRules[current] ?? [];
      const options = [current, ...next.filter((s) => s !== current)];
      return options.sort(
        (a, b) => STATUS_ORDER.indexOf(a) - STATUS_ORDER.indexOf(b),
      );
    },
    [statusRules],
  );

  const refreshLists = useCallback(async (customerId: number) => {
    const [inv, gar] = await Promise.all([
      listInvoices(customerId),
      listGarments(customerId),
    ]);
    setInvoices(inv);
    setGarments(gar);
    return { inv, gar };
  }, []);

  const loadCustomer = useCallback(
    async (
      customer: Customer,
      options: { focusGarment?: boolean; preserveInvoice?: boolean } = {},
    ) => {
      const { focusGarment = false, preserveInvoice = false } = options;
      setActive(customer);
      setName(customer.name);
      setPhone(customer.phone);
      setMessage(null);
      setError(null);
      setCustomerError(null);
      setInvoiceError(null);
      setGarmentError(null);
      await refreshLists(customer.id);
      if (!preserveInvoice) {
        const next = await getNextInvoiceNumber();
        setInvoiceNumber(next.invoice_number);
      }
      if (focusGarment) {
        garmentRef.current?.focus();
      }
    },
    [refreshLists],
  );

  useEffect(() => {
    if (search.trim().length < 2) {
      setResults([]);
      return;
    }
    const handle = window.setTimeout(() => {
      void searchCustomers(search)
        .then(setResults)
        .catch((err: Error) => setError(err.message));
    }, 200);
    return () => window.clearTimeout(handle);
  }, [search]);

  async function handleSelectCustomer(customer: Customer) {
    await loadCustomer(customer, { focusGarment: true });
    setSearch("");
    setResults([]);
  }

  async function handleEnsureCustomer(e?: FormEvent) {
    e?.preventDefault();
    setCustomerError(null);
    setError(null);
    let normalizedName: string;
    let normalizedPhone: string;
    try {
      normalizedName = validateCustomerName(name);
    } catch (err) {
      setCustomerError(err instanceof Error ? err.message : "Invalid customer name");
      return;
    }
    try {
      normalizedPhone = validatePhone(phone);
    } catch (err) {
      setCustomerError(err instanceof Error ? err.message : "Invalid phone number");
      return;
    }
    try {
      const customer = await getOrCreateCustomer(normalizedName, normalizedPhone);
      await loadCustomer(customer, { focusGarment: true });
      setMessage("Customer ready. Add invoice and garments below.");
    } catch (err) {
      setCustomerError(err instanceof Error ? err.message : "Failed to save customer");
    }
  }

  async function handleCreateInvoice(e: FormEvent) {
    e.preventDefault();
    if (!active) return;
    setInvoiceError(null);
    setError(null);
    let normalized: string;
    try {
      normalized = normalizeInvoiceNumber(invoiceNumber);
    } catch (err) {
      setInvoiceError(err instanceof Error ? err.message : "Invalid invoice number");
      return;
    }
    if (invoices.some((inv) => inv.invoice_number === normalized)) {
      setInvoiceError("Invoice number already exists");
      return;
    }
    try {
      const created = await createInvoice(active.id, normalized);
      setInvoices((prev) => [...prev, created]);
      setInvoiceNumber(created.invoice_number);
      setMessage(`Invoice ${created.invoice_number} created`);
      garmentRef.current?.focus();
    } catch (err) {
      setInvoiceError(err instanceof Error ? err.message : "Failed to create invoice");
    }
  }

  const selectedInvoiceComplete = useMemo(
    () => isInvoiceComplete(invoiceNumber, garments),
    [invoiceNumber, garments],
  );

  async function handleAddGarment(e: FormEvent) {
    e.preventDefault();
    if (!active) return;
    setGarmentError(null);
    setError(null);
    let normalizedInvoice: string;
    try {
      normalizedInvoice = normalizeInvoiceNumber(invoiceNumber);
    } catch (err) {
      setGarmentError(err instanceof Error ? err.message : "Invalid invoice number");
      return;
    }
    if (selectedInvoiceComplete) {
      setGarmentError("Invoice is complete. Create a new invoice for additional garments.");
      return;
    }
    try {
      const created = await createGarment(active.id, normalizedInvoice, garmentType, INTAKE_STATUS);
      setGarments((prev) => [...prev, created]);
      setMessage(`Added ${garmentType} to ${invoiceNumber.toUpperCase()} (received)`);
      garmentRef.current?.focus();
    } catch (err) {
      setGarmentError(err instanceof Error ? err.message : "Failed to add garment");
    }
  }

  async function handleStatusChange(garment: Garment, newStatus: string) {
    if (!active || newStatus === garment.status) return;
    setError(null);
    const previousStatus = garment.status;
    setGarments((prev) =>
      prev.map((g) => (g.id === garment.id ? { ...g, status: newStatus } : g)),
    );
    try {
      const updated = await updateGarmentStatus(garment.id, newStatus);
      setGarments((prev) => prev.map((g) => (g.id === updated.id ? updated : g)));
      setMessage(`Updated ${garment.garment_type} to ${formatStatus(newStatus)}`);
    } catch (err) {
      setGarments((prev) =>
        prev.map((g) => (g.id === garment.id ? { ...g, status: previousStatus } : g)),
      );
      setError(err instanceof Error ? err.message : "Failed to update status");
    }
  }

  if (!operatorSession) {
    return (
      <div className="shell">
        <header>
          <h1>Order Desk</h1>
          <p className="meta">Operator sign-in is required before intake or status changes</p>
        </header>
        <section className="panel login-panel">
          <h2>Operator sign-in</h2>
          <form className="form-stack" onSubmit={handleSignIn}>
            <div className="field-block">
              <label htmlFor="operator-id">Operator ID</label>
              <input
                id="operator-id"
                placeholder="Your initials or clerk code"
                value={operatorId}
                onChange={(e) => setOperatorId(e.target.value)}
                autoComplete="username"
                required
              />
            </div>
            <div className="field-block">
              <label htmlFor="operator-token">Access token</label>
              <input
                id="operator-token"
                type="password"
                placeholder="Shop access token"
                value={operatorToken}
                onChange={(e) => setOperatorToken(e.target.value)}
                autoComplete="current-password"
                required
              />
            </div>
            <button type="submit">Sign in</button>
          </form>
          {loginError ? (
            <p className="field-error" role="alert">
              {loginError}
            </p>
          ) : null}
          {import.meta.env.DEV ? (
            <p className="meta form-hint">
              Default local token: <code>dev-operator-token</code> (set <code>OPERATOR_TOKEN</code> in{" "}
              <code>.env</code> for production)
            </p>
          ) : null}
        </section>
      </div>
    );
  }

  return (
    <div className="shell">
      <header>
        <div className="header-row">
          <div>
            <h1>Order Desk</h1>
            <p className="meta">High-volume intake: search by phone, keep customer context, add garments fast</p>
          </div>
          <div className="operator-badge">
            <span>Signed in as {operatorSession.operatorId}</span>
            <button type="button" className="link-button" onClick={handleSignOut}>
              Sign out
            </button>
          </div>
        </div>
      </header>

      <section className="panel">
        <h2>1. Find or create customer</h2>
        <div className="field-block">
          <label htmlFor="customer-search">Search existing customer</label>
          <input
            id="customer-search"
            ref={phoneRef}
            placeholder="Search phone or name"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            aria-label="Search customers"
          />
        </div>
        {results.length > 0 ? (
          <ul className="results">
            {results.map((c) => (
              <li key={c.id}>
                <button type="button" onClick={() => void handleSelectCustomer(c)}>
                  {c.name} · {c.phone}
                </button>
              </li>
            ))}
          </ul>
        ) : null}
        <div className="field-divider" />
        <form className="form-stack" onSubmit={(e) => void handleEnsureCustomer(e)}>
          <div className="form-row-2">
            <div className="field-block">
              <label htmlFor="customer-name">Customer name</label>
              <input
                id="customer-name"
                placeholder="Customer name"
                value={name}
                onChange={(e) => setName(e.target.value)}
                required
              />
            </div>
            <div className="field-block">
              <label htmlFor="customer-phone">Phone</label>
              <input
                id="customer-phone"
                placeholder="Phone (at least 7 digits)"
                inputMode="tel"
                value={phone}
                onChange={(e) => {
                  setPhone(e.target.value);
                  setCustomerError(null);
                }}
                aria-invalid={customerError ? true : undefined}
                aria-describedby={customerError ? "customer-error" : undefined}
                required
              />
            </div>
          </div>
          <button type="submit">Load / create customer</button>
        </form>
        {customerError ? (
          <p id="customer-error" className="field-error" role="alert">
            {customerError}
          </p>
        ) : null}
      </section>

      {active ? (
        <>
          <section className="panel highlight">
            <h2>
              Active: {active.name} <span className="meta">({active.phone})</span>
            </h2>
            <p className="meta">
              {invoices.length} invoice(s) · {garments.length} garment(s)
            </p>
          </section>

          <div className="grid-two">
            <section className="panel">
              <h2>2. Invoice</h2>
              <form className="invoice-form" onSubmit={(e) => void handleCreateInvoice(e)}>
                <div className="field-block">
                  <label htmlFor="invoice-number">Invoice number (digits only)</label>
                  <p className="meta form-hint invoice-seq-hint">
                    Tickets are sequential shop-wide. Create 0001 before 0002, and so on.
                  </p>
                  <div className="form-row-invoice">
                    <input
                      id="invoice-number"
                      placeholder="e.g. 0005"
                      inputMode="numeric"
                      pattern="[0-9]*"
                      value={invoiceNumber}
                      onChange={(e) => {
                        setInvoiceNumber(e.target.value);
                        setInvoiceError(null);
                      }}
                      aria-invalid={invoiceError ? true : undefined}
                      aria-describedby={invoiceError ? "invoice-error" : undefined}
                      required
                    />
                    <button type="submit">Create invoice</button>
                  </div>
                </div>
              </form>
              {invoiceError ? (
                <p id="invoice-error" className="field-error" role="alert">
                  {invoiceError}
                </p>
              ) : null}
              <ul className="compact-list">
                {invoices.map((inv) => {
                  const complete = isInvoiceComplete(inv.invoice_number, garments);
                  return (
                    <li key={inv.id}>
                      <button
                        type="button"
                        className={complete ? "invoice-chip complete" : "invoice-chip"}
                        onClick={() => {
                          setInvoiceNumber(inv.invoice_number);
                          setGarmentError(
                            complete
                              ? "Invoice is complete. Create a new invoice for additional garments."
                              : null,
                          );
                        }}
                      >
                        {inv.invoice_number}
                        {complete ? " (complete)" : ""}
                      </button>
                    </li>
                  );
                })}
              </ul>
            </section>

            <section className="panel garment-panel">
              <h2>3. Add garment (Enter to submit)</h2>
              <p className="meta form-hint">New items are recorded as Received. Change status in the table below.</p>
              <form className="garment-form" onSubmit={(e) => void handleAddGarment(e)}>
                <div className="field-block">
                  <label htmlFor="garment-invoice">Invoice</label>
                  <input id="garment-invoice" value={invoiceNumber} readOnly />
                </div>
                <div className="field-block">
                  <label htmlFor="garment-type">Garment type</label>
                  <select
                    id="garment-type"
                    ref={garmentRef}
                    value={garmentType}
                    onChange={(e) => setGarmentType(e.target.value)}
                  >
                    {GARMENT_TYPES.map((t) => (
                      <option key={t} value={t}>
                        {t}
                      </option>
                    ))}
                  </select>
                </div>
                <button type="submit" disabled={selectedInvoiceComplete}>
                  Add garment
                </button>
              </form>
              {garmentError ? (
                <p id="garment-error" className="field-error" role="alert">
                  {garmentError}
                </p>
              ) : null}
            </section>
          </div>

          <section className="panel">
            <h2>Garments on file</h2>
            <p className="meta form-hint">Update status on an existing row. Only valid next steps are shown.</p>
            <table>
              <thead>
                <tr>
                  <th>Invoice</th>
                  <th>Type</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody>
                {garments.map((g) => (
                  <tr key={g.id}>
                    <td>{g.invoice_number}</td>
                    <td>{g.garment_type}</td>
                    <td className="status-cell">
                      {g.status === "completed" ? (
                        <span className={`pill status-${g.status}`}>{formatStatus(g.status)}</span>
                      ) : (
                        <select
                          className={`status-select status-${g.status}`}
                          value={g.status}
                          aria-label={`Status for ${g.garment_type}`}
                          onChange={(e) => void handleStatusChange(g, e.target.value)}
                        >
                          {statusOptions(g.status).map((s) => (
                            <option key={s} value={s}>
                              {formatStatus(s)}
                            </option>
                          ))}
                        </select>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </section>
        </>
      ) : null}

      {message ? <p className="toast ok">{message}</p> : null}
      {error ? <p className="toast err">{error}</p> : null}
    </div>
  );
}
