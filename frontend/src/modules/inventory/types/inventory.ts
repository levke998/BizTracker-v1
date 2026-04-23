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

export type InventoryItemFilters = {
  business_unit_id?: string;
  item_type?: string;
  limit?: number;
};
