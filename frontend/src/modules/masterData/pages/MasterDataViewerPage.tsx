import type { ReactNode } from "react";

import { useMasterDataViewer } from "../hooks/useMasterDataViewer";

type TableProps = {
  title: string;
  columns: string[];
  rows: ReactNode[][];
  emptyMessage: string;
};

function formatBoolean(value: boolean) {
  return value ? "Igen" : "Nem";
}

function formatProductType(value: string) {
  const labels: Record<string, string> = {
    menu_item: "Eladott termék",
    modifier: "Kiegészítő",
    service: "Szolgáltatás",
  };

  return labels[value] ?? value;
}

function DataTable({ title, columns, rows, emptyMessage }: TableProps) {
  return (
    <section className="panel">
      <div className="panel-header">
        <h2>{title}</h2>
        <span className="panel-count">{rows.length}</span>
      </div>

      {rows.length === 0 ? (
        <p className="empty-message">{emptyMessage}</p>
      ) : (
        <div className="table-wrap">
          <table className="data-table">
            <thead>
              <tr>
                {columns.map((column) => (
                  <th key={column}>{column}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {rows.map((row, rowIndex) => (
                <tr key={rowIndex}>
                  {row.map((cell, cellIndex) => (
                    <td key={cellIndex}>{cell}</td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </section>
  );
}

export function MasterDataViewerPage() {
  const {
    businessUnits,
    locations,
    categories,
    products,
    selectedBusinessUnitId,
    setSelectedBusinessUnitId,
    isLoading,
    errorMessage,
  } = useMasterDataViewer();

  return (
    <section className="page-section">
      <div className="panel filter-panel">
        <div className="panel-header">
          <h2>Törzsadatok</h2>
        </div>

        <label className="field">
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

        {errorMessage ? <p className="error-message">{errorMessage}</p> : null}
        {isLoading ? <p className="info-message">Törzsadatok betöltése...</p> : null}
      </div>

      <div className="grid-panels">
        <DataTable
          title="Telephelyek"
          columns={["Név", "Típus", "Aktív"]}
          rows={locations.map((item) => [item.name, item.kind, formatBoolean(item.is_active)])}
          emptyMessage="Nincs telephely a kiválasztott vállalkozáshoz."
        />

        <DataTable
          title="Kategóriák"
          columns={["Név", "Szülő kategória", "Aktív"]}
          rows={categories.map((item) => [
            item.name,
            item.parent_id ?? "-",
            formatBoolean(item.is_active),
          ])}
          emptyMessage="Nincs kategória a kiválasztott vállalkozáshoz."
        />

        <DataTable
          title="Termékek"
          columns={["Név", "SKU", "Típus", "Aktív"]}
          rows={products.map((item) => [
            item.name,
            item.sku ?? "-",
            formatProductType(item.product_type),
            formatBoolean(item.is_active),
          ])}
          emptyMessage="Nincs termék a kiválasztott vállalkozáshoz."
        />
      </div>
    </section>
  );
}
