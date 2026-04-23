import { Fragment, useRef, type FormEvent } from "react";

import { useImportBatches } from "../hooks/useImportBatches";
import type { ImportBatch, ImportErrorPreview, ImportRowPreview } from "../types/imports";

function formatDateTime(value: string) {
  return new Intl.DateTimeFormat("hu-HU", {
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  }).format(new Date(value));
}

function formatBytes(value: number) {
  if (value < 1024) {
    return `${value} B`;
  }

  if (value < 1024 * 1024) {
    return `${(value / 1024).toFixed(1)} KB`;
  }

  return `${(value / (1024 * 1024)).toFixed(1)} MB`;
}

function renderPayload(payload: Record<string, unknown> | null) {
  if (!payload) {
    return "-";
  }

  return <pre className="json-preview">{JSON.stringify(payload, null, 2)}</pre>;
}

function SummaryPreview({ batch }: { batch: ImportBatch }) {
  const file = batch.files[0];

  return (
    <div className="summary-grid">
      <div className="summary-item">
        <span className="summary-label">Import type</span>
        <strong>{batch.import_type}</strong>
      </div>
      <div className="summary-item">
        <span className="summary-label">Status</span>
        <strong>{batch.status}</strong>
      </div>
      <div className="summary-item">
        <span className="summary-label">Created at</span>
        <strong>{formatDateTime(batch.created_at)}</strong>
      </div>
      <div className="summary-item">
        <span className="summary-label">Started at</span>
        <strong>{formatDateTime(batch.started_at)}</strong>
      </div>
      <div className="summary-item">
        <span className="summary-label">Finished at</span>
        <strong>{batch.finished_at ? formatDateTime(batch.finished_at) : "-"}</strong>
      </div>
      <div className="summary-item">
        <span className="summary-label">File</span>
        <strong>{file?.original_name ?? "-"}</strong>
      </div>
      <div className="summary-item">
        <span className="summary-label">Uploaded at</span>
        <strong>{file ? formatDateTime(file.uploaded_at) : "-"}</strong>
      </div>
      <div className="summary-item">
        <span className="summary-label">File size</span>
        <strong>{file ? formatBytes(file.size_bytes) : "-"}</strong>
      </div>
      <div className="summary-item">
        <span className="summary-label">Counters</span>
        <strong>
          {batch.total_rows} / {batch.parsed_rows} / {batch.error_rows}
        </strong>
      </div>
    </div>
  );
}

