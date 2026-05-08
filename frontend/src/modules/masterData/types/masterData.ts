export type BusinessUnit = {
  id: string;
  code: string;
  name: string;
  type: string;
  is_active: boolean;
};

export type Location = {
  id: string;
  business_unit_id: string;
  name: string;
  kind: string;
  is_active: boolean;
};

export type UnitOfMeasure = {
  id: string;
  code: string;
  name: string;
  symbol: string | null;
};

export type VatRate = {
  id: string;
  code: string;
  name: string;
  rate_percent: string;
  rate_type: string;
  nav_code: string | null;
  description: string | null;
  valid_from: string | null;
  valid_to: string | null;
  is_active: boolean;
};

export type Category = {
  id: string;
  business_unit_id: string;
  parent_id: string | null;
  name: string;
  is_active: boolean;
};

export type Product = {
  id: string;
  business_unit_id: string;
  category_id: string | null;
  sales_uom_id: string | null;
  default_vat_rate_id: string | null;
  sku: string | null;
  name: string;
  product_type: string;
  sale_price_gross: string | null;
  sale_price_last_seen_at: string | null;
  sale_price_source: string | null;
  default_unit_cost: string | null;
  currency: string;
  is_active: boolean;
};
