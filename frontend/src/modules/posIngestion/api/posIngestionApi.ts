import { apiGet, apiPatchJson } from "../../../services/api/client";
import type {
  PosMissingRecipeProduct,
  PosProductAlias,
  PosProductAliasApprovalPayload,
} from "../types/posIngestion";

export function listPosProductAliases(businessUnitId: string, status?: string) {
  return apiGet<PosProductAlias[]>("pos-ingestion/product-aliases", {
    business_unit_id: businessUnitId,
    status,
  });
}

export function listPosProductsMissingRecipes(businessUnitId: string) {
  return apiGet<PosMissingRecipeProduct[]>(
    "pos-ingestion/products/missing-recipes",
    {
      business_unit_id: businessUnitId,
    },
  );
}

export function approvePosProductAliasMapping(
  aliasId: string,
  payload: PosProductAliasApprovalPayload,
) {
  return apiPatchJson<PosProductAliasApprovalPayload, PosProductAlias>(
    `pos-ingestion/product-aliases/${aliasId}/mapping`,
    payload,
  );
}
