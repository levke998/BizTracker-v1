import { apiGet, apiPutJson } from "../../../services/api/client";
import type {
  RecipeCostSummary,
  RecipeFilters,
  RecipePayload,
} from "../types/production";

export function listProductionRecipes(filters: RecipeFilters) {
  return apiGet<RecipeCostSummary[]>("production/recipes", filters);
}

export function saveProductRecipe(productId: string, payload: RecipePayload) {
  return apiPutJson<RecipePayload, RecipeCostSummary>(
    `production/products/${productId}/recipe`,
    payload,
  );
}
