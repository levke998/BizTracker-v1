export type DashboardScope = "overall" | "flow" | "gourmand";

export type DashboardPeriodPreset =
  | "today"
  | "week"
  | "month"
  | "year"
  | "last_7_days"
  | "last_30_days"
  | "custom";

export type DashboardPeriod = {
  preset: DashboardPeriodPreset;
  start_date: string;
  end_date: string;
  grain: "day" | "month";
};

export type DashboardKpi = {
  code: "revenue" | "cost" | "profit" | "transaction_count" | string;
  label: string;
  value: string;
  unit: string;
  source_layer: string;
};

export type DashboardTrendPoint = {
  period_start: string;
  revenue: string;
  cost: string;
  profit: string;
  estimated_cogs: string;
  margin_profit: string;
};

export type DashboardBreakdownRow = {
  label: string;
  revenue: string;
  quantity: string;
  transaction_count: number;
  source_layer: string;
};

export type DashboardExpenseRow = {
  label: string;
  amount: string;
  transaction_count: number;
  source_layer: string;
};

export type DashboardProductDetailRow = {
  product_name: string;
  category_name: string;
  revenue: string;
  quantity: string;
  transaction_count: number;
  source_layer: string;
};

export type DashboardPosSourceRow = {
  row_id: string;
  row_number: number;
  date: string | null;
  receipt_no: string | null;
  category_name: string;
  product_name: string;
  quantity: string;
  gross_amount: string;
  payment_method: string | null;
  source_layer: string;
};

export type DashboardExpenseDetailRow = {
  transaction_id: string;
  transaction_type: string;
  amount: string;
  currency: string;
  occurred_at: string;
  description: string;
  source_type: string;
  source_id: string;
  source_layer: string;
};

export type DashboardExpenseSourceLine = {
  line_id: string;
  inventory_item_id: string | null;
  description: string;
  quantity: string;
  uom_id: string;
  unit_net_amount: string;
  line_net_amount: string;
};

export type DashboardExpenseSource = {
  transaction_id: string;
  transaction_type: string;
  amount: string;
  currency: string;
  occurred_at: string;
  source_type: string;
  source_id: string;
  supplier_id: string | null;
  supplier_name: string | null;
  invoice_number: string | null;
  invoice_date: string | null;
  gross_total: string | null;
  notes: string | null;
  lines: DashboardExpenseSourceLine[];
};

export type DashboardBasketPairRow = {
  product_a: string;
  product_b: string;
  basket_count: number;
  total_gross_amount: string;
  source_layer: string;
};

export type DashboardBasketReceiptLine = {
  row_id: string;
  row_number: number;
  product_name: string;
  category_name: string;
  quantity: string;
  gross_amount: string;
  payment_method: string | null;
};

export type DashboardBasketReceipt = {
  receipt_no: string;
  date: string | null;
  gross_amount: string;
  quantity: string;
  lines: DashboardBasketReceiptLine[];
  source_layer: string;
};

export type DashboardData = {
  scope: DashboardScope;
  business_unit_id: string | null;
  business_unit_name: string | null;
  period: DashboardPeriod;
  kpis: DashboardKpi[];
  revenue_trend: DashboardTrendPoint[];
  category_breakdown: DashboardBreakdownRow[];
  top_products: DashboardBreakdownRow[];
  expense_breakdown: DashboardExpenseRow[];
  notes: string[];
};

export type DashboardFilters = {
  scope: DashboardScope;
  period: DashboardPeriodPreset;
  business_unit_id?: string;
  start_date?: string;
  end_date?: string;
};
