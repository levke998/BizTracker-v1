import { Fragment, useEffect, useRef, useState, type FormEvent } from "react";

import { useTopbarControls } from "../../../shared/components/layout/TopbarControlsContext";
import { listProducts } from "../../masterData/api/masterDataApi";
import type { BusinessUnit, Product } from "../../masterData/types/masterData";
import {
  approvePosProductAliasMapping,
  listPosProductAliases,
  listPosProductsMissingRecipes,
} from "../../posIngestion/api/posIngestionApi";
import type {
  PosMissingRecipeProduct,
  PosProductAlias,
} from "../../posIngestion/types/posIngestion";
import { useImportBatches } from "../hooks/useImportBatches";
import type {
  ImportBatch,
  ImportBatchWeatherRecommendation,
  ImportErrorPreview,
  ImportRowPreview,
} from "../types/imports";

type GourmandFileKind = "summary" | "detail" | "unknown";

type SelectedImportFile = {
  name: string;
  kind: GourmandFileKind;
};

const importTypeLabels: Record<string, string> = {
  pos_sales: "POS eladások",
  gourmand_pos_sales: "Gourmand POS CSV",
  flow_pos_sales: "Flow POS CSV",
  supplier_invoice: "Beszerzési számlák",
  ticket_sales: "Jegyeladások",
  bar_sales: "Bár eladások",
};

const importStatusLabels: Record<string, string> = {
  uploaded: "Feltöltve",
  parsing: "Feldolgozás alatt",
  parsed: "Feldolgozva",
  failed: "Hibás",
};

const rowStatusLabels: Record<string, string> = {
  pending: "Várakozik",
  parsed: "Feldolgozva",
  failed: "Hibás",
  skipped: "Kihagyva",
};

const gourmandFileKindLabels: Record<GourmandFileKind, string> = {
  summary: "Összesítő",
  detail: "Tételes",
  unknown: "Nem felismert",
};

function classifyGourmandFile(content: string, fileName: string): GourmandFileKind {
  const normalizedName = fileName.toLocaleLowerCase("hu-HU");
  const normalizedContent = content.toLocaleUpperCase("hu-HU");

  if (
    normalizedContent.includes("NAPI ÖSSZESSÍTÉS") ||
    normalizedName.includes("osszesites") ||
    normalizedName.includes("összesítés")
  ) {
    return "summary";
  }

  if (
    normalizedContent.includes("TÉTELES RENDELÉSEK") ||
    normalizedName.includes("teteles") ||
    normalizedName.includes("tételes")
  ) {
    return "detail";
  }

  return "unknown";
}

function formatDateTime(value: string) {
  return new Intl.DateTimeFormat("hu-HU", {
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  }).format(new Date(value));
}

function formatMoney(value: string | number | null | undefined) {
  const parsed = Number(value ?? 0);
  return new Intl.NumberFormat("hu-HU", {
    style: "currency",
    currency: "HUF",
    maximumFractionDigits: 0,
  }).format(Number.isFinite(parsed) ? parsed : 0);
}

function formatDate(value: string | null) {
  if (!value) {
    return "-";
  }
  return value.replace(/-/g, ". ");
}

