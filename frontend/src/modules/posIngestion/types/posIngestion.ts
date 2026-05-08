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
