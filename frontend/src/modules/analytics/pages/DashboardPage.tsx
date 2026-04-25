import { useState } from "react";

import { Button } from "../../../shared/components/ui/Button";
import { Card } from "../../../shared/components/ui/Card";
import { useDashboard } from "../hooks/useDashboard";
import type {
  DashboardBreakdownRow,
  DashboardExpenseRow,
  DashboardKpi,
  DashboardPeriodPreset,
  DashboardScope,
  DashboardTrendPoint,
} from "../types/analytics";

type TrendMetric = "revenue" | "cost" | "profit" | "estimated_cogs" | "margin_profit";

const scopeOptions: Array<{ value: DashboardScope; label: string }> = [
  { value: "overall", label: "Overall" },
  { value: "flow", label: "Flow" },
  { value: "gourmand", label: "Gourmand" },
];

const periodOptions: Array<{ value: DashboardPeriodPreset; label: string }> = [
  { value: "today", label: "Today" },
  { value: "week", label: "This week" },
  { value: "month", label: "This month" },
  { value: "last_30_days", label: "Last 30 days" },
  { value: "year", label: "This year" },
  { value: "custom", label: "Custom" },
];

function toNumber(value: string) {
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : 0;
}

function formatMoney(value: string | number) {
  return new Intl.NumberFormat("hu-HU", {
    style: "currency",
    currency: "HUF",
    maximumFractionDigits: 0,
  }).format(typeof value === "number" ? value : toNumber(value));
}

function formatNumber(value: string | number) {
  return new Intl.NumberFormat("hu-HU", {
    maximumFractionDigits: 1,
  }).format(typeof value === "number" ? value : toNumber(value));
}

function formatDate(value: string) {
  return new Intl.DateTimeFormat("hu-HU", {
    month: "short",
    day: "2-digit",
  }).format(new Date(value));
}

function getKpiValue(kpi: DashboardKpi) {
  if (kpi.unit === "HUF") {
    return formatMoney(kpi.value);
  }
  if (kpi.unit === "%") {
    return `${formatNumber(kpi.value)}%`;
  }

  return formatNumber(kpi.value);
}

const kpiHelp: Record<string, string> = {
  revenue: "Actual gross revenue from POS sale financial transactions. The secondary line shows recipe or unit-cost margin profit.",
  cost: "Actual posted outflow transactions in the selected period.",
  profit: "Actual finance profit: revenue minus posted outflows.",
  estimated_cogs: "Estimated cost of sold products from recipes or default unit costs.",
  profit_margin: "Estimated margin profit in HUF: revenue minus recipe or unit-cost COGS.",
  gross_margin_percent: "Estimated gross margin percentage: margin profit divided by revenue.",
  transaction_count: "Count of financial transaction records in the selected period.",
  average_basket_value: "Average receipt value derived from POS receipt groups.",
  average_basket_quantity: "Average sold quantity per receipt derived from POS receipt groups.",
};

function getKpiSecondary(kpi: DashboardKpi, allKpis: DashboardKpi[]) {
  if (kpi.code === "revenue") {
    const marginProfit = allKpis.find((item) => item.code === "profit_margin");
    return marginProfit ? `Margin profit: ${formatMoney(marginProfit.value)}` : null;
  }
  if (kpi.code === "profit_margin") {
    const marginPercent = allKpis.find((item) => item.code === "gross_margin_percent");
    return marginPercent ? `${formatNumber(marginPercent.value)}% gross margin` : null;
  }
  return null;
}

function getKpiTone(code: string) {
  if (code === "revenue") {
    return "primary" as const;
  }
  if (code === "cost") {
    return "secondary" as const;
  }
  if (code === "profit") {
    return "highlight" as const;
  }
  if (code === "profit_margin" || code === "average_basket_value") {
    return "secondary" as const;
  }
  return "rainbow" as const;
}

