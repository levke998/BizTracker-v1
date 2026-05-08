import {
  apiGet,
  apiPatchJson,
  apiPost,
  apiPostForm,
  apiPostJson,
  apiPutJson,
} from "../../../services/api/client";
import type {
  PurchaseInvoice,
  PurchaseInvoiceCreatePayload,
  PurchaseInvoiceFilters,
  PurchaseInvoicePdfDraft,
  PurchaseInvoicePdfReviewUpdatePayload,
  PurchaseInvoicePostingResult,
  Supplier,
  SupplierItemAlias,
  SupplierItemAliasFilters,
  SupplierItemAliasMappingPayload,
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

export function listPurchaseInvoicePdfDrafts(filters: PurchaseInvoiceFilters) {
  return apiGet<PurchaseInvoicePdfDraft[]>(
    "procurement/purchase-invoice-drafts",
    filters,
  );
}

export function uploadPurchaseInvoicePdfDraft(
  businessUnitId: string,
  file: File,
  supplierId?: string,
) {
  const formData = new FormData();
  formData.append("business_unit_id", businessUnitId);
  if (supplierId) {
    formData.append("supplier_id", supplierId);
  }
  formData.append("file", file);
  return apiPostForm<PurchaseInvoicePdfDraft>(
    "procurement/purchase-invoice-drafts/pdf",
    formData,
  );
}

export function updatePurchaseInvoicePdfReview(
  draftId: string,
  payload: PurchaseInvoicePdfReviewUpdatePayload,
) {
  return apiPutJson<PurchaseInvoicePdfReviewUpdatePayload, PurchaseInvoicePdfDraft>(
    `procurement/purchase-invoice-drafts/${draftId}/review`,
    payload,
  );
}

export function createPurchaseInvoiceFromPdfReview(draftId: string) {
  return apiPost<PurchaseInvoice>(
    `procurement/purchase-invoice-drafts/${draftId}/create-purchase-invoice`,
  );
}

export function listSupplierItemAliases(filters: SupplierItemAliasFilters) {
  return apiGet<SupplierItemAlias[]>("procurement/supplier-item-aliases", filters);
}

export function approveSupplierItemAliasMapping(
  aliasId: string,
  payload: SupplierItemAliasMappingPayload,
) {
  return apiPatchJson<SupplierItemAliasMappingPayload, SupplierItemAlias>(
    `procurement/supplier-item-aliases/${aliasId}/mapping`,
    payload,
  );
}
