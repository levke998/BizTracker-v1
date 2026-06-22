import { Fragment } from "react";

import type {
  ImportBatch,
  ImportBatchWeatherRecommendation,
  ImportErrorPreview,
  ImportRowPreview,
} from "../types/imports";
import {
  formatBytes,
  formatDate,
  formatDateTime,
  formatImportPeriod,
  formatImportStatus,
  formatImportType,
  formatRowStatus,
  getImportBatchStatusText,
  renderPayload,
  summarizeFiles,
} from "./importCenterView";

function SummaryPreview({ batch }: { batch: ImportBatch }) {
  const totalSize = batch.files.reduce((sum, file) => sum + file.size_bytes, 0);

  return (
    <div className="summary-grid">
      <div className="summary-item">
        <span className="summary-label">Import tipus</span>
        <strong>{formatImportType(batch.import_type)}</strong>
      </div>
      <div className="summary-item">
        <span className="summary-label">Statusz</span>
        <strong>{formatImportStatus(batch.status)}</strong>
      </div>
      <div className="summary-item">
        <span className="summary-label">Letrehozva</span>
        <strong>{formatDateTime(batch.created_at)}</strong>
      </div>
      <div className="summary-item">
        <span className="summary-label">Befejezve</span>
        <strong>{batch.finished_at ? formatDateTime(batch.finished_at) : "-"}</strong>
      </div>
      <div className="summary-item">
        <span className="summary-label">Fajlok</span>
        <strong>{batch.files.length || "-"}</strong>
      </div>
      <div className="summary-item">
        <span className="summary-label">Fajlmeret</span>
        <strong>{totalSize ? formatBytes(totalSize) : "-"}</strong>
      </div>
      <div className="summary-item">
        <span className="summary-label">Sorallapot</span>
        <strong>
          {batch.total_rows} / {batch.parsed_rows} / {batch.error_rows}
        </strong>
      </div>
      <div className="summary-item summary-item-wide">
        <span className="summary-label">Eredeti fajlok</span>
        <strong>{batch.files.map((file) => file.original_name).join(", ") || "-"}</strong>
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
            <th>Sor</th>
            <th>Statusz</th>
            <th>Nyers adat</th>
            <th>Normalizalt adat</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((row, index) => (
            <tr key={`${row.row_number}-${row.parse_status}-${index}`}>
              <td>{row.row_number}</td>
              <td>{formatRowStatus(row.parse_status)}</td>
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
    return <p className="empty-message">Nincs tarolt feldolgozasi hiba.</p>;
  }

  return (
    <div className="table-wrap">
      <table className="data-table details-table">
        <thead>
          <tr>
            <th>Sor</th>
            <th>Hibakod</th>
            <th>Uzenet</th>
            <th>Nyers adat</th>
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

function WeatherPreparationPanel({
  recommendation,
  isPreparing,
  onPrepare,
}: {
  recommendation: ImportBatchWeatherRecommendation | undefined;
  isPreparing: boolean;
  onPrepare: () => void;
}) {
  if (!recommendation) {
    return <p className="info-message">Idojaras-elokeszites allapotanak betoltese...</p>;
  }

  const isComplete = recommendation.requested_hours > 0 && recommendation.missing_hours === 0;
  const canStart = recommendation.can_backfill && recommendation.missing_hours > 0;

  return (
    <div className="weather-preparation-card">
      <div className="weather-preparation-copy">
        <span className="summary-label">Idojaras-elokeszites</span>
        <strong>
          {isComplete
            ? "Elokeszitve"
            : recommendation.can_backfill
              ? "Elokeszitheto"
              : "Nem indithato"}
        </strong>
        <p>
          {recommendation.reason ??
            `${formatDate(recommendation.start_date)} - ${formatDate(
              recommendation.end_date,
            )}, ${recommendation.suggested_location_name}`}
        </p>
      </div>
      <div className="weather-preparation-stats">
        <span>
          <strong>{recommendation.requested_hours}</strong>
          varhato ora
        </span>
        <span>
          <strong>{recommendation.cached_hours}</strong>
          cache-elt
        </span>
        <span>
          <strong>{recommendation.missing_hours}</strong>
          hianyzik
        </span>
      </div>
      <button
        type="button"
        className="primary-button"
        disabled={!canStart || isPreparing}
        onClick={onPrepare}
      >
        {isPreparing
          ? "Elokeszites..."
          : isComplete
            ? "Idojaras kesz"
            : "Idojaras elokeszitese"}
      </button>
    </div>
  );
}

type ImportBatchSectionProps = {
  batches: ImportBatch[];
  isLoading: boolean;
  parsingBatchId: string;
  mappingBatchId: string;
  weatherBackfillBatchId: string;
  registeredBatchIds: Record<string, boolean>;
  expandedBatchIds: Record<string, boolean>;
  detailsByBatchId: Record<string, { rows: ImportRowPreview[]; errors: ImportErrorPreview[] } | undefined>;
  weatherByBatchId: Record<string, ImportBatchWeatherRecommendation | undefined>;
  detailLoadingByBatchId: Record<string, boolean>;
  detailErrorByBatchId: Record<string, string>;
  onRegisterBatch: (batch: ImportBatch) => void;
  onToggleBatchDetails: (batchId: string) => void;
  onMapBatch: (batchId: string) => void;
  onPrepareWeatherForBatch: (batchId: string) => void;
};

export function ImportBatchCardsSection({
  batches,
  isLoading,
  parsingBatchId,
  mappingBatchId,
  registeredBatchIds,
  expandedBatchIds,
  detailsByBatchId,
  detailLoadingByBatchId,
  detailErrorByBatchId,
  onRegisterBatch,
  onToggleBatchDetails,
}: ImportBatchSectionProps) {
  return (
    <>
      <div className="panel-header">
        <h2>Import csomagok</h2>
        <span className="panel-count">{batches.length}</span>
      </div>

      {isLoading ? <p className="info-message">Import csomagok betoltese...</p> : null}

      {!isLoading && batches.length === 0 ? (
        <p className="empty-message">Nincs import csomag a kivalasztott szurokkel.</p>
      ) : null}

      {batches.length > 0 ? (
        <div className="import-batch-card-list">
          {batches.map((batch) => {
            const totalSize = batch.files.reduce((sum, file) => sum + file.size_bytes, 0);
            const isUploaded = batch.status === "uploaded";
            const isParsed = batch.status === "parsed";
            const canMapToFinance = ["pos_sales", "gourmand_pos_sales", "flow_pos_sales"].includes(
              batch.import_type,
            );
            const isParsing = parsingBatchId === batch.id;
            const isMapping = mappingBatchId === batch.id;
            const isExpanded = expandedBatchIds[batch.id] ?? false;
            const isDetailsLoading = detailLoadingByBatchId[batch.id] ?? false;
            const details = detailsByBatchId[batch.id];
            const detailsError = detailErrorByBatchId[batch.id];

            return (
              <article
                className={isExpanded ? "import-batch-card import-batch-card-open" : "import-batch-card"}
                key={batch.id}
                onClick={() => onToggleBatchDetails(batch.id)}
              >
                <div className="import-batch-card-main">
                  <div className="import-batch-card-title">
                    <span className={`status-badge status-${batch.status}`}>
                      {getImportBatchStatusText(batch)}
                    </span>
                    <div>
                      <strong>{summarizeFiles(batch)}</strong>
                      <small>
                        {formatImportPeriod(batch)} · {formatBytes(totalSize)}
                      </small>
                    </div>
                  </div>

                  <div className="import-batch-card-metrics">
                    <span>
                      <strong>{batch.files.length}</strong>
                      Fajl
                    </span>
                    <span>
                      <strong>
                        {batch.parsed_rows}/{batch.total_rows}
                      </strong>
                      Feldolgozva
                    </span>
                    <span>
                      <strong>{batch.error_rows}</strong>
                      Hiba
                    </span>
                  </div>

                  <button
                    type="button"
                    className="primary-button import-register-button"
                    onClick={(event) => {
                      event.stopPropagation();
                      onRegisterBatch(batch);
                    }}
                    disabled={
                      registeredBatchIds[batch.id] ||
                      (!isUploaded && !isParsed) ||
                      !canMapToFinance ||
                      isParsing ||
                      isMapping
                    }
                  >
                    {isParsing || isMapping || registeredBatchIds[batch.id] ? "Rogzites..." : "Rogzites"}
                  </button>
                </div>

                {isExpanded ? (
                  <div className="import-batch-card-detail">
                    <div className="selected-file-list">
                      {batch.files.map((file) => (
                        <span className="selected-file-chip" key={file.id}>
                          {file.original_name}
                        </span>
                      ))}
                    </div>

                    {isDetailsLoading ? <p className="info-message">Reszletek betoltese...</p> : null}
                    {!isDetailsLoading && detailsError ? (
                      <p className="error-message">{detailsError}</p>
                    ) : null}
                    {!isDetailsLoading && !detailsError ? (
                      <div className="import-batch-result-grid">
                        <span>
                          <strong>{details?.errors.length ?? 0}</strong>
                          Feldolgozasi hiba
                        </span>
                        <span>
                          <strong>{details?.rows.length ?? 0}</strong>
                          Elokeszitett sor
                        </span>
                        <span>
                          <strong>{formatImportType(batch.import_type)}</strong>
                          POS CSV import
                        </span>
                      </div>
                    ) : null}

                    {(details?.errors.length ?? 0) > 0 ? (
                      <ErrorsPreview errors={(details?.errors ?? []).slice(0, 5)} />
                    ) : null}
                  </div>
                ) : null}
              </article>
            );
          })}
        </div>
      ) : null}
    </>
  );
}

export function ImportBatchLegacyTable({
  batches,
  parsingBatchId,
  mappingBatchId,
  weatherBackfillBatchId,
  registeredBatchIds,
  expandedBatchIds,
  detailsByBatchId,
  weatherByBatchId,
  detailLoadingByBatchId,
  detailErrorByBatchId,
  onRegisterBatch,
  onToggleBatchDetails,
  onMapBatch,
  onPrepareWeatherForBatch,
}: ImportBatchSectionProps) {
  if (batches.length === 0) {
    return null;
  }

  return (
    <div className="table-wrap import-batch-legacy-table">
      <table className="data-table">
        <thead>
          <tr>
            <th>Import tipus</th>
            <th>Statusz</th>
            <th>Sorok</th>
            <th>Idoszak</th>
            <th>Letrehozva</th>
            <th>Eredeti fajlnev</th>
            <th>Meret</th>
            <th>Muvelet</th>
          </tr>
        </thead>
        <tbody>
          {batches.map((batch) => {
            const totalSize = batch.files.reduce((sum, file) => sum + file.size_bytes, 0);
            const isUploaded = batch.status === "uploaded";
            const isParsed = batch.status === "parsed";
            const canMapToFinance = ["pos_sales", "gourmand_pos_sales", "flow_pos_sales"].includes(
              batch.import_type,
            );
            const isParsing = parsingBatchId === batch.id;
            const isMapping = mappingBatchId === batch.id;
            const isPreparingWeather = weatherBackfillBatchId === batch.id;
            const isExpanded = expandedBatchIds[batch.id] ?? false;
            const isDetailsLoading = detailLoadingByBatchId[batch.id] ?? false;
            const details = detailsByBatchId[batch.id];
            const detailsError = detailErrorByBatchId[batch.id];

            return (
              <Fragment key={batch.id}>
                <tr className="import-batch-row" onClick={() => onToggleBatchDetails(batch.id)}>
                  <td>{formatImportType(batch.import_type)}</td>
                  <td>
                    <span className={`status-badge status-${batch.status}`}>
                      {formatImportStatus(batch.status)}
                    </span>
                  </td>
                  <td>
                    <div className="metric-stack">
                      <span>Osszes: {batch.total_rows}</span>
                      <span>Feldolgozva: {batch.parsed_rows}</span>
                      <span>Hibak: {batch.error_rows}</span>
                    </div>
                  </td>
                  <td>{formatImportPeriod(batch)}</td>
                  <td>{formatDateTime(batch.created_at)}</td>
                  <td>{summarizeFiles(batch)}</td>
                  <td>{totalSize ? formatBytes(totalSize) : "-"}</td>
                  <td>
                    <div className="inline-actions">
                      <button
                        type="button"
                        className="secondary-button"
                        onClick={(event) => {
                          event.stopPropagation();
                          onRegisterBatch(batch);
                        }}
                        disabled={
                          registeredBatchIds[batch.id] ||
                          (!isUploaded && !isParsed) ||
                          !canMapToFinance ||
                          isParsing ||
                          isMapping
                        }
                      >
                        {isParsing ? "Feldolgozas..." : "Feldolgozas"}
                      </button>
                      <button
                        type="button"
                        className="secondary-button"
                        onClick={() => onMapBatch(batch.id)}
                        disabled={!isParsed || !canMapToFinance || isMapping}
                        title="A feldolgozott POS sorokbol penzugyi tranzakciokat rogzit. A mar rogzitett sorokat nem duplazza."
                      >
                        {isMapping ? "Rogzites..." : "Penzugyi rogzites"}
                      </button>
                      <button
                        type="button"
                        className="secondary-button"
                        onClick={() => onToggleBatchDetails(batch.id)}
                      >
                        {isExpanded ? "Reszletek elrejtese" : "Reszletek"}
                      </button>
                    </div>
                  </td>
                </tr>

                {isExpanded ? (
                  <tr className="details-row">
                    <td colSpan={8}>
                      <div className="details-grid">
                        <section className="details-panel details-panel-wide">
                          <div className="details-panel-header">
                            <h3>Attekintes</h3>
                          </div>
                          <SummaryPreview batch={batch} />
                        </section>

                        <section className="details-panel details-panel-wide">
                          <div className="details-panel-header">
                            <h3>Idojaras</h3>
                            <span className="panel-count">Idojarasi adatok</span>
                          </div>
                          {isDetailsLoading ? (
                            <p className="info-message">Idojaras-elokeszites betoltese...</p>
                          ) : null}
                          {!isDetailsLoading && !detailsError ? (
                            <WeatherPreparationPanel
                              recommendation={weatherByBatchId[batch.id]}
                              isPreparing={isPreparingWeather}
                              onPrepare={() => onPrepareWeatherForBatch(batch.id)}
                            />
                          ) : null}
                        </section>

                        <section className="details-panel">
                          <div className="details-panel-header">
                            <h3>Sorok</h3>
                            <span className="panel-count">{details?.rows.length ?? 0}</span>
                          </div>
                          {isDetailsLoading ? <p className="info-message">Reszletek betoltese...</p> : null}
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
                            <span className="panel-count">{details?.errors.length ?? 0}</span>
                          </div>
                          {isDetailsLoading ? <p className="info-message">Reszletek betoltese...</p> : null}
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
  );
}
