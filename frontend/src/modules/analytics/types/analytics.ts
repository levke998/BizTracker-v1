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
