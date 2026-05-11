export type RecipeCostStatus =
  | "complete"
  | "missing_cost"
  | "no_recipe"
  | "empty_recipe";

export type RecipeReadinessStatus =
  | "ready"
  | "missing_recipe"
  | "missing_cost"
  | "missing_stock"
  | "empty_recipe";

export type IngredientStockStatus =
  | "ok"
  | "missing"
  | "insufficient"
  | "unknown"
  | "not_tracked";

export type RecipeIngredientCost = {
  inventory_item_id: string;
  inventory_item_name: string;
  quantity: string;
  uom_id: string;
  uom_code: string | null;
  item_uom_code: string | null;
  converted_quantity: string;
  unit_cost: string | null;
  estimated_cost: string | null;
  estimated_stock_quantity: string | null;
  track_stock: boolean;
  stock_status: IngredientStockStatus;
  default_vat_rate_id: string | null;
  vat_rate_percent: string | null;
  estimated_vat_amount: string | null;
  estimated_gross_cost: string | null;
};

export type RecipeCostSummary = {
  product_id: string;
  business_unit_id: string;
  product_name: string;
  category_name: string | null;
  recipe_id: string | null;
  recipe_name: string | null;
  version_id: string | null;
  version_no: number | null;
  yield_quantity: string | null;
  yield_uom_id: string | null;
  yield_uom_code: string | null;
  known_total_cost: string;
  total_cost: string | null;
  unit_cost: string | null;
  known_total_vat_amount: string | null;
  total_vat_amount: string | null;
  known_total_gross_cost: string | null;
  total_gross_cost: string | null;
  unit_gross_cost: string | null;
  tax_status: "product_vat_derived" | "missing_vat_rate" | "incomplete_cost" | "not_available" | string;
  cost_status: RecipeCostStatus;
  readiness_status: RecipeReadinessStatus;
  warnings: string[];
  ingredients: RecipeIngredientCost[];
};

export type RecipeFilters = {
  business_unit_id: string;
  product_id?: string;
  active_only?: boolean;
};

export type RecipeReadinessOverview = {
  business_unit_id: string;
  total_products: number;
  ready_count: number;
  incomplete_count: number;
  critical_count: number;
  readiness_counts: Record<string, number>;
  cost_counts: Record<string, number>;
  tax_counts: Record<string, number>;
  warning_counts: Record<string, number>;
  next_actions: string[];
};

export type RecipeIngredientPayload = {
  inventory_item_id: string;
  quantity: string;
  uom_id: string;
};

export type RecipePayload = {
  name: string;
  yield_quantity: string;
  yield_uom_id: string;
  ingredients: RecipeIngredientPayload[];
};
