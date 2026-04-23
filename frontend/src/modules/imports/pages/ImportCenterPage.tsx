import { useRef, type FormEvent } from "react";

import { useImportBatches } from "../hooks/useImportBatches";

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
    errorMessage,
    successMessage,
    uploadFile,
    parseBatch,
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

                  return (
                    <tr key={batch.id}>
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
                        <button
                          type="button"
                          className="secondary-button"
                          onClick={() => void parseBatch(batch.id)}
                          disabled={!isUploaded || isParsing}
                        >
                          {isParsing ? "Parsing..." : "Parse"}
                        </button>
                      </td>
                    </tr>
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
