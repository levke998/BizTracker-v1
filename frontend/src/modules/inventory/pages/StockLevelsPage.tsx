import { useStockLevels } from "../hooks/useStockLevels";

function formatDateTime(value: string | null) {
  if (!value) {
    return "—";
  }

  return new Intl.DateTimeFormat("hu-HU", {
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  }).format(new Date(value));
}

export function StockLevelsPage() {
  const {
    primaryBusinessUnits,
    technicalBusinessUnits,
    stockLevels,
    selectedBusinessUnitId,
    setSelectedBusinessUnitId,
    selectedItemType,
    setSelectedItemType,
    limit,
    setLimit,
    isLoading,
    errorMessage,
  } = useStockLevels();

  return (
    <section className="page-section">
      <div className="panel">
        <div className="panel-header">
          <h2>Stock Levels</h2>
          <span className="panel-count">{stockLevels.length}</span>
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

        {errorMessage ? <p className="error-message">{errorMessage}</p> : null}
        {isLoading ? <p className="info-message">Loading stock levels...</p> : null}
      </div>

      <section className="panel">
        <div className="panel-header">
          <h2>Actual stock levels</h2>
          <span className="panel-count">{stockLevels.length}</span>
        </div>

        {!isLoading && stockLevels.length === 0 ? (
          <p className="empty-message">
            No stock levels found for the selected filters.
          </p>
        ) : null}

        {stockLevels.length > 0 ? (
          <div className="table-wrap">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Name</th>
                  <th>Item type</th>
                  <th>Current quantity</th>
                  <th>UOM ID</th>
                  <th>Movement count</th>
                  <th>Last movement at</th>
                  <th>Track stock</th>
                  <th>Active</th>
                </tr>
              </thead>
              <tbody>
                {stockLevels.map((item) => (
                  <tr key={item.inventory_item_id}>
                    <td>{item.name}</td>
                    <td>{item.item_type}</td>
                    <td>{item.current_quantity}</td>
                    <td>{item.uom_id}</td>
                    <td>{item.movement_count}</td>
                    <td>{formatDateTime(item.last_movement_at)}</td>
                    <td>{item.track_stock ? "Yes" : "No"}</td>
                    <td>{item.is_active ? "Yes" : "No"}</td>
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
