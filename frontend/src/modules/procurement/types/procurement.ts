export type Supplier = {
  id: string;
  business_unit_id: string;
  name: string;
  tax_id: string | null;
  contact_name: string | null;
  email: string | null;
  phone: string | null;
  notes: string | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
};

export type SupplierFilters = {
  business_unit_id?: string;
  is_active?: boolean;
  limit?: number;
};

export type SupplierCreatePayload = {
  business_unit_id: string;
  name: string;
  tax_id?: string;
  contact_name?: string;
  email?: string;
  phone?: string;
  notes?: string;
  is_active: boolean;
};

export type PurchaseInvoiceLine = {
  id: string;
  inventory_item_id: string | null;
  description: string;
  quantity: string;
  uom_id: string;
  unit_net_amount: string;
  line_net_amount: string;
  vat_rate_id: string | null;
  vat_amount: string | null;
  line_gross_amount: string | null;
};

export type PurchaseInvoice = {
  id: string;
  business_unit_id: string;
  supplier_id: string;
  supplier_name: string;
  invoice_number: string;
  invoice_date: string;
  currency: string;
  gross_total: string;
  notes: string | null;
  is_posted: boolean;
  posted_to_finance: boolean;
  posted_inventory_movement_count: number;
  created_at: string;
  updated_at: string;
  lines: PurchaseInvoiceLine[];
};

export type PurchaseInvoiceFilters = {
  business_unit_id?: string;
  supplier_id?: string;
  limit?: number;
};

export type PurchaseInvoiceLineCreatePayload = {
  inventory_item_id?: string;
  description: string;
  quantity: string;
  uom_id: string;
  unit_net_amount: string;
  line_net_amount: string;
  vat_rate_id?: string;
  vat_amount?: string;
  line_gross_amount?: string;
};

export type PurchaseInvoiceCreatePayload = {
  business_unit_id: string;
  supplier_id: string;
  invoice_number: string;
  invoice_date: string;
  currency: string;
  gross_total: string;
  notes?: string;
  lines: PurchaseInvoiceLineCreatePayload[];
};

export type PurchaseInvoicePostingResult = {
  purchase_invoice_id: string;
  created_financial_transactions: number;
  created_inventory_movements: number;
  updated_inventory_item_costs: number;
  finance_source_type: string;
  inventory_source_type: string;
};

export type PurchaseInvoicePdfReviewHeader = {
  supplier_id: string | null;
  invoice_number: string | null;
  invoice_date: string | null;
  currency: string;
  gross_total: string | null;
  notes: string | null;
};

export type PurchaseInvoicePdfReviewLine = {
  line_index: number;
  description: string;
  supplier_product_name: string | null;
  inventory_item_id: string | null;
  inventory_item_name: string | null;
  quantity: string | null;
  uom_id: string | null;
  vat_rate_id: string | null;
  vat_rate_percent: string | null;
  unit_net_amount: string | null;
  line_net_amount: string | null;
  vat_amount: string | null;
  line_gross_amount: string | null;
  calculation_status: "ok" | "review_needed";
  calculation_issues: string[];
  notes: string | null;
};

export type PurchaseInvoicePdfReviewPayload = {
  header: Partial<PurchaseInvoicePdfReviewHeader>;
  lines: PurchaseInvoicePdfReviewLine[];
};

export type PurchaseInvoicePdfReviewLineInput = {
  description: string;
  supplier_product_name?: string;
  inventory_item_id?: string;
  quantity?: string;
  uom_id?: string;
  vat_rate_id?: string;
  unit_net_amount?: string;
  line_net_amount?: string;
  vat_amount?: string;
  line_gross_amount?: string;
  notes?: string;
};

export type PurchaseInvoicePdfReviewUpdatePayload = {
  supplier_id?: string;
  invoice_number?: string;
  invoice_date?: string;
  currency: string;
  gross_total?: string;
  notes?: string;
  lines: PurchaseInvoicePdfReviewLineInput[];
};

export type PurchaseInvoicePdfDraft = {
  id: string;
  business_unit_id: string;
  supplier_id: string | null;
  original_name: string;
  stored_path: string;
  mime_type: string | null;
  size_bytes: number;
  status: string;
  extraction_status: string;
  raw_extraction: Record<string, unknown> | null;
  review_payload: PurchaseInvoicePdfReviewPayload | null;
  notes: string | null;
  created_at: string;
  updated_at: string;
};

export type SupplierItemAlias = {
  id: string;
  business_unit_id: string;
  supplier_id: string;
  inventory_item_id: string | null;
  source_item_name: string;
  source_item_key: string;
  internal_display_name: string | null;
  status: string;
  mapping_confidence: string;
  occurrence_count: number;
  first_seen_at: string;
  last_seen_at: string;
  notes: string | null;
  created_at: string;
  updated_at: string;
};

export type SupplierItemAliasFilters = {
  business_unit_id?: string;
  supplier_id?: string;
  status?: string;
  limit?: number;
};

export type SupplierItemAliasMappingPayload = {
  inventory_item_id: string;
  internal_display_name?: string;
  notes?: string;
};
