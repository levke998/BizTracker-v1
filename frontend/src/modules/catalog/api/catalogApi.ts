import { apiGet } from "../../../services/api/client";
import type { CatalogIngredient, CatalogProduct } from "../types/catalog";

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
