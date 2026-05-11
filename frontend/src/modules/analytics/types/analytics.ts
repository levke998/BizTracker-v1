export type DashboardScope = "overall" | "flow" | "gourmand";

export type DashboardPeriodPreset =
  | "last_1_hour"
  | "last_6_hours"
  | "last_12_hours"
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
  grain: "hour" | "day" | "month";
};

export type DashboardKpi = {
  code: "revenue" | "cost" | "profit" | "transaction_count" | string;
  label: string;
  value: string;
  unit: string;
  source_layer: string;
  amount_basis: "gross" | "net" | "vat" | "mixed" | string | null;
  amount_origin: "actual" | "derived" | string | null;
};

export type DashboardTrendPoint = {
  period_start: string;
  revenue: string;
  cost: string;
  profit: string;
  estimated_cogs: string;
  margin_profit: string;
  revenue_amount_basis: string;
  revenue_amount_origin: string;
  cost_amount_basis: string;
  cost_amount_origin: string;
};

export type DashboardBreakdownRow = {
  label: string;
  revenue: string;
  net_revenue: string | null;
  vat_amount: string | null;
  quantity: string;
  transaction_count: number;
  source_layer: string;
  amount_basis: string;
  tax_breakdown_source: string;
};

export type DashboardVatReadiness = {
  status: "complete" | "partial" | "missing" | "no_data" | string;
  coverage_percent: string;
  gross_revenue: string;
  covered_gross_revenue: string;
  missing_gross_revenue: string;
  total_row_count: number;
  covered_row_count: number;
  missing_row_count: number;
  source_layer: string;
  amount_basis: string;
  tax_breakdown_source: string;
};

export type DashboardHeatmapCell = {
  weekday: number;
  hour: number;
  revenue: string;
  transaction_count: number;
  source_layer: string;
};

export type DashboardCategoryTrendRow = {
  label: string;
  current_revenue: string;
  previous_revenue: string;
  revenue_change: string;
  revenue_change_percent: string;
  current_quantity: string;
  previous_quantity: string;
  current_transaction_count: number;
  previous_transaction_count: number;
  source_layer: string;
};

export type DashboardWeatherCategoryInsightRow = {
  category_name: string;
  weather_condition: string;
  revenue: string;
  quantity: string;
  transaction_count: number;
  average_temperature_c: string | null;
  source_layer: string;
};

export type DashboardTemperatureBandInsightRow = {
  temperature_band: string;
  revenue: string;
  quantity: string;
  transaction_count: number;
  basket_count: number;
  average_basket_value: string;
  average_temperature_c: string | null;
  top_category_name: string;
  top_category_revenue: string;
  source_layer: string;
};

export type DashboardWeatherConditionInsightRow = {
  condition_band: string;
  revenue: string;
  quantity: string;
  transaction_count: number;
  basket_count: number;
  average_basket_value: string;
  average_cloud_cover_percent: string | null;
  precipitation_mm: string;
  top_category_name: string;
  top_category_revenue: string;
  source_layer: string;
};

export type DashboardForecastImpactRow = {
  forecast_date: string;
  forecast_hours: number;
  dominant_temperature_band: string;
  dominant_condition_band: string;
  average_temperature_c: string | null;
  precipitation_mm: string;
  expected_revenue: string;
  historical_average_revenue: string;
  confidence: "magas" | "kozepes" | "alacsony" | string;
  recommendation: string;
  forecast_updated_at: string | null;
  source_layer: string;
};

export type DashboardForecastCategoryDemandRow = {
  forecast_date: string;
  category_name: string;
  dominant_temperature_band: string;
  dominant_condition_band: string;
  expected_revenue: string;
  expected_quantity: string;
  historical_average_revenue: string;
  revenue_uplift_percent: string;
  confidence: "magas" | "kozepes" | "alacsony" | string;
  demand_signal: "emelkedo" | "normal" | "visszafogott" | string;
  recommendation: string;
  source_layer: string;
};

export type DashboardForecastPreparationRow = {
  forecast_date: string;
  category_name: string;
  expected_revenue: string;
  expected_quantity: string;
  demand_signal: "emelkedo" | "normal" | "visszafogott" | string;
  confidence: "magas" | "kozepes" | "alacsony" | string;
  product_count: number;
  risky_product_count: number;
  low_stock_ingredient_count: number;
  missing_stock_ingredient_count: number;
  readiness_level: "rendben" | "figyelendo" | "kritikus" | string;
  recommendation: string;
  source_layer: string;
};

export type DashboardForecastProductDemandRow = {
  forecast_date: string;
  product_name: string;
  category_name: string;
  dominant_temperature_band: string;
  dominant_condition_band: string;
  expected_revenue: string;
  expected_quantity: string;
  historical_average_revenue: string;
  revenue_uplift_percent: string;
  confidence: "magas" | "kozepes" | "alacsony" | string;
  demand_signal: "emelkedo" | "normal" | "visszafogott" | string;
  recommendation: string;
  source_layer: string;
};

