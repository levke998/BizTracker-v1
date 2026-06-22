import type { FormEventHandler, MutableRefObject } from "react";

import {
  gourmandFileKindLabels,
  hasReadyGourmandPackage,
  type SelectedImportFile,
} from "./importCenterView";

function GourmandImportGuide({ selectedFiles }: { selectedFiles: SelectedImportFile[] }) {
  const hasSummary = selectedFiles.some((file) => file.kind === "summary");
  const detailCount = selectedFiles.filter((file) => file.kind === "detail").length;
  const hasUnknown = selectedFiles.some((file) => file.kind === "unknown");
  const isReady = hasReadyGourmandPackage(selectedFiles);

  return (
    <div className="import-guide-card">
      <div className="import-guide-header">
        <span>POS CSV csomag</span>
        <strong>{isReady ? "Feltoltheto" : "Hianyos csomag"}</strong>
      </div>
      <div className="import-checklist">
        <span className={hasSummary ? "check-item is-ready" : "check-item"}>
          1 osszesito CSV
        </span>
        <span className={detailCount > 0 ? "check-item is-ready" : "check-item"}>
          legalabb 1 teteles CSV
        </span>
        <span
          className={
            !hasUnknown && selectedFiles.length > 0 ? "check-item is-ready" : "check-item"
          }
        >
          felismerheto fajltipusok
        </span>
      </div>
      <div className="import-flow-steps import-flow-steps-pos" aria-label="Import folyamat">
        <span>Feltoltes</span>
        <span>Ellenorzes</span>
        <span>Rogzites</span>
      </div>
      <p className="import-guide-note">
        Az osszesito fajl adja a kategoriakat es termekarakat, a teteles fajlok adjak
        az idopontos eladasi sorokat. Azonos idoszak lekerdezeseit toltsd fel; egy
        osszesitohoz tobb teteles CSV is tartozhat.
      </p>
    </div>
  );
}

function SelectedFilesPreview({
  files,
  isGourmandImport,
}: {
  files: SelectedImportFile[];
  isGourmandImport: boolean;
}) {
  if (files.length === 0) {
    return null;
  }

  return (
    <div className="selected-file-list">
      {files.map((file) => (
        <span key={file.name} className={`selected-file-chip file-kind-${file.kind}`}>
          {isGourmandImport ? <strong>{gourmandFileKindLabels[file.kind]}</strong> : null}
          {file.name}
        </span>
      ))}
    </div>
  );
}

type ImportUploadPanelProps = {
  waitingBatches: number;
  isGourmandImport: boolean;
  isUploading: boolean;
  selectedFiles: SelectedImportFile[];
  summaryFile: File | null;
  detailFiles: File[];
  genericFileInputRef: MutableRefObject<HTMLInputElement | null>;
  summaryFileInputRef: MutableRefObject<HTMLInputElement | null>;
  detailFilesInputRef: MutableRefObject<HTMLInputElement | null>;
  hasSelectedFiles: boolean;
  isGourmandPackageReady: boolean;
  onRefreshGenericFileSelection: () => void;
  onRefreshSummaryFileSelection: () => void;
  onAppendDetailFileSelection: () => void;
  onSubmit: FormEventHandler<HTMLFormElement>;
};

export function ImportUploadPanel({
  waitingBatches,
  isGourmandImport,
  isUploading,
  selectedFiles,
  summaryFile,
  detailFiles,
  genericFileInputRef,
  summaryFileInputRef,
  detailFilesInputRef,
  hasSelectedFiles,
  isGourmandPackageReady,
  onRefreshGenericFileSelection,
  onRefreshSummaryFileSelection,
  onAppendDetailFileSelection,
  onSubmit,
}: ImportUploadPanelProps) {
  return (
    <div className="panel">
      <div className="panel-header">
        <h2>Fajl feltoltese</h2>
        <span className="panel-count">
          {waitingBatches > 0 ? `${waitingBatches} feldolgozasra var` : "Import"}
        </span>
      </div>

      {isGourmandImport ? <GourmandImportGuide selectedFiles={selectedFiles} /> : null}

      <form
        className={isGourmandImport ? "form-grid import-upload-form" : "form-grid"}
        onSubmit={onSubmit}
      >
        {isGourmandImport ? (
          <>
            <label
              className={
                summaryFile
                  ? "field import-upload-zone import-upload-zone-ready"
                  : "field import-upload-zone"
              }
            >
              <span>Osszesito CSV</span>
              <strong>Kategoriak es termekarak</strong>
              <small>Egy fajl, az adott idoszak osszesitett lekerdezese.</small>
              <input
                ref={summaryFileInputRef}
                type="file"
                className="field-input"
                accept=".csv,.txt"
                onChange={onRefreshSummaryFileSelection}
              />
              <em>{summaryFile ? summaryFile.name : "Nincs kivalasztott osszesito"}</em>
            </label>
            <label
              className={
                detailFiles.length > 0
                  ? "field import-upload-zone import-upload-zone-ready"
                  : "field import-upload-zone"
              }
            >
              <span>Teteles CSV-k</span>
              <strong>Nyugtak es idopontok</strong>
              <small>Tobb heti teteles fajl is feltoltheto ugyanahhoz az osszesitohoz.</small>
              <input
                ref={detailFilesInputRef}
                type="file"
                className="field-input"
                accept=".csv,.txt"
                multiple
                onChange={onAppendDetailFileSelection}
              />
              <em>
                {detailFiles.length > 0
                  ? `${detailFiles.length} teteles fajl kivalasztva`
                  : "Nincs kivalasztott teteles fajl"}
              </em>
            </label>
          </>
        ) : (
          <label className="field">
            <span>Fajl</span>
            <input
              ref={genericFileInputRef}
              type="file"
              className="field-input"
              accept=".csv,.xlsx,.xls,.txt"
              onChange={onRefreshGenericFileSelection}
            />
          </label>
        )}

        <SelectedFilesPreview files={selectedFiles} isGourmandImport={isGourmandImport} />

        <div className="form-actions">
          <button
            type="submit"
            className="primary-button"
            disabled={isUploading || !hasSelectedFiles || !isGourmandPackageReady}
          >
            {isUploading
              ? "Feltoltes..."
              : isGourmandImport
                ? "POS CSV csomag feltoltese"
                : "Fajl feltoltese"}
          </button>
        </div>
      </form>
    </div>
  );
}
