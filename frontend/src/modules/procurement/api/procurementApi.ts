import { apiGet, apiPost, apiPostJson } from "../../../services/api/client";
import type {
  PurchaseInvoice,
  PurchaseInvoiceCreatePayload,
  PurchaseInvoiceFilters,
  PurchaseInvoicePostingResult,
  Supplier,
  SupplierCreatePayload,
  SupplierFilters,
} from "../types/procurement";

export function listSuppliers(filters: SupplierFilters) {
  return apiGet<Supplier[]>("procurement/suppliers", filters);
}

export function createSupplier(payload: SupplierCreatePayload) {
  return apiPostJson<SupplierCreatePayload, Supplier>("procurement/suppliers", payload);
}

export function listPurchaseInvoices(filters: PurchaseInvoiceFilters) {
  return apiGet<PurchaseInvoice[]>("procurement/purchase-invoices", filters);
}

export function createPurchaseInvoice(payload: PurchaseInvoiceCreatePayload) {
  return apiPostJson<PurchaseInvoiceCreatePayload, PurchaseInvoice>(
    "procurement/purchase-invoices",
    payload
  );
}

export function postPurchaseInvoice(invoiceId: string) {
  return apiPost<PurchaseInvoicePostingResult>(
    `procurement/purchase-invoices/${invoiceId}/post`
  );
}