function buildLinePath(
  points: DashboardTrendPoint[],
  valueSelector: (point: DashboardTrendPoint) => number,
) {
  if (points.length === 0) {
    return "";
  }

  const width = 680;
  const height = 220;
  const padding = 24;
  const values = points.flatMap((point) => [
    toNumber(point.revenue),
    toNumber(point.cost),
    toNumber(point.profit),
    toNumber(point.estimated_cogs),
    toNumber(point.margin_profit),
  ]);
  const maxValue = Math.max(...values, 1);
  const minValue = Math.min(...values, 0);
  const range = Math.max(maxValue - minValue, 1);
  const step = points.length > 1 ? (width - padding * 2) / (points.length - 1) : 0;

  return points
    .map((point, index) => {
      const x = padding + step * index;
      const normalized = (valueSelector(point) - minValue) / range;
      const y = height - padding - normalized * (height - padding * 2);
      return `${index === 0 ? "M" : "L"} ${x.toFixed(1)} ${y.toFixed(1)}`;
    })
    .join(" ");
}

const trendMetricConfig: Record<
  TrendMetric,
  { label: string; color: string; dash?: string; value: (point: DashboardTrendPoint) => number }
> = {
  revenue: {
    label: "Revenue",
    color: "url(#businessRevenueGradient)",
    value: (point) => toNumber(point.revenue),
  },
  cost: {
    label: "Cost",
    color: "#fb7185",
    dash: "7 8",
    value: (point) => toNumber(point.cost),
  },
  profit: {
    label: "Profit",
    color: "#34d399",
    value: (point) => toNumber(point.profit),
  },
  estimated_cogs: {
    label: "Estimated COGS",
    color: "#f59e0b",
    dash: "5 7",
    value: (point) => toNumber(point.estimated_cogs),
  },
  margin_profit: {
    label: "Margin profit",
    color: "#38bdf8",
    value: (point) => toNumber(point.margin_profit),
  },
};

function TrendChart({
  points,
  visibleMetrics,
}: {
  points: DashboardTrendPoint[];
  visibleMetrics: TrendMetric[];
}) {
  const paths: Record<TrendMetric, string> = {
    revenue: buildLinePath(points, (point) => toNumber(point.revenue)),
    cost: buildLinePath(points, (point) => toNumber(point.cost)),
    profit: buildLinePath(points, (point) => toNumber(point.profit)),
    estimated_cogs: buildLinePath(points, (point) => toNumber(point.estimated_cogs)),
    margin_profit: buildLinePath(points, (point) => toNumber(point.margin_profit)),
  };

  return (
    <div className="business-chart-surface">
      <svg className="chart-svg" viewBox="0 0 680 220" role="img">
        <defs>
          <linearGradient id="businessRevenueGradient" x1="0%" x2="100%">
            <stop offset="0%" stopColor="#8b5cf6" />
            <stop offset="55%" stopColor="#d946ef" />
            <stop offset="100%" stopColor="#38bdf8" />
          </linearGradient>
        </defs>
        {visibleMetrics.map((metric) => (
          <path
            key={metric}
            d={paths[metric]}
            fill="none"
            stroke={trendMetricConfig[metric].color}
            strokeWidth={metric === "revenue" ? "4" : "3"}
            strokeLinecap="round"
            strokeDasharray={trendMetricConfig[metric].dash}
          />
        ))}
      </svg>
      <div className="business-chart-axis">
        {points.slice(0, 6).map((point) => (
          <span key={point.period_start}>{formatDate(point.period_start)}</span>
        ))}
      </div>
      <div className="business-chart-values">
        {points
          .filter((point) =>
            visibleMetrics.some((metric) => trendMetricConfig[metric].value(point) > 0),
          )
          .slice(-8)
          .map((point) => (
            <div key={point.period_start}>
              <strong>{formatDate(point.period_start)}</strong>
              {visibleMetrics.map((metric) => (
                <span key={metric}>
                  {trendMetricConfig[metric].label}:{" "}
                  {formatMoney(trendMetricConfig[metric].value(point))}
                </span>
              ))}
            </div>
          ))}
      </div>
    </div>
  );
}

