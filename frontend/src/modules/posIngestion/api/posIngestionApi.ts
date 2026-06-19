import { apiGet, apiPatchJson } from "../../../services/api/client";
import type {
  PosMissingRecipeProduct,
  PosMappingReadiness,
  PosProductAlias,
  PosProductAliasApprovalPayload,
  PosProductAliasBulkApprovalPayload,
  PosProductAliasBulkApprovalResult,
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

export function getPosMappingReadiness(filters: {
  business_unit_id?: string;
  start_date?: string;
  end_date?: string;
}) {
  return apiGet<PosMappingReadiness>(
    "pos-ingestion/mapping-readiness",
    filters,
  );
}

export function bulkApprovePosProductAliasMappings(
  payload: PosProductAliasBulkApprovalPayload,
) {
  return apiPatchJson<
    PosProductAliasBulkApprovalPayload,
    PosProductAliasBulkApprovalResult
  >("pos-ingestion/product-aliases/mappings", payload);
}
