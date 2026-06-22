import type {
  CatalogIngredient,
  CatalogIngredientPayload,
} from "../../catalog/types/catalog";
import type {
  IngredientStockStatus,
  RecipeCostStatus,
  RecipeCostSummary,
  RecipePayload,
  RecipeReadinessStatus,
} from "../types/production";

export type RecipeFilter =
  | "all"
  | "missing_recipe"
  | "missing_cost"
  | "missing_vat"
  | "missing_stock"
  | "empty_recipe"
  | "ready";

export type RecipeFormLine = {
  inventory_item_id: string;
  quantity: string;
  uom_id: string;
};

export type RecipeFormState = {
  name: string;
  yield_quantity: string;
  yield_uom_id: string;
  ingredients: RecipeFormLine[];
};

const RECIPE_FILTER_VALUES = new Set<RecipeFilter>([
  "all",
  "missing_recipe",
  "missing_cost",
  "missing_vat",
  "missing_stock",
  "empty_recipe",
  "ready",
]);

export function parseRecipeFilter(value: string | null): RecipeFilter {
  if (value && RECIPE_FILTER_VALUES.has(value as RecipeFilter)) {
    return value as RecipeFilter;
  }
  return "all";
}

export function toNumber(value: string | number | null | undefined) {
  const parsed = Number(value ?? 0);
  return Number.isFinite(parsed) ? parsed : 0;
}

export function formatMoney(value: string | number | null | undefined) {
  if (value === null || value === undefined || value === "") {
    return "-";
  }

  return new Intl.NumberFormat("hu-HU", {
    style: "currency",
    currency: "HUF",
    maximumFractionDigits: 0,
  }).format(toNumber(value));
}

export function formatNumber(value: string | number | null | undefined) {
  if (value === null || value === undefined || value === "") {
    return "-";
  }

  return new Intl.NumberFormat("hu-HU", {
    maximumFractionDigits: 2,
  }).format(toNumber(value));
}

export function formatQuantity(value: string | null, unit?: string | null) {
  if (value === null) {
    return "-";
  }
  return unit ? `${formatNumber(value)} ${unit}` : formatNumber(value);
}

export function formatCostStatus(value: RecipeCostStatus) {
  const labels: Record<RecipeCostStatus, string> = {
    complete: "Teljes koltseg",
    missing_cost: "Hianyzo ar",
    no_recipe: "Nincs recept",
    empty_recipe: "Ures recept",
  };
  return labels[value] ?? value;
}

export function formatTaxStatus(value: RecipeCostSummary["tax_status"]) {
  const labels: Record<string, string> = {
    product_vat_derived: "AFA szamolt",
    missing_vat_rate: "AFA kulcs hianyzik",
    incomplete_cost: "AFA nem teljes",
    not_available: "AFA nincs",
  };
  return labels[value] ?? value;
}

export function formatReadinessStatus(value: RecipeReadinessStatus) {
  const labels: Record<RecipeReadinessStatus, string> = {
    ready: "Rendben",
    missing_recipe: "Recept hianyzik",
    missing_cost: "Ar hianyzik",
    missing_stock: "Keszletjelzes",
    empty_recipe: "Ures recept",
  };
  return labels[value] ?? value;
}

export function formatStockStatus(value: IngredientStockStatus) {
  const labels: Record<IngredientStockStatus, string> = {
    ok: "Rendben",
    missing: "Nincs keszlet",
    insufficient: "Keves keszlet",
    unknown: "Nincs keszletadat",
    not_tracked: "Nem kovetett",
  };
  return labels[value] ?? value;
}

export function getReadinessClass(value: RecipeReadinessStatus) {
  if (value === "ready") {
    return "status-pill status-pill-success";
  }
  if (value === "missing_cost") {
    return "status-pill status-pill-danger";
  }
  return "status-pill status-pill-warning";
}

