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
  finance_source_type: string;
  inventory_source_type: string;
};
