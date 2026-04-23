import { useQuery } from "@tanstack/react-query";
import { useMemo, useState } from "react";

import { listBusinessUnits } from "../../masterData/api/masterDataApi";
import type { BusinessUnit } from "../../masterData/types/masterData";
import {
  listInventoryItems,
  listInventoryMovements,
  listInventoryStockLevels,
} from "../api/inventoryApi";

type InventoryOverviewState = {
  primaryBusinessUnits: BusinessUnit[];
  technicalBusinessUnits: BusinessUnit[];
  selectedBusinessUnitId: string;
  setSelectedBusinessUnitId: (value: string) => void;
  itemsCount: number;
  trackedItemsCount: number;
  stockLevelRowsCount: number;
  nonZeroStockRowsCount: number;
  recentMovements: Awaited<ReturnType<typeof listInventoryMovements>>;
  stockHighlights: Awaited<ReturnType<typeof listInventoryStockLevels>>;
  isLoading: boolean;
  errorMessage: string;
};

const TECHNICAL_BUSINESS_UNIT_CODES = new Set(["test-integration"]);
const NON_ZERO_STOCK_VALUES = new Set(["0", "0.0", "0.00", "0.000"]);

function sortBusinessUnits(items: BusinessUnit[]) {
  return [...items].sort((left, right) => {
    const leftIsTechnical = TECHNICAL_BUSINESS_UNIT_CODES.has(left.code);
    const rightIsTechnical = TECHNICAL_BUSINESS_UNIT_CODES.has(right.code);

    if (leftIsTechnical !== rightIsTechnical) {
      return leftIsTechnical ? 1 : -1;
    }

    return left.name.localeCompare(right.name);
  });
}

function splitBusinessUnits(items: BusinessUnit[]) {
  return {
    primary: items.filter((item) => !TECHNICAL_BUSINESS_UNIT_CODES.has(item.code)),
    technical: items.filter((item) => TECHNICAL_BUSINESS_UNIT_CODES.has(item.code)),
  };
}

export function useInventoryOverview(): InventoryOverviewState {
  const [selectedBusinessUnitId, setSelectedBusinessUnitId] = useState("");

  const businessUnitsQuery = useQuery({
    queryKey: ["business-units"],
    queryFn: async () => sortBusinessUnits(await listBusinessUnits()),
  });

  const businessUnits = businessUnitsQuery.data ?? [];
  const { primary: primaryBusinessUnits, technical: technicalBusinessUnits } =
    splitBusinessUnits(businessUnits);

  const effectiveBusinessUnitId =
    selectedBusinessUnitId ||
    primaryBusinessUnits[0]?.id ||
    businessUnits[0]?.id ||
    "";

  const inventoryItemsQuery = useQuery({
    queryKey: ["inventory-overview-items", effectiveBusinessUnitId],
    queryFn: () =>
      listInventoryItems({
        business_unit_id: effectiveBusinessUnitId,
        limit: 200,
      }),
    enabled: Boolean(effectiveBusinessUnitId),
  });

  const stockLevelsQuery = useQuery({
    queryKey: ["inventory-overview-stock-levels", effectiveBusinessUnitId],
    queryFn: () =>
      listInventoryStockLevels({
        business_unit_id: effectiveBusinessUnitId,
        limit: 200,
      }),
    enabled: Boolean(effectiveBusinessUnitId),
  });

  const movementsQuery = useQuery({
    queryKey: ["inventory-overview-movements", effectiveBusinessUnitId],
    queryFn: () =>
      listInventoryMovements({
        business_unit_id: effectiveBusinessUnitId,
        limit: 6,
      }),
    enabled: Boolean(effectiveBusinessUnitId),
  });

  const items = inventoryItemsQuery.data ?? [];
  const stockLevels = stockLevelsQuery.data ?? [];
  const recentMovements = movementsQuery.data ?? [];

  const stockHighlights = useMemo(
    () =>
      [...stockLevels]
        .sort((left, right) => {
          if (!left.last_movement_at && !right.last_movement_at) {
            return left.name.localeCompare(right.name);
          }
          if (!left.last_movement_at) {
            return 1;
          }
          if (!right.last_movement_at) {
            return -1;
          }

          return right.last_movement_at.localeCompare(left.last_movement_at);
        })
        .slice(0, 6),
    [stockLevels]
  );

  return {
    primaryBusinessUnits,
    technicalBusinessUnits,
    selectedBusinessUnitId: effectiveBusinessUnitId,
    setSelectedBusinessUnitId,
    itemsCount: items.length,
    trackedItemsCount: items.filter((item) => item.track_stock).length,
    stockLevelRowsCount: stockLevels.length,
    nonZeroStockRowsCount: stockLevels.filter(
      (item) => !NON_ZERO_STOCK_VALUES.has(item.current_quantity)
    ).length,
    recentMovements,
    stockHighlights,
    isLoading:
      businessUnitsQuery.isLoading ||
      inventoryItemsQuery.isLoading ||
      stockLevelsQuery.isLoading ||
      movementsQuery.isLoading,
    errorMessage:
      (businessUnitsQuery.error instanceof Error && businessUnitsQuery.error.message) ||
      (inventoryItemsQuery.error instanceof Error && inventoryItemsQuery.error.message) ||
      (stockLevelsQuery.error instanceof Error && stockLevelsQuery.error.message) ||
      (movementsQuery.error instanceof Error && movementsQuery.error.message) ||
      "",
  };
}
