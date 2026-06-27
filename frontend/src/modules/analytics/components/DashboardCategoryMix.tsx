import { useState } from "react";

import { Card } from "../../../shared/components/ui/Card";
import type {
  DashboardBreakdownRow,
  DashboardPosSourceRow,
  DashboardProductDetailRow,
} from "../types/analytics";
import {
  formatCostSource,
  formatMarginStatus,
  formatMoney,
  formatNumber,
  formatPaymentMethod,
  mixPalette,
  toNumber,
} from "./dashboardView";

export type MixMetric = "revenue" | "quantity";
function getMixValue(
  row: Pick<DashboardBreakdownRow | DashboardProductDetailRow, "revenue" | "quantity">,
  metric: MixMetric,
) {
  return metric === "revenue" ? toNumber(row.revenue) : toNumber(row.quantity);
}

function formatMixValue(value: number, metric: MixMetric) {
  return metric === "revenue" ? formatMoney(value) : `${formatNumber(value)} db`;
}

type CategoryMixDisplayRow = {
  key: string;
  label: string;
  revenue: string;
  quantity: string;
  transaction_count: number;
  product: DashboardProductDetailRow | null;
  isOther?: boolean;
  children?: CategoryMixDisplayRow[];
};

function groupSmallCategoryRows(
  rows: CategoryMixDisplayRow[],
  metric: MixMetric,
  shouldGroup: boolean,
) {
  if (!shouldGroup) {
    return rows;
  }

  const total = rows.reduce((sum, row) => sum + getMixValue(row, metric), 0);
  if (total <= 0) {
    return rows;
  }

  const visibleRows: CategoryMixDisplayRow[] = [];
  const otherRows: CategoryMixDisplayRow[] = [];

  rows.forEach((row) => {
    const share = (getMixValue(row, metric) / total) * 100;
    if (share < 10) {
      otherRows.push(row);
      return;
    }
    visibleRows.push(row);
  });

  if (otherRows.length === 0) {
    return rows;
  }

  visibleRows.push({
    key: "__other__",
    label: "Egyéb",
    revenue: String(otherRows.reduce((sum, row) => sum + toNumber(row.revenue), 0)),
    quantity: String(otherRows.reduce((sum, row) => sum + toNumber(row.quantity), 0)),
    transaction_count: otherRows.reduce((sum, row) => sum + row.transaction_count, 0),
    product: null,
    isOther: true,
    children: otherRows,
  });

  return visibleRows;
}

function buildDonutGradient(
  rows: Array<{ revenue: string; quantity: string }>,
  metric: MixMetric,
) {
  const total = rows.reduce((sum, row) => sum + getMixValue(row, metric), 0);
  if (total <= 0) {
    return "conic-gradient(rgba(148, 163, 184, 0.24) 0deg 360deg)";
  }

  let cursor = 0;
  return `conic-gradient(${rows
    .map((row, index) => {
      const value = getMixValue(row, metric);
      const start = cursor;
      const size = (value / total) * 360;
      cursor += size;
      return `${mixPalette[index % mixPalette.length]} ${start.toFixed(2)}deg ${cursor.toFixed(
        2,
      )}deg`;
    })
    .join(", ")})`;
}

