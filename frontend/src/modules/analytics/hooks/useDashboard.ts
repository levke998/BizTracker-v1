import { useQuery } from "@tanstack/react-query";
import { useState } from "react";

import {
  getDashboardExpenseSource,
  getDashboardData,
  listDashboardBasketPairReceipts,
  listDashboardBasketPairs,
  listDashboardExpenses,
  listDashboardProductRows,
  listDashboardProducts,
} from "../api/analyticsApi";
import type {
  DashboardBasketPairRow,
  DashboardBasketReceipt,
  DashboardData,
  DashboardExpenseDetailRow,
  DashboardExpenseSource,
  DashboardPeriodPreset,
  DashboardPosSourceRow,
  DashboardProductDetailRow,
  DashboardScope,
} from "../types/analytics";

export type DashboardDrilldown =
  | { type: "category"; label: string }
  | { type: "expense"; label: string }
  | null;

type DashboardState = {
  dashboard: DashboardData | null;
  basketPairs: DashboardBasketPairRow[];
  basketReceipts: DashboardBasketReceipt[];
  productDetails: DashboardProductDetailRow[];
  productSourceRows: DashboardPosSourceRow[];
  expenseDetails: DashboardExpenseDetailRow[];
  expenseSource: DashboardExpenseSource | null;
  drilldown: DashboardDrilldown;
  setDrilldown: (value: DashboardDrilldown) => void;
  selectedProduct: DashboardProductDetailRow | null;
  setSelectedProduct: (value: DashboardProductDetailRow | null) => void;
  selectedExpense: DashboardExpenseDetailRow | null;
  setSelectedExpense: (value: DashboardExpenseDetailRow | null) => void;
  selectedBasketPair: DashboardBasketPairRow | null;
  setSelectedBasketPair: (value: DashboardBasketPairRow | null) => void;
  scope: DashboardScope;
  setScope: (value: DashboardScope) => void;
  period: DashboardPeriodPreset;
  setPeriod: (value: DashboardPeriodPreset) => void;
  startDate: string;
  setStartDate: (value: string) => void;
  endDate: string;
  setEndDate: (value: string) => void;
  isLoading: boolean;
  isDrilldownLoading: boolean;
  errorMessage: string;
};

