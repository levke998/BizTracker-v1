import { useState } from "react";
import type { CSSProperties } from "react";

import { Card } from "../../../shared/components/ui/Card";
import type { DashboardTopProductRow } from "../hooks/useDashboard";
import type {
  DashboardBreakdownRow,
  DashboardHeatmapCell,
  DashboardScope,
} from "../types/analytics";
import {
  formatBasketValueBand,
  formatCostSource,
  formatHeatmapHour,
  formatMarginStatus,
  formatMoney,
  formatNumber,
  heatmapWeekdays,
  mixPalette,
  toNumber,
} from "./dashboardView";
export function DashboardTopProducts({
  rows,
  categories,
  selectedCategory,
  setSelectedCategory,
  isLoading,
  scope,
}: {
  rows: DashboardTopProductRow[];
  categories: DashboardBreakdownRow[];
  selectedCategory: string;
  setSelectedCategory: (value: string) => void;
  isLoading: boolean;
  scope: DashboardScope;
}) {
  const [selectedProductKey, setSelectedProductKey] = useState<string | null>(null);
  const sortedRows = [...rows]
    .sort((left, right) => toNumber(right.revenue) - toNumber(left.revenue))
    .slice(0, 8);
  const maxRevenue = Math.max(...sortedRows.map((row) => toNumber(row.revenue)), 1);
  const totalRevenue = rows.reduce((sum, row) => sum + toNumber(row.revenue), 0);
  const totalQuantity = rows.reduce((sum, row) => sum + toNumber(row.quantity), 0);
  const hasMarginRows = rows.some(
    (row) =>
      row.estimated_cogs_net != null ||
      row.estimated_net_margin_amount != null,
  );
  const totalCogs = rows.reduce(
    (sum, row) => sum + toNumber(row.estimated_cogs_net ?? "0"),
    0,
  );
  const totalNetMargin = rows.reduce(
    (sum, row) => sum + toNumber(row.estimated_net_margin_amount ?? "0"),
    0,
  );
  return (
    <Card
      tone="rainbow"
      hoverable
      className="top-products-card"
      eyebrow="Top termékek"
      title="Legjobban teljesítő termékek"
      subtitle="Kategória szerint szűrhető eladási rangsor"
      count={sortedRows.length}
      actions={
        <label className="field dashboard-card-filter">
          <span>Kategória</span>
          <select
            className="field-input"
            value={selectedCategory}
            onChange={(event) => setSelectedCategory(event.target.value)}
          >
            <option value="all">Minden kategória</option>
            {categories.map((category) => (
              <option key={category.label} value={category.label}>
                {category.label}
              </option>
            ))}
          </select>
        </label>
      }
    >
      <div className="top-products-summary">
        <span>
          <strong>{formatMoney(totalRevenue)}</strong>
          Bevétel
        </span>
        <span>
          <strong>{formatNumber(totalQuantity)} db</strong>
          Eladott mennyiség
        </span>
        {hasMarginRows ? (
          <>
            <span>
              <strong>{formatMoney(totalCogs)}</strong>
              Nettó COGS
            </span>
            <span>
              <strong>{formatMoney(totalNetMargin)}</strong>
              Nettó margin
            </span>
          </>
        ) : null}
      </div>

      {isLoading ? <p className="info-message">Terméklista betöltése...</p> : null}

      <div className="top-products-list">
        {sortedRows.map((row, index) => {
          const rank = index + 1;
          const revenue = toNumber(row.revenue);
          const width = `${Math.max(4, (revenue / maxRevenue) * 100)}%`;

          const productKey = `${row.label}-${row.category_name ?? "all"}`;
          const isSelected = selectedProductKey === productKey;
          const revenueShare = totalRevenue > 0 ? (revenue / totalRevenue) * 100 : 0;

          return (
            <div className="top-product-entry" key={productKey}>
            <button
              type="button"
              className={isSelected ? "top-product-row top-product-row-active" : "top-product-row"}
              onClick={() => setSelectedProductKey(isSelected ? null : productKey)}
            >
              <span className={`top-product-rank rank-${rank <= 3 ? rank : "default"}`}>
                {rank <= 3 ? `TOP ${rank}` : rank}
              </span>
              <span className="top-product-content">
                <span className="top-product-heading">
                  <strong>{row.label}</strong>
                  <span>{formatMoney(row.revenue)}</span>
                </span>
                <span className="top-product-bar">
                  <span style={{ width }} />
                </span>
                <span className="top-product-meta">
                  <span>{formatNumber(row.quantity)} db eladva</span>
                  <span>{row.transaction_count} nyugtasor</span>
                  <span>{row.category_name ?? "Kategória nélkül"}</span>
                  <span
                    className={
                      toNumber(row.revenue_change_percent ?? "0") >= 0
                        ? "top-product-change positive"
                        : "top-product-change negative"
                    }
                  >
                    {toNumber(row.revenue_change_percent ?? "0") >= 0 ? "+" : ""}
                    {formatNumber(row.revenue_change_percent ?? "0")}%
                  </span>
                  <span>{formatMarginStatus(row.margin_status)}</span>
                </span>
              </span>
            </button>
            {isSelected ? (
              <div className="top-product-drilldown">
                <span>
                  <strong>{formatNumber(revenueShare)}%</strong>
                  Arány a top listában
                </span>
                <span>
                  <strong>{formatMoney(row.revenue)}</strong>
                  Bruttó termékbevétel
                </span>
                {row.estimated_cogs_net != null ? (
                  <span>
                    <strong>{formatMoney(row.estimated_cogs_net ?? 0)}</strong>
                    Nettó COGS
                  </span>
                ) : null}
                {row.estimated_net_margin_amount != null ? (
                  <span>
                    <strong>
                      {formatMoney(row.estimated_net_margin_amount ?? 0)} /{" "}
                      {formatNumber(row.estimated_margin_percent ?? 0)}%
                    </strong>
                    Nettó margin
                  </span>
                ) : null}
                {row.net_revenue !== null || row.vat_amount !== null ? (
                  <span>
                    <strong>
                      Nettó {formatMoney(row.net_revenue ?? 0)} / ÁFA{" "}
                      {formatMoney(row.vat_amount ?? 0)}
                    </strong>
                    Termék ÁFA-ból számolt
                  </span>
                ) : null}
                <span>
                  <strong>{row.category_name ?? "-"}</strong>
                  Kategória
                </span>
                <span>
                  <strong>{row.transaction_count}</strong>
                  Érintett nyugtasor
                </span>
                <span>
                  <strong>{formatCostSource(row.cost_source)}</strong>
                  {formatMarginStatus(row.margin_status)}
                </span>
              </div>
            ) : null}
            </div>
          );
        })}
      </div>

      {sortedRows.length === 0 && !isLoading ? (
        <p className="empty-message">Nincs megjeleníthető termék ebben az időszakban.</p>
      ) : null}
    </Card>
  );
}

