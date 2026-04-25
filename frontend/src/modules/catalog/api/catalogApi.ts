import { apiGet, apiPatchJson, apiPostJson } from "../../../services/api/client";
import type {
  CatalogIngredient,
  CatalogIngredientPayload,
  CatalogProduct,
  CatalogProductPayload,
} from "../types/catalog";

export function listCatalogProducts(businessUnitId: string) {
  return apiGet<CatalogProduct[]>("catalog/products", {
    business_unit_id: businessUnitId,
  });
}

export function listCatalogIngredients(businessUnitId: string) {
  return apiGet<CatalogIngredient[]>("catalog/ingredients", {
    business_unit_id: businessUnitId,
  });
}

export function createCatalogProduct(payload: CatalogProductPayload) {
  return apiPostJson<CatalogProductPayload, CatalogProduct>("catalog/products", payload);
}

export function updateCatalogProduct(productId: string, payload: CatalogProductPayload) {
  return apiPatchJson<CatalogProductPayload, CatalogProduct>(
    `catalog/products/${productId}`,
    payload,
  );
}

export function createCatalogIngredient(payload: CatalogIngredientPayload) {
  return apiPostJson<CatalogIngredientPayload, CatalogIngredient>(
    "catalog/ingredients",
    payload,
  );
}

export function updateCatalogIngredient(
  inventoryItemId: string,
  payload: CatalogIngredientPayload,
) {
  return apiPatchJson<CatalogIngredientPayload, CatalogIngredient>(
    `catalog/ingredients/${inventoryItemId}`,
    payload,
  );
}