export function DashboardCategoryMix({
  categories,
  activeCategory,
  productDetails,
  selectedProduct,
  productSourceRows,
  isLoading,
  metric,
  setMetric,
  openCategory,
  closeCategory,
  selectProduct,
}: {
  categories: DashboardBreakdownRow[];
  activeCategory: string | null;
  productDetails: DashboardProductDetailRow[];
  selectedProduct: DashboardProductDetailRow | null;
  productSourceRows: DashboardPosSourceRow[];
  isLoading: boolean;
  metric: MixMetric;
  setMetric: (value: MixMetric) => void;
  openCategory: (category: string) => void;
  closeCategory: () => void;
  selectProduct: (product: DashboardProductDetailRow) => void;
}) {
  const [isOtherOpen, setIsOtherOpen] = useState(false);
  const rawRows: CategoryMixDisplayRow[] = activeCategory
    ? productDetails.map((row) => ({
        key: `${row.product_name}-${row.category_name}`,
        label: row.product_name,
        revenue: row.revenue,
        quantity: row.quantity,
        transaction_count: row.transaction_count,
        product: row,
      }))
    : categories.map((row) => ({
        key: row.label,
        label: row.label,
        revenue: row.revenue,
        quantity: row.quantity,
        transaction_count: row.transaction_count,
        product: null,
      }));
  const rows = groupSmallCategoryRows(rawRows, metric, !activeCategory);
  const otherRow = rows.find((row) => row.isOther) ?? null;
  const total = rows.reduce((sum, row) => sum + getMixValue(row, metric), 0);
  const leader = rows[0] ?? null;

  return (
    <Card
      tone="secondary"
      hoverable
      eyebrow="Bevételi megoszlás"
      title={activeCategory ? `${activeCategory} termékei` : "Kategóriák"}
      subtitle={activeCategory ? "Termékmegoszlás a kiválasztott kategóriában" : "Érték vagy mennyiség alapú kategóriaarány"}
      count={rows.length}
      actions={
        <div className="dashboard-mix-actions">
          <button
            type="button"
            className={metric === "revenue" ? "filter-chip filter-chip-active" : "filter-chip"}
            onClick={() => setMetric("revenue")}
          >
            Érték
          </button>
          <button
            type="button"
            className={metric === "quantity" ? "filter-chip filter-chip-active" : "filter-chip"}
            onClick={() => setMetric("quantity")}
          >
            Mennyiség
          </button>
          {activeCategory ? (
            <button type="button" className="secondary-button" onClick={closeCategory}>
              Kategóriák
            </button>
          ) : null}
        </div>
      }
    >
      {isLoading ? <p className="info-message">Megoszlás betöltése...</p> : null}
      <div className="dashboard-mix-layout">
        <div className="dashboard-donut-wrap">
          <div
            className="dashboard-donut"
            style={{ background: buildDonutGradient(rows, metric) }}
            aria-label="Bevételi megoszlás diagram"
          >
            <div className="dashboard-donut-center">
              <span>{metric === "revenue" ? "Összes érték" : "Összes mennyiség"}</span>
              <strong>{formatMixValue(total, metric)}</strong>
            </div>
          </div>
          {leader ? (
            <p className="section-note">
              Legnagyobb szelet: {leader.label} · {formatMixValue(getMixValue(leader, metric), metric)}
            </p>
          ) : (
            <p className="empty-message">Nincs megjeleníthető megoszlás ebben az időszakban.</p>
          )}
        </div>

        <div className="dashboard-mix-list">
          {rows.map((row, index) => {
            const value = getMixValue(row, metric);
            const percentage = total > 0 ? (value / total) * 100 : 0;
            const selected =
              activeCategory && selectedProduct?.product_name === row.label;
            return (
              <button
                key={row.key}
                type="button"
                className={selected ? "dashboard-mix-row dashboard-mix-row-active" : "dashboard-mix-row"}
                onClick={() => {
                  if (row.isOther) {
                    setIsOtherOpen((current) => !current);
                    return;
                  }
                  setIsOtherOpen(false);
                  if (activeCategory && row.product) {
                    selectProduct(row.product);
                    return;
                  }
                  openCategory(row.label);
                }}
              >
                <span
                  className="dashboard-mix-swatch"
                  style={{ background: mixPalette[index % mixPalette.length] }}
                />
                <span className="dashboard-mix-label">{row.label}</span>
                <span className="dashboard-mix-value">
                  {formatMixValue(value, metric)}
                  <small>{percentage.toFixed(1)}%</small>
                </span>
              </button>
            );
          })}
        </div>
      </div>

      {isOtherOpen && otherRow?.children ? (
        <div className="dashboard-card-drilldown dashboard-other-drilldown">
          <div className="section-heading-row">
            <div>
              <h3>Egyéb kategóriák</h3>
              <p className="section-note">A 10% alatti szeletek összevonása.</p>
            </div>
            <span className="status-pill">{otherRow.children.length} kategória</span>
          </div>
          <div className="dashboard-other-list">
            {otherRow.children.map((child, index) => {
              const childValue = getMixValue(child, metric);
              const percentage = total > 0 ? (childValue / total) * 100 : 0;
              return (
                <button
                  key={child.key}
                  type="button"
                  className="dashboard-mix-row"
                  onClick={() => openCategory(child.label)}
                >
                  <span
                    className="dashboard-mix-swatch"
                    style={{ background: mixPalette[(index + rows.length) % mixPalette.length] }}
                  />
                  <span className="dashboard-mix-label">{child.label}</span>
                  <span className="dashboard-mix-value">
                    {formatMixValue(childValue, metric)}
                    <small>{percentage.toFixed(1)}%</small>
                  </span>
                </button>
              );
            })}
          </div>
        </div>
      ) : null}

      {selectedProduct ? (
        <div className="dashboard-card-drilldown">
          <div className="section-heading-row">
            <div>
              <h3>{selectedProduct.product_name}</h3>
              <p className="section-note">Kapcsolódó nyugtasorok</p>
            </div>
            <span className="status-pill">{productSourceRows.length} sor</span>
          </div>
          {selectedProduct.net_revenue !== null ||
          selectedProduct.vat_amount !== null ||
          selectedProduct.estimated_cogs_net !== null ||
          selectedProduct.estimated_net_margin_amount !== null ? (
            <div className="expense-summary-strip">
              <span>
                <strong>{formatMoney(selectedProduct.revenue)}</strong>
                <small>Bruttó actual</small>
                Bevétel
              </span>
              <span>
                <strong>{formatMoney(selectedProduct.net_revenue ?? 0)}</strong>
                <small>Derived</small>
                Nettó
              </span>
              <span>
                <strong>{formatMoney(selectedProduct.vat_amount ?? 0)}</strong>
                <small>Derived</small>
                ÁFA
              </span>
              {selectedProduct.estimated_cogs_net !== null ? (
                <span>
                  <strong>{formatMoney(selectedProduct.estimated_cogs_net)}</strong>
                  <small>{formatCostSource(selectedProduct.cost_source)}</small>
                  Nettó COGS
                </span>
              ) : null}
              {selectedProduct.estimated_net_margin_amount !== null ? (
                <span>
                  <strong>{formatMoney(selectedProduct.estimated_net_margin_amount)}</strong>
                  <small>
                    {formatNumber(selectedProduct.estimated_margin_percent ?? 0)}%
                  </small>
                  Nettó margin
                </span>
              ) : null}
              <span>
                <strong>{formatMarginStatus(selectedProduct.margin_status)}</strong>
                <small>Readiness</small>
                Margin státusz
              </span>
            </div>
          ) : null}
          <div className="table-wrap dashboard-embedded-table">
            <table className="data-table details-table">
              <thead>
                <tr>
                  <th>Dátum</th>
                  <th>Nyugta</th>
                  <th>Mennyiség</th>
                  <th>Bruttó összeg</th>
                  <th>Nettó / ÁFA</th>
                  <th>Fizetés</th>
                </tr>
              </thead>
              <tbody>
                {productSourceRows.map((row) => (
                  <tr key={row.row_id}>
                    <td>{row.date ?? "-"}</td>
                    <td>{row.receipt_no ?? "-"}</td>
                    <td>{formatNumber(row.quantity)}</td>
                    <td>{formatMoney(row.gross_amount)}</td>
                    <td>
                      {row.net_amount !== null || row.vat_amount !== null
                        ? `${formatMoney(row.net_amount ?? 0)} / ${formatMoney(
                            row.vat_amount ?? 0,
                          )}`
                        : "-"}
                    </td>
                    <td>{row.payment_method ? formatPaymentMethod(row.payment_method) : "-"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      ) : null}
    </Card>
  );
}

