export type PosProductAlias = {
  id: string;
  business_unit_id: string;
  product_id: string | null;
  source_system: string;
  source_product_key: string;
  source_product_name: string;
  source_sku: string | null;
  source_barcode: string | null;
  status: string;
  mapping_confidence: string;
  occurrence_count: number;
  first_seen_at: string | null;
  last_seen_at: string | null;
  last_import_batch_id: string | null;
  last_import_row_id: string | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
};

export type PosProductAliasApprovalPayload = {
  product_id: string;
  notes?: string | null;
};

export type PosProductAliasBulkApprovalItem = PosProductAliasApprovalPayload & {
  alias_id: string;
};

export type PosProductAliasBulkApprovalPayload = {
  mappings: PosProductAliasBulkApprovalItem[];
};

export type PosProductAliasBulkApprovalResult = {
  updated_count: number;
  aliases: PosProductAlias[];
};

export type PosMappingReadiness = {
  status: "complete" | "partial" | "missing" | "no_data" | string;
  alias_coverage_percent: string;
  row_coverage_percent: string;
  gross_revenue_coverage_percent: string;
  total_alias_count: number;
  mapped_alias_count: number;
  automatic_alias_count: number;
  missing_alias_count: number;
  total_row_count: number;
  mapped_row_count: number;
  automatic_row_count: number;
  missing_row_count: number;
  total_gross_revenue: string;
  mapped_gross_revenue: string;
  automatic_gross_revenue: string;
  missing_gross_revenue: string;
  source_layer: string;
};

export type PosMissingRecipeProduct = {
  product_id: string;
  business_unit_id: string;
  product_name: string;
  category_name: string | null;
  product_type: string;
  sale_price_gross: string | null;
  sale_price_last_seen_at: string | null;
  sale_price_source: string | null;
  alias_count: number;
  occurrence_count: number;
  first_seen_at: string | null;
  last_seen_at: string | null;
  latest_source_product_name: string | null;
  latest_source_system: string | null;
};