export function getCostStatusClass(value: RecipeCostStatus) {
  if (value === "complete") {
    return "status-pill status-pill-success";
  }
  if (value === "missing_cost") {
    return "status-pill status-pill-danger";
  }
  return "status-pill status-pill-warning";
}

export function getStockStatusClass(value: IngredientStockStatus) {
  if (value === "ok" || value === "not_tracked") {
    return "status-pill status-pill-success";
  }
  if (value === "missing" || value === "insufficient") {
    return "status-pill status-pill-warning";
  }
  return "status-pill";
}

export function getNextAction(row: RecipeCostSummary) {
  if (row.readiness_status === "missing_recipe") {
    return "Recept letrehozasa a katalogusban.";
  }
  if (row.readiness_status === "missing_cost") {
    return "Beszerzesi/default ar potlasa az erintett osszetevoknel.";
  }
  if (row.readiness_status === "missing_stock") {
    return "Keszletjelzes ellenorzese; az eladas ettol meg nem blokkolt.";
  }
  if (row.readiness_status === "empty_recipe") {
    return "Osszetevo sorok hozzaadasa a recepthez.";
  }
  if (row.tax_status === "missing_vat_rate") {
    return "AFA kulcs potlasa az erintett osszetevoknel.";
  }
  return "Nincs surgos recept oldali teendo.";
}

export function formatNextVersion(row: RecipeCostSummary) {
  return row.version_no === null ? "v1" : `v${row.version_no + 1}`;
}

export function matchesFilter(row: RecipeCostSummary, filter: RecipeFilter) {
  if (filter === "all") {
    return true;
  }
  if (filter === "missing_vat") {
    return row.tax_status === "missing_vat_rate";
  }
  if (filter === "missing_stock") {
    return row.readiness_status === "missing_stock";
  }
  if (filter === "ready") {
    return row.readiness_status === "ready";
  }
  return row.cost_status === filter || row.readiness_status === filter;
}

export function buildRecipeForm(
  row: RecipeCostSummary,
  fallbackUnitId: string,
): RecipeFormState {
  return {
    name: row.recipe_name ?? `${row.product_name} recept`,
    yield_quantity: row.yield_quantity ?? "1",
    yield_uom_id: row.yield_uom_id ?? fallbackUnitId,
    ingredients: row.ingredients.map((ingredient) => ({
      inventory_item_id: ingredient.inventory_item_id,
      quantity: ingredient.quantity,
      uom_id: ingredient.uom_id,
    })),
  };
}

export function buildRecipePayload(form: RecipeFormState): RecipePayload {
  return {
    name: form.name.trim(),
    yield_quantity: form.yield_quantity,
    yield_uom_id: form.yield_uom_id,
    ingredients: form.ingredients
      .filter((ingredient) => ingredient.inventory_item_id && ingredient.uom_id)
      .map((ingredient) => ({
        inventory_item_id: ingredient.inventory_item_id,
        quantity: ingredient.quantity,
        uom_id: ingredient.uom_id,
      })),
  };
}

export function ingredientDefaultUnitId(
  ingredients: CatalogIngredient[],
  inventoryItemId: string,
  fallbackUnitId: string,
) {
  return (
    ingredients.find((ingredient) => ingredient.id === inventoryItemId)?.uom_id ??
    fallbackUnitId
  );
}

export function buildIngredientPayload(
  ingredient: CatalogIngredient,
  patch: Partial<CatalogIngredientPayload>,
): CatalogIngredientPayload {
  return {
    business_unit_id: ingredient.business_unit_id,
    name: ingredient.name,
    item_type: ingredient.item_type,
    uom_id: ingredient.uom_id,
    default_vat_rate_id: ingredient.default_vat_rate_id,
    track_stock: ingredient.track_stock,
    default_unit_cost: ingredient.default_unit_cost,
    estimated_stock_quantity: ingredient.estimated_stock_quantity,
    is_active: ingredient.is_active,
    ...patch,
  };
}
