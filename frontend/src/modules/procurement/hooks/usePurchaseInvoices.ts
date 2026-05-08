import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useMemo, useState } from "react";

import { createInventoryItem, listInventoryItems } from "../../inventory/api/inventoryApi";
import type { InventoryItem, InventoryItemCreatePayload } from "../../inventory/types/inventory";
import {
  listBusinessUnits,
  listUnitsOfMeasure,
  listVatRates,
} from "../../masterData/api/masterDataApi";
import type { BusinessUnit, UnitOfMeasure, VatRate } from "../../masterData/types/masterData";
import {
  approveSupplierItemAliasMapping,
  createPurchaseInvoice,
  createPurchaseInvoiceFromPdfReview,
  listSupplierItemAliases,
  listPurchaseInvoicePdfDrafts,
  listPurchaseInvoices,
  listSuppliers,
  postPurchaseInvoice,
  updatePurchaseInvoicePdfReview,
  uploadPurchaseInvoicePdfDraft,
} from "../api/procurementApi";
import type {
  PurchaseInvoiceCreatePayload,
  PurchaseInvoicePdfDraft,
  PurchaseInvoicePdfReviewUpdatePayload,
  PurchaseInvoicePostingResult,
  SupplierItemAlias,
  SupplierItemAliasMappingPayload,
} from "../types/procurement";