function BreakdownBars({
  rows,
  valueKey,
}: {
  rows: DashboardBreakdownRow[] | DashboardExpenseRow[];
  valueKey: "revenue" | "amount";
}) {
  const getRowValue = (row: DashboardBreakdownRow | DashboardExpenseRow) => {
    if (valueKey === "revenue" && "revenue" in row) {
      return row.revenue;
    }
    if (valueKey === "amount" && "amount" in row) {
      return row.amount;
    }
    return "0";
  };
  const maxValue = Math.max(
    ...rows.map((row) => toNumber(getRowValue(row))),
    1,
  );

  return (
    <div className="business-breakdown-list">
      {rows.map((row) => {
        const value = getRowValue(row);
        const width = `${Math.max(3, (toNumber(value) / maxValue) * 100)}%`;

        return (
          <div className="business-breakdown-row" key={row.label}>
            <div className="business-breakdown-top">
              <strong>{row.label}</strong>
              <span>{formatMoney(value)}</span>
            </div>
            <div className="chart-bar">
              <span style={{ width }} />
            </div>
            <span className="section-note">
              {row.transaction_count} records · {row.source_layer}
            </span>
          </div>
        );
      })}
    </div>
  );
}

export function DashboardPage() {
  const [visibleTrendMetrics, setVisibleTrendMetrics] = useState<TrendMetric[]>([
    "revenue",
    "cost",
    "profit",
  ]);
  const {
    dashboard,
    basketPairs,
    basketReceipts,
    productDetails,
    productSourceRows,
    expenseDetails,
    expenseSource,
    drilldown,
    setDrilldown,
    selectedProduct,
    setSelectedProduct,
    selectedExpense,
    setSelectedExpense,
    selectedBasketPair,
    setSelectedBasketPair,
    scope,
    setScope,
    period,
    setPeriod,
    startDate,
    setStartDate,
    endDate,
    setEndDate,
    isLoading,
    isDrilldownLoading,
    errorMessage,
  } = useDashboard();

  return (
    <section className="page-section">
      <section className="panel business-dashboard-toolbar">
        <div className="business-segmented-control">
          {scopeOptions.map((option) => (
            <button
              key={option.value}
              type="button"
              className={
                scope === option.value
                  ? "filter-chip filter-chip-active"
                  : "filter-chip"
              }
              onClick={() => setScope(option.value)}
            >
              {option.label}
            </button>
          ))}
        </div>

        <div className="business-dashboard-filters">
          <label className="field">
            <span>Period</span>
            <select
              className="field-input"
              value={period}
              onChange={(event) =>
                setPeriod(event.target.value as DashboardPeriodPreset)
              }
            >
              {periodOptions.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          </label>

          {period === "custom" ? (
            <>
              <label className="field">
                <span>Start date</span>
                <input
                  className="field-input"
                  type="date"
                  value={startDate}
                  onChange={(event) => setStartDate(event.target.value)}
                />
              </label>
              <label className="field">
                <span>End date</span>
                <input
                  className="field-input"
                  type="date"
                  value={endDate}
                  onChange={(event) => setEndDate(event.target.value)}
                />
              </label>
            </>
          ) : null}

          <Button variant="secondary">Export</Button>
        </div>
      </section>

      {errorMessage ? <p className="error-message">{errorMessage}</p> : null}
      {isLoading ? <p className="info-message">Loading business dashboard...</p> : null}

      {dashboard ? (
        <>
          <div className="kpi-grid">
            {dashboard.kpis.map((kpi) => (
              <Card
                key={kpi.code}
                tone={getKpiTone(kpi.code)}
                className="kpi-card"
                hoverable
                eyebrow={kpi.label}
                data-tooltip={kpiHelp[kpi.code] ?? kpi.label}
              >
                <span className="kpi-value">{getKpiValue(kpi)}</span>
                {getKpiSecondary(kpi, dashboard.kpis) ? (
                  <span className="kpi-caption">
                    {getKpiSecondary(kpi, dashboard.kpis)}
                  </span>
                ) : null}
                <span className="kpi-caption">{kpi.source_layer}</span>
              </Card>
            ))}
          </div>

          <div className="dashboard-main">
            <div className="dashboard-stack">
              <Card
                tone="rainbow"
                className="chart-card"
                hoverable
                eyebrow={`${dashboard.period.start_date} - ${dashboard.period.end_date}`}
                title="Revenue, cost and profit"
                subtitle={`Grouped by ${dashboard.period.grain}`}
                actions={
                  <div className="chart-legend">
                    {(Object.keys(trendMetricConfig) as TrendMetric[]).map((metric) => (
                      <button
                        key={metric}
                        type="button"
                        className={
                          visibleTrendMetrics.includes(metric)
                            ? "chart-legend-item active"
                            : "chart-legend-item"
                        }
                        onClick={() =>
                          setVisibleTrendMetrics((current) =>
                            current.includes(metric)
                              ? current.filter((item) => item !== metric)
                              : [...current, metric],
                          )
                        }
                      >
                        <span
                          className="chart-legend-swatch"
                          style={{
                            background:
                              metric === "revenue"
                                ? "linear-gradient(135deg, #8b5cf6, #38bdf8)"
                                : trendMetricConfig[metric].color,
                          }}
                        />
                        {trendMetricConfig[metric].label}
                      </button>
                    ))}
                  </div>
                }
              >
                <TrendChart
                  points={dashboard.revenue_trend}
                  visibleMetrics={visibleTrendMetrics}
                />
              </Card>

              <Card
                hoverable
                eyebrow="Top products"
                title="Best selling products"
                subtitle="POS import derived revenue and quantity"
                count={dashboard.top_products.length}
              >
                <BreakdownBars rows={dashboard.top_products} valueKey="revenue" />
              </Card>

              <Card
                hoverable
                eyebrow="Basket analysis"
                title="Frequently bought together"
                subtitle="Product pairs derived from POS receipt groups"
                count={basketPairs.length}
              >
                <div className="table-wrap">
                  <table className="data-table">
                    <thead>
                      <tr>
                        <th>Product pair</th>
                        <th>Baskets</th>
                        <th>Gross amount</th>
                      </tr>
                    </thead>
                    <tbody>
                      {basketPairs.map((row) => (
                        <tr
                          key={`${row.product_a}-${row.product_b}`}
                          className={
                            selectedBasketPair?.product_a === row.product_a &&
                            selectedBasketPair?.product_b === row.product_b
                              ? "selected-row"
                              : undefined
                          }
                          onClick={() => setSelectedBasketPair(row)}
                        >
                          <td>
                            {row.product_a} + {row.product_b}
                          </td>
                          <td>{row.basket_count}</td>
                          <td>{formatMoney(row.total_gross_amount)}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                  {basketPairs.length === 0 ? (
                    <p className="info-message">No basket pairs for this period.</p>
                  ) : null}
                  {selectedBasketPair ? (
                    <div className="drilldown-nested-panel">
                      <div className="section-heading-row">
                        <div>
                          <h3>
                            {selectedBasketPair.product_a} +{" "}
                            {selectedBasketPair.product_b}
                          </h3>
                          <p className="section-note">
                            Source receipts containing this product pair
                          </p>
                        </div>
                        <span className="status-pill">
                          {basketReceipts.length} receipts
                        </span>
                      </div>
                      <div className="activity-list">
                        {basketReceipts.map((receipt) => (
                          <article className="activity-item" key={receipt.receipt_no}>
                            <div className="activity-meta">
                              <strong>{receipt.receipt_no}</strong>
                              <span>{receipt.date ?? "-"}</span>
                            </div>
                            <p>
                              {formatMoney(receipt.gross_amount)} -{" "}
                              {formatNumber(receipt.quantity)} items
                            </p>
                            <table className="data-table">
                              <thead>
                                <tr>
                                  <th>Product</th>
                                  <th>Category</th>
                                  <th>Quantity</th>
                                  <th>Gross amount</th>
                                  <th>Payment</th>
                                </tr>
                              </thead>
                              <tbody>
                                {receipt.lines.map((line) => (
                                  <tr key={line.row_id}>
                                    <td>{line.product_name}</td>
                                    <td>{line.category_name}</td>
                                    <td>{formatNumber(line.quantity)}</td>
                                    <td>{formatMoney(line.gross_amount)}</td>
                                    <td>{line.payment_method ?? "-"}</td>
                                  </tr>
                                ))}
                              </tbody>
                            </table>
                          </article>
                        ))}
                      </div>
                    </div>
                  ) : null}
                </div>
              </Card>
            </div>

            <div className="dashboard-stack">
              <Card
                tone="secondary"
                hoverable
                eyebrow="Revenue mix"
                title="Category breakdown"
                subtitle="Categories come from optional POS import category_name values"
                count={dashboard.category_breakdown.length}
              >
                <div className="business-breakdown-actions">
                  {dashboard.category_breakdown.map((row) => (
                    <button
                      key={row.label}
                      type="button"
                      className="business-drilldown-button"
                      onClick={() => {
                        setSelectedProduct(null);
                        setDrilldown({ type: "category", label: row.label });
                      }}
                    >
                      <span>{row.label}</span>
                      <strong>{formatMoney(row.revenue)}</strong>
                    </button>
                  ))}
                </div>
              </Card>

              <Card
                tone="highlight"
                hoverable
                eyebrow="Cost control"
                title="Expense breakdown"
                subtitle="Financial actual outflows by transaction type"
                count={dashboard.expense_breakdown.length}
              >
                <div className="business-breakdown-actions">
                  {dashboard.expense_breakdown.map((row) => (
                    <button
                      key={row.label}
                      type="button"
                      className="business-drilldown-button"
                      onClick={() => {
                        setSelectedExpense(null);
                        setDrilldown({ type: "expense", label: row.label });
                      }}
                    >
                      <span>{row.label}</span>
                      <strong>{formatMoney(row.amount)}</strong>
                    </button>
                  ))}
                </div>
              </Card>

              <Card hoverable eyebrow="Model notes" title="Data lineage">
                <div className="activity-list">
                  {dashboard.notes.map((note) => (
                    <article className="activity-item" key={note}>
                      <p>{note}</p>
                    </article>
                  ))}
                </div>
              </Card>
            </div>
          </div>

          {drilldown ? (
            <Card
              hoverable
              eyebrow="Drill-down"
              title={drilldown.label}
              subtitle={
                drilldown.type === "category"
                  ? "Product-level revenue rows for the selected category"
                  : "Expense transactions for the selected type"
              }
              actions={
                <Button
                  variant="secondary"
                  onClick={() => {
                    setSelectedProduct(null);
                    setSelectedExpense(null);
                    setSelectedBasketPair(null);
                    setDrilldown(null);
                  }}
                >
                  Close
                </Button>
              }
            >
              {isDrilldownLoading ? (
                <p className="info-message">Loading drill-down...</p>
              ) : null}

              {drilldown.type === "category" ? (
                <div className="table-wrap">
                  <table className="data-table">
                    <thead>
                      <tr>
                        <th>Product</th>
                        <th>Category</th>
                        <th>Revenue</th>
                        <th>Quantity</th>
                        <th>Rows</th>
                      </tr>
                    </thead>
                    <tbody>
                      {productDetails.map((row) => (
                        <tr
                          key={`${row.product_name}-${row.category_name}`}
                          className={
                            selectedProduct?.product_name === row.product_name &&
                            selectedProduct?.category_name === row.category_name
                              ? "selected-row"
                              : undefined
                          }
                          onClick={() => setSelectedProduct(row)}
                        >
                          <td>{row.product_name}</td>
                          <td>{row.category_name}</td>
                          <td>{formatMoney(row.revenue)}</td>
                          <td>{formatNumber(row.quantity)}</td>
                          <td>{row.transaction_count}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                  {selectedProduct ? (
                    <div className="drilldown-nested-panel">
                      <div className="section-heading-row">
                        <div>
                          <h3>{selectedProduct.product_name}</h3>
                          <p className="section-note">
                            Source POS rows for this product
                          </p>
                        </div>
                        <span className="status-pill">
                          {productSourceRows.length} rows
                        </span>
                      </div>
                      <table className="data-table">
                        <thead>
                          <tr>
                            <th>Date</th>
                            <th>Receipt</th>
                            <th>Quantity</th>
                            <th>Gross amount</th>
                            <th>Payment</th>
                            <th>Source row</th>
                          </tr>
                        </thead>
                        <tbody>
                          {productSourceRows.map((row) => (
                            <tr key={row.row_id}>
                              <td>{row.date ?? "—"}</td>
                              <td>{row.receipt_no ?? "—"}</td>
                              <td>{formatNumber(row.quantity)}</td>
                              <td>{formatMoney(row.gross_amount)}</td>
                              <td>{row.payment_method ?? "—"}</td>
                              <td>{row.row_number}</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  ) : null}
                </div>
              ) : null}

              {drilldown.type === "expense" ? (
                <div className="table-wrap">
                  <table className="data-table">
                    <thead>
                      <tr>
                        <th>Date</th>
                        <th>Type</th>
                        <th>Amount</th>
                        <th>Description</th>
                        <th>Source</th>
                      </tr>
                    </thead>
                    <tbody>
                      {expenseDetails.map((row) => (
                        <tr
                          key={row.transaction_id}
                          className={
                            selectedExpense?.transaction_id === row.transaction_id
                              ? "selected-row"
                              : undefined
                          }
                          onClick={() => setSelectedExpense(row)}
                        >
                          <td>{row.occurred_at}</td>
                          <td>{row.transaction_type}</td>
                          <td>{formatMoney(row.amount)}</td>
                          <td>{row.description}</td>
                          <td>{row.source_type}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                  {selectedExpense && expenseSource ? (
                    <div className="drilldown-nested-panel">
                      <div className="section-heading-row">
                        <div>
                          <h3>
                            {expenseSource.invoice_number ??
                              expenseSource.source_type}
                          </h3>
                          <p className="section-note">
                            {expenseSource.supplier_name ?? "Source record"} ·{" "}
                            {expenseSource.invoice_date ?? expenseSource.occurred_at}
                          </p>
                        </div>
                        <span className="status-pill">
                          {expenseSource.lines.length} lines
                        </span>
                      </div>
                      <div className="details-grid">
                        <article className="detail-item">
                          <span>Gross total</span>
                          <strong>
                            {expenseSource.gross_total
                              ? formatMoney(expenseSource.gross_total)
                              : formatMoney(expenseSource.amount)}
                          </strong>
                        </article>
                        <article className="detail-item">
                          <span>Source</span>
                          <strong>{expenseSource.source_type}</strong>
                        </article>
                      </div>
                      {expenseSource.lines.length > 0 ? (
                        <table className="data-table">
                          <thead>
                            <tr>
                              <th>Description</th>
                              <th>Quantity</th>
                              <th>Unit net</th>
                              <th>Line net</th>
                              <th>Inventory item</th>
                            </tr>
                          </thead>
                          <tbody>
                            {expenseSource.lines.map((line) => (
                              <tr key={line.line_id}>
                                <td>{line.description}</td>
                                <td>{formatNumber(line.quantity)}</td>
                                <td>{formatMoney(line.unit_net_amount)}</td>
                                <td>{formatMoney(line.line_net_amount)}</td>
                                <td>{line.inventory_item_id ?? "—"}</td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      ) : (
                        <p className="info-message">
                          No structured source lines are available for this transaction.
                        </p>
                      )}
                    </div>
                  ) : null}
                </div>
              ) : null}
            </Card>
          ) : null}
        </>
      ) : null}
    </section>
  );
}
