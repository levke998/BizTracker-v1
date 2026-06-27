export type EventStatus = "planned" | "confirmed" | "completed" | "cancelled";
export type PerformerSettlementType = "revenue_share" | "fixed_fee" | "hybrid";

export type EventRecord = {
  id: string;
  business_unit_id: string;
  location_id: string | null;
  title: string;
  status: EventStatus;
  starts_at: string;
  ends_at: string | null;
  performer_name: string | null;
  expected_attendance: number | null;
  ticket_revenue_gross: string;
  bar_revenue_gross: string;
  performer_settlement_type: PerformerSettlementType | string;
  performer_share_percent: string;
  performer_fixed_fee: string;
  event_cost_amount: string;
  notes: string | null;
  is_active: boolean;
  performer_share_amount: string;
  performer_fixed_fee_amount: string;
  performer_total_compensation_gross: string;
  retained_ticket_revenue: string;
  own_revenue: string;
  event_profit_lite: string;
  created_at: string;
  updated_at: string;
};

export type EventPayload = {
  business_unit_id: string;
  location_id: string | null;
  title: string;
  status: EventStatus;
  starts_at: string;
  ends_at: string | null;
  performer_name: string | null;
  expected_attendance: number | null;
  ticket_revenue_gross: string;
  bar_revenue_gross: string;
  performer_settlement_type: PerformerSettlementType | string;
  performer_share_percent: string;
  performer_fixed_fee: string;
  event_cost_amount: string;
  notes: string | null;
  is_active: boolean;
};

export type EventTicketActual = {
  id: string;
  event_id: string;
  source_name: string | null;
  source_reference: string | null;
  sold_quantity: string;
  gross_revenue: string;
  net_revenue: string | null;
  vat_amount: string | null;
  vat_rate_id: string | null;
  platform_fee_gross: string;
  reported_at: string | null;
  notes: string | null;
  created_at: string;
  updated_at: string;
};

export type EventTicketActualPayload = {
  source_name: string | null;
  source_reference: string | null;
  sold_quantity: string;
  gross_revenue: string;
  net_revenue: string | null;
  vat_amount: string | null;
  vat_rate_id: string | null;
  platform_fee_gross: string;
  reported_at: string | null;
  notes: string | null;
};

export type EventCostLine = {
  id: string;
  event_id: string;
  category: string;
  description: string;
  amount_gross: string;
  source_type: string;
  source_reference: string | null;
  incurred_at: string | null;
  notes: string | null;
  created_at: string;
  updated_at: string;
};

export type EventCostLinePayload = {
  category: string;
  description: string;
  amount_gross: string;
  source_type: string;
  source_reference: string | null;
  incurred_at: string | null;
  notes: string | null;
};

export type EventFilters = {
  business_unit_id?: string;
  status?: string;
  is_active?: boolean;
  starts_from?: string;
  starts_to?: string;
  limit?: number;
};

export type EventPerformanceCategory = {
  category_name: string;
  gross_amount: string;
  quantity: string;
  row_count: number;
};

export type EventPerformanceProduct = {
  product_name: string;
  category_name: string;
  gross_amount: string;
  quantity: string;
  row_count: number;
};

export type EventWeatherSummary = {
  observation_count: number;
  dominant_condition: string | null;
  average_temperature_c: string | null;
  total_precipitation_mm: string;
  average_cloud_cover_percent: string | null;
  average_wind_speed_kmh: string | null;
};

export type EventPerformance = {
  event_id: string;
  business_unit_id: string;
  starts_at: string;
  ends_at: string;
  source_row_count: number;
  receipt_count: number;
  ticket_revenue_gross: string;
  bar_revenue_gross: string;
  total_revenue_gross: string;
  ticket_quantity: string;
  bar_quantity: string;
  performer_settlement_type: PerformerSettlementType | string;
  performer_share_percent: string;
  performer_share_amount: string;
  performer_fixed_fee_amount: string;
  performer_total_compensation_gross: string;
  retained_ticket_revenue: string;
  platform_fee_gross: string;
  event_cost_lines_gross: string;
  own_revenue: string;
  operating_cost_gross: string;
  event_profit_lite: string;
  event_profit_margin_percent: string | null;
  operating_cost_ratio_percent: string | null;
  ticket_revenue_share_percent: string | null;
  bar_revenue_share_percent: string | null;
  profit_status: "profitable" | "break_even" | "loss" | "no_revenue" | string;
  ticket_revenue_source: string;
  settlement_status: string;
  categories: EventPerformanceCategory[];
  top_products: EventPerformanceProduct[];
  weather: EventWeatherSummary;
};

export type EventAnalyticsMetrics = {
  event_count: number;
  ticket_revenue_gross: string;
  bar_revenue_gross: string;
  own_revenue: string;
  event_profit_lite: string;
  receipt_count: number;
  ticket_actual_count: number;
  missing_ticket_actual_count: number;
  ticket_actual_coverage_percent: string;
  profitable_count: number;
  loss_count: number;
};

export type EventAnalyticsHighlight = {
  event_id: string | null;
  title: string | null;
  performer_name: string | null;
  starts_at: string | null;
  metric_value: string | null;
};

export type EventAnalyticsHighlights = {
  top_profit: EventAnalyticsHighlight;
  most_popular: EventAnalyticsHighlight;
  highest_revenue: EventAnalyticsHighlight;
  top_margin: EventAnalyticsHighlight;
  highest_cost_ratio: EventAnalyticsHighlight;
};

export type EventPerformerAnalyticsRow = {
  performer: string;
  event_count: number;
  ticket_revenue_gross: string;
  bar_revenue_gross: string;
  own_revenue: string;
  event_profit_lite: string;
};

export type EventAnalyticsInsight = {
  key: string;
  tone: "success" | "warning" | "danger" | "neutral" | string;
  title: string;
  event_id: string;
  event_title: string;
  metric: string;
  detail: string;
};

export type EventAnalyticsSummary = {
  metrics: EventAnalyticsMetrics;
  highlights: EventAnalyticsHighlights;
  performer_rows: EventPerformerAnalyticsRow[];
  insights: EventAnalyticsInsight[];
};

export type EventWeatherCoverage = {
  status: "covered" | "backfilled" | "skipped";
  reason: string | null;
  start_at: string;
  end_at: string;
  requested_hours: number;
  cached_hours: number;
  missing_hours: number;
  backfill_attempted: boolean;
  created_count: number;
  updated_count: number;
  skipped_count: number;
};
