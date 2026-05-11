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
import { listEventPerformances, listEvents } from "../../events/api/eventsApi";
import type { EventPerformance, EventRecord } from "../../events/types/events";
import type {
  DashboardBasketPairRow,
  DashboardBasketReceipt,
  DashboardBreakdownRow,
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

export type DashboardTopProductRow = DashboardBreakdownRow & {
  category_name?: string;
  previous_revenue?: string;
  revenue_change_percent?: string;
  estimated_unit_cost_net?: string | null;
  estimated_cogs_net?: string | null;
  estimated_net_margin_amount?: string | null;
  estimated_margin_percent?: string | null;
  cost_source?: string;
  margin_status?: string;
};

type DashboardState = {
  dashboard: DashboardData | null;
  basketPairs: DashboardBasketPairRow[];
  basketReceipts: DashboardBasketReceipt[];
  flowEvents: EventRecord[];
  flowEventPerformances: EventPerformance[];
  topProducts: DashboardTopProductRow[];
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
  topProductCategory: string;
  setTopProductCategory: (value: string) => void;
  isLoading: boolean;
  isDrilldownLoading: boolean;
  isTopProductsLoading: boolean;
  isBasketReceiptsLoading: boolean;
  isFlowEventsLoading: boolean;
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
  const [topProductCategory, setTopProductCategory] = useState("all");

  const baseFilters = {
    scope,
    period,
    start_date: period === "custom" ? startDate : undefined,
    end_date: period === "custom" ? endDate : undefined,
  };

  function getPreviousProductFilters() {
    const periodStart = dashboardQuery.data?.period.start_date;
    const periodEnd = dashboardQuery.data?.period.end_date;
    if (!periodStart || !periodEnd) {
      return null;
    }

    const start = new Date(`${periodStart}T00:00:00`);
    const end = new Date(`${periodEnd}T00:00:00`);
    const dayCount = Math.max(
      1,
      Math.round((end.getTime() - start.getTime()) / 86_400_000) + 1,
    );
    const previousEnd = new Date(start);
    previousEnd.setDate(previousEnd.getDate() - 1);
    const previousStart = new Date(previousEnd);
    previousStart.setDate(previousStart.getDate() - dayCount + 1);
    const toDateInput = (value: Date) => value.toISOString().slice(0, 10);

    return {
      scope,
      period: "custom" as const,
      start_date: toDateInput(previousStart),
      end_date: toDateInput(previousEnd),
      category_name: topProductCategory === "all" ? undefined : topProductCategory,
    };
  }

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

  const topProductsQuery = useQuery({
    queryKey: [
      "analytics-dashboard-top-products",
      scope,
      period,
      startDate,
      endDate,
      topProductCategory,
    ],
    queryFn: () =>
      listDashboardProducts({
        ...baseFilters,
        category_name: topProductCategory === "all" ? undefined : topProductCategory,
      }),
    enabled: period !== "custom" || (Boolean(startDate) && Boolean(endDate)),
  });

  const previousTopProductsQuery = useQuery({
    queryKey: [
      "analytics-dashboard-top-products-previous",
      scope,
      dashboardQuery.data?.period.start_date ?? "",
      dashboardQuery.data?.period.end_date ?? "",
      topProductCategory,
    ],
    queryFn: () => {
      const previousFilters = getPreviousProductFilters();
      if (!previousFilters) {
        return [];
      }
      return listDashboardProducts(previousFilters);
    },
    enabled:
      Boolean(dashboardQuery.data) &&
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
  const flowEventPerformancesQuery = useQuery({
    queryKey: [
      "analytics-dashboard-flow-event-performances",
      scope,
      dashboardQuery.data?.business_unit_id ?? "",
      dashboardQuery.data?.period.start_date ?? "",
      dashboardQuery.data?.period.end_date ?? "",
    ],
    queryFn: () =>
      listEventPerformances({
        business_unit_id: dashboardQuery.data?.business_unit_id ?? undefined,
        starts_from: dashboardQuery.data
          ? `${dashboardQuery.data.period.start_date}T00:00:00`
          : undefined,
        starts_to: dashboardQuery.data
          ? `${dashboardQuery.data.period.end_date}T23:59:59`
          : undefined,
        limit: 100,
      }),
    enabled:
      scope === "flow" &&
      Boolean(dashboardQuery.data?.business_unit_id) &&
      (period !== "custom" || (Boolean(startDate) && Boolean(endDate))),
  });
  const flowEventsQuery = useQuery({
    queryKey: [
      "analytics-dashboard-flow-events",
      scope,
      dashboardQuery.data?.business_unit_id ?? "",
      dashboardQuery.data?.period.start_date ?? "",
      dashboardQuery.data?.period.end_date ?? "",
    ],
    queryFn: () =>
      listEvents({
        business_unit_id: dashboardQuery.data?.business_unit_id ?? undefined,
        starts_from: dashboardQuery.data
          ? `${dashboardQuery.data.period.start_date}T00:00:00`
          : undefined,
        starts_to: dashboardQuery.data
          ? `${dashboardQuery.data.period.end_date}T23:59:59`
          : undefined,
        limit: 100,
      }),
    enabled:
      scope === "flow" &&
      Boolean(dashboardQuery.data?.business_unit_id) &&
      (period !== "custom" || (Boolean(startDate) && Boolean(endDate))),
  });

  return {
    dashboard: dashboardQuery.data ?? null,
    basketPairs: basketPairsQuery.data ?? [],
    basketReceipts: basketReceiptsQuery.data ?? [],
    flowEvents: flowEventsQuery.data ?? [],
    flowEventPerformances: flowEventPerformancesQuery.data ?? [],
    topProducts: (topProductsQuery.data ?? []).map((row) => {
      const previousRow = (previousTopProductsQuery.data ?? []).find(
        (item) =>
          item.product_name === row.product_name &&
          item.category_name === row.category_name,
      );
      const previousRevenue = previousRow?.revenue ?? "0";
      const currentRevenue = Number(row.revenue);
      const previousRevenueNumber = Number(previousRevenue);
      const revenueChangePercent =
        Number.isFinite(previousRevenueNumber) && previousRevenueNumber > 0
          ? ((currentRevenue - previousRevenueNumber) / previousRevenueNumber) * 100
          : currentRevenue > 0
            ? 100
            : 0;

      return {
        label: row.product_name,
        category_name: row.category_name,
        revenue: row.revenue,
        net_revenue: row.net_revenue,
        vat_amount: row.vat_amount,
        quantity: row.quantity,
        transaction_count: row.transaction_count,
        source_layer: row.source_layer,
        amount_basis: row.amount_basis,
        tax_breakdown_source: row.tax_breakdown_source,
        estimated_unit_cost_net: row.estimated_unit_cost_net,
        estimated_cogs_net: row.estimated_cogs_net,
        estimated_net_margin_amount: row.estimated_net_margin_amount,
        estimated_margin_percent: row.estimated_margin_percent,
        cost_source: row.cost_source,
        margin_status: row.margin_status,
        previous_revenue: previousRevenue,
        revenue_change_percent: String(revenueChangePercent),
      };
    }),
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
    topProductCategory,
    setTopProductCategory,
    isLoading: dashboardQuery.isLoading,
    isDrilldownLoading:
      productDetailsQuery.isLoading ||
      productSourceRowsQuery.isLoading ||
      expenseSourceQuery.isLoading ||
      basketReceiptsQuery.isLoading ||
      expenseDetailsQuery.isLoading,
    isTopProductsLoading:
      topProductsQuery.isLoading || previousTopProductsQuery.isLoading,
    isBasketReceiptsLoading: basketReceiptsQuery.isLoading,
    isFlowEventsLoading:
      flowEventPerformancesQuery.isLoading || flowEventsQuery.isLoading,
    errorMessage:
      (dashboardQuery.error instanceof Error && dashboardQuery.error.message) ||
      (flowEventsQuery.error instanceof Error &&
        flowEventsQuery.error.message) ||
      (flowEventPerformancesQuery.error instanceof Error &&
        flowEventPerformancesQuery.error.message) ||
      (productDetailsQuery.error instanceof Error &&
        productDetailsQuery.error.message) ||
      (productSourceRowsQuery.error instanceof Error &&
        productSourceRowsQuery.error.message) ||
      (topProductsQuery.error instanceof Error &&
        topProductsQuery.error.message) ||
      (previousTopProductsQuery.error instanceof Error &&
        previousTopProductsQuery.error.message) ||
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