export function DashboardTrafficHeatmap({
  cells,
  scope,
  basketRows,
}: {
  cells: DashboardHeatmapCell[];
  scope: DashboardScope;
  basketRows: DashboardBreakdownRow[];
}) {
  const [selectedBasketBand, setSelectedBasketBand] = useState<string | null>(null);
  const hours =
    scope === "gourmand"
      ? Array.from({ length: 14 }, (_item, index) => index + 7)
      : Array.from({ length: 24 }, (_item, index) => index);
  const cellBySlot = new Map(
    cells.map((cell) => [`${cell.weekday}-${cell.hour}`, cell]),
  );
  const activeCells = cells.filter((cell) => cell.transaction_count > 0);
  const maxRevenue = Math.max(
    ...cells.map((cell) => toNumber(cell.revenue)),
    0,
  );
  const totalRevenue = cells.reduce((sum, cell) => sum + toNumber(cell.revenue), 0);
  const totalTransactions = cells.reduce(
    (sum, cell) => sum + cell.transaction_count,
    0,
  );
  const strongestSlot = [...activeCells].sort(
    (left, right) => toNumber(right.revenue) - toNumber(left.revenue),
  )[0];
  const totalBaskets = basketRows.reduce((sum, row) => sum + row.transaction_count, 0);
  const totalBasketRevenue = basketRows.reduce((sum, row) => sum + toNumber(row.revenue), 0);
  const maxBasketCount = Math.max(...basketRows.map((row) => row.transaction_count), 1);
  const selectedBasketRow =
    basketRows.find((row) => row.label === selectedBasketBand) ?? null;

  return (
    <Card
      hoverable
      tone="rainbow"
      className="traffic-rhythm-card"
      eyebrow="Forgalmi hőtérkép"
      title="Mikor érkezik a bevétel?"
      subtitle="Órás bontás a rögzített kasszasorok alapján"
      count={activeCells.length}
    >
      <div className="traffic-heatmap-summary">
        <span>
          <strong>{formatMoney(totalRevenue)}</strong>
          Összes bevétel
        </span>
        <span>
          <strong>{totalTransactions}</strong>
          Nyugtasor
        </span>
        <span>
          <strong>{totalBaskets}</strong>
          Kosár
        </span>
        <span>
          <strong>
            {strongestSlot
              ? `${heatmapWeekdays[strongestSlot.weekday]} ${formatHeatmapHour(
                  strongestSlot.hour,
                )}`
              : "-"}
          </strong>
          Legerősebb idősáv
        </span>
      </div>

      <div className="traffic-heatmap-scroll" aria-label="Forgalmi hőtérkép">
        <div
          className="traffic-heatmap-grid"
          style={{ "--heatmap-hour-count": hours.length } as CSSProperties}
        >
          <span className="traffic-heatmap-corner" />
          {hours.map((hour) => (
            <span className="traffic-heatmap-hour" key={hour}>
              {hour % 2 === 0 ? formatHeatmapHour(hour) : ""}
            </span>
          ))}

          {heatmapWeekdays.map((weekdayLabel, weekday) => (
            <div className="traffic-heatmap-row" key={weekdayLabel}>
              <span className="traffic-heatmap-day">{weekdayLabel}</span>
              {hours.map((hour) => {
                const cell =
                  cellBySlot.get(`${weekday}-${hour}`) ??
                  ({
                    weekday,
                    hour,
                    revenue: "0",
                    transaction_count: 0,
                    source_layer: "import_derived",
                  } satisfies DashboardHeatmapCell);
                const revenue = toNumber(cell.revenue);
                const intensity = maxRevenue > 0 ? revenue / maxRevenue : 0;
                const alpha = 0.08 + intensity * 0.62;

                return (
                  <span
                    className={
                      cell.transaction_count > 0
                        ? "traffic-heatmap-cell active"
                        : "traffic-heatmap-cell"
                    }
                    key={`${weekday}-${hour}`}
                    style={{
                      background: `linear-gradient(135deg, rgba(139, 92, 246, ${alpha}), rgba(56, 189, 248, ${
                        0.04 + intensity * 0.3
                      }))`,
                      borderColor:
                        cell.transaction_count > 0
                          ? `rgba(167, 139, 250, ${0.18 + intensity * 0.42})`
                          : undefined,
                    }}
                    title={`${weekdayLabel} ${formatHeatmapHour(hour)} - ${formatMoney(
                      cell.revenue,
                    )}, ${cell.transaction_count} nyugtasor`}
                  >
                    <strong>{cell.transaction_count || ""}</strong>
                  </span>
                );
              })}
            </div>
          ))}
        </div>
      </div>

      <div className="traffic-heatmap-legend">
        <span>Alacsonyabb</span>
        <span className="traffic-heatmap-legend-bar" />
        <span>Magasabb forgalom</span>
      </div>

      <div className="traffic-rhythm-basket">
        <div className="traffic-rhythm-basket-heading">
          <span>
            <strong>Vásárlási sávok</strong>
            Kosárérték eloszlás
          </span>
          <strong>{formatMoney(totalBasketRevenue)}</strong>
        </div>

        <div className="traffic-rhythm-basket-grid">
          {basketRows.map((row, index) => {
            const percentage =
              totalBaskets > 0 ? (row.transaction_count / totalBaskets) * 100 : 0;
            const width = `${Math.max(
              row.transaction_count > 0 ? 5 : 0,
              (row.transaction_count / maxBasketCount) * 100,
            )}%`;
            const isSelected = selectedBasketBand === row.label;

            return (
              <button
                key={row.label}
                type="button"
                className={
                  isSelected
                    ? "traffic-rhythm-basket-row traffic-rhythm-basket-row-active"
                    : "traffic-rhythm-basket-row"
                }
                onClick={() => setSelectedBasketBand(isSelected ? null : row.label)}
              >
                <span className="traffic-rhythm-basket-top">
                  <strong>{formatBasketValueBand(row.label)}</strong>
                  <small>
                    {row.transaction_count} kosár · {percentage.toFixed(1)}%
                  </small>
                </span>
                <span className="traffic-rhythm-basket-track">
                  <span
                    style={{
                      width,
                      background: `linear-gradient(135deg, ${
                        mixPalette[index % mixPalette.length]
                      }, ${mixPalette[(index + 2) % mixPalette.length]})`,
                    }}
                  />
                </span>
              </button>
            );
          })}
        </div>

        {selectedBasketRow ? (
          <div className="traffic-rhythm-basket-detail">
            <span>
              <strong>{formatBasketValueBand(selectedBasketRow.label)}</strong>
              Kiválasztott vásárlási sáv
            </span>
            <span>
              <strong>{selectedBasketRow.transaction_count}</strong>
              Kosár
            </span>
            <span>
              <strong>{formatMoney(selectedBasketRow.revenue)}</strong>
              Bruttó érték
            </span>
          </div>
        ) : null}
      </div>

      {activeCells.length === 0 ? (
        <p className="empty-message">Nincs forgalmi adat ebben az időszakban.</p>
      ) : null}
    </Card>
  );
}

