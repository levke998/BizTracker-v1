import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";

import {
  listBusinessUnits,
  listUnitsOfMeasure,
} from "../../masterData/api/masterDataApi";
import type { BusinessUnit, UnitOfMeasure } from "../../masterData/types/masterData";
import {
  createInventoryItem,
  archiveInventoryItem,
  listInventoryItems,
  updateInventoryItem,
} from "../api/inventoryApi";
import type {
  InventoryItemCreatePayload,
  InventoryItemUpdatePayload,
} from "../types/inventory";

type InventoryItemsState = {
  businessUnits: BusinessUnit[];
  primaryBusinessUnits: BusinessUnit[];
  technicalBusinessUnits: BusinessUnit[];
  unitsOfMeasure: UnitOfMeasure[];
  items: Awaited<ReturnType<typeof listInventoryItems>>;
  selectedBusinessUnitId: string;
  setSelectedBusinessUnitId: (value: string) => void;
  selectedItemType: string;
  setSelectedItemType: (value: string) => void;
  limit: number;
  setLimit: (value: number) => void;
  createItem: (payload: InventoryItemCreatePayload) => Promise<void>;
  updateItem: (inventoryItemId: string, payload: InventoryItemUpdatePayload) => Promise<void>;
  archiveItem: (inventoryItemId: string) => Promise<void>;
  isSaving: boolean;
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

export function useInventoryItems(): InventoryItemsState {
  const queryClient = useQueryClient();
  const [selectedBusinessUnitId, setSelectedBusinessUnitId] = useState("");
  const [selectedItemType, setSelectedItemType] = useState("");
  const [limit, setLimit] = useState(50);

  const businessUnitsQuery = useQuery({
    queryKey: ["business-units"],
    queryFn: async () => sortBusinessUnits(await listBusinessUnits()),
  });

  const businessUnits = businessUnitsQuery.data ?? [];
  const unitsOfMeasureQuery = useQuery({
    queryKey: ["units-of-measure"],
    queryFn: listUnitsOfMeasure,
  });
  const unitsOfMeasure = unitsOfMeasureQuery.data ?? [];
  const { primary: primaryBusinessUnits, technical: technicalBusinessUnits } =
    splitBusinessUnits(businessUnits);

  const effectiveBusinessUnitId =
    selectedBusinessUnitId ||
    primaryBusinessUnits[0]?.id ||
    businessUnits[0]?.id ||
    "";

  const inventoryItemsQuery = useQuery({
    queryKey: [
      "inventory-items",
      effectiveBusinessUnitId,
      selectedItemType,
      limit,
    ],
    queryFn: () =>
      listInventoryItems({
        business_unit_id: effectiveBusinessUnitId,
        item_type: selectedItemType,
        limit,
      }),
    enabled: Boolean(effectiveBusinessUnitId),
  });

  const refreshInventoryQueries = async () => {
    await Promise.all([
      queryClient.invalidateQueries({ queryKey: ["inventory-items"] }),
      queryClient.invalidateQueries({ queryKey: ["inventory-stock-levels"] }),
      queryClient.invalidateQueries({ queryKey: ["inventory-theoretical-stock"] }),
      queryClient.invalidateQueries({ queryKey: ["inventory-overview-items"] }),
      queryClient.invalidateQueries({ queryKey: ["inventory-overview-stock-levels"] }),
    ]);
  };

  const updateMutation = useMutation({
    mutationFn: ({
      inventoryItemId,
      payload,
    }: {
      inventoryItemId: string;
      payload: InventoryItemUpdatePayload;
    }) => updateInventoryItem(inventoryItemId, payload),
    onSuccess: refreshInventoryQueries,
  });

  const createMutation = useMutation({
    mutationFn: (payload: InventoryItemCreatePayload) => createInventoryItem(payload),
    onSuccess: refreshInventoryQueries,
  });

  const archiveMutation = useMutation({
    mutationFn: (inventoryItemId: string) => archiveInventoryItem(inventoryItemId),
    onSuccess: refreshInventoryQueries,
  });

  return {
    businessUnits,
    primaryBusinessUnits,
    technicalBusinessUnits,
    unitsOfMeasure,
    items: inventoryItemsQuery.data ?? [],
    selectedBusinessUnitId: effectiveBusinessUnitId,
    setSelectedBusinessUnitId,
    selectedItemType,
    setSelectedItemType,
    limit,
    setLimit,
    createItem: async (payload) => {
      await createMutation.mutateAsync(payload);
    },
    updateItem: async (inventoryItemId, payload) => {
      await updateMutation.mutateAsync({ inventoryItemId, payload });
    },
    archiveItem: async (inventoryItemId) => {
      await archiveMutation.mutateAsync(inventoryItemId);
    },
    isSaving:
      createMutation.isPending || updateMutation.isPending || archiveMutation.isPending,
    isLoading:
      businessUnitsQuery.isLoading ||
      unitsOfMeasureQuery.isLoading ||
      inventoryItemsQuery.isLoading,
    errorMessage:
      (businessUnitsQuery.error instanceof Error && businessUnitsQuery.error.message) ||
      (unitsOfMeasureQuery.error instanceof Error && unitsOfMeasureQuery.error.message) ||
      (inventoryItemsQuery.error instanceof Error && inventoryItemsQuery.error.message) ||
      "",
  };
}
