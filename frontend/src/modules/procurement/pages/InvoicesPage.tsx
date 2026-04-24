import { useEffect, useMemo, useState } from "react";

import type { InventoryItem } from "../../inventory/types/inventory";
import type { UnitOfMeasure } from "../../masterData/types/masterData";
import type {
  PurchaseInvoiceCreatePayload,
  PurchaseInvoiceLineCreatePayload,
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

const INITIAL_LINE: PurchaseInvoiceLineFormState = {
  inventory_item_id: "",
  description: "",
  quantity: "",
  uom_id: "",
  unit_net_amount: "",
  line_net_amount: "",
};

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

function getInventoryItemById(items: InventoryItem[], inventoryItemId: string) {
  return items.find((item) => item.id === inventoryItemId) ?? null;
}

function getPostingStatusLabel(isPosted: boolean, movementCount: number) {
  if (!isPosted) {
    return "Pending";
  }

  if (movementCount > 0) {
    return "Posted";
  }

  return "Posted to finance";
}

export function InvoicesPage() {
  const {
    primaryBusinessUnits,
    technicalBusinessUnits,
    suppliers,
    inventoryItems,
    unitsOfMeasure,
    invoices,
    selectedBusinessUnitId,
    setSelectedBusinessUnitId,
    selectedSupplierId,
    setSelectedSupplierId,
    limit,
    setLimit,
    createPurchaseInvoice,
    postPurchaseInvoice,
    isSaving,
    isPosting,
    isLoading,
    errorMessage,
  } = usePurchaseInvoices();

  const [actionMessage, setActionMessage] = useState("");
  const [actionErrorMessage, setActionErrorMessage] = useState("");
  const [form, setForm] = useState<PurchaseInvoiceFormState>(() =>
    buildInitialForm("", "")
  );

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
      setActionErrorMessage("Select a business unit before creating an invoice.");
      return;
    }

    if (!form.supplier_id) {
      setActionMessage("");
      setActionErrorMessage("Select a supplier before creating an invoice.");
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
      setActionMessage(`Purchase invoice "${payload.invoice_number}" created successfully.`);
      resetForm();
    } catch (error) {
      setActionErrorMessage(
        error instanceof Error ? error.message : "Failed to create purchase invoice."
      );
    }
  };

  const handlePost = async (invoiceId: string, invoiceNumber: string) => {
    setActionMessage("");
    setActionErrorMessage("");

    try {
      const result = await postPurchaseInvoice(invoiceId);
      setActionMessage(
        `Purchase invoice "${invoiceNumber}" posted: ${result.created_financial_transactions} finance transaction, ${result.created_inventory_movements} inventory movements.`
      );
    } catch (error) {
      setActionErrorMessage(
        error instanceof Error ? error.message : "Failed to post purchase invoice."
      );
    }
  };

  return (
    <section className="page-section">
      <section className="panel">
        <div className="panel-header">
          <h2>Purchase Invoices</h2>
          <span className="panel-count">{invoices.length}</span>
        </div>

        <div className="form-grid inventory-filter-grid">
          <label className="field">
            <span>Business unit</span>
            <select
              value={selectedBusinessUnitId}
              onChange={(event) => setSelectedBusinessUnitId(event.target.value)}
              className="field-input"
            >
              <option value="">Select a business unit</option>
              {primaryBusinessUnits.length > 0 ? (
                <optgroup label="Business units">
                  {primaryBusinessUnits.map((businessUnit) => (
                    <option key={businessUnit.id} value={businessUnit.id}>
                      {businessUnit.name}
                    </option>
                  ))}
                </optgroup>
              ) : null}
              {technicalBusinessUnits.length > 0 ? (
                <optgroup label="Technical">
                  {technicalBusinessUnits.map((businessUnit) => (
                    <option key={businessUnit.id} value={businessUnit.id}>
                      {businessUnit.name} ({businessUnit.code})
                    </option>
                  ))}
                </optgroup>
              ) : null}
            </select>
          </label>

          <label className="field">
            <span>Supplier filter</span>
            <select
              value={selectedSupplierId}
              onChange={(event) => setSelectedSupplierId(event.target.value)}
              className="field-input"
            >
              <option value="">All suppliers</option>
              {suppliers.map((supplier) => (
                <option key={supplier.id} value={supplier.id}>
                  {supplier.name}
                </option>
              ))}
            </select>
          </label>

          <label className="field">
            <span>Limit</span>
            <select
              value={String(limit)}
              onChange={(event) => setLimit(Number(event.target.value))}
              className="field-input"
            >
              <option value="25">25</option>
              <option value="50">50</option>
              <option value="100">100</option>
              <option value="200">200</option>
            </select>
          </label>
        </div>

        {actionMessage ? <p className="success-message">{actionMessage}</p> : null}
        {actionErrorMessage ? <p className="error-message">{actionErrorMessage}</p> : null}
        {errorMessage ? <p className="error-message">{errorMessage}</p> : null}
        {isLoading ? <p className="info-message">Loading purchase invoices...</p> : null}
      </section>

      <section className="panel">
        <div className="panel-header">
          <h2>Create purchase invoice</h2>
          <span className="panel-count">{totalLineCount} lines</span>
        </div>

        {suppliers.length === 0 ? (
          <p className="empty-message">
            Create at least one supplier for the selected business unit before adding invoices.
          </p>
        ) : (
          <>
            <div className="form-grid inventory-edit-grid">
              <label className="field">
                <span>Supplier</span>
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
                <span>Invoice number</span>
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
                <span>Invoice date</span>
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
                <span>Currency</span>
                <input
                  value={form.currency}
                  onChange={(event) =>
                    setForm((current) => ({ ...current, currency: event.target.value }))
                  }
                  className="field-input"
                />
              </label>

              <label className="field">
                <span>Gross total</span>
                <input
                  value={form.gross_total}
                  onChange={(event) =>
                    setForm((current) => ({ ...current, gross_total: event.target.value }))
                  }
                  className="field-input"
                  placeholder="e.g. 12500.00"
                />
              </label>

              <label className="field">
                <span>Notes</span>
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
                <h3>Invoice lines</h3>
                <span className="panel-count">{form.lines.length}</span>
              </div>

              {form.lines.map((line, index) => (
                <div key={`invoice-line-${index}`} className="form-grid inventory-movement-create-grid">
                  <label className="field">
                    <span>Inventory item</span>
                    <select
                      value={line.inventory_item_id}
                      onChange={(event) =>
                        handleInventoryItemChange(index, event.target.value)
                      }
                      className="field-input"
                    >
                      <option value="">Not linked</option>
                      {inventoryItems.map((item) => (
                        <option key={item.id} value={item.id}>
                          {item.name} ({item.item_type})
                        </option>
                      ))}
                    </select>
                  </label>

                  <label className="field">
                    <span>Description</span>
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
                    <span>Quantity</span>
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
                    <span>UOM</span>
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
                    <span>Unit net amount</span>
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
                    <span>Line net amount</span>
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
                      Remove line
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
                  Add line
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
                Create invoice
              </button>
            </div>
          </>
        )}
      </section>

      <section className="panel">
        <div className="panel-header">
          <h2>Invoice list</h2>
          <span className="panel-count">{invoices.length}</span>
        </div>

        {!isLoading && invoices.length === 0 ? (
          <p className="empty-message">
            No purchase invoices found for the selected filters.
          </p>
        ) : null}

        {invoices.length > 0 ? (
          <div className="table-wrap">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Invoice number</th>
                  <th>Supplier</th>
                  <th>Invoice date</th>
                  <th>Currency</th>
                  <th>Gross total</th>
                  <th>Lines</th>
                  <th>Status</th>
                  <th>Updated at</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {invoices.map((invoice) => (
                  <tr key={invoice.id}>
                    <td>{invoice.invoice_number}</td>
                    <td>{invoice.supplier_name}</td>
                    <td>{formatDate(invoice.invoice_date)}</td>
                    <td>{invoice.currency}</td>
                    <td>{invoice.gross_total}</td>
                    <td>{invoice.lines.length}</td>
                    <td>
                      {getPostingStatusLabel(
                        invoice.is_posted,
                        invoice.posted_inventory_movement_count
                      )}
                    </td>
                    <td>{formatDateTime(invoice.updated_at)}</td>
                    <td>
                      <button
                        type="button"
                        className="secondary-button"
                        onClick={() => handlePost(invoice.id, invoice.invoice_number)}
                        disabled={isPosting || invoice.is_posted}
                      >
                        Post
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
