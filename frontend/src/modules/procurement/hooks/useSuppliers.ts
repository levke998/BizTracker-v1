import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";

import {
  listBusinessUnits,
} from "../../masterData/api/masterDataApi";
import type { BusinessUnit } from "../../masterData/types/masterData";
import { createSupplier, listSuppliers } from "../api/procurementApi";
import type { SupplierCreatePayload } from "../types/procurement";

type SuppliersState = {
  primaryBusinessUnits: BusinessUnit[];
  technicalBusinessUnits: BusinessUnit[];
  suppliers: Awaited<ReturnType<typeof listSuppliers>>;
  selectedBusinessUnitId: string;
  setSelectedBusinessUnitId: (value: string) => void;
  selectedStatus: string;
  setSelectedStatus: (value: string) => void;
  limit: number;
  setLimit: (value: number) => void;
  createSupplier: (payload: SupplierCreatePayload) => Promise<void>;
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

function mapSelectedStatus(value: string): boolean | undefined {
  if (value === "active") {
    return true;
  }
  if (value === "inactive") {
    return false;
  }
  return undefined;
}

export function useSuppliers(): SuppliersState {
  const queryClient = useQueryClient();
  const [selectedBusinessUnitId, setSelectedBusinessUnitId] = useState("");
  const [selectedStatus, setSelectedStatus] = useState("active");
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

  const suppliersQuery = useQuery({
    queryKey: ["procurement-suppliers", effectiveBusinessUnitId, selectedStatus, limit],
    queryFn: () =>
      listSuppliers({
        business_unit_id: effectiveBusinessUnitId,
        is_active: mapSelectedStatus(selectedStatus),
        limit,
      }),
    enabled: Boolean(effectiveBusinessUnitId),
  });

  const createSupplierMutation = useMutation({
    mutationFn: (payload: SupplierCreatePayload) => createSupplier(payload),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["procurement-suppliers"] });
    },
  });

  return {
    primaryBusinessUnits,
    technicalBusinessUnits,
    suppliers: suppliersQuery.data ?? [],
    selectedBusinessUnitId: effectiveBusinessUnitId,
    setSelectedBusinessUnitId,
    selectedStatus,
    setSelectedStatus,
    limit,
    setLimit,
    createSupplier: async (payload) => {
      await createSupplierMutation.mutateAsync(payload);
    },
    isSaving: createSupplierMutation.isPending,
    isLoading: businessUnitsQuery.isLoading || suppliersQuery.isLoading,
    errorMessage:
      (businessUnitsQuery.error instanceof Error && businessUnitsQuery.error.message) ||
      (suppliersQuery.error instanceof Error && suppliersQuery.error.message) ||
      (createSupplierMutation.error instanceof Error &&
        createSupplierMutation.error.message) ||
      "",
  };
}
