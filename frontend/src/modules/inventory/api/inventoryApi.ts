import {
  apiDelete,
  apiGet,
  apiPatchJson,
  apiPostJson,
  apiPutJson,
} from "../../../services/api/client";
import type {
  InventoryItemCreatePayload,
  InventoryItem,
  InventoryItemFilters,
  InventoryItemUpdatePayload,
  InventoryMovementCreatePayload,
  InventoryMovement,
  InventoryMovementFilters,
  PhysicalStockCountCreatePayload,
  PhysicalStockCountResult,
  EstimatedConsumptionAudit,
  EstimatedConsumptionAuditFilters,
  InventoryStockLevel,
  InventoryStockLevelFilters,
  InventoryTheoreticalStock,
  InventoryTheoreticalStockFilters,
  InventoryVarianceItemSummary,
  InventoryVarianceItemSummaryFilters,
  InventoryVariancePeriodComparison,
  InventoryVariancePeriodComparisonFilters,
  InventoryVarianceReasonSummary,
  InventoryVarianceReasonSummaryFilters,
  InventoryVarianceThreshold,
  InventoryVarianceThresholdUpdatePayload,
  InventoryVarianceTrendFilters,
  InventoryVarianceTrendPoint,
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

export function listInventoryVarianceReasonSummary(
  filters: InventoryVarianceReasonSummaryFilters
) {
  return apiGet<InventoryVarianceReasonSummary[]>("inventory/variance-reasons", filters);
}

export function listInventoryVarianceTrend(filters: InventoryVarianceTrendFilters) {
  return apiGet<InventoryVarianceTrendPoint[]>("inventory/variance-trend", filters);
}

export function listInventoryVarianceItemSummary(
  filters: InventoryVarianceItemSummaryFilters
) {
  return apiGet<InventoryVarianceItemSummary[]>("inventory/variance-items", filters);
}

export function getInventoryVariancePeriodComparison(
  filters: InventoryVariancePeriodComparisonFilters
) {
  return apiGet<InventoryVariancePeriodComparison>(
    "inventory/variance-period-comparison",
    filters
  );
}

export function getInventoryVarianceThreshold(businessUnitId: string) {
  return apiGet<InventoryVarianceThreshold>("inventory/variance-thresholds", {
    business_unit_id: businessUnitId,
  });
}

export function updateInventoryVarianceThreshold(
  payload: InventoryVarianceThresholdUpdatePayload
) {
  return apiPutJson<InventoryVarianceThresholdUpdatePayload, InventoryVarianceThreshold>(
    "inventory/variance-thresholds",
    payload
  );
}

export function listEstimatedConsumptionAudit(
  filters: EstimatedConsumptionAuditFilters
) {
  return apiGet<EstimatedConsumptionAudit[]>(
    "inventory/estimated-consumption",
    filters
  );
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

export function registerPhysicalStockCount(payload: PhysicalStockCountCreatePayload) {
  return apiPostJson<PhysicalStockCountCreatePayload, PhysicalStockCountResult>(
    "inventory/physical-stock-counts",
    payload
  );
}
