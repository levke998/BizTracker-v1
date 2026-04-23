export type FinancialTransaction = {
  id: string;
  business_unit_id: string;
  direction: string;
  transaction_type: string;
  amount: string;
  currency: string;
  occurred_at: string;
  description: string;
  source_type: string;
  source_id: string;
  created_at: string;
};

export type FinancialTransactionFilters = {
  business_unit_id?: string;
  transaction_type?: string;
  source_type?: string;
  limit?: number;
};
