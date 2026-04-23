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

export type InventoryMovement = {
  id: string;
  business_unit_id: string;
  inventory_item_id: string;
  movement_type: string;
  quantity: string;
  uom_id: string;
  unit_cost: string | null;
  note: string | null;
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
  note?: string;
  occurred_at?: string;
};

export type InventoryMovementFilters = {
  business_unit_id?: string;
  inventory_item_id?: string;
  movement_type?: string;
  limit?: number;
};
