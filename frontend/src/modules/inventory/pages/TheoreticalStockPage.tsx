import { useState } from "react";

import { useEstimatedConsumptionAudit } from "../hooks/useEstimatedConsumptionAudit";
import { useTheoreticalStock } from "../hooks/useTheoreticalStock";

function formatDateTime(value: string | null) {
  if (!value) {
    return "-";
  }

  return new Intl.DateTimeFormat("hu-HU", {
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  }).format(new Date(value));
}

function formatQuantity(value: string | null) {
  return value ?? "Not configured";
}

function formatEstimationBasis(value: string) {
  if (value === "not_configured") {
    return "Not configured";
  }

  return value;
}

export function TheoreticalStockPage() {
  const [selectedInventoryItemId, setSelectedInventoryItemId] = useState("");
  const {
    primaryBusinessUnits,
    technicalBusinessUnits,
    stockRows,
    selectedBusinessUnitId,
    setSelectedBusinessUnitId,
    selectedItemType,
    setSelectedItemType,
    limit,
    setLimit,
    isLoading,
    errorMessage,
  } = useTheoreticalStock();
  const selectedStockRow = stockRows.find(
    (item) => item.inventory_item_id === selectedInventoryItemId
  );
  const auditQuery = useEstimatedConsumptionAudit({
    business_unit_id: selectedBusinessUnitId,
    inventory_item_id: selectedInventoryItemId,
    limit: 25,
  });
  const auditRows = auditQuery.data ?? [];

  return (
    <section className="page-section">
      <div className="panel">
        <div className="panel-header">
          <h2>Theoretical Stock</h2>
          <span className="panel-count">{stockRows.length}</span>
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
            <span>Item type</span>
            <select
              value={selectedItemType}
              onChange={(event) => setSelectedItemType(event.target.value)}
              className="field-input"
            >
              <option value="">All item types</option>
              <option value="raw_material">raw_material</option>
              <option value="packaging">packaging</option>
              <option value="finished_good">finished_good</option>
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

        <p className="info-message">
          This view keeps actual and estimated stock separate. The current MVP shows
          readiness only until recipe and consumption rules are configured.
        </p>

        {errorMessage ? <p className="error-message">{errorMessage}</p> : null}
        {isLoading ? <p className="info-message">Loading theoretical stock...</p> : null}
      </div>

      <section className="panel">
        <div className="panel-header">
          <h2>Theoretical stock readiness</h2>
          <span className="panel-count">{stockRows.length}</span>
        </div>

        {!isLoading && stockRows.length === 0 ? (
          <p className="empty-message">
            No theoretical stock rows found for the selected filters.
          </p>
        ) : null}

        {stockRows.length > 0 ? (
          <div className="table-wrap">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Name</th>
                  <th>Item type</th>
                  <th>Actual quantity</th>
                  <th>Theoretical quantity</th>
                  <th>Variance</th>
                  <th>Estimation basis</th>
                  <th>Last actual movement</th>
                  <th>Last estimated event</th>
                  <th>Track stock</th>
                  <th>Active</th>
                  <th>Audit</th>
                </tr>
              </thead>
              <tbody>
                {stockRows.map((item) => (
                  <tr key={item.inventory_item_id}>
                    <td>{item.name}</td>
                    <td>{item.item_type}</td>
                    <td>{item.actual_quantity}</td>
                    <td>{formatQuantity(item.theoretical_quantity)}</td>
                    <td>{formatQuantity(item.variance_quantity)}</td>
                    <td>{formatEstimationBasis(item.estimation_basis)}</td>
                    <td>{formatDateTime(item.last_actual_movement_at)}</td>
                    <td>{formatDateTime(item.last_estimated_event_at)}</td>
                    <td>{item.track_stock ? "Yes" : "No"}</td>
                    <td>{item.is_active ? "Yes" : "No"}</td>
                    <td>
                      <button
                        className="secondary-button inventory-audit-button"
                        type="button"
                        onClick={() => setSelectedInventoryItemId(item.inventory_item_id)}
                      >
                        Details
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : null}
      </section>

      <section className="panel">
        <div className="panel-header">
          <h2>Estimated consumption audit</h2>
          <span className="panel-count">{auditRows.length}</span>
        </div>

        {!selectedStockRow ? (
          <p className="empty-message">Select an inventory item to inspect estimated consumption.</p>
        ) : null}

        {selectedStockRow ? (
          <p className="info-message">
            {selectedStockRow.name} estimated stock changes from POS sales.
          </p>
        ) : null}

        {auditQuery.error instanceof Error ? (
          <p className="error-message">{auditQuery.error.message}</p>
        ) : null}
        {auditQuery.isLoading ? (
          <p className="info-message">Loading estimated consumption audit...</p>
        ) : null}

        {selectedStockRow && !auditQuery.isLoading && auditRows.length === 0 ? (
          <p className="empty-message">No estimated consumption audit rows found.</p>
        ) : null}

        {auditRows.length > 0 ? (
          <div className="table-wrap">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Occurred at</th>
                  <th>Product</th>
                  <th>Basis</th>
                  <th>Quantity</th>
                  <th>Before</th>
                  <th>After</th>
                  <th>Receipt</th>
                  <th>Source</th>
                </tr>
              </thead>
              <tbody>
                {auditRows.map((row) => (
                  <tr key={row.id}>
                    <td>{formatDateTime(row.occurred_at)}</td>
                    <td>{row.product_name}</td>
                    <td>{formatEstimationBasis(row.estimation_basis)}</td>
                    <td>
                      {row.quantity} {row.uom_code}
                    </td>
                    <td>{row.quantity_before}</td>
                    <td>{row.quantity_after}</td>
                    <td>{row.receipt_no ?? "-"}</td>
                    <td className="mono-cell">{row.source_id}</td>
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
