import { Link } from "react-router-dom";

import { routes } from "../../../shared/constants/routes";
import { useInventoryOverview } from "../hooks/useInventoryOverview";

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

export function InventoryOverviewPage() {
  const {
    primaryBusinessUnits,
    technicalBusinessUnits,
    selectedBusinessUnitId,
    setSelectedBusinessUnitId,
    itemsCount,
    trackedItemsCount,
    stockLevelRowsCount,
    nonZeroStockRowsCount,
    recentMovements,
    stockHighlights,
    isLoading,
    errorMessage,
  } = useInventoryOverview();

  return (
    <section className="page-section">
      <div className="panel">
        <div className="panel-header">
          <h2>Inventory Overview</h2>
          <span className="panel-count">{itemsCount}</span>
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
        </div>

        <div className="inline-actions">
          <Link className="secondary-button" to={routes.inventoryItems}>
            Inventory Items
          </Link>
          <Link className="secondary-button" to={routes.inventoryMovements}>
            Inventory Movements
          </Link>
          <Link className="secondary-button" to={routes.inventoryStockLevels}>
            Stock Levels
          </Link>
          <Link className="secondary-button" to={routes.inventoryTheoreticalStock}>
            Theoretical Stock
          </Link>
        </div>

        {errorMessage ? <p className="error-message">{errorMessage}</p> : null}
        {isLoading ? <p className="info-message">Loading inventory overview...</p> : null}
      </div>

      <section className="panel">
        <div className="panel-header">
          <h2>Summary</h2>
          <span className="panel-count">4</span>
        </div>

        <div className="summary-grid">
          <div className="summary-item">
            <span className="summary-label">Inventory items</span>
            <strong>{itemsCount}</strong>
          </div>
          <div className="summary-item">
            <span className="summary-label">Tracked items</span>
            <strong>{trackedItemsCount}</strong>
          </div>
          <div className="summary-item">
            <span className="summary-label">Stock level rows</span>
            <strong>{stockLevelRowsCount}</strong>
          </div>
          <div className="summary-item">
            <span className="summary-label">Rows with stock</span>
            <strong>{nonZeroStockRowsCount}</strong>
          </div>
        </div>
      </section>

      <section className="grid-panels">
        <div className="panel">
          <div className="panel-header">
            <h2>Recent movements</h2>
            <span className="panel-count">{recentMovements.length}</span>
          </div>

          {!isLoading && recentMovements.length === 0 ? (
            <p className="empty-message">No inventory movements available.</p>
          ) : null}

          {recentMovements.length > 0 ? (
            <div className="table-wrap">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Occurred at</th>
                    <th>Type</th>
                    <th>Quantity</th>
                    <th>Note</th>
                  </tr>
                </thead>
                <tbody>
                  {recentMovements.map((movement) => (
                    <tr key={movement.id}>
                      <td>{formatDateTime(movement.occurred_at)}</td>
                      <td>{movement.movement_type}</td>
                      <td>{movement.quantity}</td>
                      <td>{movement.note ?? "-"}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : null}
        </div>

        <div className="panel">
          <div className="panel-header">
            <h2>Stock highlights</h2>
            <span className="panel-count">{stockHighlights.length}</span>
          </div>

          {!isLoading && stockHighlights.length === 0 ? (
            <p className="empty-message">No stock levels available.</p>
          ) : null}

          {stockHighlights.length > 0 ? (
            <div className="table-wrap">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Name</th>
                    <th>Quantity</th>
                    <th>Type</th>
                    <th>Last movement</th>
                  </tr>
                </thead>
                <tbody>
                  {stockHighlights.map((item) => (
                    <tr key={item.inventory_item_id}>
                      <td>{item.name}</td>
                      <td>{item.current_quantity}</td>
                      <td>{item.item_type}</td>
                      <td>{formatDateTime(item.last_movement_at)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : null}
        </div>
      </section>
    </section>
  );
}
