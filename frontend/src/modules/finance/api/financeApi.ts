import { apiGet } from "../../../services/api/client";
import type { FinancialTransaction, FinancialTransactionFilters } from "../types/finance";

export function listFinancialTransactions(filters: FinancialTransactionFilters) {
  return apiGet<FinancialTransaction[]>("finance/transactions", filters);
}
