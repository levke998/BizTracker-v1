export type ImportFile = {
  id: string;
  batch_id: string;
  original_name: string;
  stored_path: string;
  mime_type: string | null;
  size_bytes: number;
  uploaded_at: string;
};

export type ImportBatch = {
  id: string;
  business_unit_id: string;
  import_type: string;
  status: string;
  started_at: string;
  finished_at: string | null;
  total_rows: number;
  parsed_rows: number;
  error_rows: number;
  first_occurred_at: string | null;
  last_occurred_at: string | null;
  created_at: string;
  updated_at: string;
  files: ImportFile[];
};

export type ImportRowPreview = {
  row_number: number;
  parse_status: string;
  raw_payload: Record<string, unknown>;
  normalized_payload: Record<string, unknown> | null;
};

export type ImportErrorPreview = {
  row_number: number | null;
  error_code: string;
  message: string;
  raw_payload: Record<string, unknown> | null;
};

export type UploadImportFilePayload = {
  businessUnitId: string;
  importType: string;
  files: File[];
};

export type ImportBatchWeatherRecommendation = {
  batch_id: string;
  business_unit_id: string;
  business_unit_code: string;
  business_unit_name: string;
  import_type: string;
  status: string;
  parsed_rows: number;
  can_backfill: boolean;
  reason: string | null;
  first_sale_at: string | null;
  last_sale_at: string | null;
  start_date: string | null;
  end_date: string | null;
  timezone_name: string;
  suggested_location_name: string;
  latitude: string;
  longitude: string;
  provider_name: string;
  requested_hours: number;
  cached_hours: number;
  missing_hours: number;
};

export type ImportBatchWeatherBackfillResult = {
  provider: string;
  start_date: string;
  end_date: string;
  requested_hours: number;
  created_count: number;
  updated_count: number;
  skipped_count: number;
};

export type ImportBatchWeatherCoverageResult = {
  batch_id: string;
  status: "covered" | "backfilled" | "skipped";
  reason: string | null;
  start_date: string | null;
  end_date: string | null;
  requested_hours: number;
  cached_hours: number;
  missing_hours: number;
  backfill_attempted: boolean;
  created_count: number;
  updated_count: number;
  skipped_count: number;
};
