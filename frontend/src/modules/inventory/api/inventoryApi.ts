import { apiGet } from "../../../services/api/client";
import type { InventoryItem, InventoryItemFilters } from "../types/inventory";

export function listInventoryItems(filters: InventoryItemFilters) {
  return apiGet<InventoryItem[]>("inventory/items", filters);
}
