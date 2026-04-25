import { apiGet, apiPostJson } from "../../../services/api/client";
import type {
  DemoPosCatalogProduct,
  DemoPosReceipt,
  DemoPosReceiptRequest,
} from "../types/demoPos";

export function listDemoPosCatalog(businessUnitId: string) {
  return apiGet<DemoPosCatalogProduct[]>("demo-pos/catalog", {
    business_unit_id: businessUnitId,
  });
}

export function createDemoPosReceipt(payload: DemoPosReceiptRequest) {
  return apiPostJson<DemoPosReceiptRequest, DemoPosReceipt>(
    "pos-ingestion/receipts",
    payload,
  );
}
