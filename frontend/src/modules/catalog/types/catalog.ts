export type CatalogRecipeIngredient = {
  inventory_item_id: string;
  name: string;
  quantity: string;
  uom_code: string | null;
  unit_cost: string | null;
  estimated_cost: string | null;
};

export type CatalogProduct = {
  id: string;
  business_unit_id: string;
  category_id: string | null;
  category_name: string | null;
  sales_uom_id: string | null;
  sales_uom_code: string | null;
  sales_uom_symbol: string | null;
  sku: string | null;
  name: string;
  product_type: string;
  sale_price_gross: string | null;
  estimated_unit_cost: string | null;
  estimated_margin_amount: string | null;
  estimated_margin_percent: string | null;
  currency: string;
  has_recipe: boolean;
  recipe_name: string | null;
  recipe_yield_quantity: string | null;
  recipe_yield_uom_code: string | null;
  ingredients: CatalogRecipeIngredient[];
  is_active: boolean;
};

export type CatalogIngredient = {
  id: string;
  business_unit_id: string;
  name: string;
  item_type: string;
  uom_id: string;
  uom_code: string | null;
  uom_symbol: string | null;
  default_unit_cost: string | null;
  estimated_stock_quantity: string | null;
  used_by_product_count: number;
  track_stock: boolean;
  is_active: boolean;
};

export type CatalogRecipeIngredientPayload = {
  inventory_item_id: string;
  quantity: string;
  uom_id: string;
};

export type CatalogRecipePayload = {
  name: string;
  yield_quantity: string;
  yield_uom_id: string;
  ingredients: CatalogRecipeIngredientPayload[];
};

export type CatalogProductPayload = {
  business_unit_id?: string;
  category_id: string | null;
  sales_uom_id: string | null;
  sku: string | null;
  name: string;
  product_type: string;
  sale_price_gross: string | null;
  default_unit_cost: string | null;
  currency: string;
  is_active: boolean;
  recipe: CatalogRecipePayload | null;
};

export type CatalogIngredientPayload = {
  business_unit_id?: string;
  name: string;
  item_type: string;
  uom_id: string;
  track_stock: boolean;
  default_unit_cost: string | null;
  estimated_stock_quantity: string | null;
  is_active: boolean;
};