export type DashboardForecastPeakTimeRow = {
  forecast_date: string;
  time_window: string;
  start_hour: number;
  end_hour: number;
  dominant_temperature_band: string;
  dominant_condition_band: string;
  expected_revenue: string;
  expected_quantity: string;
  expected_transaction_count: number;
  historical_average_revenue: string;
  revenue_uplift_percent: string;
  confidence: "magas" | "kozepes" | "alacsony" | string;
  demand_signal: "emelkedo" | "normal" | "visszafogott" | string;
  recommendation: string;
  source_layer: string;
};

export type DashboardFlowForecastEventRow = {
  event_id: string;
  title: string;
  performer_name: string | null;
  starts_at: string;
  ends_at: string;
  expected_attendance: number | null;
  forecast_hours: number;
  dominant_condition_band: string;
  average_temperature_c: string | null;
  precipitation_mm: string;
  average_wind_speed_kmh: string | null;
  preparation_level: "rendben" | "figyelendo" | "kritikus" | string;
  focus_area: string;
  recommendation: string;
  source_layer: string;
};

export type DashboardProductRiskRow = {
  product_id: string;
  product_name: string;
  category_name: string;
  sale_price_gross: string;
  estimated_unit_cost: string;
  estimated_margin_amount: string;
  estimated_margin_percent: string;
  risk_level: "warning" | "danger" | string;
  risk_reasons: string[];
  low_stock_ingredient_count: number;
  missing_stock_ingredient_count: number;
  source_layer: string;
};

export type DashboardStockRiskRow = {
  inventory_item_id: string;
  item_name: string;
  item_type: string;
  current_quantity: string;
  theoretical_quantity: string | null;
  variance_quantity: string | null;
  used_by_product_count: number;
  movement_count: number;
  last_movement_at: string | null;
  risk_level: "warning" | "danger" | string;
  risk_reasons: string[];
  source_layer: string;
};

export type DashboardExpenseRow = {
  label: string;
  amount: string;
  gross_amount: string;
  net_amount: string | null;
  vat_amount: string | null;
  transaction_count: number;
  source_layer: string;
  amount_basis: string;
  tax_breakdown_source: string;
};

export type DashboardProductDetailRow = {
  product_name: string;
  category_name: string;
  revenue: string;
  net_revenue: string | null;
  vat_amount: string | null;
  estimated_unit_cost_net: string | null;
  estimated_cogs_net: string | null;
  estimated_net_margin_amount: string | null;
  estimated_margin_percent: string | null;
  quantity: string;
  transaction_count: number;
  source_layer: string;
  amount_basis: string;
  tax_breakdown_source: string;
  cost_source: string;
  margin_status: string;
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
  net_amount: string | null;
  vat_amount: string | null;
  vat_rate_percent: string | null;
  payment_method: string | null;
  source_layer: string;
  amount_basis: string;
  tax_breakdown_source: string;
};

export type DashboardExpenseDetailRow = {
  transaction_id: string;
  transaction_type: string;
  amount: string;
  gross_amount: string;
  net_amount: string | null;
  vat_amount: string | null;
  currency: string;
  occurred_at: string;
  description: string;
  source_type: string;
  source_id: string;
  source_layer: string;
  amount_basis: string;
  tax_breakdown_source: string;
};

export type DashboardExpenseSourceLine = {
  line_id: string;
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

export type DashboardExpenseSource = {
  transaction_id: string;
  transaction_type: string;
  amount: string;
  gross_amount: string;
  net_amount: string | null;
  vat_amount: string | null;
  currency: string;
  occurred_at: string;
  source_type: string;
  source_id: string;
  supplier_id: string | null;
  supplier_name: string | null;
  invoice_number: string | null;
  invoice_date: string | null;
  gross_total: string | null;
  net_total: string | null;
  vat_total: string | null;
  notes: string | null;
  amount_basis: string;
  tax_breakdown_source: string;
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
  vat_readiness: DashboardVatReadiness;
  payment_method_breakdown: DashboardBreakdownRow[];
  basket_value_distribution: DashboardBreakdownRow[];
  traffic_heatmap: DashboardHeatmapCell[];
  category_trends: DashboardCategoryTrendRow[];
  weather_category_insights: DashboardWeatherCategoryInsightRow[];
  temperature_band_insights: DashboardTemperatureBandInsightRow[];
  weather_condition_insights: DashboardWeatherConditionInsightRow[];
  forecast_impact_insights: DashboardForecastImpactRow[];
  forecast_category_demand_insights: DashboardForecastCategoryDemandRow[];
  forecast_preparation_insights: DashboardForecastPreparationRow[];
  forecast_product_demand_insights: DashboardForecastProductDemandRow[];
  forecast_peak_time_insights: DashboardForecastPeakTimeRow[];
  flow_forecast_event_insights: DashboardFlowForecastEventRow[];
  product_risks: DashboardProductRiskRow[];
  stock_risks: DashboardStockRiskRow[];
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
