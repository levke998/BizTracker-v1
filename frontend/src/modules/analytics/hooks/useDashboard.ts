import { useQuery } from "@tanstack/react-query";
import { useState } from "react";

import {
  getDashboardData,
  listDashboardExpenses,
  listDashboardProducts,
} from "../api/analyticsApi";
import type {
  DashboardData,
  DashboardExpenseDetailRow,
  DashboardPeriodPreset,
  DashboardProductDetailRow,
  DashboardScope,
} from "../types/analytics";

export type DashboardDrilldown =
  | { type: "category"; label: string }
  | { type: "expense"; label: string }
  | null;

type DashboardState = {
  dashboard: DashboardData | null;
  productDetails: DashboardProductDetailRow[];
  expenseDetails: DashboardExpenseDetailRow[];
  drilldown: DashboardDrilldown;
  setDrilldown: (value: DashboardDrilldown) => void;
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

  return {
    dashboard: dashboardQuery.data ?? null,
    productDetails: productDetailsQuery.data ?? [],
    expenseDetails: expenseDetailsQuery.data ?? [],
    drilldown,
    setDrilldown,
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
      productDetailsQuery.isLoading || expenseDetailsQuery.isLoading,
    errorMessage:
      (dashboardQuery.error instanceof Error && dashboardQuery.error.message) ||
      (productDetailsQuery.error instanceof Error &&
        productDetailsQuery.error.message) ||
      (expenseDetailsQuery.error instanceof Error &&
        expenseDetailsQuery.error.message) ||
      "",
  };
}
