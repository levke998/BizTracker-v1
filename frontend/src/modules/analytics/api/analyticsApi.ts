import { apiGet } from "../../../services/api/client";
import type {
  DashboardBreakdownRow,
  DashboardData,
  DashboardExpenseDetailRow,
  DashboardFilters,
  DashboardProductDetailRow,
} from "../types/analytics";

export function getDashboardData(filters: DashboardFilters) {
  return apiGet<DashboardData>("analytics/dashboard", filters);
}

export function listDashboardCategories(filters: DashboardFilters) {
  return apiGet<DashboardBreakdownRow[]>("analytics/dashboard/categories", filters);
}

export function listDashboardProducts(
  filters: DashboardFilters & { category_name?: string },
) {
  return apiGet<DashboardProductDetailRow[]>("analytics/dashboard/products", filters);
}

export function listDashboardExpenses(
  filters: DashboardFilters & { transaction_type?: string },
) {
  return apiGet<DashboardExpenseDetailRow[]>("analytics/dashboard/expenses", filters);
}
