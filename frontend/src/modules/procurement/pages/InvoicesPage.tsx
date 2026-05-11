import { useEffect, useMemo, useState } from "react";

import { useTopbarControls } from "../../../shared/components/layout/TopbarControlsContext";
import type { InventoryItem } from "../../inventory/types/inventory";
import type { BusinessUnit, UnitOfMeasure, VatRate } from "../../masterData/types/masterData";
import type {
  PurchaseInvoice,
  PurchaseInvoiceCreatePayload,
  PurchaseInvoiceLineCreatePayload,
  PurchaseInvoicePdfDraft,
  PurchaseInvoicePdfReviewLineInput,
  PurchaseInvoicePdfReviewUpdatePayload,
  Supplier,
  SupplierItemAlias,
} from "../types/procurement";
import { usePurchaseInvoices } from "../hooks/usePurchaseInvoices";

type PurchaseInvoiceLineFormState = {
  inventory_item_id: string;
  description: string;
  quantity: string;
  uom_id: string;
  unit_net_amount: string;
  line_net_amount: string;
};

type PurchaseInvoiceFormState = {
  supplier_id: string;
  invoice_number: string;
  invoice_date: string;
  currency: string;
  gross_total: string;
  notes: string;
  lines: PurchaseInvoiceLineFormState[];
};

type PurchaseInvoicePdfReviewLineFormState = {
  description: string;
  supplier_product_name: string;
  inventory_item_id: string;
  quantity: string;
  uom_id: string;
  vat_rate_id: string;
  unit_net_amount: string;
  line_net_amount: string;
  vat_amount: string;
  line_gross_amount: string;
  notes: string;
  new_inventory_item_name: string;
  new_inventory_item_type: string;
  new_inventory_track_stock: boolean;
};

type PurchaseInvoicePdfReviewFormState = {
  supplier_id: string;
  invoice_number: string;
  invoice_date: string;
  currency: string;
  gross_total: string;
  notes: string;
  lines: PurchaseInvoicePdfReviewLineFormState[];
};

const INITIAL_LINE: PurchaseInvoiceLineFormState = {
  inventory_item_id: "",
  description: "",
  quantity: "",
  uom_id: "",
  unit_net_amount: "",
  line_net_amount: "",
};

const INITIAL_REVIEW_LINE: PurchaseInvoicePdfReviewLineFormState = {
  description: "",
  supplier_product_name: "",
  inventory_item_id: "",
  quantity: "",
  uom_id: "",
  vat_rate_id: "",
  unit_net_amount: "",
  line_net_amount: "",
  vat_amount: "",
  line_gross_amount: "",
  notes: "",
  new_inventory_item_name: "",
  new_inventory_item_type: "raw_material",
  new_inventory_track_stock: true,
};

const limitOptions = [25, 50, 100, 200];

function buildInitialForm(defaultSupplierId: string, defaultUomId: string) {
  return {
    supplier_id: defaultSupplierId,
    invoice_number: "",
    invoice_date: "",
    currency: "HUF",
    gross_total: "",
    notes: "",
    lines: [{ ...INITIAL_LINE, uom_id: defaultUomId }],
  };
}

