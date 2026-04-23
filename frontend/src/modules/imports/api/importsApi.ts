import { apiGet, apiPost, apiPostForm } from "../../../services/api/client";

import type {
  ImportBatch,
  ImportErrorPreview,
  ImportRowPreview,
  UploadImportFilePayload,
} from "../types/imports";

export function listImportBatches(businessUnitId?: string) {
  return apiGet<ImportBatch[]>("imports/batches", {
    business_unit_id: businessUnitId,
  });
}

export function uploadImportFile(payload: UploadImportFilePayload) {
  const formData = new FormData();
  formData.append("business_unit_id", payload.businessUnitId);
  formData.append("import_type", payload.importType);
  formData.append("file", payload.file);

  return apiPostForm<ImportBatch>("imports/files", formData);
}

export function parseImportBatch(batchId: string) {
  return apiPost<ImportBatch>(`imports/batches/${batchId}/parse`);
}

export function getImportRows(batchId: string, limit = 20) {
  return apiGet<ImportRowPreview[]>(`imports/batches/${batchId}/rows`, {
    limit,
  });
}

export function getImportErrors(batchId: string, limit = 20) {
  return apiGet<ImportErrorPreview[]>(`imports/batches/${batchId}/errors`, {
    limit,
  });
}
