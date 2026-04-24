import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";

import { listInventoryItems } from "../../inventory/api/inventoryApi";
import type { InventoryItem } from "../../inventory/types/inventory";
import {
  listBusinessUnits,
  listUnitsOfMeasure,
} from "../../masterData/api/masterDataApi";
import type { BusinessUnit, UnitOfMeasure } from "../../masterData/types/masterData";
import {
  createPurchaseInvoice,
  listPurchaseInvoices,
  listSuppliers,
  postPurchaseInvoice,
} from "../api/procurementApi";
import type {
  PurchaseInvoiceCreatePayload,
  PurchaseInvoicePostingResult,
} from "../types/procurement";

type PurchaseInvoicesState = {
  primaryBusinessUnits: BusinessUnit[];
  technicalBusinessUnits: BusinessUnit[];
  suppliers: Awaited<ReturnType<typeof listSuppliers>>;
  inventoryItems: InventoryItem[];
  unitsOfMeasure: UnitOfMeasure[];
  invoices: Awaited<ReturnType<typeof listPurchaseInvoices>>;
  selectedBusinessUnitId: string;
  setSelectedBusinessUnitId: (value: string) => void;
  selectedSupplierId: string;
  setSelectedSupplierId: (value: string) => void;
  limit: number;
  setLimit: (value: number) => void;
  createPurchaseInvoice: (payload: PurchaseInvoiceCreatePayload) => Promise<void>;
  postPurchaseInvoice: (invoiceId: string) => Promise<PurchaseInvoicePostingResult>;
  isSaving: boolean;
  isPosting: boolean;
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

export function usePurchaseInvoices(): PurchaseInvoicesState {
  const queryClient = useQueryClient();
  const [selectedBusinessUnitId, setSelectedBusinessUnitId] = useState("");
  const [selectedSupplierId, setSelectedSupplierId] = useState("");
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
    queryKey: ["procurement-form-suppliers", effectiveBusinessUnitId],
    queryFn: () =>
      listSuppliers({
        business_unit_id: effectiveBusinessUnitId,
        is_active: true,
        limit: 200,
      }),
    enabled: Boolean(effectiveBusinessUnitId),
  });

  const inventoryItemsQuery = useQuery({
    queryKey: ["procurement-form-inventory-items", effectiveBusinessUnitId],
    queryFn: () =>
      listInventoryItems({
        business_unit_id: effectiveBusinessUnitId,
        limit: 200,
      }),
    enabled: Boolean(effectiveBusinessUnitId),
  });

  const unitsOfMeasureQuery = useQuery({
    queryKey: ["units-of-measure"],
    queryFn: listUnitsOfMeasure,
  });

  const invoicesQuery = useQuery({
    queryKey: [
      "procurement-purchase-invoices",
      effectiveBusinessUnitId,
      selectedSupplierId,
      limit,
    ],
    queryFn: () =>
      listPurchaseInvoices({
        business_unit_id: effectiveBusinessUnitId,
        supplier_id: selectedSupplierId || undefined,
        limit,
      }),
    enabled: Boolean(effectiveBusinessUnitId),
  });

  const createMutation = useMutation({
    mutationFn: (payload: PurchaseInvoiceCreatePayload) => createPurchaseInvoice(payload),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["procurement-purchase-invoices"] });
    },
  });

  const postMutation = useMutation({
    mutationFn: (invoiceId: string) => postPurchaseInvoice(invoiceId),
    onSuccess: async () => {
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ["procurement-purchase-invoices"] }),
        queryClient.invalidateQueries({ queryKey: ["inventory-movements"] }),
        queryClient.invalidateQueries({ queryKey: ["inventory-stock-levels"] }),
        queryClient.invalidateQueries({ queryKey: ["finance-transactions"] }),
      ]);
    },
  });

  return {
    primaryBusinessUnits,
    technicalBusinessUnits,
    suppliers: suppliersQuery.data ?? [],
    inventoryItems: inventoryItemsQuery.data ?? [],
    unitsOfMeasure: unitsOfMeasureQuery.data ?? [],
    invoices: invoicesQuery.data ?? [],
    selectedBusinessUnitId: effectiveBusinessUnitId,
    setSelectedBusinessUnitId,
    selectedSupplierId,
    setSelectedSupplierId,
    limit,
    setLimit,
    createPurchaseInvoice: async (payload) => {
      await createMutation.mutateAsync(payload);
    },
    postPurchaseInvoice: postMutation.mutateAsync,
    isSaving: createMutation.isPending,
    isPosting: postMutation.isPending,
    isLoading:
      businessUnitsQuery.isLoading ||
      suppliersQuery.isLoading ||
      inventoryItemsQuery.isLoading ||
      unitsOfMeasureQuery.isLoading ||
      invoicesQuery.isLoading,
    errorMessage:
      (businessUnitsQuery.error instanceof Error && businessUnitsQuery.error.message) ||
      (suppliersQuery.error instanceof Error && suppliersQuery.error.message) ||
      (inventoryItemsQuery.error instanceof Error && inventoryItemsQuery.error.message) ||
      (unitsOfMeasureQuery.error instanceof Error &&
        unitsOfMeasureQuery.error.message) ||
      (invoicesQuery.error instanceof Error && invoicesQuery.error.message) ||
      (createMutation.error instanceof Error && createMutation.error.message) ||
      (postMutation.error instanceof Error && postMutation.error.message) ||
      "",
  };
}