export function useDashboard(): DashboardState {
  const [scope, setScope] = useState<DashboardScope>("overall");
  const [period, setPeriod] = useState<DashboardPeriodPreset>("last_30_days");
  const [startDate, setStartDate] = useState("");
  const [endDate, setEndDate] = useState("");
  const [drilldown, setDrilldown] = useState<DashboardDrilldown>(null);
  const [selectedProduct, setSelectedProduct] =
    useState<DashboardProductDetailRow | null>(null);
  const [selectedExpense, setSelectedExpense] =
    useState<DashboardExpenseDetailRow | null>(null);
  const [selectedBasketPair, setSelectedBasketPair] =
    useState<DashboardBasketPairRow | null>(null);

  const baseFilters = {
    scope,
    period,
    start_date: period === "custom" ? startDate : undefined,
    end_date: period === "custom" ? endDate : undefined,
  };

  const dashboardQuery = useQuery({
    queryKey: ["analytics-dashboard", scope, period, startDate, endDate],
    queryFn: () =>
      getDashboardData(baseFilters),
    enabled: period !== "custom" || (Boolean(startDate) && Boolean(endDate)),
  });

  const productDetailsQuery = useQuery({
    queryKey: [
      "analytics-dashboard-products",
      scope,
      period,
      startDate,
      endDate,
      drilldown?.type === "category" ? drilldown.label : "",
    ],
    queryFn: () =>
      listDashboardProducts({
        ...baseFilters,
        category_name: drilldown?.type === "category" ? drilldown.label : undefined,
      }),
    enabled:
      drilldown?.type === "category" &&
      (period !== "custom" || (Boolean(startDate) && Boolean(endDate))),
  });

  const expenseDetailsQuery = useQuery({
    queryKey: [
      "analytics-dashboard-expenses",
      scope,
      period,
      startDate,
      endDate,
      drilldown?.type === "expense" ? drilldown.label : "",
    ],
    queryFn: () =>
      listDashboardExpenses({
        ...baseFilters,
        transaction_type: drilldown?.type === "expense" ? drilldown.label : undefined,
      }),
    enabled:
      drilldown?.type === "expense" &&
      (period !== "custom" || (Boolean(startDate) && Boolean(endDate))),
  });

  const productSourceRowsQuery = useQuery({
    queryKey: [
      "analytics-dashboard-product-source-rows",
      scope,
      period,
      startDate,
      endDate,
      selectedProduct?.product_name ?? "",
      selectedProduct?.category_name ?? "",
    ],
    queryFn: () =>
      listDashboardProductRows({
        ...baseFilters,
        product_name: selectedProduct?.product_name ?? "",
        category_name: selectedProduct?.category_name,
        limit: 50,
      }),
    enabled:
      drilldown?.type === "category" &&
      selectedProduct !== null &&
      (period !== "custom" || (Boolean(startDate) && Boolean(endDate))),
  });

  const expenseSourceQuery = useQuery({
    queryKey: [
      "analytics-dashboard-expense-source",
      selectedExpense?.transaction_id ?? "",
    ],
    queryFn: () => getDashboardExpenseSource(selectedExpense?.transaction_id ?? ""),
    enabled: drilldown?.type === "expense" && selectedExpense !== null,
  });

  const basketPairsQuery = useQuery({
    queryKey: ["analytics-dashboard-basket-pairs", scope, period, startDate, endDate],
    queryFn: () => listDashboardBasketPairs({ ...baseFilters, limit: 8 }),
    enabled: period !== "custom" || (Boolean(startDate) && Boolean(endDate)),
  });

  const basketReceiptsQuery = useQuery({
    queryKey: [
      "analytics-dashboard-basket-pair-receipts",
      scope,
      period,
      startDate,
      endDate,
      selectedBasketPair?.product_a ?? "",
      selectedBasketPair?.product_b ?? "",
    ],
    queryFn: () =>
      listDashboardBasketPairReceipts({
        ...baseFilters,
        product_a: selectedBasketPair?.product_a ?? "",
        product_b: selectedBasketPair?.product_b ?? "",
        limit: 20,
      }),
    enabled:
      selectedBasketPair !== null &&
      (period !== "custom" || (Boolean(startDate) && Boolean(endDate))),
  });

  return {
    dashboard: dashboardQuery.data ?? null,
    basketPairs: basketPairsQuery.data ?? [],
    basketReceipts: basketReceiptsQuery.data ?? [],
    productDetails: productDetailsQuery.data ?? [],
    productSourceRows: productSourceRowsQuery.data ?? [],
    expenseDetails: expenseDetailsQuery.data ?? [],
    expenseSource: expenseSourceQuery.data ?? null,
    drilldown,
    setDrilldown,
    selectedProduct,
    setSelectedProduct,
    selectedExpense,
    setSelectedExpense,
    selectedBasketPair,
    setSelectedBasketPair,
    scope,
    setScope,
    period,
    setPeriod,
    startDate,
    setStartDate,
    endDate,
    setEndDate,
    isLoading: dashboardQuery.isLoading,
    isDrilldownLoading:
      productDetailsQuery.isLoading ||
      productSourceRowsQuery.isLoading ||
      expenseSourceQuery.isLoading ||
      basketReceiptsQuery.isLoading ||
      expenseDetailsQuery.isLoading,
    errorMessage:
      (dashboardQuery.error instanceof Error && dashboardQuery.error.message) ||
      (productDetailsQuery.error instanceof Error &&
        productDetailsQuery.error.message) ||
      (productSourceRowsQuery.error instanceof Error &&
        productSourceRowsQuery.error.message) ||
      (expenseDetailsQuery.error instanceof Error &&
        expenseDetailsQuery.error.message) ||
      (expenseSourceQuery.error instanceof Error &&
        expenseSourceQuery.error.message) ||
      (basketPairsQuery.error instanceof Error &&
        basketPairsQuery.error.message) ||
      (basketReceiptsQuery.error instanceof Error &&
        basketReceiptsQuery.error.message) ||
      "",
  };
}
