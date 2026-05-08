import { useStockLevels } from "../hooks/useStockLevels";

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

function formatItemType(value: string) {
  const labels: Record<string, string> = {
    raw_material: "Alapanyag",
    packaging: "Csomagolóanyag",
    finished_good: "Késztermék",
  };

  return labels[value] ?? value;
}

function formatBoolean(value: boolean) {
  return value ? "Igen" : "Nem";
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
          <h2>Készletszintek</h2>
          <span className="panel-count">{stockLevels.length}</span>
        </div>

        <div className="form-grid inventory-filter-grid">
          <label className="field">
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
                <optgroup label="Technikai">
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
            <span>Tételtípus</span>
            <select
              value={selectedItemType}
              onChange={(event) => setSelectedItemType(event.target.value)}
              className="field-input"
            >
              <option value="">Minden tételtípus</option>
              <option value="raw_material">Alapanyag</option>
              <option value="packaging">Csomagolóanyag</option>
              <option value="finished_good">Késztermék</option>
            </select>
          </label>

          <label className="field">
            <span>Megjelenített sorok</span>
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
        {isLoading ? <p className="info-message">Készletszintek betöltése...</p> : null}
      </div>

      <section className="panel">
        <div className="panel-header">
          <h2>Aktuális készletszintek</h2>
          <span className="panel-count">{stockLevels.length}</span>
        </div>

        {!isLoading && stockLevels.length === 0 ? (
          <p className="empty-message">
            Nincs készletszint a kiválasztott szűrőkkel.
          </p>
        ) : null}

        {stockLevels.length > 0 ? (
          <div className="table-wrap">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Név</th>
                  <th>Tételtípus</th>
                  <th>Aktuális mennyiség</th>
                  <th>Egység</th>
                  <th>Mozgások</th>
                  <th>Utolsó mozgás</th>
                  <th>Készletkezelt</th>
                  <th>Aktív</th>
                </tr>
              </thead>
              <tbody>
                {stockLevels.map((item) => (
                  <tr key={item.inventory_item_id}>
                    <td>{item.name}</td>
                    <td>{formatItemType(item.item_type)}</td>
                    <td>{item.current_quantity}</td>
                    <td>{item.uom_id}</td>
                    <td>{item.movement_count}</td>
                    <td>{formatDateTime(item.last_movement_at)}</td>
                    <td>{formatBoolean(item.track_stock)}</td>
                    <td>{formatBoolean(item.is_active)}</td>
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
