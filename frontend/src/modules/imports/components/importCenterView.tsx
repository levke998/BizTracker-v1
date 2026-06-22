import type { ReactNode } from "react";

import type { Product, UnitOfMeasure } from "../../masterData/types/masterData";
import type { PosProductAlias } from "../../posIngestion/types/posIngestion";
import type { ImportBatch } from "../types/imports";

export type GourmandFileKind = "summary" | "detail" | "unknown";

export type SelectedImportFile = {
  name: string;
  kind: GourmandFileKind;
};

export type QuickProductForm = {
  name: string;
  sku: string;
  categoryId: string;
  salesUomId: string;
  vatRateId: string;
  productType: string;
  salePriceGross: string;
};

const importTypeLabels: Record<string, string> = {
  pos_sales: "POS eladasok",
  gourmand_pos_sales: "Gourmand POS CSV",
  flow_pos_sales: "Flow POS CSV",
  supplier_invoice: "Beszerzesi szamlak",
  ticket_sales: "Jegyeladasok",
  bar_sales: "Bar eladasok",
};

const importStatusLabels: Record<string, string> = {
  uploaded: "Feltoltve",
  parsing: "Feldolgozas alatt",
  parsed: "Feldolgozva",
  failed: "Hibas",
};

const rowStatusLabels: Record<string, string> = {
  pending: "Varakozik",
  parsed: "Feldolgozva",
  failed: "Hibas",
  skipped: "Kihagyva",
};

export const gourmandFileKindLabels: Record<GourmandFileKind, string> = {
  summary: "Osszesito",
  detail: "Teteles",
  unknown: "Nem felismert",
};

export function buildQuickProductForm(
  alias: PosProductAlias,
  units: UnitOfMeasure[],
): QuickProductForm {
  const defaultUnit =
    units.find((unit) => unit.code === "pcs") ??
    units.find((unit) => unit.code === "db") ??
    units[0];
  return {
    name: alias.source_product_name,
    sku: alias.source_sku ?? "",
    categoryId: "",
    salesUomId: defaultUnit?.id ?? "",
    vatRateId: "",
    productType: "finished_good",
    salePriceGross: "",
  };
}

export function classifyGourmandFile(content: string, fileName: string): GourmandFileKind {
  const normalizedName = fileName.toLocaleLowerCase("hu-HU");
  const normalizedContent = content.toLocaleUpperCase("hu-HU");

  if (
    normalizedContent.includes("NAPI OSSZESITES") ||
    normalizedName.includes("osszesites") ||
    normalizedName.includes("osszesites")
  ) {
    return "summary";
  }

  if (
    normalizedContent.includes("TETELES RENDELESEK") ||
    normalizedName.includes("teteles") ||
    normalizedName.includes("teteles")
  ) {
    return "detail";
  }

  return "unknown";
}

export function formatDateTime(value: string) {
  return new Intl.DateTimeFormat("hu-HU", {
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  }).format(new Date(value));
}

export function formatMoney(value: string | number | null | undefined) {
  const parsed = Number(value ?? 0);
  return new Intl.NumberFormat("hu-HU", {
    style: "currency",
    currency: "HUF",
    maximumFractionDigits: 0,
  }).format(Number.isFinite(parsed) ? parsed : 0);
}

export function formatDate(value: string | null) {
  if (!value) {
    return "-";
  }
  return value.replace(/-/g, ". ");
}

export function formatImportPeriod(batch: ImportBatch) {
  if (!batch.first_occurred_at || !batch.last_occurred_at) {
    return "Idoszak: feldolgozas utan latszik";
  }
  return `${formatDateTime(batch.first_occurred_at)} - ${formatDateTime(
    batch.last_occurred_at,
  )}`;
}

export function formatBytes(value: number) {
  if (value < 1024) {
    return `${value} B`;
  }
  if (value < 1024 * 1024) {
    return `${(value / 1024).toFixed(1)} KB`;
  }
  return `${(value / (1024 * 1024)).toFixed(1)} MB`;
}

export function formatImportType(value: string) {
  return importTypeLabels[value] ?? value;
}

export function formatImportStatus(value: string) {
  return importStatusLabels[value] ?? value;
}

export function formatRowStatus(value: string) {
  return rowStatusLabels[value] ?? value;
}

export function summarizeBatches(batches: ImportBatch[]) {
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

export function summarizeFiles(batch: ImportBatch) {
  if (batch.files.length === 0) {
    return "-";
  }
  if (batch.files.length === 1) {
    return batch.files[0].original_name;
  }
  return `${batch.files.length} fajl`;
}

export function hasReadyGourmandPackage(files: SelectedImportFile[]) {
  return (
    files.some((file) => file.kind === "summary") &&
    files.some((file) => file.kind === "detail") &&
    files.every((file) => file.kind !== "unknown")
  );
}

export function renderPayload(payload: Record<string, unknown> | null): ReactNode {
  if (!payload) {
    return "-";
  }
  return <pre className="json-preview">{JSON.stringify(payload, null, 2)}</pre>;
}

export function getImportBatchStatusText(batch: ImportBatch) {
  if (batch.error_rows > 0 || batch.status === "failed") {
    return "Ellenorzest igenyel";
  }
  if (batch.status === "parsed") {
    return "Rogzitesre kesz";
  }
  if (batch.status === "uploaded") {
    return "Feltoltve";
  }
  return formatImportStatus(batch.status);
}

export function formatAliasStatus(value: string) {
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

export function formatMappingReadinessStatus(value: string) {
  if (value === "complete") {
    return "Teljes";
  }
  if (value === "partial") {
    return "Reszleges";
  }
  if (value === "missing") {
    return "Nincs jovahagyott mapping";
  }
  return "Nincs POS adat";
}

export function toCatalogProductOptionLabel(product: Product) {
  return `${product.name}${product.sku ? ` (${product.sku})` : ""}`;
}
