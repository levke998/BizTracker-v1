import {
  apiDelete,
  apiGet,
  apiPatchJson,
  apiPostJson,
} from "../../../services/api/client";
import type {
  InventoryItemCreatePayload,
  InventoryItem,
  InventoryItemFilters,
  InventoryItemUpdatePayload,
  InventoryMovementCreatePayload,
  InventoryMovement,
  InventoryMovementFilters,
  InventoryStockLevel,
  InventoryStockLevelFilters,
  InventoryTheoreticalStock,
  InventoryTheoreticalStockFilters,
} from "../types/inventory";

export function listInventoryItems(filters: InventoryItemFilters) {
  return apiGet<InventoryItem[]>("inventory/items", filters);
}

export function createInventoryItem(payload: InventoryItemCreatePayload) {
  return apiPostJson<InventoryItemCreatePayload, InventoryItem>("inventory/items", payload);
}

export function updateInventoryItem(
  inventoryItemId: string,
  payload: InventoryItemUpdatePayload
) {
  return apiPatchJson<InventoryItemUpdatePayload, InventoryItem>(
    `inventory/items/${inventoryItemId}`,
    payload
  );
}

export function archiveInventoryItem(inventoryItemId: string) {
  return apiDelete<InventoryItem>(`inventory/items/${inventoryItemId}`);
}

export function listInventoryStockLevels(filters: InventoryStockLevelFilters) {
  return apiGet<InventoryStockLevel[]>("inventory/stock-levels", filters);
}

export function listInventoryTheoreticalStock(
  filters: InventoryTheoreticalStockFilters
) {
  return apiGet<InventoryTheoreticalStock[]>("inventory/theoretical-stock", filters);
}

export function listInventoryMovements(filters: InventoryMovementFilters) {
  return apiGet<InventoryMovement[]>("inventory/movements", filters);
}

export function createInventoryMovement(payload: InventoryMovementCreatePayload) {
  return apiPostJson<InventoryMovementCreatePayload, InventoryMovement>(
    "inventory/movements",
    payload
  );
}
