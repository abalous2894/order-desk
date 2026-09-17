import { getOperatorSession, operatorAuthHeaders } from "./auth";

export type Customer = { id: number; name: string; phone: string };
export type CustomerProfile = Customer & { invoice_count: number; garment_count: number };
export type Invoice = { id: number; invoice_number: string; customer_id: number; created_at: string };
export type Garment = {
  id: number;
  customer_id: number;
  invoice_id: number;
  invoice_number: string;
  garment_type: string;
  status: string;
};

function parseErrorDetail(body: unknown, status: number): string {
  if (body && typeof body === "object" && "detail" in body) {
    const detail = (body as { detail: unknown }).detail;
    if (typeof detail === "string") return detail;
    if (Array.isArray(detail)) {
      return detail
        .map((item) =>
          typeof item === "object" && item && "msg" in item
            ? String((item as { msg: string }).msg)
            : String(item),
        )
        .join(", ");
    }
  }
  return `Request failed (${status})`;
}

function newRequestId(): string {
  if (typeof crypto !== "undefined" && "randomUUID" in crypto) {
    return crypto.randomUUID();
  }
  return `req-${Date.now()}`;
}

function buildHeaders(init?: RequestInit): Record<string, string> {
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(init?.headers as Record<string, string> | undefined),
  };
  const method = (init?.method ?? "GET").toUpperCase();
  if (!headers["X-Request-Id"]) {
    headers["X-Request-Id"] = newRequestId();
  }
  if (method === "POST" || method === "PATCH") {
    const session = getOperatorSession();
    if (!session) {
      throw new Error("Operator sign-in is required before saving changes");
    }
    Object.assign(headers, operatorAuthHeaders(session));
  }
  return headers;
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(path, {
    ...init,
    headers: buildHeaders(init),
  });  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(parseErrorDetail(body, res.status));
  }
  return res.json() as Promise<T>;
}

const INVOICE_NUMBER_WIDTH = 4;

const MIN_PHONE_DIGITS = 7;
const MAX_PHONE_DIGITS = 15;
const MIN_NAME_LENGTH = 2;
const MAX_NAME_LENGTH = 200;

export function normalizePhoneDigits(value: string): string {
  return [...value.trim()].filter((ch) => /\d/.test(ch) || ch === "+").join("");
}

export function validatePhone(value: string): string {
  const normalized = normalizePhoneDigits(value);
  const digitCount = [...normalized].filter((ch) => /\d/.test(ch)).length;
  if (digitCount < MIN_PHONE_DIGITS) {
    throw new Error(
      `Phone must contain at least ${MIN_PHONE_DIGITS} digits (for example 5550100)`,
    );
  }
  if (digitCount > MAX_PHONE_DIGITS) {
    throw new Error(`Phone must contain at most ${MAX_PHONE_DIGITS} digits`);
  }
  return normalized;
}

export function validateCustomerName(value: string): string {
  const collapsed = value.trim().replace(/\s+/g, " ");
  if (collapsed.length < MIN_NAME_LENGTH) {
    throw new Error(`Customer name must be at least ${MIN_NAME_LENGTH} characters`);
  }
  if (collapsed.length > MAX_NAME_LENGTH) {
    throw new Error(`Customer name must be at most ${MAX_NAME_LENGTH} characters`);
  }
  if (/^\d+$/.test(collapsed)) {
    throw new Error("Customer name cannot be numbers only");
  }
  if (!/[A-Za-z]/.test(collapsed)) {
    throw new Error("Customer name must contain at least one letter");
  }
  return collapsed;
}

export function tryNormalizeInvoiceNumber(value: string): string | null {
  const cleaned = value.trim().toUpperCase();
  if (!/^\d+$/.test(cleaned)) {
    return null;
  }
  const canonical = String(parseInt(cleaned, 10));
  return canonical.length <= INVOICE_NUMBER_WIDTH
    ? canonical.padStart(INVOICE_NUMBER_WIDTH, "0")
    : canonical;
}

export function normalizeInvoiceNumber(value: string): string {
  const normalized = tryNormalizeInvoiceNumber(value);
  if (!normalized) {
    throw new Error("Invoice number must contain digits only (for example 0005)");
  }
  return normalized;
}

export function searchCustomers(q: string) {
  return request<Customer[]>(`/api/v1/customers/search?q=${encodeURIComponent(q)}`);
}

export function getOrCreateCustomer(name: string, phone: string) {
  return request<Customer>("/api/v1/customers/get-or-create", {
    method: "POST",
    body: JSON.stringify({ name, phone }),
  });
}

export function getCustomerProfile(id: number) {
  return request<CustomerProfile>(`/api/v1/customers/${id}`);
}

export function createInvoice(customerId: number, invoiceNumber: string) {
  return request<Invoice>("/api/v1/invoices", {
    method: "POST",
    body: JSON.stringify({ customer_id: customerId, invoice_number: invoiceNumber }),
  });
}

export function listInvoices(customerId: number) {
  return request<Invoice[]>(`/api/v1/invoices/by-customer/${customerId}`);
}

export function getNextInvoiceNumber() {
  return request<{ invoice_number: string }>("/api/v1/invoices/next-number");
}

export function createGarment(
  customerId: number,
  invoiceNumber: string,
  garmentType: string,
  status: string,
) {
  return request<Garment>("/api/v1/garments", {
    method: "POST",
    body: JSON.stringify({
      customer_id: customerId,
      invoice_number: invoiceNumber,
      garment_type: garmentType,
      status,
    }),
  });
}

export function listGarments(customerId: number) {
  return request<Garment[]>(`/api/v1/garments/by-customer/${customerId}`);
}

export function listStatuses() {
  return request<string[]>("/api/v1/garments/statuses");
}

export function listStatusTransitionRules() {
  return request<Record<string, string[]>>("/api/v1/status-lifecycle/rules");
}

export function updateGarmentStatus(garmentId: number, status: string) {
  return request<Garment>(`/api/v1/garments/${garmentId}/status`, {
    method: "PATCH",
    body: JSON.stringify({ status }),
  });
}

export type GarmentStatusEvent = {
  id: number;
  garment_id: number;
  from_status: string | null;
  to_status: string;
  actor: string;
  created_at: string;
};

export function listGarmentStatusEvents(garmentId: number) {
  return request<GarmentStatusEvent[]>(`/api/v1/garments/${garmentId}/status-events`);
}

export function formatStatus(status: string): string {
  return status.replaceAll("_", " ");
}

export function isInvoiceComplete(invoiceNumber: string, garments: Garment[]): boolean {
  const normalized = tryNormalizeInvoiceNumber(invoiceNumber);
  const onInvoice = garments.filter((g) =>
    normalized ? g.invoice_number === normalized : g.invoice_number === invoiceNumber.trim().toUpperCase(),
  );
  return onInvoice.length > 0 && onInvoice.every((g) => g.status === "completed");
}