function buildInitialPdfReviewForm(
  draft: PurchaseInvoicePdfDraft | null,
  defaultSupplierId: string,
  defaultUomId: string,
): PurchaseInvoicePdfReviewFormState {
  const header = draft?.review_payload?.header ?? {};
  const reviewedLines = draft?.review_payload?.lines ?? [];

  return {
    supplier_id: header.supplier_id ?? draft?.supplier_id ?? defaultSupplierId,
    invoice_number: header.invoice_number ?? "",
    invoice_date: header.invoice_date ?? "",
    currency: header.currency ?? "HUF",
    gross_total: header.gross_total ?? "",
    notes: header.notes ?? "",
    lines:
      reviewedLines.length > 0
        ? reviewedLines.map((line) => ({
            description: line.description ?? "",
            supplier_product_name: line.supplier_product_name ?? "",
            inventory_item_id: line.inventory_item_id ?? "",
            quantity: line.quantity ?? "",
            uom_id: line.uom_id ?? defaultUomId,
            vat_rate_id: line.vat_rate_id ?? "",
            unit_net_amount: line.unit_net_amount ?? "",
            line_net_amount: line.line_net_amount ?? "",
            vat_amount: line.vat_amount ?? "",
            line_gross_amount: line.line_gross_amount ?? "",
            notes: line.notes ?? "",
            new_inventory_item_name: "",
            new_inventory_item_type: "raw_material",
            new_inventory_track_stock: true,
          }))
        : [{ ...INITIAL_REVIEW_LINE, uom_id: defaultUomId }],
  };
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

function formatDate(value: string) {
  return new Intl.DateTimeFormat("hu-HU", {
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
  }).format(new Date(value));
}

function getUomLabel(item: UnitOfMeasure) {
  if (item.symbol) {
    return `${item.name} (${item.code} / ${item.symbol})`;
  }

  return `${item.name} (${item.code})`;
}

function buildLinePayload(line: PurchaseInvoiceLineFormState): PurchaseInvoiceLineCreatePayload {
  return {
    inventory_item_id: line.inventory_item_id || undefined,
    description: line.description.trim(),
    quantity: line.quantity.trim(),
    uom_id: line.uom_id,
    unit_net_amount: line.unit_net_amount.trim(),
    line_net_amount: line.line_net_amount.trim(),
  };
}

function compactOptional(value: string) {
  const trimmed = value.trim();
  return trimmed ? trimmed : undefined;
}

function buildReviewLinePayload(
  line: PurchaseInvoicePdfReviewLineFormState,
): PurchaseInvoicePdfReviewLineInput {
  return {
    description: line.description.trim(),
    supplier_product_name: compactOptional(line.supplier_product_name),
    inventory_item_id: compactOptional(line.inventory_item_id),
    quantity: compactOptional(line.quantity),
    uom_id: compactOptional(line.uom_id),
    vat_rate_id: compactOptional(line.vat_rate_id),
    unit_net_amount: compactOptional(line.unit_net_amount),
    line_net_amount: compactOptional(line.line_net_amount),
    vat_amount: compactOptional(line.vat_amount),
    line_gross_amount: compactOptional(line.line_gross_amount),
    notes: compactOptional(line.notes),
  };
}

function getInventoryItemById(items: InventoryItem[], inventoryItemId: string) {
  return items.find((item) => item.id === inventoryItemId) ?? null;
}

function getVatRateLabel(vatRate: VatRate) {
  return `${vatRate.name} (${Number(vatRate.rate_percent).toFixed(0)}%)`;
}

function getPostingStatusLabel(isPosted: boolean, movementCount: number) {
  if (!isPosted) {
    return "Rögzítve";
  }

  if (movementCount > 0) {
    return "Könyvelve és készletre véve";
  }

  return "Pénzügyre könyvelve";
}

function getPostingStatusClass(isPosted: boolean) {
  return isPosted ? "status-pill status-pill-success" : "status-pill";
}

function countUnmappedInvoiceLines(invoice: PurchaseInvoice) {
  return invoice.lines.filter((line) => !line.inventory_item_id).length;
}

function getInvoiceMappingStatusLabel(invoice: PurchaseInvoice) {
  const missingCount = countUnmappedInvoiceLines(invoice);
  if (missingCount === 0) {
    return "Inventory mapping rendben";
  }
  return `${missingCount} sor mapping nelkul`;
}

function getInvoiceMappingStatusClass(invoice: PurchaseInvoice) {
  return countUnmappedInvoiceLines(invoice) === 0
    ? "status-pill status-pill-success"
    : "status-pill status-pill-warning";
}

function getInvoiceTaxBreakdownStatusLabel(invoice: PurchaseInvoice) {
  const labels: Record<PurchaseInvoice["tax_breakdown_source"], string> = {
    supplier_invoice_actual: "Teljes ÁFA bontás",
    partial_supplier_invoice_actual: "Részleges ÁFA bontás",
    not_available: "Nincs ÁFA bontás",
  };
  return labels[invoice.tax_breakdown_source] ?? invoice.tax_breakdown_source;
}

function getInvoiceTaxBreakdownStatusClass(invoice: PurchaseInvoice) {
  if (invoice.tax_breakdown_source === "supplier_invoice_actual") {
    return "status-pill status-pill-success";
  }
  if (invoice.tax_breakdown_source === "partial_supplier_invoice_actual") {
    return "status-pill status-pill-warning";
  }
  return "status-pill status-pill-danger";
}

function getAliasStatusClass(status: string) {
  return status === "mapped" ? "status-pill status-pill-success" : "status-pill status-pill-warning";
}

function getPdfExtractionStatusLabel(status: string) {
  const labels: Record<string, string> = {
    parsed_review_required: "Előtöltve, review kell",
    no_candidates: "Nincs felismerhető adat",
    no_text: "Nincs PDF text layer",
    not_started: "Nincs indítva",
  };
  return labels[status] ?? status;
}

function getPdfExtractionStatusClass(status: string) {
  if (status === "parsed_review_required") {
    return "status-pill status-pill-warning";
  }
  if (status === "no_candidates" || status === "no_text") {
    return "status-pill status-pill-danger";
  }
  return "status-pill";
}

function formatConfidencePercent(value: string | null | undefined) {
  const parsed = Number(value);
  if (!Number.isFinite(parsed)) {
    return "-";
  }
  return `${Math.round(parsed * 100)}%`;
}

function getAliasInventoryItemName(alias: SupplierItemAlias, items: InventoryItem[]) {
  if (!alias.inventory_item_id) {
    return "-";
  }
  return getInventoryItemById(items, alias.inventory_item_id)?.name ?? alias.inventory_item_id;
}

function formatMoney(value: string, currency: string) {
  const parsed = Number(value);
  if (!Number.isFinite(parsed)) {
    return `${value} ${currency}`;
  }
  return new Intl.NumberFormat("hu-HU", {
    style: "currency",
    currency,
    maximumFractionDigits: 0,
  }).format(parsed);
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

function summarizeInvoices(invoices: PurchaseInvoice[]) {
  return invoices.reduce(
    (summary, invoice) => {
      const grossAmount = Number(invoice.gross_total);
      const netAmount = Number(invoice.net_total);
      const vatAmount = Number(invoice.vat_total ?? "0");
      summary.total += Number.isFinite(grossAmount) ? grossAmount : 0;
      summary.netTotal += Number.isFinite(netAmount) ? netAmount : 0;
      summary.vatTotal += Number.isFinite(vatAmount) ? vatAmount : 0;
      if (invoice.is_posted) {
        summary.posted += 1;
      }
      return summary;
    },
    { total: 0, netTotal: 0, vatTotal: 0, posted: 0 },
  );
}

function InvoicesHeaderControls({
  primaryBusinessUnits,
  technicalBusinessUnits,
  suppliers,
  selectedBusinessUnitId,
  setSelectedBusinessUnitId,
  selectedSupplierId,
  setSelectedSupplierId,
  limit,
  setLimit,
}: {
  primaryBusinessUnits: BusinessUnit[];
  technicalBusinessUnits: BusinessUnit[];
  suppliers: Supplier[];
  selectedBusinessUnitId: string;
  setSelectedBusinessUnitId: (value: string) => void;
  selectedSupplierId: string;
  setSelectedSupplierId: (value: string) => void;
  limit: number;
  setLimit: (value: number) => void;
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
          {primaryBusinessUnits.length > 0 ? (
            <optgroup label="Vállalkozások">
              {primaryBusinessUnits.map((businessUnit) => (
                <option key={businessUnit.id} value={businessUnit.id}>
                  {businessUnit.name}
                </option>
              ))}
            </optgroup>
          ) : null}
          {technicalBusinessUnits.length > 0 ? (
            <optgroup label="Technikai adatok">
              {technicalBusinessUnits.map((businessUnit) => (
                <option key={businessUnit.id} value={businessUnit.id}>
                  {businessUnit.name} ({businessUnit.code})
                </option>
              ))}
            </optgroup>
          ) : null}
        </select>
      </label>

      <label className="field topbar-field">
        <span>Beszállító</span>
        <select
          value={selectedSupplierId}
          onChange={(event) => setSelectedSupplierId(event.target.value)}
          className="field-input"
        >
          <option value="">Minden beszállító</option>
          {suppliers.map((supplier) => (
            <option key={supplier.id} value={supplier.id}>
              {supplier.name}
            </option>
          ))}
        </select>
      </label>

      <label className="field topbar-field topbar-field-compact">
        <span>Találat</span>
        <select
          value={String(limit)}
          onChange={(event) => setLimit(Number(event.target.value))}
          className="field-input"
        >
          {limitOptions.map((option) => (
            <option key={option} value={option}>
              {option}
            </option>
          ))}
        </select>
      </label>
    </div>
  );
}

export function InvoicesPage() {
  const { setControls } = useTopbarControls();
  const {
    primaryBusinessUnits,
    technicalBusinessUnits,
    suppliers,
    inventoryItems,
    unitsOfMeasure,
    vatRates,
    invoices,
    pdfDrafts,
    supplierItemAliases,
    selectedBusinessUnitId,
    setSelectedBusinessUnitId,
    selectedSupplierId,
    setSelectedSupplierId,
    limit,
    setLimit,
    createPurchaseInvoice,
    createPurchaseInvoiceFromPdfReview,
    createInventoryItemFromPdfReview,
    postPurchaseInvoice,
    uploadPurchaseInvoicePdfDraft,
    updatePurchaseInvoicePdfReview,
    approveSupplierItemAliasMapping,
    isSaving,
    isPosting,
    isUploadingPdfDraft,
    isUpdatingPdfReview,
    isApprovingSupplierAlias,
    isLoading,
    errorMessage,
  } = usePurchaseInvoices();

  const [actionMessage, setActionMessage] = useState("");
  const [actionErrorMessage, setActionErrorMessage] = useState("");
  const [selectedPdfFile, setSelectedPdfFile] = useState<File | null>(null);
  const [selectedPdfDraftId, setSelectedPdfDraftId] = useState("");
  const [aliasSelections, setAliasSelections] = useState<Record<string, string>>({});
  const [form, setForm] = useState<PurchaseInvoiceFormState>(() =>
    buildInitialForm("", "")
  );
  const [pdfReviewForm, setPdfReviewForm] = useState<PurchaseInvoicePdfReviewFormState>(() =>
    buildInitialPdfReviewForm(null, "", "")
  );
  const summary = summarizeInvoices(invoices);

  useEffect(() => {
    setControls(
      <InvoicesHeaderControls
        primaryBusinessUnits={primaryBusinessUnits}
        technicalBusinessUnits={technicalBusinessUnits}
        suppliers={suppliers}
        selectedBusinessUnitId={selectedBusinessUnitId}
        setSelectedBusinessUnitId={setSelectedBusinessUnitId}
        selectedSupplierId={selectedSupplierId}
        setSelectedSupplierId={setSelectedSupplierId}
        limit={limit}
        setLimit={setLimit}
      />,
    );

    return () => setControls(null);
  }, [
    limit,
    primaryBusinessUnits,
    selectedBusinessUnitId,
    selectedSupplierId,
    setControls,
    setLimit,
    setSelectedBusinessUnitId,
    setSelectedSupplierId,
    suppliers,
    technicalBusinessUnits,
  ]);

  useEffect(() => {
    if (!form.supplier_id && suppliers[0]?.id) {
      setForm((current) => ({ ...current, supplier_id: suppliers[0].id }));
    }
  }, [form.supplier_id, suppliers]);

  useEffect(() => {
    if (!form.lines[0]?.uom_id && unitsOfMeasure[0]?.id) {
      setForm((current) => ({
        ...current,
        lines: current.lines.map((line, index) =>
          index === 0 ? { ...line, uom_id: unitsOfMeasure[0].id } : line
        ),
      }));
    }
  }, [form.lines, unitsOfMeasure]);

  const canCreate = Boolean(
    selectedBusinessUnitId &&
      form.supplier_id &&
      form.invoice_number.trim() &&
      form.invoice_date &&
      form.gross_total.trim() &&
      form.lines.length > 0 &&
      form.lines.every(
        (line) =>
          line.description.trim() &&
          line.quantity.trim() &&
          line.uom_id &&
          line.unit_net_amount.trim() &&
          line.line_net_amount.trim()
      )
  );

  const totalLineCount = useMemo(
    () => invoices.reduce((sum, invoice) => sum + invoice.lines.length, 0),
    [invoices]
  );
  const pdfDraftsRequiringReview = useMemo(
    () => pdfDrafts.filter((draft) => draft.status === "review_required").length,
    [pdfDrafts],
  );
  const supplierAliasesRequiringReview = useMemo(
    () => supplierItemAliases.filter((alias) => alias.status !== "mapped").length,
    [supplierItemAliases],
  );
  const selectedPdfDraft = useMemo(
    () => pdfDrafts.find((draft) => draft.id === selectedPdfDraftId) ?? null,
    [pdfDrafts, selectedPdfDraftId],
  );

  useEffect(() => {
    if (selectedPdfDraftId && !selectedPdfDraft) {
      setSelectedPdfDraftId("");
    }
  }, [selectedPdfDraft, selectedPdfDraftId]);

  useEffect(() => {
    setAliasSelections((current) => {
      const next: Record<string, string> = {};
      supplierItemAliases.forEach((alias) => {
        next[alias.id] = current[alias.id] ?? alias.inventory_item_id ?? "";
      });
      return next;
    });
  }, [supplierItemAliases]);

  const updateLine = (
    index: number,
    updater: (line: PurchaseInvoiceLineFormState) => PurchaseInvoiceLineFormState
  ) => {
    setForm((current) => ({
      ...current,
      lines: current.lines.map((line, lineIndex) =>
        lineIndex === index ? updater(line) : line
      ),
    }));
  };

  const handleInventoryItemChange = (index: number, inventoryItemId: string) => {
    const selectedInventoryItem = getInventoryItemById(inventoryItems, inventoryItemId);
    updateLine(index, (line) => ({
      ...line,
      inventory_item_id: inventoryItemId,
      uom_id: selectedInventoryItem?.uom_id ?? line.uom_id,
    }));
  };

  const updateReviewLine = (
    index: number,
    updater: (
      line: PurchaseInvoicePdfReviewLineFormState
    ) => PurchaseInvoicePdfReviewLineFormState
  ) => {
    setPdfReviewForm((current) => ({
      ...current,
      lines: current.lines.map((line, lineIndex) =>
        lineIndex === index ? updater(line) : line
      ),
    }));
  };

  const handleReviewInventoryItemChange = (index: number, inventoryItemId: string) => {
    const selectedInventoryItem = getInventoryItemById(inventoryItems, inventoryItemId);
    updateReviewLine(index, (line) => ({
      ...line,
      inventory_item_id: inventoryItemId,
      uom_id: selectedInventoryItem?.uom_id ?? line.uom_id,
    }));
  };

  const selectPdfDraftForReview = (draft: PurchaseInvoicePdfDraft) => {
    setSelectedPdfDraftId(draft.id);
    setPdfReviewForm(
      buildInitialPdfReviewForm(
        draft,
        form.supplier_id || suppliers[0]?.id || "",
        unitsOfMeasure[0]?.id ?? "",
      ),
    );
  };

  const addReviewLine = () => {
    setPdfReviewForm((current) => ({
      ...current,
      lines: [
        ...current.lines,
        { ...INITIAL_REVIEW_LINE, uom_id: unitsOfMeasure[0]?.id ?? "" },
      ],
    }));
  };

  const removeReviewLine = (index: number) => {
    setPdfReviewForm((current) => ({
      ...current,
      lines: current.lines.filter((_, lineIndex) => lineIndex !== index),
    }));
  };

  const addLine = () => {
    setForm((current) => ({
      ...current,
      lines: [
        ...current.lines,
        { ...INITIAL_LINE, uom_id: unitsOfMeasure[0]?.id ?? "" },
      ],
    }));
  };

  const removeLine = (index: number) => {
    setForm((current) => ({
      ...current,
      lines: current.lines.filter((_, lineIndex) => lineIndex !== index),
    }));
  };

  const resetForm = () => {
    setForm(buildInitialForm(suppliers[0]?.id ?? "", unitsOfMeasure[0]?.id ?? ""));
  };

  const handleCreate = async () => {
    if (!selectedBusinessUnitId) {
      setActionMessage("");
      setActionErrorMessage("Számla létrehozásához válassz vállalkozást.");
      return;
    }

    if (!form.supplier_id) {
      setActionMessage("");
      setActionErrorMessage("Számla létrehozásához válassz beszállítót.");
      return;
    }

    const payload: PurchaseInvoiceCreatePayload = {
      business_unit_id: selectedBusinessUnitId,
      supplier_id: form.supplier_id,
      invoice_number: form.invoice_number.trim(),
      invoice_date: form.invoice_date,
      currency: form.currency.trim().toUpperCase(),
      gross_total: form.gross_total.trim(),
      notes: form.notes.trim() || undefined,
      lines: form.lines.map(buildLinePayload),
    };

    setActionMessage("");
    setActionErrorMessage("");

    try {
      await createPurchaseInvoice(payload);
      setActionMessage(`A(z) "${payload.invoice_number}" beszerzési számla létrejött.`);
      resetForm();
    } catch (error) {
      setActionErrorMessage(
        error instanceof Error ? error.message : "Nem sikerült létrehozni a számlát."
      );
    }
  };

  const handlePost = async (invoiceId: string, invoiceNumber: string) => {
    setActionMessage("");
    setActionErrorMessage("");

    try {
      const result = await postPurchaseInvoice(invoiceId);
      setActionMessage(
        `A(z) "${invoiceNumber}" számla könyvelve: ${result.created_financial_transactions} pénzügyi tranzakció, ${result.created_inventory_movements} készletmozgás, ${result.updated_inventory_item_costs} beszerzési költség frissítés.`
      );
    } catch (error) {
      setActionErrorMessage(
        error instanceof Error ? error.message : "Nem sikerült könyvelni a számlát."
      );
    }
  };

  const handlePdfDraftUpload = async () => {
    if (!selectedBusinessUnitId) {
      setActionMessage("");
      setActionErrorMessage("PDF feltolteshez valassz vallalkozast.");
      return;
    }
    if (!selectedPdfFile) {
      setActionMessage("");
      setActionErrorMessage("Valassz feltoltendo PDF szamlat.");
      return;
    }

    setActionMessage("");
    setActionErrorMessage("");
    try {
      const draft = await uploadPurchaseInvoicePdfDraft(
        selectedPdfFile,
        form.supplier_id || undefined,
      );
      setActionMessage(`A(z) "${draft.original_name}" PDF review draftra kerult.`);
      setSelectedPdfFile(null);
      selectPdfDraftForReview(draft);
    } catch (error) {
      setActionErrorMessage(
        error instanceof Error ? error.message : "Nem sikerult feltolteni a PDF szamlat.",
      );
    }
  };

  const canSavePdfReview = Boolean(
    selectedPdfDraft &&
      pdfReviewForm.lines.length > 0 &&
      pdfReviewForm.lines.every((line) => line.description.trim())
  );

  const handleSavePdfReview = async () => {
    if (!selectedPdfDraft) {
      setActionMessage("");
      setActionErrorMessage("Valassz PDF draftot a review mentesehez.");
      return;
    }

    const payload: PurchaseInvoicePdfReviewUpdatePayload = {
      supplier_id: compactOptional(pdfReviewForm.supplier_id),
      invoice_number: compactOptional(pdfReviewForm.invoice_number),
      invoice_date: compactOptional(pdfReviewForm.invoice_date),
      currency: pdfReviewForm.currency.trim().toUpperCase() || "HUF",
      gross_total: compactOptional(pdfReviewForm.gross_total),
      notes: compactOptional(pdfReviewForm.notes),
      lines: pdfReviewForm.lines.map(buildReviewLinePayload),
    };

    setActionMessage("");
    setActionErrorMessage("");
    try {
      const draft = await updatePurchaseInvoicePdfReview(selectedPdfDraft.id, payload);
      setActionMessage(`A(z) "${draft.original_name}" PDF review mentve.`);
      setSelectedPdfDraftId(draft.id);
      setPdfReviewForm(
        buildInitialPdfReviewForm(
          draft,
          form.supplier_id || suppliers[0]?.id || "",
          unitsOfMeasure[0]?.id ?? "",
        ),
      );
    } catch (error) {
      setActionErrorMessage(
        error instanceof Error ? error.message : "Nem sikerult menteni a PDF reviewt.",
      );
    }
  };

  const handleCreateInvoiceFromPdfReview = async () => {
    if (!selectedPdfDraft) {
      setActionMessage("");
      setActionErrorMessage("Valassz review-ready PDF draftot.");
      return;
    }

    setActionMessage("");
    setActionErrorMessage("");
    try {
      await createPurchaseInvoiceFromPdfReview(selectedPdfDraft.id);
      setActionMessage(
        `A(z) "${selectedPdfDraft.original_name}" review-bol vegleges beszerzesi szamla keszult.`,
      );
    } catch (error) {
      setActionErrorMessage(
        error instanceof Error
          ? error.message
          : "Nem sikerult vegleges szamlat letrehozni a PDF reviewbol.",
      );
    }
  };

  const handleCreateReviewInventoryItem = async (index: number) => {
    const line = pdfReviewForm.lines[index];
    if (!selectedBusinessUnitId || !line.uom_id || !line.new_inventory_item_name.trim()) {
      setActionMessage("");
      setActionErrorMessage("Uj torzselemhez belso nev, egyseg es vallalkozas kell.");
      return;
    }

    setActionMessage("");
    setActionErrorMessage("");
    try {
      const item = await createInventoryItemFromPdfReview({
        business_unit_id: selectedBusinessUnitId,
        name: line.new_inventory_item_name.trim(),
        item_type: line.new_inventory_item_type.trim() || "raw_material",
        uom_id: line.uom_id,
        track_stock: line.new_inventory_track_stock,
        is_active: true,
      });
      updateReviewLine(index, (current) => ({
        ...current,
        inventory_item_id: item.id,
        description: current.description.trim() || item.name,
        new_inventory_item_name: "",
      }));
      setActionMessage(`A(z) "${item.name}" belso torzselem letrejott es a sorhoz kapcsolodott.`);
    } catch (error) {
      setActionErrorMessage(
        error instanceof Error ? error.message : "Nem sikerult letrehozni a belso torzselemet.",
      );
    }
  };

  const handleApproveSupplierAlias = async (alias: SupplierItemAlias) => {
    const inventoryItemId = aliasSelections[alias.id] ?? "";
    if (!inventoryItemId) {
      setActionMessage("");
      setActionErrorMessage("Alias jovahagyasahoz valassz belso keszletelemet.");
      return;
    }

    const selectedInventoryItem = getInventoryItemById(inventoryItems, inventoryItemId);
    setActionMessage("");
    setActionErrorMessage("");
    try {
      const mappedAlias = await approveSupplierItemAliasMapping(alias.id, {
        inventory_item_id: inventoryItemId,
        internal_display_name:
          alias.internal_display_name ?? selectedInventoryItem?.name ?? undefined,
      });
      setActionMessage(
        `A(z) "${mappedAlias.source_item_name}" beszallitoi tetel kapcsolva.`,
      );
    } catch (error) {
      setActionErrorMessage(
        error instanceof Error ? error.message : "Nem sikerult jovahagyni az aliast.",
      );
    }
  };

  return (
    <section className="page-section">
      {actionMessage ? <p className="success-message">{actionMessage}</p> : null}
      {actionErrorMessage ? <p className="error-message">{actionErrorMessage}</p> : null}
      {errorMessage ? <p className="error-message">{errorMessage}</p> : null}
      {isLoading ? <p className="info-message">Beszerzési számlák betöltése...</p> : null}

      <div className="finance-summary-grid">
        <article className="finance-summary-card">
          <span>Bruttó összesen</span>
          <strong>{formatMoney(String(summary.total), "HUF")}</strong>
        </article>
        <article className="finance-summary-card">
          <span>Nettó összesen</span>
          <strong>{formatMoney(String(summary.netTotal), "HUF")}</strong>
        </article>
        <article className="finance-summary-card">
          <span>ÁFA összesen</span>
          <strong>{formatMoney(String(summary.vatTotal), "HUF")}</strong>
        </article>
        <article className="finance-summary-card">
          <span>Könyvelt számlák</span>
          <strong>{summary.posted}</strong>
        </article>
        <article className="finance-summary-card">
          <span>Találatok</span>
          <strong>{invoices.length}</strong>
        </article>
        <article className="finance-summary-card">
          <span>PDF review</span>
          <strong>{pdfDraftsRequiringReview}</strong>
        </article>
        <article className="finance-summary-card">
          <span>Alias review</span>
          <strong>{supplierAliasesRequiringReview}</strong>
        </article>
      </div>

      <section className="panel">
        <div className="panel-header">
          <h2>PDF szamla review</h2>
          <span className="panel-count">{pdfDrafts.length}</span>
        </div>

        <div className="form-grid inventory-edit-grid">
          <label className="field">
            <span>Beszallito</span>
            <select
              value={form.supplier_id}
              onChange={(event) =>
                setForm((current) => ({ ...current, supplier_id: event.target.value }))
              }
              className="field-input"
            >
              <option value="">Kesobb valasztom ki</option>
              {suppliers.map((supplier) => (
                <option key={supplier.id} value={supplier.id}>
                  {supplier.name}
                </option>
              ))}
            </select>
          </label>
          <label className="field">
            <span>PDF szamla</span>
            <input
              className="field-input"
              type="file"
              accept="application/pdf,.pdf"
              onChange={(event) => setSelectedPdfFile(event.target.files?.[0] ?? null)}
            />
          </label>
          <div className="form-actions">
            <button
              type="button"
              className="primary-button"
              disabled={!selectedPdfFile || isUploadingPdfDraft}
              onClick={() => void handlePdfDraftUpload()}
            >
              {isUploadingPdfDraft ? "Feltoltes..." : "PDF draft letrehozasa"}
            </button>
          </div>
        </div>

        {pdfDrafts.length === 0 ? (
          <p className="empty-message">Nincs feltoltott PDF szamla draft.</p>
        ) : (
          <div className="table-wrap">
            <table className="data-table details-table">
              <thead>
                <tr>
                  <th>Fajl</th>
                  <th>Statusz</th>
                  <th>Kinyeres</th>
                  <th>Meret</th>
                  <th>Feltoltve</th>
                  <th>Muvelet</th>
                </tr>
              </thead>
              <tbody>
                {pdfDrafts.map((draft) => (
                  <tr key={draft.id}>
                    <td>
                      <strong>{draft.original_name}</strong>
                      <div className="metric-stack">
                        <span>{draft.mime_type ?? "-"}</span>
                      </div>
                    </td>
                    <td>
                      <span className="status-pill status-pill-warning">
                        {draft.status}
                      </span>
                    </td>
                    <td>
                      <span className={getPdfExtractionStatusClass(draft.extraction_status)}>
                        {getPdfExtractionStatusLabel(draft.extraction_status)}
                      </span>
                    </td>
                    <td>{formatBytes(draft.size_bytes)}</td>
                    <td>{formatDateTime(draft.created_at)}</td>
                    <td>
                      <button
                        type="button"
                        className="secondary-button"
                        onClick={() => selectPdfDraftForReview(draft)}
                      >
                        Review
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {selectedPdfDraft ? (
          <div className="panel-subsection">
            <div className="panel-header">
              <h3>PDF review adatok</h3>
              <span className="panel-count">{selectedPdfDraft.original_name}</span>
            </div>

            <div className="form-grid inventory-edit-grid">
              <label className="field">
                <span>Beszallito</span>
                <select
                  value={pdfReviewForm.supplier_id}
                  onChange={(event) =>
                    setPdfReviewForm((current) => ({
                      ...current,
                      supplier_id: event.target.value,
                    }))
                  }
                  className="field-input"
                >
                  <option value="">Kesobb valasztom ki</option>
                  {suppliers.map((supplier) => (
                    <option key={supplier.id} value={supplier.id}>
                      {supplier.name}
                    </option>
                  ))}
                </select>
              </label>

              <label className="field">
                <span>Szamlaszam</span>
                <input
                  value={pdfReviewForm.invoice_number}
                  onChange={(event) =>
                    setPdfReviewForm((current) => ({
                      ...current,
                      invoice_number: event.target.value,
                    }))
                  }
                  className="field-input"
                />
              </label>

              <label className="field">
                <span>Szamla datuma</span>
                <input
                  type="date"
                  value={pdfReviewForm.invoice_date}
                  onChange={(event) =>
                    setPdfReviewForm((current) => ({
                      ...current,
                      invoice_date: event.target.value,
                    }))
                  }
                  className="field-input"
                />
              </label>

              <label className="field">
                <span>Penznem</span>
                <input
                  value={pdfReviewForm.currency}
                  onChange={(event) =>
                    setPdfReviewForm((current) => ({
                      ...current,
                      currency: event.target.value,
                    }))
                  }
                  className="field-input"
                />
              </label>

              <label className="field">
                <span>Brutto vegosszeg</span>
                <input
                  value={pdfReviewForm.gross_total}
                  onChange={(event) =>
                    setPdfReviewForm((current) => ({
                      ...current,
                      gross_total: event.target.value,
                    }))
                  }
                  className="field-input"
                />
              </label>

              <label className="field">
                <span>Megjegyzes</span>
                <textarea
                  value={pdfReviewForm.notes}
                  onChange={(event) =>
                    setPdfReviewForm((current) => ({
                      ...current,
                      notes: event.target.value,
                    }))
                  }
                  className="field-input"
                  rows={3}
                />
              </label>
            </div>

            <div className="panel-subsection">
              <div className="panel-header">
                <h3>Review sorok</h3>
                <span className="panel-count">{pdfReviewForm.lines.length}</span>
              </div>

              {pdfReviewForm.lines.map((line, index) => {
                const reviewedLine = selectedPdfDraft.review_payload?.lines[index];
                return (
                  <div key={`pdf-review-line-${index}`} className="form-grid inventory-movement-create-grid">
                    <label className="field">
                      <span>Szamlai tetelnev</span>
                      <input
                        value={line.supplier_product_name}
                        onChange={(event) =>
                          updateReviewLine(index, (current) => ({
                            ...current,
                            supplier_product_name: event.target.value,
                          }))
                        }
                        className="field-input"
                      />
                    </label>

                    <label className="field">
                      <span>Belso nev / leiras</span>
                      <input
                        value={line.description}
                        onChange={(event) =>
                          updateReviewLine(index, (current) => ({
                            ...current,
                            description: event.target.value,
                          }))
                        }
                        className="field-input"
                      />
                    </label>

                    <label className="field">
                      <span>Keszletelem</span>
                      <select
                        value={line.inventory_item_id}
                        onChange={(event) =>
                          handleReviewInventoryItemChange(index, event.target.value)
                        }
                        className="field-input"
                      >
                        <option value="">Nincs kapcsolva</option>
                        {inventoryItems.map((item) => (
                          <option key={item.id} value={item.id}>
                            {item.name} ({item.item_type})
                          </option>
                        ))}
                      </select>
                    </label>

                    <label className="field">
                      <span>Uj belso torzsnev</span>
                      <input
                        value={line.new_inventory_item_name}
                        onChange={(event) =>
                          updateReviewLine(index, (current) => ({
                            ...current,
                            new_inventory_item_name: event.target.value,
                          }))
                        }
                        className="field-input"
                        placeholder={line.description || line.supplier_product_name}
                      />
                    </label>

                    <label className="field">
                      <span>Uj elem tipusa</span>
                      <select
                        value={line.new_inventory_item_type}
                        onChange={(event) =>
                          updateReviewLine(index, (current) => ({
                            ...current,
                            new_inventory_item_type: event.target.value,
                          }))
                        }
                        className="field-input"
                      >
                        <option value="raw_material">Alapanyag</option>
                        <option value="finished_product">Kesztermek / aru</option>
                        <option value="beverage">Ital</option>
                        <option value="packaging">Csomagoloanyag</option>
                        <option value="service">Szolgaltatas</option>
                      </select>
                    </label>

                    <label className="field checkbox-field">
                      <span>Keszletkovetes</span>
                      <input
                        type="checkbox"
                        checked={line.new_inventory_track_stock}
                        onChange={(event) =>
                          updateReviewLine(index, (current) => ({
                            ...current,
                            new_inventory_track_stock: event.target.checked,
                          }))
                        }
                      />
                    </label>

                    <label className="field">
                      <span>Mennyiseg</span>
                      <input
                        value={line.quantity}
                        onChange={(event) =>
                          updateReviewLine(index, (current) => ({
                            ...current,
                            quantity: event.target.value,
                          }))
                        }
                        className="field-input"
                      />
                    </label>

                    <label className="field">
                      <span>Egyseg</span>
                      <select
                        value={line.uom_id}
                        onChange={(event) =>
                          updateReviewLine(index, (current) => ({
                            ...current,
                            uom_id: event.target.value,
                          }))
                        }
                        className="field-input"
                      >
                        <option value="">Nincs megadva</option>
                        {unitsOfMeasure.map((unit) => (
                          <option key={unit.id} value={unit.id}>
                            {getUomLabel(unit)}
                          </option>
                        ))}
                      </select>
                    </label>

                    <label className="field">
                      <span>AFA kulcs</span>
                      <select
                        value={line.vat_rate_id}
                        onChange={(event) =>
                          updateReviewLine(index, (current) => ({
                            ...current,
                            vat_rate_id: event.target.value,
                          }))
                        }
                        className="field-input"
                      >
                        <option value="">Nincs megadva</option>
                        {vatRates.map((vatRate) => (
                          <option key={vatRate.id} value={vatRate.id}>
                            {getVatRateLabel(vatRate)}
                          </option>
                        ))}
                      </select>
                    </label>

                    <label className="field">
                      <span>Netto sor</span>
                      <input
                        value={line.line_net_amount}
                        onChange={(event) =>
                          updateReviewLine(index, (current) => ({
                            ...current,
                            line_net_amount: event.target.value,
                          }))
                        }
                        className="field-input"
                      />
                    </label>

                    <label className="field">
                      <span>AFA osszeg</span>
                      <input
                        value={line.vat_amount}
                        onChange={(event) =>
                          updateReviewLine(index, (current) => ({
                            ...current,
                            vat_amount: event.target.value,
                          }))
                        }
                        className="field-input"
                      />
                    </label>

                    <label className="field">
                      <span>Brutto sor</span>
                      <input
                        value={line.line_gross_amount}
                        onChange={(event) =>
                          updateReviewLine(index, (current) => ({
                            ...current,
                            line_gross_amount: event.target.value,
                          }))
                        }
                        className="field-input"
                      />
                    </label>

                    <label className="field">
                      <span>Netto egysegar</span>
                      <input
                        value={line.unit_net_amount}
                        onChange={(event) =>
                          updateReviewLine(index, (current) => ({
                            ...current,
                            unit_net_amount: event.target.value,
                          }))
                        }
                        className="field-input"
                      />
                    </label>

                    <div className="metric-stack">
                      <span className={reviewedLine?.calculation_status === "ok" ? "status-pill status-pill-success" : "status-pill status-pill-warning"}>
                        {reviewedLine?.calculation_status ?? "nincs mentve"}
                      </span>
                      <small>
                        Netto {reviewedLine?.line_net_amount ?? "-"} / AFA {reviewedLine?.vat_amount ?? "-"} / Brutto {reviewedLine?.line_gross_amount ?? "-"}
                      </small>
                      {reviewedLine?.extraction_confidence_score ? (
                        <small>
                          PDF bizalom: {formatConfidencePercent(reviewedLine.extraction_confidence_score)}
                        </small>
                      ) : null}
                      {reviewedLine?.calculation_issues.length ? (
                        <small>{reviewedLine.calculation_issues.join(", ")}</small>
                      ) : null}
                    </div>

                    <div className="inline-actions">
                      <button
                        type="button"
                        className="secondary-button"
                        onClick={() => void handleCreateReviewInventoryItem(index)}
                        disabled={
                          isSaving ||
                          !line.new_inventory_item_name.trim() ||
                          !line.uom_id
                        }
                      >
                        Uj torzselem
                      </button>
                      <button
                        type="button"
                        className="secondary-button"
                        onClick={() => removeReviewLine(index)}
                        disabled={pdfReviewForm.lines.length === 1 || isUpdatingPdfReview}
                      >
                        Sor torlese
                      </button>
                    </div>
                  </div>
                );
              })}

              <div className="inline-actions">
                <button
                  type="button"
                  className="secondary-button"
                  onClick={addReviewLine}
                  disabled={isUpdatingPdfReview}
                >
                  Review sor hozzaadasa
                </button>
                <button
                  type="button"
                  className="primary-button"
                  onClick={() => void handleSavePdfReview()}
                  disabled={!canSavePdfReview || isUpdatingPdfReview}
                >
                  {isUpdatingPdfReview ? "Review mentese..." : "PDF review mentese"}
                </button>
                <button
                  type="button"
                  className="primary-button"
                  onClick={() => void handleCreateInvoiceFromPdfReview()}
                  disabled={selectedPdfDraft.status !== "review_ready" || isSaving}
                >
                  Vegleges szamla letrehozasa
                </button>
              </div>
            </div>
          </div>
        ) : null}
      </section>

      <section className="panel">
        <div className="panel-header">
          <h2>Beszallitoi alias munkalista</h2>
          <span className="panel-count">{supplierItemAliases.length}</span>
        </div>

        {supplierItemAliases.length === 0 ? (
          <p className="empty-message">Nincs beszallitoi tetel alias a kivalasztott szurokkel.</p>
        ) : (
          <div className="table-wrap">
            <table className="data-table details-table">
              <thead>
                <tr>
                  <th>Szamlai tetelnev</th>
                  <th>Belso nev</th>
                  <th>Beszallito</th>
                  <th>Statusz</th>
                  <th>Kapcsolt elem</th>
                  <th>Elfordulas</th>
                  <th>Muvelet</th>
                </tr>
              </thead>
              <tbody>
                {supplierItemAliases.map((alias) => {
                  const supplierName =
                    suppliers.find((supplier) => supplier.id === alias.supplier_id)?.name ??
                    alias.supplier_id;
                  return (
                    <tr key={alias.id}>
                      <td>
                        <strong>{alias.source_item_name}</strong>
                        <div className="metric-stack">
                          <span>{alias.source_item_key}</span>
                        </div>
                      </td>
                      <td>{alias.internal_display_name ?? "-"}</td>
                      <td>{supplierName}</td>
                      <td>
                        <span className={getAliasStatusClass(alias.status)}>
                          {alias.status}
                        </span>
                      </td>
                      <td>
                        <select
                          value={aliasSelections[alias.id] ?? alias.inventory_item_id ?? ""}
                          onChange={(event) =>
                            setAliasSelections((current) => ({
                              ...current,
                              [alias.id]: event.target.value,
                            }))
                          }
                          className="field-input"
                        >
                          <option value="">Nincs kapcsolva</option>
                          {inventoryItems.map((item) => (
                            <option key={item.id} value={item.id}>
                              {item.name} ({item.item_type})
                            </option>
                          ))}
                        </select>
                        <small>{getAliasInventoryItemName(alias, inventoryItems)}</small>
                      </td>
                      <td>
                        <div className="metric-stack">
                          <span>{alias.occurrence_count} sor</span>
                          <span>{formatDateTime(alias.last_seen_at)}</span>
                        </div>
                      </td>
                      <td>
                        <button
                          type="button"
                          className="secondary-button"
                          disabled={
                            isApprovingSupplierAlias ||
                            !(aliasSelections[alias.id] ?? alias.inventory_item_id)
                          }
                          onClick={() => void handleApproveSupplierAlias(alias)}
                        >
                          Jovahagyas
                        </button>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </section>

      <section className="panel">
        <div className="panel-header">
          <h2>Új beszerzési számla</h2>
          <span className="panel-count">{totalLineCount} sor</span>
        </div>

        {suppliers.length === 0 ? (
          <p className="empty-message">
            Számlarögzítés előtt hozz létre legalább egy beszállítót a kiválasztott vállalkozáshoz.
          </p>
        ) : (
          <>
            <div className="form-grid inventory-edit-grid">
              <label className="field">
                <span>Beszállító</span>
                <select
                  value={form.supplier_id}
                  onChange={(event) =>
                    setForm((current) => ({ ...current, supplier_id: event.target.value }))
                  }
                  className="field-input"
                >
                  {suppliers.map((supplier) => (
                    <option key={supplier.id} value={supplier.id}>
                      {supplier.name}
                    </option>
                  ))}
                </select>
              </label>

              <label className="field">
                <span>Számlaszám</span>
                <input
                  value={form.invoice_number}
                  onChange={(event) =>
                    setForm((current) => ({
                      ...current,
                      invoice_number: event.target.value,
                    }))
                  }
                  className="field-input"
                />
              </label>

              <label className="field">
                <span>Számla dátuma</span>
                <input
                  type="date"
                  value={form.invoice_date}
                  onChange={(event) =>
                    setForm((current) => ({ ...current, invoice_date: event.target.value }))
                  }
                  className="field-input"
                />
              </label>

              <label className="field">
                <span>Pénznem</span>
                <input
                  value={form.currency}
                  onChange={(event) =>
                    setForm((current) => ({ ...current, currency: event.target.value }))
                  }
                  className="field-input"
                />
              </label>

              <label className="field">
                <span>Bruttó végösszeg</span>
                <input
                  value={form.gross_total}
                  onChange={(event) =>
                    setForm((current) => ({ ...current, gross_total: event.target.value }))
                  }
                  className="field-input"
                  placeholder="pl. 12500.00"
                />
              </label>

              <label className="field">
                <span>Megjegyzés</span>
                <textarea
                  value={form.notes}
                  onChange={(event) =>
                    setForm((current) => ({ ...current, notes: event.target.value }))
                  }
                  className="field-input"
                  rows={3}
                />
              </label>
            </div>

            <div className="panel-subsection">
              <div className="panel-header">
                <h3>Számlasorok</h3>
                <span className="panel-count">{form.lines.length}</span>
              </div>

              {form.lines.map((line, index) => (
                <div key={`invoice-line-${index}`} className="form-grid inventory-movement-create-grid">
                  <label className="field">
                    <span>Készletelem</span>
                    <select
                      value={line.inventory_item_id}
                      onChange={(event) =>
                        handleInventoryItemChange(index, event.target.value)
                      }
                      className="field-input"
                    >
                      <option value="">Nincs kapcsolva</option>
                      {inventoryItems.map((item) => (
                        <option key={item.id} value={item.id}>
                          {item.name} ({item.item_type})
                        </option>
                      ))}
                    </select>
                  </label>

                  <label className="field">
                    <span>Leírás</span>
                    <input
                      value={line.description}
                      onChange={(event) =>
                        updateLine(index, (current) => ({
                          ...current,
                          description: event.target.value,
                        }))
                      }
                      className="field-input"
                    />
                  </label>

                  <label className="field">
                    <span>Mennyiség</span>
                    <input
                      value={line.quantity}
                      onChange={(event) =>
                        updateLine(index, (current) => ({
                          ...current,
                          quantity: event.target.value,
                        }))
                      }
                      className="field-input"
                    />
                  </label>

                  <label className="field">
                    <span>Egység</span>
                    <select
                      value={line.uom_id}
                      onChange={(event) =>
                        updateLine(index, (current) => ({
                          ...current,
                          uom_id: event.target.value,
                        }))
                      }
                      className="field-input"
                    >
                      {unitsOfMeasure.map((unit) => (
                        <option key={unit.id} value={unit.id}>
                          {getUomLabel(unit)}
                        </option>
                      ))}
                    </select>
                  </label>

                  <label className="field">
                    <span>Nettó egységár</span>
                    <input
                      value={line.unit_net_amount}
                      onChange={(event) =>
                        updateLine(index, (current) => ({
                          ...current,
                          unit_net_amount: event.target.value,
                        }))
                      }
                      className="field-input"
                    />
                  </label>

                  <label className="field">
                    <span>Nettó sorösszeg</span>
                    <input
                      value={line.line_net_amount}
                      onChange={(event) =>
                        updateLine(index, (current) => ({
                          ...current,
                          line_net_amount: event.target.value,
                        }))
                      }
                      className="field-input"
                    />
                  </label>

                  <div className="inline-actions">
                    <button
                      type="button"
                      className="secondary-button"
                      onClick={() => removeLine(index)}
                      disabled={form.lines.length === 1 || isSaving}
                    >
                      Sor törlése
                    </button>
                  </div>
                </div>
              ))}

              <div className="inline-actions">
                <button
                  type="button"
                  className="secondary-button"
                  onClick={addLine}
                  disabled={isSaving}
                >
                  Sor hozzáadása
                </button>
              </div>
            </div>

            <div className="inline-actions">
              <button
                type="button"
                className="primary-button"
                onClick={handleCreate}
                disabled={isSaving || !canCreate}
              >
                Számla létrehozása
              </button>
            </div>
          </>
        )}
      </section>

      <section className="panel">
        <div className="panel-header">
          <h2>Beszerzési számlák</h2>
          <span className="panel-count">{invoices.length}</span>
        </div>

        {!isLoading && invoices.length === 0 ? (
          <p className="empty-message">
            Nincs beszerzési számla a kiválasztott szűrőkkel.
          </p>
        ) : null}

        {invoices.length > 0 ? (
          <div className="table-wrap">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Számlaszám</th>
                  <th>Beszállító</th>
                  <th>Dátum</th>
                  <th>Pénznem</th>
                  <th>Bruttó összeg</th>
                  <th>Nettó / ÁFA</th>
                  <th>ÁFA forrás</th>
                  <th>Sorok</th>
                  <th>Mapping</th>
                  <th>Státusz</th>
                  <th>Frissítve</th>
                  <th>Művelet</th>
                </tr>
              </thead>
              <tbody>
                {invoices.map((invoice) => (
                  <tr key={invoice.id}>
                    <td>{invoice.invoice_number}</td>
                    <td>{invoice.supplier_name}</td>
                    <td>{formatDate(invoice.invoice_date)}</td>
                    <td>{invoice.currency}</td>
                    <td>{formatMoney(invoice.gross_total, invoice.currency)}</td>
                    <td>
                      {formatMoney(invoice.net_total, invoice.currency)} /{" "}
                      {invoice.vat_total
                        ? formatMoney(invoice.vat_total, invoice.currency)
                        : "-"}
                    </td>
                    <td>
                      <span className={getInvoiceTaxBreakdownStatusClass(invoice)}>
                        {getInvoiceTaxBreakdownStatusLabel(invoice)}
                      </span>
                    </td>
                    <td>{invoice.lines.length}</td>
                    <td>
                      <span className={getInvoiceMappingStatusClass(invoice)}>
                        {getInvoiceMappingStatusLabel(invoice)}
                      </span>
                    </td>
                    <td>
                      <span className={getPostingStatusClass(invoice.is_posted)}>
                        {getPostingStatusLabel(
                          invoice.is_posted,
                          invoice.posted_inventory_movement_count
                        )}
                      </span>
                    </td>
                    <td>{formatDateTime(invoice.updated_at)}</td>
                    <td>
                      <button
                        type="button"
                        className="secondary-button"
                        onClick={() => handlePost(invoice.id, invoice.invoice_number)}
                        disabled={isPosting || invoice.is_posted}
                      >
                        Könyvelés
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : null}
      </section>
    </section>
  );
}
