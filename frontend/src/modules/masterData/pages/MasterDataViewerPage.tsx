import type { ReactNode } from "react";

import { useMasterDataViewer } from "../hooks/useMasterDataViewer";

type TableProps = {
  title: string;
  columns: string[];
  rows: ReactNode[][];
  emptyMessage: string;
};

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
          <h2>Master Data Viewer</h2>
        </div>

        <label className="field">
          <span>Business unit</span>
          <select
            value={selectedBusinessUnitId}
            onChange={(event) => setSelectedBusinessUnitId(event.target.value)}
            className="field-input"
          >
            <option value="">Select a business unit</option>
            {businessUnits.map((businessUnit) => (
              <option key={businessUnit.id} value={businessUnit.id}>
                {businessUnit.name}
              </option>
            ))}
          </select>
        </label>

        {errorMessage ? <p className="error-message">{errorMessage}</p> : null}
        {isLoading ? <p className="info-message">Loading data...</p> : null}
      </div>

      <div className="grid-panels">
        <DataTable
          title="Locations"
          columns={["Name", "Kind", "Active"]}
          rows={locations.map((item) => [item.name, item.kind, item.is_active ? "Yes" : "No"])}
          emptyMessage="No locations found for the selected business unit."
        />

        <DataTable
          title="Categories"
          columns={["Name", "Parent category", "Active"]}
          rows={categories.map((item) => [
            item.name,
            item.parent_id ?? "-",
            item.is_active ? "Yes" : "No",
          ])}
          emptyMessage="No categories found for the selected business unit."
        />

        <DataTable
          title="Products"
          columns={["Name", "SKU", "Type", "Active"]}
          rows={products.map((item) => [
            item.name,
            item.sku ?? "-",
            item.product_type,
            item.is_active ? "Yes" : "No",
          ])}
          emptyMessage="No products found for the selected business unit."
        />
      </div>
    </section>
  );
}
