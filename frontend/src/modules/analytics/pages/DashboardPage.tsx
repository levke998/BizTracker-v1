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

  return formatNumber(kpi.value);
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

function TrendChart({ points }: { points: DashboardTrendPoint[] }) {
  const revenuePath = buildLinePath(points, (point) => toNumber(point.revenue));
  const costPath = buildLinePath(points, (point) => toNumber(point.cost));
  const profitPath = buildLinePath(points, (point) => toNumber(point.profit));

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
        <path
          d={revenuePath}
          fill="none"
          stroke="url(#businessRevenueGradient)"
          strokeWidth="4"
          strokeLinecap="round"
        />
        <path
          d={costPath}
          fill="none"
          stroke="#fb7185"
          strokeWidth="3"
          strokeLinecap="round"
          strokeDasharray="7 8"
        />
        <path
          d={profitPath}
          fill="none"
          stroke="#34d399"
          strokeWidth="3"
          strokeLinecap="round"
        />
      </svg>
      <div className="business-chart-axis">
        {points.slice(0, 6).map((point) => (
          <span key={point.period_start}>{formatDate(point.period_start)}</span>
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
  const {
    dashboard,
    productDetails,
    expenseDetails,
    drilldown,
    setDrilldown,
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
              >
                <span className="kpi-value">{getKpiValue(kpi)}</span>
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
                    <span className="chart-legend-item">
                      <span className="chart-legend-swatch business-swatch-revenue" />
                      Revenue
                    </span>
                    <span className="chart-legend-item">
                      <span className="chart-legend-swatch business-swatch-cost" />
                      Cost
                    </span>
                    <span className="chart-legend-item">
                      <span className="chart-legend-swatch business-swatch-profit" />
                      Profit
                    </span>
                  </div>
                }
              >
                <TrendChart points={dashboard.revenue_trend} />
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
                      onClick={() => setDrilldown({ type: "category", label: row.label })}
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
                      onClick={() => setDrilldown({ type: "expense", label: row.label })}
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
                <Button variant="secondary" onClick={() => setDrilldown(null)}>
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
                        <tr key={`${row.product_name}-${row.category_name}`}>
                          <td>{row.product_name}</td>
                          <td>{row.category_name}</td>
                          <td>{formatMoney(row.revenue)}</td>
                          <td>{formatNumber(row.quantity)}</td>
                          <td>{row.transaction_count}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
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
                        <tr key={row.transaction_id}>
                          <td>{row.occurred_at}</td>
                          <td>{row.transaction_type}</td>
                          <td>{formatMoney(row.amount)}</td>
                          <td>{row.description}</td>
                          <td>{row.source_type}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              ) : null}
            </Card>
          ) : null}
        </>
      ) : null}
    </section>
  );
}
