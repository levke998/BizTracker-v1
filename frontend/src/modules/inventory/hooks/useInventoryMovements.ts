import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";

import { listBusinessUnits } from "../../masterData/api/masterDataApi";
import type { BusinessUnit } from "../../masterData/types/masterData";
import {
  createInventoryMovement,
  listInventoryItems,
  listInventoryMovements,
} from "../api/inventoryApi";
import type {
  InventoryItem,
  InventoryMovementCreatePayload,
} from "../types/inventory";

type InventoryMovementsState = {
  businessUnits: BusinessUnit[];
  primaryBusinessUnits: BusinessUnit[];
  technicalBusinessUnits: BusinessUnit[];
  inventoryItems: InventoryItem[];
  movements: Awaited<ReturnType<typeof listInventoryMovements>>;
  selectedBusinessUnitId: string;
  setSelectedBusinessUnitId: (value: string) => void;
  selectedMovementType: string;
  setSelectedMovementType: (value: string) => void;
  limit: number;
  setLimit: (value: number) => void;
  createMovement: (payload: InventoryMovementCreatePayload) => Promise<void>;
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

export function useInventoryMovements(): InventoryMovementsState {
  const queryClient = useQueryClient();
  const [selectedBusinessUnitId, setSelectedBusinessUnitId] = useState("");
  const [selectedMovementType, setSelectedMovementType] = useState("");
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

  const inventoryMovementsQuery = useQuery({
    queryKey: [
      "inventory-movements",
      effectiveBusinessUnitId,
      selectedMovementType,
      limit,
    ],
    queryFn: () =>
      listInventoryMovements({
        business_unit_id: effectiveBusinessUnitId,
        movement_type: selectedMovementType,
        limit,
      }),
    enabled: Boolean(effectiveBusinessUnitId),
  });

  const inventoryItemsQuery = useQuery({
    queryKey: ["inventory-movement-form-items", effectiveBusinessUnitId],
    queryFn: () =>
      listInventoryItems({
        business_unit_id: effectiveBusinessUnitId,
        limit: 200,
      }),
    enabled: Boolean(effectiveBusinessUnitId),
  });

  const refreshInventoryQueries = async () => {
    await Promise.all([
      queryClient.invalidateQueries({ queryKey: ["inventory-movements"] }),
      queryClient.invalidateQueries({ queryKey: ["inventory-stock-levels"] }),
      queryClient.invalidateQueries({ queryKey: ["inventory-theoretical-stock"] }),
      queryClient.invalidateQueries({ queryKey: ["inventory-overview-movements"] }),
      queryClient.invalidateQueries({ queryKey: ["inventory-overview-stock-levels"] }),
    ]);
  };

  const createMutation = useMutation({
    mutationFn: (payload: InventoryMovementCreatePayload) => createInventoryMovement(payload),
    onSuccess: refreshInventoryQueries,
  });

  return {
    businessUnits,
    primaryBusinessUnits,
    technicalBusinessUnits,
    inventoryItems: inventoryItemsQuery.data ?? [],
    movements: inventoryMovementsQuery.data ?? [],
    selectedBusinessUnitId: effectiveBusinessUnitId,
    setSelectedBusinessUnitId,
    selectedMovementType,
    setSelectedMovementType,
    limit,
    setLimit,
    createMovement: async (payload) => {
      await createMutation.mutateAsync(payload);
    },
    isSaving: createMutation.isPending,
    isLoading:
      businessUnitsQuery.isLoading ||
      inventoryItemsQuery.isLoading ||
      inventoryMovementsQuery.isLoading,
    errorMessage:
      (businessUnitsQuery.error instanceof Error && businessUnitsQuery.error.message) ||
      (inventoryItemsQuery.error instanceof Error && inventoryItemsQuery.error.message) ||
      (inventoryMovementsQuery.error instanceof Error &&
        inventoryMovementsQuery.error.message) ||
      (createMutation.error instanceof Error && createMutation.error.message) ||
      "",
  };
}
