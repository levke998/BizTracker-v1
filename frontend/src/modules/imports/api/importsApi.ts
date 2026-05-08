import { apiGet, apiPost, apiPostForm } from "../../../services/api/client";

import type {
  ImportBatch,
  ImportBatchWeatherBackfillResult,
  ImportBatchWeatherCoverageResult,
  ImportBatchWeatherRecommendation,
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
  payload.files.forEach((file) => formData.append("files", file));

  if (
    payload.files.length === 1 &&
    !["gourmand_pos_sales", "flow_pos_sales"].includes(payload.importType)
  ) {
    const singleFileFormData = new FormData();
    singleFileFormData.append("business_unit_id", payload.businessUnitId);
    singleFileFormData.append("import_type", payload.importType);
    singleFileFormData.append("file", payload.files[0]);
    return apiPostForm<ImportBatch>("imports/files", singleFileFormData);
  }

  return apiPostForm<ImportBatch>("imports/file-set", formData);
}

export function parseImportBatch(batchId: string) {
  return apiPost<ImportBatch>(`imports/batches/${batchId}/parse`);
}

export function mapImportBatchToFinancialTransactions(batchId: string) {
  return apiPost<{
    batch_id: string;
    created_transactions: number;
    transaction_type: string;
    source_type: string;
  }>(`imports/batches/${batchId}/map/financial-transactions`);
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

export function getImportBatchWeatherRecommendation(batchId: string) {
  return apiGet<ImportBatchWeatherRecommendation>(
    `weather/import-batches/${batchId}/recommendation`,
  );
}

export function backfillImportBatchWeather(batchId: string) {
  return apiPost<ImportBatchWeatherBackfillResult>(
    `weather/import-batches/${batchId}/backfill`,
  );
}

export function ensureImportBatchWeatherCoverage(batchId: string) {
  return apiPost<ImportBatchWeatherCoverageResult>(
    `weather/import-batches/${batchId}/ensure-coverage`,
  );
}
