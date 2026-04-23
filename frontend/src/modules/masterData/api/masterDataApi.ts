import { apiGet } from "../../../services/api/client";
import type {
  BusinessUnit,
  Category,
  Location,
  Product,
  UnitOfMeasure,
} from "../types/masterData";

export function listBusinessUnits() {
  return apiGet<BusinessUnit[]>("master-data/business-units");
}

export function listLocations(businessUnitId: string) {
  return apiGet<Location[]>("master-data/locations", {
    business_unit_id: businessUnitId,
  });
}

export function listUnitsOfMeasure() {
  return apiGet<UnitOfMeasure[]>("master-data/units-of-measure");
}

export function listCategories(businessUnitId: string) {
  return apiGet<Category[]>("master-data/categories", {
    business_unit_id: businessUnitId,
  });
}

export function listProducts(businessUnitId: string) {
  return apiGet<Product[]>("master-data/products", {
    business_unit_id: businessUnitId,
  });
}