type PurchaseInvoicesState = {
  primaryBusinessUnits: BusinessUnit[];
  technicalBusinessUnits: BusinessUnit[];
  suppliers: Awaited<ReturnType<typeof listSuppliers>>;
  inventoryItems: InventoryItem[];
  unitsOfMeasure: UnitOfMeasure[];
  vatRates: VatRate[];
  invoices: Awaited<ReturnType<typeof listPurchaseInvoices>>;
  pdfDrafts: PurchaseInvoicePdfDraft[];
  supplierItemAliases: SupplierItemAlias[];
  selectedBusinessUnitId: string;
  setSelectedBusinessUnitId: (value: string) => void;
  selectedSupplierId: string;
  setSelectedSupplierId: (value: string) => void;
  limit: number;
  setLimit: (value: number) => void;
  createPurchaseInvoice: (payload: PurchaseInvoiceCreatePayload) => Promise<void>;
  createPurchaseInvoiceFromPdfReview: (draftId: string) => Promise<void>;
  createInventoryItemFromPdfReview: (
    payload: InventoryItemCreatePayload,
  ) => Promise<InventoryItem>;
  postPurchaseInvoice: (invoiceId: string) => Promise<PurchaseInvoicePostingResult>;
  uploadPurchaseInvoicePdfDraft: (file: File, supplierId?: string) => Promise<PurchaseInvoicePdfDraft>;
  updatePurchaseInvoicePdfReview: (
    draftId: string,
    payload: PurchaseInvoicePdfReviewUpdatePayload,
  ) => Promise<PurchaseInvoicePdfDraft>;
  approveSupplierItemAliasMapping: (
    aliasId: string,
    payload: SupplierItemAliasMappingPayload,
  ) => Promise<SupplierItemAlias>;
  isSaving: boolean;
  isPosting: boolean;
  isUploadingPdfDraft: boolean;
  isUpdatingPdfReview: boolean;
  isApprovingSupplierAlias: boolean;
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
    useMemo(() => splitBusinessUnits(businessUnits), [businessUnits]);

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

  const vatRatesQuery = useQuery({
    queryKey: ["vat-rates"],
    queryFn: listVatRates,
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

  const pdfDraftsQuery = useQuery({
    queryKey: ["procurement-purchase-invoice-pdf-drafts", effectiveBusinessUnitId, limit],
    queryFn: () =>
      listPurchaseInvoicePdfDrafts({
        business_unit_id: effectiveBusinessUnitId,
        limit,
      }),
    enabled: Boolean(effectiveBusinessUnitId),
  });

  const supplierItemAliasesQuery = useQuery({
    queryKey: [
      "procurement-supplier-item-aliases",
      effectiveBusinessUnitId,
      selectedSupplierId,
      limit,
    ],
    queryFn: () =>
      listSupplierItemAliases({
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

  const pdfReviewCreateInvoiceMutation = useMutation({
    mutationFn: (draftId: string) => createPurchaseInvoiceFromPdfReview(draftId),
    onSuccess: async () => {
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ["procurement-purchase-invoices"] }),
        queryClient.invalidateQueries({
          queryKey: ["procurement-purchase-invoice-pdf-drafts"],
        }),
      ]);
    },
  });

  const reviewInventoryItemMutation = useMutation({
    mutationFn: (payload: InventoryItemCreatePayload) => createInventoryItem(payload),
    onSuccess: async () => {
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ["procurement-form-inventory-items"] }),
        queryClient.invalidateQueries({ queryKey: ["inventory-items"] }),
        queryClient.invalidateQueries({ queryKey: ["inventory-stock-levels"] }),
      ]);
    },
  });

  const pdfDraftUploadMutation = useMutation({
    mutationFn: ({ file, supplierId }: { file: File; supplierId?: string }) =>
      uploadPurchaseInvoicePdfDraft(effectiveBusinessUnitId, file, supplierId),
    onSuccess: async () => {
      await queryClient.invalidateQueries({
        queryKey: ["procurement-purchase-invoice-pdf-drafts"],
      });
    },
  });

  const pdfReviewMutation = useMutation({
    mutationFn: ({
      draftId,
      payload,
    }: {
      draftId: string;
      payload: PurchaseInvoicePdfReviewUpdatePayload;
    }) => updatePurchaseInvoicePdfReview(draftId, payload),
    onSuccess: async () => {
      await queryClient.invalidateQueries({
        queryKey: ["procurement-purchase-invoice-pdf-drafts"],
      });
    },
  });

  const supplierAliasMappingMutation = useMutation({
    mutationFn: ({
      aliasId,
      payload,
    }: {
      aliasId: string;
      payload: SupplierItemAliasMappingPayload;
    }) => approveSupplierItemAliasMapping(aliasId, payload),
    onSuccess: async () => {
      await queryClient.invalidateQueries({
        queryKey: ["procurement-supplier-item-aliases"],
      });
    },
  });

  return {
    primaryBusinessUnits,
    technicalBusinessUnits,
    suppliers: suppliersQuery.data ?? [],
    inventoryItems: inventoryItemsQuery.data ?? [],
    unitsOfMeasure: unitsOfMeasureQuery.data ?? [],
    vatRates: vatRatesQuery.data ?? [],
    invoices: invoicesQuery.data ?? [],
    pdfDrafts: pdfDraftsQuery.data ?? [],
    supplierItemAliases: supplierItemAliasesQuery.data ?? [],
    selectedBusinessUnitId: effectiveBusinessUnitId,
    setSelectedBusinessUnitId,
    selectedSupplierId,
    setSelectedSupplierId,
    limit,
    setLimit,
    createPurchaseInvoice: async (payload) => {
      await createMutation.mutateAsync(payload);
    },
    createPurchaseInvoiceFromPdfReview: async (draftId) => {
      await pdfReviewCreateInvoiceMutation.mutateAsync(draftId);
    },
    createInventoryItemFromPdfReview: (payload) =>
      reviewInventoryItemMutation.mutateAsync(payload),
    postPurchaseInvoice: postMutation.mutateAsync,
    uploadPurchaseInvoicePdfDraft: (file, supplierId) =>
      pdfDraftUploadMutation.mutateAsync({ file, supplierId }),
    updatePurchaseInvoicePdfReview: (draftId, payload) =>
      pdfReviewMutation.mutateAsync({ draftId, payload }),
    approveSupplierItemAliasMapping: (aliasId, payload) =>
      supplierAliasMappingMutation.mutateAsync({ aliasId, payload }),
    isSaving:
      createMutation.isPending ||
      pdfReviewCreateInvoiceMutation.isPending ||
      reviewInventoryItemMutation.isPending,
    isPosting: postMutation.isPending,
    isUploadingPdfDraft: pdfDraftUploadMutation.isPending,
    isUpdatingPdfReview: pdfReviewMutation.isPending,
    isApprovingSupplierAlias: supplierAliasMappingMutation.isPending,
    isLoading:
      businessUnitsQuery.isLoading ||
      suppliersQuery.isLoading ||
      inventoryItemsQuery.isLoading ||
      unitsOfMeasureQuery.isLoading ||
      vatRatesQuery.isLoading ||
      invoicesQuery.isLoading ||
      pdfDraftsQuery.isLoading ||
      supplierItemAliasesQuery.isLoading,
    errorMessage:
      (businessUnitsQuery.error instanceof Error && businessUnitsQuery.error.message) ||
      (suppliersQuery.error instanceof Error && suppliersQuery.error.message) ||
      (inventoryItemsQuery.error instanceof Error && inventoryItemsQuery.error.message) ||
      (unitsOfMeasureQuery.error instanceof Error &&
        unitsOfMeasureQuery.error.message) ||
      (vatRatesQuery.error instanceof Error && vatRatesQuery.error.message) ||
      (invoicesQuery.error instanceof Error && invoicesQuery.error.message) ||
      (pdfDraftsQuery.error instanceof Error && pdfDraftsQuery.error.message) ||
      (supplierItemAliasesQuery.error instanceof Error &&
        supplierItemAliasesQuery.error.message) ||
      (createMutation.error instanceof Error && createMutation.error.message) ||
      (pdfReviewCreateInvoiceMutation.error instanceof Error &&
        pdfReviewCreateInvoiceMutation.error.message) ||
      (reviewInventoryItemMutation.error instanceof Error &&
        reviewInventoryItemMutation.error.message) ||
      (postMutation.error instanceof Error && postMutation.error.message) ||
      (pdfDraftUploadMutation.error instanceof Error &&
        pdfDraftUploadMutation.error.message) ||
      (pdfReviewMutation.error instanceof Error && pdfReviewMutation.error.message) ||
      (supplierAliasMappingMutation.error instanceof Error &&
        supplierAliasMappingMutation.error.message) ||
      "",
  };
}