function formatImportPeriod(batch: ImportBatch) {
  if (!batch.first_occurred_at || !batch.last_occurred_at) {
    return "Időszak: feldolgozás után látszik";
  }
  return `${formatDateTime(batch.first_occurred_at)} - ${formatDateTime(
    batch.last_occurred_at,
  )}`;
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

function formatImportType(value: string) {
  return importTypeLabels[value] ?? value;
}

function formatImportStatus(value: string) {
  return importStatusLabels[value] ?? value;
}

function formatRowStatus(value: string) {
  return rowStatusLabels[value] ?? value;
}

function summarizeBatches(batches: ImportBatch[]) {
  return batches.reduce(
    (summary, batch) => {
      summary.totalRows += batch.total_rows;
      summary.parsedRows += batch.parsed_rows;
      summary.errorRows += batch.error_rows;
      if (batch.status === "uploaded") {
        summary.waitingBatches += 1;
      }
      return summary;
    },
    { totalRows: 0, parsedRows: 0, errorRows: 0, waitingBatches: 0 },
  );
}

function summarizeFiles(batch: ImportBatch) {
  if (batch.files.length === 0) {
    return "-";
  }
  if (batch.files.length === 1) {
    return batch.files[0].original_name;
  }
  return `${batch.files.length} fájl`;
}

function hasReadyGourmandPackage(files: SelectedImportFile[]) {
  return (
    files.some((file) => file.kind === "summary") &&
    files.some((file) => file.kind === "detail") &&
    files.every((file) => file.kind !== "unknown")
  );
}

function renderPayload(payload: Record<string, unknown> | null) {
  if (!payload) {
    return "-";
  }
  return <pre className="json-preview">{JSON.stringify(payload, null, 2)}</pre>;
}

function ImportHeaderControls({
  businessUnits,
  selectedBusinessUnitId,
  setSelectedBusinessUnitId,
}: {
  businessUnits: BusinessUnit[];
  selectedBusinessUnitId: string;
  setSelectedBusinessUnitId: (value: string) => void;
}) {
  return (
    <div className="business-dashboard-filters topbar-dashboard-filters">
      <label className="field topbar-field">
        <span>Vállalkozás</span>
        <select
          value={selectedBusinessUnitId}
          onChange={(event) => setSelectedBusinessUnitId(event.target.value)}
          className="field-input"
        >
          <option value="">Válassz vállalkozást</option>
          {businessUnits.map((businessUnit) => (
            <option key={businessUnit.id} value={businessUnit.id}>
              {businessUnit.name}
            </option>
          ))}
        </select>
      </label>

      <label className="field topbar-field">
        <span>Import típus</span>
        <select
          value=""
          disabled
          onChange={() => undefined}
          className="field-input"
        >
          <option value="">POS CSV</option>
        </select>
      </label>
    </div>
  );
}

function GourmandImportGuide({ selectedFiles }: { selectedFiles: SelectedImportFile[] }) {
  const hasSummary = selectedFiles.some((file) => file.kind === "summary");
  const detailCount = selectedFiles.filter((file) => file.kind === "detail").length;
  const hasUnknown = selectedFiles.some((file) => file.kind === "unknown");
  const isReady = hasReadyGourmandPackage(selectedFiles);

  return (
    <div className="import-guide-card">
      <div className="import-guide-header">
        <span>POS CSV csomag</span>
        <strong>{isReady ? "Feltölthető" : "Hiányos csomag"}</strong>
      </div>
      <div className="import-checklist">
        <span className={hasSummary ? "check-item is-ready" : "check-item"}>
          1 összesítő CSV
        </span>
        <span className={detailCount > 0 ? "check-item is-ready" : "check-item"}>
          legalább 1 tételes CSV
        </span>
        <span className={!hasUnknown && selectedFiles.length > 0 ? "check-item is-ready" : "check-item"}>
          felismerhető fájltípusok
        </span>
      </div>
      <div className="import-flow-steps import-flow-steps-pos" aria-label="Import folyamat">
        <span>Feltöltés</span>
        <span>Ellenőrzés</span>
        <span>Rögzítés</span>
      </div>
      <p className="import-guide-note">
        Az összesítő fájl adja a kategóriákat és termékárakat, a tételes fájlok adják
        az időpontos eladási sorokat. Azonos időszak lekérdezéseit töltsd fel; egy
        összesítőhöz több tételes CSV is tartozhat.
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

function SummaryPreview({ batch }: { batch: ImportBatch }) {
  const totalSize = batch.files.reduce((sum, file) => sum + file.size_bytes, 0);

  return (
    <div className="summary-grid">
      <div className="summary-item">
        <span className="summary-label">Import típus</span>
        <strong>{formatImportType(batch.import_type)}</strong>
      </div>
      <div className="summary-item">
        <span className="summary-label">Státusz</span>
        <strong>{formatImportStatus(batch.status)}</strong>
      </div>
      <div className="summary-item">
        <span className="summary-label">Létrehozva</span>
        <strong>{formatDateTime(batch.created_at)}</strong>
      </div>
      <div className="summary-item">
        <span className="summary-label">Befejezve</span>
        <strong>{batch.finished_at ? formatDateTime(batch.finished_at) : "-"}</strong>
      </div>
      <div className="summary-item">
        <span className="summary-label">Fájlok</span>
        <strong>{batch.files.length || "-"}</strong>
      </div>
      <div className="summary-item">
        <span className="summary-label">Fájlméret</span>
        <strong>{totalSize ? formatBytes(totalSize) : "-"}</strong>
      </div>
      <div className="summary-item">
        <span className="summary-label">Sorállapot</span>
        <strong>
          {batch.total_rows} / {batch.parsed_rows} / {batch.error_rows}
        </strong>
      </div>
      <div className="summary-item summary-item-wide">
        <span className="summary-label">Eredeti fájlok</span>
        <strong>{batch.files.map((file) => file.original_name).join(", ") || "-"}</strong>
      </div>
    </div>
  );
}

function RowsPreview({ rows }: { rows: ImportRowPreview[] }) {
  if (rows.length === 0) {
    return <p className="empty-message">Nincs megjeleníthető staging sor.</p>;
  }

  return (
    <div className="table-wrap">
      <table className="data-table details-table">
        <thead>
          <tr>
            <th>Sor</th>
            <th>Státusz</th>
            <th>Nyers adat</th>
            <th>Normalizált adat</th>
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
    return <p className="empty-message">Nincs tárolt feldolgozási hiba.</p>;
  }

  return (
    <div className="table-wrap">
      <table className="data-table details-table">
        <thead>
          <tr>
            <th>Sor</th>
            <th>Hibakód</th>
            <th>Üzenet</th>
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
    return <p className="info-message">Időjárás-előkészítés állapotának betöltése...</p>;
  }

  const isComplete =
    recommendation.requested_hours > 0 && recommendation.missing_hours === 0;
  const canStart = recommendation.can_backfill && recommendation.missing_hours > 0;

  return (
    <div className="weather-preparation-card">
      <div className="weather-preparation-copy">
        <span className="summary-label">Időjárás-előkészítés</span>
        <strong>
          {isComplete
            ? "Előkészítve"
            : recommendation.can_backfill
              ? "Előkészíthető"
              : "Nem indítható"}
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
          várható óra
        </span>
        <span>
          <strong>{recommendation.cached_hours}</strong>
          cache-elt
        </span>
        <span>
          <strong>{recommendation.missing_hours}</strong>
          hiányzik
        </span>
      </div>
      <button
        type="button"
        className="primary-button"
        disabled={!canStart || isPreparing}
        onClick={onPrepare}
      >
        {isPreparing
          ? "Előkészítés..."
          : isComplete
            ? "Időjárás kész"
            : "Időjárás előkészítése"}
      </button>
    </div>
  );
}

function getImportBatchStatusText(batch: ImportBatch) {
  if (batch.error_rows > 0 || batch.status === "failed") {
    return "Ellenőrzést igényel";
  }
  if (batch.status === "parsed") {
    return "Rögzítésre kész";
  }
  if (batch.status === "uploaded") {
    return "Feltöltve";
  }
  return formatImportStatus(batch.status);
}

function formatAliasStatus(value: string) {
  if (value === "mapped") {
    return "Jovahagyva";
  }
  if (value === "auto_created") {
    return "Ellenorzendo";
  }
  if (value === "needs_review") {
    return "Review";
  }
  return value;
}

function PosAliasReviewPanel({
  aliases,
  products,
  isLoading,
  approvingAliasId,
  selectedProductIds,
  onSelectProduct,
  onApprove,
}: {
  aliases: PosProductAlias[];
  products: Product[];
  isLoading: boolean;
  approvingAliasId: string;
  selectedProductIds: Record<string, string>;
  onSelectProduct: (aliasId: string, productId: string) => void;
  onApprove: (aliasId: string) => void;
}) {
  const pendingAliases = aliases.filter((alias) => alias.status !== "mapped");
  const mappedAliases = aliases.filter((alias) => alias.status === "mapped");
  const productById = new Map(products.map((product) => [product.id, product]));

  return (
    <section className="panel">
      <div className="panel-header">
        <h2>POS termek mapping</h2>
        <span className="panel-count">
          {pendingAliases.length > 0
            ? `${pendingAliases.length} ellenorzendo`
            : `${mappedAliases.length} jovahagyva`}
        </span>
      </div>

      {isLoading ? <p className="info-message">POS mapping lista betoltese...</p> : null}

      {!isLoading && aliases.length === 0 ? (
        <p className="empty-message">Nincs POS termek alias a kivalasztott vallalkozasnal.</p>
      ) : null}

      {aliases.length > 0 ? (
        <div className="table-wrap">
          <table className="data-table details-table">
            <thead>
              <tr>
                <th>Kassza termek</th>
                <th>Forras</th>
                <th>Allapot</th>
                <th>Belso termek</th>
                <th>Elofordulas</th>
                <th>Muvelet</th>
              </tr>
            </thead>
            <tbody>
              {aliases.map((alias) => {
                const selectedProductId =
                  selectedProductIds[alias.id] ?? alias.product_id ?? "";
                const selectedProduct = selectedProductId
                  ? productById.get(selectedProductId)
                  : undefined;

                return (
                  <tr key={alias.id}>
                    <td>
                      <strong>{alias.source_product_name}</strong>
                      <div className="metric-stack">
                        <span>{alias.source_product_key}</span>
                        {alias.source_sku ? <span>SKU: {alias.source_sku}</span> : null}
                      </div>
                    </td>
                    <td>{alias.source_system}</td>
                    <td>
                      <span className={`status-badge status-${alias.status}`}>
                        {formatAliasStatus(alias.status)}
                      </span>
                    </td>
                    <td>
                      <select
                        className="field-input"
                        value={selectedProductId}
                        onChange={(event) =>
                          onSelectProduct(alias.id, event.target.value)
                        }
                      >
                        <option value="">Valassz termeket</option>
                        {products.map((product) => (
                          <option key={product.id} value={product.id}>
                            {product.name}
                            {product.sku ? ` (${product.sku})` : ""}
                          </option>
                        ))}
                      </select>
                      {selectedProduct ? (
                        <small>{selectedProduct.product_type}</small>
                      ) : null}
                    </td>
                    <td>
                      <div className="metric-stack">
                        <span>{alias.occurrence_count} sor</span>
                        <span>
                          {alias.last_seen_at ? formatDateTime(alias.last_seen_at) : "-"}
                        </span>
                      </div>
                    </td>
                    <td>
                      <button
                        type="button"
                        className="secondary-button"
                        disabled={!selectedProductId || approvingAliasId === alias.id}
                        onClick={() => onApprove(alias.id)}
                      >
                        {approvingAliasId === alias.id
                          ? "Mentes..."
                          : alias.status === "mapped"
                            ? "Frissites"
                            : "Jovahagyas"}
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
  );
}

function PosMissingRecipePanel({
  items,
  isLoading,
}: {
  items: PosMissingRecipeProduct[];
  isLoading: boolean;
}) {
  return (
    <section className="panel">
      <div className="panel-header">
        <h2>POS recept munkalista</h2>
        <span className="panel-count">
          {items.length > 0 ? `${items.length} recept hianyzik` : "Receptfedettseg"}
        </span>
      </div>

      {isLoading ? <p className="info-message">Recept munkalista betoltese...</p> : null}

      {!isLoading && items.length === 0 ? (
        <p className="empty-message">
          Nincs POS-bol erkezett aktiv termek recept hiany jelzessel.
        </p>
      ) : null}

      {items.length > 0 ? (
        <div className="table-wrap">
          <table className="data-table details-table">
            <thead>
              <tr>
                <th>Termek</th>
                <th>Kategoria</th>
                <th>Aktualis ar</th>
                <th>POS forras</th>
                <th>Eladasi jelzes</th>
                <th>Utoljara latva</th>
              </tr>
            </thead>
            <tbody>
              {items.map((item) => (
                <tr key={item.product_id}>
                  <td>
                    <strong>{item.product_name}</strong>
                    <div className="metric-stack">
                      <span>{item.product_type}</span>
                      {item.latest_source_product_name &&
                      item.latest_source_product_name !== item.product_name ? (
                        <span>POS nev: {item.latest_source_product_name}</span>
                      ) : null}
                    </div>
                  </td>
                  <td>{item.category_name ?? "-"}</td>
                  <td>
                    <div className="metric-stack">
                      <span>{formatMoney(item.sale_price_gross)}</span>
                      <span>{item.sale_price_source ?? "-"}</span>
                    </div>
                  </td>
                  <td>
                    <div className="metric-stack">
                      <span>{item.latest_source_system ?? "-"}</span>
                      <span>{item.alias_count} alias</span>
                    </div>
                  </td>
                  <td>{item.occurrence_count} sor</td>
                  <td>{item.last_seen_at ? formatDateTime(item.last_seen_at) : "-"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : null}
    </section>
  );
}

export function ImportCenterPage() {
  const { setControls } = useTopbarControls();
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
    mappingBatchId,
    weatherBackfillBatchId,
    expandedBatchIds,
    detailsByBatchId,
    weatherByBatchId,
    detailLoadingByBatchId,
    detailErrorByBatchId,
    errorMessage,
    successMessage,
    uploadFile,
    parseBatch,
    mapBatch,
    prepareWeatherForBatch,
    toggleBatchDetails,
  } = useImportBatches();
  const genericFileInputRef = useRef<HTMLInputElement | null>(null);
  const summaryFileInputRef = useRef<HTMLInputElement | null>(null);
  const detailFilesInputRef = useRef<HTMLInputElement | null>(null);
  const [genericFiles, setGenericFiles] = useState<File[]>([]);
  const [summaryFile, setSummaryFile] = useState<File | null>(null);
  const [detailFiles, setDetailFiles] = useState<File[]>([]);
  const [selectedFiles, setSelectedFiles] = useState<SelectedImportFile[]>([]);
  const [registeredBatchIds, setRegisteredBatchIds] = useState<Record<string, boolean>>({});
  const [posAliases, setPosAliases] = useState<PosProductAlias[]>([]);
  const [posAliasProducts, setPosAliasProducts] = useState<Product[]>([]);
  const [posMissingRecipeProducts, setPosMissingRecipeProducts] = useState<
    PosMissingRecipeProduct[]
  >([]);
  const [posAliasSelections, setPosAliasSelections] = useState<Record<string, string>>({});
  const [isLoadingPosAliases, setIsLoadingPosAliases] = useState(false);
  const [approvingAliasId, setApprovingAliasId] = useState("");
  const [posAliasError, setPosAliasError] = useState("");
  const [posAliasSuccess, setPosAliasSuccess] = useState("");
  const summary = summarizeBatches(batches);
  const isGourmandImport = ["gourmand_pos_sales", "flow_pos_sales"].includes(
    selectedImportType,
  );
  const isGourmandPackageReady = !isGourmandImport || hasReadyGourmandPackage(selectedFiles);
  const hasSelectedFiles = selectedFiles.length > 0;

  useEffect(() => {
    setControls(
      <ImportHeaderControls
        businessUnits={businessUnits}
        selectedBusinessUnitId={selectedBusinessUnitId}
        setSelectedBusinessUnitId={setSelectedBusinessUnitId}
      />,
    );

    return () => setControls(null);
  }, [
    businessUnits,
    selectedBusinessUnitId,
    setControls,
    setSelectedBusinessUnitId,
  ]);

  useEffect(() => {
    const selectedUnit = businessUnits.find((unit) => unit.id === selectedBusinessUnitId);
    const nextImportType =
      selectedUnit?.code.toLocaleLowerCase("hu-HU").includes("flow")
        ? "flow_pos_sales"
        : "gourmand_pos_sales";

    if (importTypes.includes(nextImportType) && selectedImportType !== nextImportType) {
      setSelectedImportType(nextImportType);
    }
  }, [
    businessUnits,
    importTypes,
    selectedBusinessUnitId,
    selectedImportType,
    setSelectedImportType,
  ]);

  useEffect(() => {
    clearSelectedFileState();
    clearFileInputs();
  }, [selectedImportType]);

  useEffect(() => {
    void refreshPosAliasReview();
  }, [selectedBusinessUnitId]);

  async function refreshPosAliasReview() {
    if (!selectedBusinessUnitId) {
      setPosAliases([]);
      setPosAliasProducts([]);
      setPosMissingRecipeProducts([]);
      setPosAliasSelections({});
      return;
    }

    setIsLoadingPosAliases(true);
    setPosAliasError("");
    try {
      const [aliases, products, missingRecipeProducts] = await Promise.all([
        listPosProductAliases(selectedBusinessUnitId),
        listProducts(selectedBusinessUnitId),
        listPosProductsMissingRecipes(selectedBusinessUnitId),
      ]);
      setPosAliases(aliases);
      setPosAliasProducts(products);
      setPosMissingRecipeProducts(missingRecipeProducts);
      setPosAliasSelections((current) => {
        const next: Record<string, string> = {};
        aliases.forEach((alias) => {
          next[alias.id] = current[alias.id] ?? alias.product_id ?? "";
        });
        return next;
      });
    } catch {
      setPosAliases([]);
      setPosAliasProducts([]);
      setPosMissingRecipeProducts([]);
      setPosAliasError("Nem sikerult betolteni a POS mapping listat.");
    } finally {
      setIsLoadingPosAliases(false);
    }
  }

  async function approveAlias(aliasId: string) {
    const productId = posAliasSelections[aliasId];
    if (!productId) {
      return;
    }

    setApprovingAliasId(aliasId);
    setPosAliasError("");
    setPosAliasSuccess("");
    try {
      await approvePosProductAliasMapping(aliasId, {
        product_id: productId,
      });
      await refreshPosAliasReview();
      setPosAliasSuccess("POS termek mapping jovahagyva.");
    } catch (error) {
      setPosAliasError(
        error instanceof Error ? error.message : "Nem sikerult menteni a POS mappinget.",
      );
    } finally {
      setApprovingAliasId("");
    }
  }

  function clearSelectedFileState() {
    setGenericFiles([]);
    setSummaryFile(null);
    setDetailFiles([]);
    setSelectedFiles([]);
  }

  function clearFileInputs() {
    for (const inputRef of [
      genericFileInputRef,
      summaryFileInputRef,
      detailFilesInputRef,
    ]) {
      if (inputRef.current) {
        inputRef.current.value = "";
      }
    }
  }

  async function registerBatch(batch: ImportBatch) {
    if (registeredBatchIds[batch.id]) {
      return;
    }

    setRegisteredBatchIds((current) => ({ ...current, [batch.id]: true }));
    try {
      if (batch.status === "uploaded") {
        await parseBatch(batch.id);
      }
      if (["uploaded", "parsed"].includes(batch.status)) {
        await mapBatch(batch.id);
      }
      await refreshPosAliasReview();
    } catch {
      setRegisteredBatchIds((current) => ({ ...current, [batch.id]: false }));
    } finally {
      setRegisteredBatchIds((current) => ({ ...current, [batch.id]: false }));
    }
  }

  async function refreshGenericFileSelection() {
    const files = Array.from(genericFileInputRef.current?.files ?? []);
    setGenericFiles(files);
    setSelectedFiles(files.map((file) => ({ name: file.name, kind: "unknown" })));
  }

  async function rebuildGourmandPreview(nextSummaryFile: File | null, nextDetailFiles: File[]) {
    const summaryItems = await Promise.all(
      (nextSummaryFile ? [nextSummaryFile] : []).map(async (file) => ({
        name: file.name,
        kind: classifyGourmandFile(await file.text(), file.name),
      })),
    );
    const detailItems = await Promise.all(
      nextDetailFiles.map(async (file) => ({
        name: file.name,
        kind: classifyGourmandFile(await file.text(), file.name),
      })),
    );
    setSelectedFiles([...summaryItems, ...detailItems]);
  }

  async function refreshSummaryFileSelection() {
    const file = Array.from(summaryFileInputRef.current?.files ?? [])[0] ?? null;
    setSummaryFile(file);
    await rebuildGourmandPreview(file, detailFiles);
  }

  async function appendDetailFileSelection() {
    const incomingFiles = Array.from(detailFilesInputRef.current?.files ?? []);
    const mergedFiles = [...detailFiles];
    for (const file of incomingFiles) {
      const alreadySelected = mergedFiles.some(
        (currentFile) =>
          currentFile.name === file.name &&
          currentFile.size === file.size &&
          currentFile.lastModified === file.lastModified,
      );
      if (!alreadySelected) {
        mergedFiles.push(file);
      }
    }
    setDetailFiles(mergedFiles);
    await rebuildGourmandPreview(summaryFile, mergedFiles);
    if (detailFilesInputRef.current) {
      detailFilesInputRef.current.value = "";
    }
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const files = isGourmandImport
      ? [summaryFile, ...detailFiles].filter((file): file is File => file !== null)
      : genericFiles;
    await uploadFile(files);
    clearFileInputs();
    clearSelectedFileState();
  }

  return (
    <section className="page-section">
      {errorMessage ? <p className="error-message">{errorMessage}</p> : null}
      {successMessage ? <p className="success-message">{successMessage}</p> : null}

      <div className="finance-summary-grid">
        <article className="finance-summary-card">
          <span>Import csomagok</span>
          <strong>{batches.length}</strong>
        </article>
        <article className="finance-summary-card">
          <span>Feldolgozott sorok</span>
          <strong>
            {summary.parsedRows}/{summary.totalRows}
          </strong>
        </article>
        <article className="finance-summary-card">
          <span>Hibák</span>
          <strong>{summary.errorRows}</strong>
        </article>
      </div>

      {posAliasError ? <p className="error-message">{posAliasError}</p> : null}
      {posAliasSuccess ? <p className="success-message">{posAliasSuccess}</p> : null}
      <PosAliasReviewPanel
        aliases={posAliases}
        products={posAliasProducts}
        isLoading={isLoadingPosAliases}
        approvingAliasId={approvingAliasId}
        selectedProductIds={posAliasSelections}
        onSelectProduct={(aliasId, productId) =>
          setPosAliasSelections((current) => ({ ...current, [aliasId]: productId }))
        }
        onApprove={(aliasId) => void approveAlias(aliasId)}
      />
      <PosMissingRecipePanel
        items={posMissingRecipeProducts}
        isLoading={isLoadingPosAliases}
      />

      <div className="panel">
        <div className="panel-header">
          <h2>Fájl feltöltése</h2>
          <span className="panel-count">
            {summary.waitingBatches > 0
              ? `${summary.waitingBatches} feldolgozásra vár`
              : "Import"}
          </span>
        </div>

        {isGourmandImport ? <GourmandImportGuide selectedFiles={selectedFiles} /> : null}

        <form className={isGourmandImport ? "form-grid import-upload-form" : "form-grid"} onSubmit={handleSubmit}>
          {isGourmandImport ? (
            <>
              <label className={summaryFile ? "field import-upload-zone import-upload-zone-ready" : "field import-upload-zone"}>
                <span>Összesítő CSV</span>
                <strong>Kategóriák és termékárak</strong>
                <small>Egy fájl, az adott időszak összesített lekérdezése.</small>
                <input
                  ref={summaryFileInputRef}
                  type="file"
                  className="field-input"
                  accept=".csv,.txt"
                  onChange={() => void refreshSummaryFileSelection()}
                />
                <em>{summaryFile ? summaryFile.name : "Nincs kiválasztott összesítő"}</em>
              </label>
              <label className={detailFiles.length > 0 ? "field import-upload-zone import-upload-zone-ready" : "field import-upload-zone"}>
                <span>Tételes CSV-k</span>
                <strong>Nyugták és időpontok</strong>
                <small>Több heti tételes fájl is feltölthető ugyanahhoz az összesítőhöz.</small>
                <input
                  ref={detailFilesInputRef}
                  type="file"
                  className="field-input"
                  accept=".csv,.txt"
                  multiple
                  onChange={() => void appendDetailFileSelection()}
                />
                <em>
                  {detailFiles.length > 0
                    ? `${detailFiles.length} tételes fájl kiválasztva`
                    : "Nincs kiválasztott tételes fájl"}
                </em>
              </label>
            </>
          ) : (
            <label className="field">
              <span>Fájl</span>
              <input
                ref={genericFileInputRef}
                type="file"
                className="field-input"
                accept=".csv,.xlsx,.xls,.txt"
                onChange={() => void refreshGenericFileSelection()}
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
                ? "Feltöltés..."
                : isGourmandImport
                  ? "POS CSV csomag feltöltése"
                  : "Fájl feltöltése"}
            </button>
          </div>
        </form>
      </div>

      <section className="panel">
        <div className="panel-header">
          <h2>Import csomagok</h2>
          <span className="panel-count">{batches.length}</span>
        </div>

        {isLoading ? <p className="info-message">Import csomagok betöltése...</p> : null}

        {!isLoading && batches.length === 0 ? (
          <p className="empty-message">Nincs import csomag a kiválasztott szűrőkkel.</p>
        ) : null}

        {batches.length > 0 ? (
          <div className="import-batch-card-list">
            {batches.map((batch) => {
              const totalSize = batch.files.reduce((sum, file) => sum + file.size_bytes, 0);
              const isUploaded = batch.status === "uploaded";
              const isParsed = batch.status === "parsed";
              const canMapToFinance = [
                "pos_sales",
                "gourmand_pos_sales",
                "flow_pos_sales",
              ].includes(batch.import_type);
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
                  onClick={() => void toggleBatchDetails(batch.id)}
                >
                  <div className="import-batch-card-main">
                    <div className="import-batch-card-title">
                      <span className={`status-badge status-${batch.status}`}>
                        {getImportBatchStatusText(batch)}
                      </span>
                      <div>
                        <strong>{summarizeFiles(batch)}</strong>
                        <small>{formatImportPeriod(batch)} · {formatBytes(totalSize)}</small>
                      </div>
                    </div>

                    <div className="import-batch-card-metrics">
                      <span>
                        <strong>{batch.files.length}</strong>
                        Fájl
                      </span>
                      <span>
                        <strong>{batch.parsed_rows}/{batch.total_rows}</strong>
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
                        void registerBatch(batch);
                      }}
                      disabled={
                        registeredBatchIds[batch.id] ||
                        (!isUploaded && !isParsed) ||
                        !canMapToFinance ||
                        isParsing ||
                        isMapping
                      }
                    >
                      {isParsing || isMapping
                        ? "Rögzítés..."
                        : registeredBatchIds[batch.id]
                          ? "Rögzítés..."
                          : "Rögzítés"}
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

                      {isDetailsLoading ? (
                        <p className="info-message">Részletek betöltése...</p>
                      ) : null}
                      {!isDetailsLoading && detailsError ? (
                        <p className="error-message">{detailsError}</p>
                      ) : null}
                      {!isDetailsLoading && !detailsError ? (
                        <div className="import-batch-result-grid">
                          <span>
                            <strong>{details?.errors.length ?? 0}</strong>
                            Feldolgozási hiba
                          </span>
                          <span>
                            <strong>{details?.rows.length ?? 0}</strong>
                            Előkészített sor
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

        {batches.length > 0 ? (
          <div className="table-wrap import-batch-legacy-table">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Import típus</th>
                  <th>Státusz</th>
                  <th>Sorok</th>
                  <th>Időszak</th>
                  <th>Létrehozva</th>
                  <th>Eredeti fájlnév</th>
                  <th>Méret</th>
                  <th>Művelet</th>
                </tr>
              </thead>
              <tbody>
                {batches.map((batch) => {
                  const totalSize = batch.files.reduce((sum, file) => sum + file.size_bytes, 0);
                  const isUploaded = batch.status === "uploaded";
                  const isParsed = batch.status === "parsed";
                  const canMapToFinance = [
                    "pos_sales",
                    "gourmand_pos_sales",
                    "flow_pos_sales",
                  ].includes(batch.import_type);
                  const isParsing = parsingBatchId === batch.id;
                  const isMapping = mappingBatchId === batch.id;
                  const isPreparingWeather = weatherBackfillBatchId === batch.id;
                  const isExpanded = expandedBatchIds[batch.id] ?? false;
                  const isDetailsLoading = detailLoadingByBatchId[batch.id] ?? false;
                  const details = detailsByBatchId[batch.id];
                  const detailsError = detailErrorByBatchId[batch.id];

                  return (
                    <Fragment key={batch.id}>
                      <tr
                        className="import-batch-row"
                        onClick={() => void toggleBatchDetails(batch.id)}
                      >
                        <td>{formatImportType(batch.import_type)}</td>
                        <td>
                          <span className={`status-badge status-${batch.status}`}>
                            {formatImportStatus(batch.status)}
                          </span>
                        </td>
                        <td>
                          <div className="metric-stack">
                            <span>Összes: {batch.total_rows}</span>
                            <span>Feldolgozva: {batch.parsed_rows}</span>
                            <span>Hibák: {batch.error_rows}</span>
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
                                void registerBatch(batch);
                              }}
                              disabled={
                                registeredBatchIds[batch.id] ||
                                (!isUploaded && !isParsed) ||
                                !canMapToFinance ||
                                isParsing ||
                                isMapping
                              }
                            >
                              {isParsing ? "Feldolgozás..." : "Feldolgozás"}
                            </button>
                            <button
                              type="button"
                              className="secondary-button"
                              onClick={() => void mapBatch(batch.id)}
                              disabled={!isParsed || !canMapToFinance || isMapping}
                              title="A feldolgozott POS sorokból pénzügyi tranzakciókat rögzít. A már rögzített sorokat nem duplázza."
                            >
                              {isMapping ? "Rögzítés..." : "Pénzügyi rögzítés"}
                            </button>
                            <button
                              type="button"
                              className="secondary-button"
                              onClick={() => void toggleBatchDetails(batch.id)}
                            >
                              {isExpanded ? "Részletek elrejtése" : "Részletek"}
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
                                  <h3>Áttekintés</h3>
                                </div>
                                <SummaryPreview batch={batch} />
                              </section>

                              <section className="details-panel details-panel-wide">
                                <div className="details-panel-header">
                                  <h3>Időjárás</h3>
                                  <span className="panel-count">Időjárási adatok</span>
                                </div>
                                {isDetailsLoading ? (
                                  <p className="info-message">Időjárás-előkészítés betöltése...</p>
                                ) : null}
                                {!isDetailsLoading && !detailsError ? (
                                  <WeatherPreparationPanel
                                    recommendation={weatherByBatchId[batch.id]}
                                    isPreparing={isPreparingWeather}
                                    onPrepare={() => void prepareWeatherForBatch(batch.id)}
                                  />
                                ) : null}
                              </section>

                              <section className="details-panel">
                                <div className="details-panel-header">
                                  <h3>Sorok</h3>
                                  <span className="panel-count">
                                    {details?.rows.length ?? 0}
                                  </span>
                                </div>
                                {isDetailsLoading ? (
                                  <p className="info-message">Részletek betöltése...</p>
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
                                  <h3>Hibák</h3>
                                  <span className="panel-count">
                                    {details?.errors.length ?? 0}
                                  </span>
                                </div>
                                {isDetailsLoading ? (
                                  <p className="info-message">Részletek betöltése...</p>
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
