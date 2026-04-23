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
  sku: string | null;
  name: string;
  product_type: string;
  is_active: boolean;
};
