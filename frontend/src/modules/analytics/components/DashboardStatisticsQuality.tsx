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

function trendLabel(value: string) {
  const labels: Record<string, string> = {
    increasing: "Emelkedő trend",
    decreasing: "Csökkenő trend",
    volatile: "Volatilis",
    flat: "Stabil oldalazás",
    insufficient_data: "Kevés adat",
  };
  return labels[value] ?? value;
}

function trendClass(value: string) {
  if (value === "increasing" || value === "flat") {
    return "status-pill status-pill-success";
  }
  if (value === "volatile" || value === "decreasing") {
    return "status-pill status-pill-warning";
  }
  return "status-pill";
}

function flagClass(severity: string) {
  return severity === "danger"
    ? "status-pill status-pill-danger"
    : "status-pill status-pill-warning";
}

function insightClass(severity: string) {
  if (severity === "success") {
    return "dashboard-insight dashboard-insight-success";
  }
  if (severity === "danger") {
    return "dashboard-insight dashboard-insight-danger";
  }
  if (severity === "warning") {
    return "dashboard-insight dashboard-insight-warning";
  }
  return "dashboard-insight";
}

function confidenceLabel(value: string) {
  const labels: Record<string, string> = {
    high: "Magas bizalom",
    medium: "Közepes bizalom",
    low: "Alacsony bizalom",
    very_low: "Nagyon alacsony bizalom",
  };
  return labels[value] ?? value;
}

function categoryLabel(value: string) {
  const labels: Record<string, string> = {
    data_quality: "Adatminőség",
    trend: "Trend",
    demand: "Kereslet",
    inventory: "Készlet",
  };
  return labels[value] ?? value;
}

type DashboardStatisticsQualityProps = {
  statistics: DashboardStatisticsQualityModel;
  viewMode: "overview" | "professional";
};

export function DashboardStatisticsQuality({
  statistics,
  viewMode,
}: DashboardStatisticsQualityProps) {
  const isProfessional = viewMode === "professional";
  const latestRollingPoints = statistics.rolling_points.slice(-3);
  const topDemandRows = statistics.product_demand_percentiles.slice(0, 3);

  return (
    <section className="panel dashboard-statistics-quality">
      <div className="panel-header">
        <div>
          <h2>Statisztikai minőség</h2>
          <p className="panel-description">
            Mintaméret, rolling trend, medián és percentilis alap a pontosabb
            döntéstámogatáshoz.
          </p>
        </div>
        <span className={qualityClass(statistics.quality_level)}>
          {qualityLabel(statistics.quality_level)}
        </span>
        <span className={trendClass(statistics.trend_direction)}>
          {trendLabel(statistics.trend_direction)}
        </span>
      </div>

      {statistics.insights.length > 0 ? (
        <div className="dashboard-insight-grid">
          {statistics.insights.slice(0, 3).map((insight) => (
            <article className={insightClass(insight.severity)} key={insight.code}>
              <div className="dashboard-insight-topline">
                <span>{categoryLabel(insight.category)}</span>
                <strong>{confidenceLabel(insight.confidence)}</strong>
              </div>
              <h3>{insight.title}</h3>
              <p>{insight.summary}</p>
              <small>{insight.recommendation}</small>
            </article>
          ))}
        </div>
      ) : null}

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
        <article className="finance-summary-card">
          <span>Trend változás</span>
          <strong>{formatPercent(statistics.trend_change_percent)}</strong>
          <small>volatilitás: {formatPercent(statistics.volatility_percent)}</small>
        </article>
      </div>

      {isProfessional ? (
        <>
          <div className="dashboard-statistics-grid">
            <div className="metric-stack">
              <strong>Napi bevétel eloszlás</strong>
              <span>P25: {formatMoney(statistics.p25_daily_revenue)}</span>
              <span>P75: {formatMoney(statistics.p75_daily_revenue)}</span>
              <span>
                P90/P95: {formatMoney(statistics.p90_daily_revenue)} /{" "}
                {formatMoney(statistics.p95_daily_revenue)}
              </span>
            </div>
            <div className="metric-stack">
              <strong>Kosárérték eloszlás</strong>
              <span>P25: {formatMoney(statistics.p25_basket_value)}</span>
              <span>P75: {formatMoney(statistics.p75_basket_value)}</span>
              <span>
                P90/P95: {formatMoney(statistics.p90_basket_value)} /{" "}
                {formatMoney(statistics.p95_basket_value)}
              </span>
            </div>
          </div>

          {latestRollingPoints.length > 0 ? (
            <div className="dashboard-statistics-grid">
              {latestRollingPoints.map((point) => (
                <div className="metric-stack" key={point.business_date}>
                  <strong>{point.business_date}</strong>
                  <span>Napi bevétel: {formatMoney(point.daily_revenue)}</span>
                  <span>
                    7 napos átlag:{" "}
                    {formatMoney(point.rolling_7_day_average_revenue)}
                  </span>
                  <span>
                    Mozgó medián: {formatMoney(point.moving_7_day_median_revenue)}
                  </span>
                </div>
              ))}
            </div>
          ) : null}

          <div className="dashboard-statistics-grid">
            <div className="metric-stack">
              <strong>Outlier / import kontroll</strong>
              {statistics.outlier_flags.length > 0 ? (
                statistics.outlier_flags.slice(0, 3).map((flag) => (
                  <span key={`${flag.code}-${flag.business_date ?? "basket"}`}>
                    <span className={flagClass(flag.severity)}>{flag.label}</span>{" "}
                    {flag.business_date ?? "kosár"}: {formatMoney(flag.metric_value)}
                  </span>
                ))
              ) : (
                <span>Nincs kiemelt statisztikai figyelmeztetés.</span>
              )}
            </div>
            <div className="metric-stack">
              <strong>Keresleti percentilis alap</strong>
              {topDemandRows.length > 0 ? (
                topDemandRows.map((row) => (
                  <span key={row.label}>
                    {row.label}: P90 {row.p90_daily_quantity} db / P95{" "}
                    {row.p95_daily_quantity} db
                  </span>
                ))
              ) : (
                <span>Nincs termékszintű keresleti minta.</span>
              )}
            </div>
          </div>
        </>
      ) : null}

      <p className="info-message">{statistics.trend_recommendation}</p>
      {isProfessional ? (
        <p className="info-message">
          {statistics.inventory_turnover_readiness.recommendation}
        </p>
      ) : null}
      <p className="info-message">{statistics.recommendation}</p>
    </section>
  );
}