function RowsPreview({ rows }: { rows: ImportRowPreview[] }) {
  if (rows.length === 0) {
    return <p className="empty-message">Nincs megjelenitheto staging sor.</p>;
  }

  return (
    <div className="table-wrap">
      <table className="data-table details-table">
        <thead>
          <tr>
            <th>Row</th>
            <th>Status</th>
            <th>Raw payload</th>
            <th>Normalized payload</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => (
            <tr key={`${row.row_number}-${row.parse_status}`}>
              <td>{row.row_number}</td>
              <td>{row.parse_status}</td>
              <td>{renderPayload(row.raw_payload)}</td>
              <td>{renderPayload(row.normalized_payload)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function ErrorsPreview({ errors }: { errors: ImportErrorPreview[] }) {
  if (errors.length === 0) {
    return <p className="empty-message">Nincs tarolt parse hiba.</p>;
  }

  return (
    <div className="table-wrap">
      <table className="data-table details-table">
        <thead>
          <tr>
            <th>Row</th>
            <th>Error code</th>
            <th>Message</th>
            <th>Raw payload</th>
          </tr>
        </thead>
        <tbody>
          {errors.map((error, index) => (
            <tr key={`${error.error_code}-${error.row_number ?? "na"}-${index}`}>
              <td>{error.row_number ?? "-"}</td>
              <td>{error.error_code}</td>
              <td>{error.message}</td>
              <td>{renderPayload(error.raw_payload)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export function ImportCenterPage() {
  const {
    businessUnits,
    importTypes,
    selectedBusinessUnitId,
    setSelectedBusinessUnitId,
    selectedImportType,
    setSelectedImportType,
    batches,
    isLoading,
    isUploading,
    parsingBatchId,
    expandedBatchIds,
    detailsByBatchId,
    detailLoadingByBatchId,
    detailErrorByBatchId,
    errorMessage,
    successMessage,
    uploadFile,
    parseBatch,
    toggleBatchDetails,
  } = useImportBatches();
  const fileInputRef = useRef<HTMLInputElement | null>(null);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const file = fileInputRef.current?.files?.[0] ?? null;
    await uploadFile(file);

    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
  }

  return (
    <section className="page-section">
      <div className="panel">
        <div className="panel-header">
          <h2>Upload import file</h2>
        </div>

        <form className="form-grid" onSubmit={handleSubmit}>
          <label className="field">
            <span>Business unit</span>
            <select
              value={selectedBusinessUnitId}
              onChange={(event) => setSelectedBusinessUnitId(event.target.value)}
              className="field-input"
            >
              <option value="">Select a business unit</option>
              {businessUnits.map((businessUnit) => (
                <option key={businessUnit.id} value={businessUnit.id}>
                  {businessUnit.name}
                </option>
              ))}
            </select>
          </label>

          <label className="field">
            <span>Import type</span>
            <select
              value={selectedImportType}
              onChange={(event) => setSelectedImportType(event.target.value)}
              className="field-input"
            >
              {importTypes.map((importType) => (
                <option key={importType} value={importType}>
                  {importType}
                </option>
              ))}
            </select>
          </label>

          <label className="field">
            <span>File</span>
            <input
              ref={fileInputRef}
              type="file"
              className="field-input"
              accept=".csv,.xlsx,.xls,.txt"
            />
          </label>

          <div className="form-actions">
            <button type="submit" className="primary-button" disabled={isUploading}>
              {isUploading ? "Uploading..." : "Upload file"}
            </button>
          </div>
        </form>

        {errorMessage ? <p className="error-message">{errorMessage}</p> : null}
        {successMessage ? <p className="success-message">{successMessage}</p> : null}
      </div>

      <section className="panel">
        <div className="panel-header">
          <h2>Import batches</h2>
          <span className="panel-count">{batches.length}</span>
        </div>

        {isLoading ? <p className="info-message">Loading batches...</p> : null}

        {!isLoading && batches.length === 0 ? (
          <p className="empty-message">No import batches found.</p>
        ) : null}

        {batches.length > 0 ? (
          <div className="table-wrap">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Import type</th>
                  <th>Status</th>
                  <th>Rows</th>
                  <th>Created at</th>
                  <th>Original file name</th>
                  <th>Size</th>
                  <th>Action</th>
                </tr>
              </thead>
              <tbody>
                {batches.map((batch) => {
                  const file = batch.files[0];
                  const isUploaded = batch.status === "uploaded";
                  const isParsing = parsingBatchId === batch.id;
                  const isExpanded = expandedBatchIds[batch.id] ?? false;
                  const isDetailsLoading = detailLoadingByBatchId[batch.id] ?? false;
                  const details = detailsByBatchId[batch.id];
                  const detailsError = detailErrorByBatchId[batch.id];

                  return (
                    <Fragment key={batch.id}>
                      <tr>
                        <td>{batch.import_type}</td>
                        <td>
                          <span className={`status-badge status-${batch.status}`}>
                            {batch.status}
                          </span>
                        </td>
                        <td>
                          <div className="metric-stack">
                            <span>Total: {batch.total_rows}</span>
                            <span>Parsed: {batch.parsed_rows}</span>
                            <span>Errors: {batch.error_rows}</span>
                          </div>
                        </td>
                        <td>{formatDateTime(batch.created_at)}</td>
                        <td>{file?.original_name ?? "-"}</td>
                        <td>{file ? formatBytes(file.size_bytes) : "-"}</td>
                        <td>
                          <div className="inline-actions">
                            <button
                              type="button"
                              className="secondary-button"
                              onClick={() => void parseBatch(batch.id)}
                              disabled={!isUploaded || isParsing}
                            >
                              {isParsing ? "Parsing..." : "Parse"}
                            </button>
                            <button
                              type="button"
                              className="secondary-button"
                              onClick={() => void toggleBatchDetails(batch.id)}
                            >
                              {isExpanded ? "Hide details" : "Details"}
                            </button>
                          </div>
                        </td>
                      </tr>

                      {isExpanded ? (
                        <tr className="details-row">
                          <td colSpan={7}>
                            <div className="details-grid">
                              <section className="details-panel details-panel-wide">
                                <div className="details-panel-header">
                                  <h3>Overview</h3>
                                </div>
                                <SummaryPreview batch={batch} />
                              </section>

                              <section className="details-panel">
                                <div className="details-panel-header">
                                  <h3>Sorok</h3>
                                  <span className="panel-count">
                                    {details?.rows.length ?? 0}
                                  </span>
                                </div>
                                {isDetailsLoading ? (
                                  <p className="info-message">Reszletek betoltese...</p>
                                ) : null}
                                {!isDetailsLoading && detailsError ? (
                                  <p className="error-message">{detailsError}</p>
                                ) : null}
                                {!isDetailsLoading && !detailsError ? (
                                  <RowsPreview rows={details?.rows ?? []} />
                                ) : null}
                              </section>

                              <section className="details-panel">
                                <div className="details-panel-header">
                                  <h3>Hibak</h3>
                                  <span className="panel-count">
                                    {details?.errors.length ?? 0}
                                  </span>
                                </div>
                                {isDetailsLoading ? (
                                  <p className="info-message">Reszletek betoltese...</p>
                                ) : null}
                                {!isDetailsLoading && detailsError ? (
                                  <p className="error-message">{detailsError}</p>
                                ) : null}
                                {!isDetailsLoading && !detailsError ? (
                                  <ErrorsPreview errors={details?.errors ?? []} />
                                ) : null}
                              </section>
                            </div>
                          </td>
                        </tr>
                      ) : null}
                    </Fragment>
                  );
                })}
              </tbody>
            </table>
          </div>
        ) : null}
      </section>
    </section>
  );
}
