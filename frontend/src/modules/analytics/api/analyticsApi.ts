import { apiGet } from "../../../services/api/client";
import type {
  DashboardBasketPairRow,
  DashboardBasketReceipt,
  DashboardBreakdownRow,
  DashboardData,
  DashboardExpenseDetailRow,
  DashboardExpenseSource,
  DashboardFilters,
  DashboardPosSourceRow,
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

export function listDashboardProductRows(
  filters: DashboardFilters & {
    product_name: string;
    category_name?: string;
    limit?: number;
  },
) {
  return apiGet<DashboardPosSourceRow[]>(
    "analytics/dashboard/product-rows",
    filters,
  );
}

export function listDashboardExpenses(
  filters: DashboardFilters & { transaction_type?: string },
) {
  return apiGet<DashboardExpenseDetailRow[]>("analytics/dashboard/expenses", filters);
}

export function getDashboardExpenseSource(transactionId: string) {
  return apiGet<DashboardExpenseSource>("analytics/dashboard/expense-source", {
    transaction_id: transactionId,
  });
}

export function listDashboardBasketPairs(
  filters: DashboardFilters & { limit?: number },
) {
  return apiGet<DashboardBasketPairRow[]>(
    "analytics/dashboard/basket-pairs",
    filters,
  );
}

export function listDashboardBasketPairReceipts(
  filters: DashboardFilters & {
    product_a: string;
    product_b: string;
    limit?: number;
  },
) {
  return apiGet<DashboardBasketReceipt[]>(
    "analytics/dashboard/basket-pair-receipts",
    filters,
  );
}
