import { useQuery } from "@tanstack/react-query";
import { useState } from "react";

import { listBusinessUnits } from "../../masterData/api/masterDataApi";
import type { BusinessUnit } from "../../masterData/types/masterData";
import { listInventoryStockLevels } from "../api/inventoryApi";

type StockLevelsState = {
  businessUnits: BusinessUnit[];
  primaryBusinessUnits: BusinessUnit[];
  technicalBusinessUnits: BusinessUnit[];
  stockLevels: Awaited<ReturnType<typeof listInventoryStockLevels>>;
  selectedBusinessUnitId: string;
  setSelectedBusinessUnitId: (value: string) => void;
  selectedItemType: string;
  setSelectedItemType: (value: string) => void;
  limit: number;
  setLimit: (value: number) => void;
  isLoading: boolean;
  errorMessage: string;
};

const TECHNICAL_BUSINESS_UNIT_CODES = new Set(["test-integration"]);

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

export function useStockLevels(): StockLevelsState {
  const [selectedBusinessUnitId, setSelectedBusinessUnitId] = useState("");
  const [selectedItemType, setSelectedItemType] = useState("");
  const [limit, setLimit] = useState(50);

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

  const stockLevelsQuery = useQuery({
    queryKey: [
      "inventory-stock-levels",
      effectiveBusinessUnitId,
      selectedItemType,
      limit,
    ],
    queryFn: () =>
      listInventoryStockLevels({
        business_unit_id: effectiveBusinessUnitId,
        item_type: selectedItemType,
        limit,
      }),
    enabled: Boolean(effectiveBusinessUnitId),
  });

  return {
    businessUnits,
    primaryBusinessUnits,
    technicalBusinessUnits,
    stockLevels: stockLevelsQuery.data ?? [],
    selectedBusinessUnitId: effectiveBusinessUnitId,
    setSelectedBusinessUnitId,
    selectedItemType,
    setSelectedItemType,
    limit,
    setLimit,
    isLoading: businessUnitsQuery.isLoading || stockLevelsQuery.isLoading,
    errorMessage:
      (businessUnitsQuery.error instanceof Error && businessUnitsQuery.error.message) ||
      (stockLevelsQuery.error instanceof Error && stockLevelsQuery.error.message) ||
      "",
  };
}
