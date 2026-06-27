import type { DashboardStatisticsQuality as DashboardStatisticsQualityModel } from "../types/analytics";

function formatMoney(value: string) {
  const parsed = Number(value);
  if (!Number.isFinite(parsed)) {
    return `${value} HUF`;
  }
  return new Intl.NumberFormat("hu-HU", {
    style: "currency",
    currency: "HUF",
    maximumFractionDigits: 0,
  }).format(parsed);
}

function formatPercent(value: string) {
  const parsed = Number(value);
  if (!Number.isFinite(parsed)) {
    return `${value}%`;
  }
  return `${parsed.toFixed(1)}%`;
}

function qualityLabel(value: string) {
  const labels: Record<string, string> = {
    strong: "Erős minta",
    usable: "Használható minta",
    limited: "Korlátozott minta",
    insufficient: "Kevés adat",
  };
  return labels[value] ?? value;
}

function qualityClass(value: string) {
  if (value === "strong") {
    return "status-pill status-pill-success";
  }
  if (value === "usable") {
    return "status-pill";
  }
  if (value === "limited") {
    return "status-pill status-pill-warning";
  }
  return "status-pill status-pill-danger";
}

type DashboardStatisticsQualityProps = {
  statistics: DashboardStatisticsQualityModel;
};

export function DashboardStatisticsQuality({
  statistics,
}: DashboardStatisticsQualityProps) {
  return (
    <section className="panel dashboard-statistics-quality">
      <div className="panel-header">
        <div>
          <h2>Statisztikai minőség</h2>
          <p className="panel-description">
            Mintaméret, medián és percentilis alap a pontosabb döntéstámogatáshoz.
          </p>
        </div>
        <span className={qualityClass(statistics.quality_level)}>
          {qualityLabel(statistics.quality_level)}
        </span>
      </div>

      <div className="finance-summary-grid">
        <article className="finance-summary-card">
          <span>Időszaki lefedettség</span>
          <strong>{formatPercent(statistics.coverage_percent)}</strong>
          <small>
            {statistics.active_sales_day_count}/{statistics.period_day_count} aktív nap
          </small>
        </article>
        <article className="finance-summary-card">
          <span>POS sor / kosár</span>
          <strong>
            {statistics.pos_row_count}/{statistics.basket_count}
          </strong>
          <small>mintaméret</small>
        </article>
        <article className="finance-summary-card">
          <span>Napi bevétel medián</span>
          <strong>{formatMoney(statistics.median_daily_revenue)}</strong>
          <small>átlag: {formatMoney(statistics.average_daily_revenue)}</small>
        </article>
        <article className="finance-summary-card">
          <span>Kosár medián</span>
          <strong>{formatMoney(statistics.median_basket_value)}</strong>
          <small>átlag: {formatMoney(statistics.average_basket_value)}</small>
        </article>
      </div>

      <div className="dashboard-statistics-grid">
        <div className="metric-stack">
          <strong>Napi bevétel eloszlás</strong>
          <span>P25: {formatMoney(statistics.p25_daily_revenue)}</span>
          <span>P75: {formatMoney(statistics.p75_daily_revenue)}</span>
          <span>P90/P95: {formatMoney(statistics.p90_daily_revenue)} / {formatMoney(statistics.p95_daily_revenue)}</span>
        </div>
        <div className="metric-stack">
          <strong>Kosárérték eloszlás</strong>
          <span>P25: {formatMoney(statistics.p25_basket_value)}</span>
          <span>P75: {formatMoney(statistics.p75_basket_value)}</span>
          <span>P90/P95: {formatMoney(statistics.p90_basket_value)} / {formatMoney(statistics.p95_basket_value)}</span>
        </div>
      </div>

      <p className="info-message">{statistics.recommendation}</p>
    </section>
  );
}
