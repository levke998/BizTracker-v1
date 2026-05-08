export type InventoryItem = {
  id: string;
  business_unit_id: string;
  name: string;
  item_type: string;
  uom_id: string;
  track_stock: boolean;
  is_active: boolean;
  created_at: string;
  updated_at: string;
};

export type InventoryItemUpdatePayload = {
  name: string;
  item_type: string;
  uom_id: string;
  track_stock: boolean;
  is_active: boolean;
};

export type InventoryItemCreatePayload = {
  business_unit_id: string;
  name: string;
  item_type: string;
  uom_id: string;
  track_stock: boolean;
  is_active: boolean;
};

export type InventoryItemFilters = {
  business_unit_id?: string;
  item_type?: string;
  limit?: number;
};

export type InventoryStockLevel = {
  inventory_item_id: string;
  business_unit_id: string;
  name: string;
  item_type: string;
  uom_id: string;
  track_stock: boolean;
  is_active: boolean;
  current_quantity: string;
  last_movement_at: string | null;
  movement_count: number;
};

export type InventoryStockLevelFilters = {
  business_unit_id?: string;
  inventory_item_id?: string;
  item_type?: string;
  limit?: number;
};

export type InventoryTheoreticalStock = {
  inventory_item_id: string;
  business_unit_id: string;
  name: string;
  item_type: string;
  uom_id: string;
  track_stock: boolean;
  is_active: boolean;
  actual_quantity: string;
  theoretical_quantity: string | null;
  variance_quantity: string | null;
  default_unit_cost: string | null;
  actual_stock_value: string | null;
  theoretical_stock_value: string | null;
  variance_stock_value: string | null;
  variance_status: string;
  last_actual_movement_at: string | null;
  last_estimated_event_at: string | null;
  estimation_basis: string;
};

export type InventoryTheoreticalStockFilters = {
  business_unit_id?: string;
  inventory_item_id?: string;
  item_type?: string;
  limit?: number;
};

export type InventoryVarianceReasonSummary = {
  reason_code: string;
  movement_count: number;
  total_quantity: string;
  net_quantity_delta: string;
  latest_occurred_at: string | null;
};

export type InventoryVarianceReasonSummaryFilters = {
  business_unit_id?: string;
  inventory_item_id?: string;
  limit?: number;
};

export type InventoryVarianceTrendPoint = {
  bucket_date: string;
  movement_count: number;
  shortage_quantity: string;
  surplus_quantity: string;
  net_quantity_delta: string;
  estimated_shortage_value: string;
  estimated_surplus_value: string;
  estimated_net_value_delta: string;
  missing_cost_movement_count: number;
};

export type InventoryVarianceTrendFilters = {
  business_unit_id?: string;
  inventory_item_id?: string;
  days?: number;
};

export type InventoryVarianceItemSummary = {
  inventory_item_id: string;
  name: string;
  item_type: string;
  default_unit_cost: string | null;
  movement_count: number;
  shortage_quantity: string;
  surplus_quantity: string;
  net_quantity_delta: string;
  estimated_shortage_value: string | null;
  estimated_surplus_value: string | null;
  estimated_net_value_delta: string | null;
  missing_cost_movement_count: number;
  anomaly_status: string;
  latest_occurred_at: string | null;
};

export type InventoryVarianceItemSummaryFilters = {
  business_unit_id?: string;
  limit?: number;
};

export type InventoryVariancePeriodComparison = {
  current_start_at: string;
  current_end_at: string;
  previous_start_at: string;
  previous_end_at: string;
  period_days: number;
  current_movement_count: number;
  previous_movement_count: number;
  movement_count_change: number;
  current_shortage_quantity: string;
  previous_shortage_quantity: string;
  shortage_quantity_change: string;
  current_estimated_shortage_value: string;
  previous_estimated_shortage_value: string;
  estimated_shortage_value_change: string;
  estimated_shortage_value_change_percent: string | null;
  current_missing_cost_movement_count: number;
  previous_missing_cost_movement_count: number;
  decision_status: string;
  recommendation: string;
};

export type InventoryVariancePeriodComparisonFilters = {
  business_unit_id?: string;
  inventory_item_id?: string;
  days?: number;
  high_loss_value_threshold?: string;
  worsening_percent_threshold?: string;
};

export type InventoryVarianceThreshold = {
  id: string | null;
  business_unit_id: string;
  high_loss_value_threshold: string;
  worsening_percent_threshold: string;
  is_default: boolean;
  created_at: string | null;
  updated_at: string | null;
};

export type InventoryVarianceThresholdUpdatePayload = {
  business_unit_id: string;
  high_loss_value_threshold: string;
  worsening_percent_threshold: string;
};

export type EstimatedConsumptionAudit = {
  id: string;
  business_unit_id: string;
  product_id: string;
  product_name: string;
  inventory_item_id: string;
  inventory_item_name: string;
  recipe_version_id: string | null;
  source_type: string;
  source_id: string;
  source_dedupe_key: string | null;
  receipt_no: string | null;
  estimation_basis: string;
  quantity: string;
  uom_id: string;
  uom_code: string;
  quantity_before: string;
  quantity_after: string;
  occurred_at: string;
  created_at: string;
};

export type EstimatedConsumptionAuditFilters = {
  business_unit_id?: string;
  inventory_item_id?: string;
  product_id?: string;
  source_type?: string;
  limit?: number;
};

export type InventoryMovement = {
  id: string;
  business_unit_id: string;
  inventory_item_id: string;
  movement_type: string;
  quantity: string;
  uom_id: string;
  unit_cost: string | null;
  reason_code: string | null;
  note: string | null;
  source_type: string | null;
  source_id: string | null;
  occurred_at: string;
  created_at: string;
};

export type InventoryMovementCreatePayload = {
  business_unit_id: string;
  inventory_item_id: string;
  movement_type: "purchase" | "adjustment" | "waste" | "initial_stock";
  quantity: string;
  uom_id: string;
  unit_cost?: string;
  reason_code?: string;
  note?: string;
  occurred_at?: string;
};

export type PhysicalStockCountCreatePayload = {
  business_unit_id: string;
  inventory_item_id: string;
  counted_quantity: string;
  uom_id: string;
  reason_code: string;
  note?: string;
  occurred_at?: string;
};

export type PhysicalStockCountResult = {
  inventory_item_id: string;
  business_unit_id: string;
  previous_quantity: string;
  counted_quantity: string;
  adjustment_quantity: string;
  movement: InventoryMovement;
};

export type InventoryMovementFilters = {
  business_unit_id?: string;
  inventory_item_id?: string;
  movement_type?: string;
  limit?: number;
};
