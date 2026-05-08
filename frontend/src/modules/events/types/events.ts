export type EventStatus = "planned" | "confirmed" | "completed" | "cancelled";

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
  performer_share_percent: string;
  performer_fixed_fee: string;
  event_cost_amount: string;
  notes: string | null;
  is_active: boolean;
  performer_share_amount: string;
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
  performer_share_percent: string;
  performer_share_amount: string;
  retained_ticket_revenue: string;
  own_revenue: string;
  event_profit_lite: string;
  categories: EventPerformanceCategory[];
  top_products: EventPerformanceProduct[];
  weather: EventWeatherSummary;
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
