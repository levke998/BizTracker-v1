export type DemoPosCatalogProduct = {
  id: string;
  business_unit_id: string;
  category_id: string | null;
  category_name: string | null;
  sales_uom_id: string | null;
  sales_uom_code: string | null;
  sales_uom_symbol: string | null;
  sku: string | null;
  name: string;
  product_type: string;
  sale_price_gross: string;
  default_unit_cost: string | null;
  currency: string;
};

export type DemoPosReceiptLineRequest = {
  product_id: string;
  quantity: number;
};

export type DemoPosReceiptRequest = {
  business_unit_id: string;
  payment_method: string;
  receipt_no?: string;
  occurred_at?: string;
  lines: DemoPosReceiptLineRequest[];
};

export type DemoPosReceiptLine = {
  product_id: string;
  product_name: string;
  category_name: string | null;
  quantity: string;
  unit_price_gross: string;
  gross_amount: string;
  import_row_id: string;
  transaction_id: string;
};

export type DemoPosReceipt = {
  business_unit_id: string;
  receipt_no: string;
  payment_method: string;
  occurred_at: string;
  batch_id: string;
  gross_total: string;
  transaction_count: number;
  lines: DemoPosReceiptLine[];
};
