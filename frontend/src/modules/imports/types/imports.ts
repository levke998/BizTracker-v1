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
  file: File;
};
