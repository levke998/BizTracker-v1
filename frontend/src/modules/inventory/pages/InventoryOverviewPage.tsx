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

function formatMovementType(value: string) {
  const labels: Record<string, string> = {
    purchase: "Beszerzés",
    adjustment: "Korrekció",
    waste: "Selejt",
    initial_stock: "Nyitókészlet",
  };

  return labels[value] ?? value;
}

function formatItemType(value: string) {
  const labels: Record<string, string> = {
    raw_material: "Alapanyag",
    packaging: "Csomagolóanyag",
    finished_good: "Késztermék",
  };

  return labels[value] ?? value;
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
          <h2>Készletáttekintés</h2>
          <span className="panel-count">{itemsCount}</span>
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
        </div>

        <div className="inline-actions">
          <Link className="secondary-button" to={routes.inventoryItems}>
            Készletelemek
          </Link>
          <Link className="secondary-button" to={routes.inventoryMovements}>
            Készletmozgások
          </Link>
          <Link className="secondary-button" to={routes.inventoryStockLevels}>
            Készletszintek
          </Link>
          <Link className="secondary-button" to={routes.inventoryTheoreticalStock}>
            Becsült készlet
          </Link>
        </div>

        {errorMessage ? <p className="error-message">{errorMessage}</p> : null}
        {isLoading ? <p className="info-message">Készletáttekintés betöltése...</p> : null}
      </div>

      <section className="panel">
        <div className="panel-header">
          <h2>Áttekintés</h2>
          <span className="panel-count">4</span>
        </div>

        <div className="summary-grid">
          <div className="summary-item">
            <span className="summary-label">Készletelemek</span>
            <strong>{itemsCount}</strong>
          </div>
          <div className="summary-item">
            <span className="summary-label">Készletkezelt tételek</span>
            <strong>{trackedItemsCount}</strong>
          </div>
          <div className="summary-item">
            <span className="summary-label">Készletsorok</span>
            <strong>{stockLevelRowsCount}</strong>
          </div>
          <div className="summary-item">
            <span className="summary-label">Készlettel rendelkező sorok</span>
            <strong>{nonZeroStockRowsCount}</strong>
          </div>
        </div>
      </section>

      <section className="grid-panels">
        <div className="panel">
          <div className="panel-header">
            <h2>Legutóbbi mozgások</h2>
            <span className="panel-count">{recentMovements.length}</span>
          </div>

          {!isLoading && recentMovements.length === 0 ? (
            <p className="empty-message">Nincs rögzített készletmozgás.</p>
          ) : null}

          {recentMovements.length > 0 ? (
            <div className="table-wrap">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Időpont</th>
                    <th>Típus</th>
                    <th>Mennyiség</th>
                    <th>Megjegyzés</th>
                  </tr>
                </thead>
                <tbody>
                  {recentMovements.map((movement) => (
                    <tr key={movement.id}>
                      <td>{formatDateTime(movement.occurred_at)}</td>
                      <td>{formatMovementType(movement.movement_type)}</td>
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
            <h2>Készletkiemelések</h2>
            <span className="panel-count">{stockHighlights.length}</span>
          </div>

          {!isLoading && stockHighlights.length === 0 ? (
            <p className="empty-message">Nincs elérhető készletszint.</p>
          ) : null}

          {stockHighlights.length > 0 ? (
            <div className="table-wrap">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Név</th>
                    <th>Mennyiség</th>
                    <th>Típus</th>
                    <th>Utolsó mozgás</th>
                  </tr>
                </thead>
                <tbody>
                  {stockHighlights.map((item) => (
                    <tr key={item.inventory_item_id}>
                      <td>{item.name}</td>
                      <td>{item.current_quantity}</td>
                      <td>{formatItemType(item.item_type)}</td>
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
