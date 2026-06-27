import { useState } from "react";

import { Card } from "../../../shared/components/ui/Card";
import type {
  DashboardForecastCategoryDemandRow,
  DashboardForecastImpactRow,
  DashboardForecastPeakTimeRow,
  DashboardForecastProductDemandRow,
  DashboardTemperatureBandInsightRow,
  DashboardWeatherCategoryInsightRow,
  DashboardWeatherConditionInsightRow,
} from "../types/analytics";
import {
  formatDemandSignal,
  formatForecastConfidence,
  formatForecastDate,
  formatMoney,
  formatNumber,
  formatTemperatureBand,
  formatWeatherCondition,
  formatWeatherConditionBand,
  toNumber,
} from "./dashboardView";
export function DashboardWeatherImpact({
  temperatureRows,
  conditionRows,
  categoryRows,
  forecastRows,
}: {
  temperatureRows: DashboardTemperatureBandInsightRow[];
  conditionRows: DashboardWeatherConditionInsightRow[];
  categoryRows: DashboardWeatherCategoryInsightRow[];
  forecastRows: DashboardForecastImpactRow[];
}) {
  const [activeView, setActiveView] = useState<WeatherImpactView>("temperature");
  const totalHistoricalRevenue = temperatureRows.reduce(
    (sum, row) => sum + toNumber(row.revenue),
    0,
  );
  const totalForecastRevenue = forecastRows.reduce(
    (sum, row) => sum + toNumber(row.expected_revenue),
    0,
  );
  const strongestTemperature = [...temperatureRows].sort(
    (left, right) => toNumber(right.revenue) - toNumber(left.revenue),
  )[0];
  const strongestCondition = [...conditionRows].sort(
    (left, right) => toNumber(right.revenue) - toNumber(left.revenue),
  )[0];
  const visibleRows =
    activeView === "temperature"
      ? temperatureRows.map((row) => ({
          key: row.temperature_band,
          label: formatTemperatureBand(row.temperature_band),
          value: toNumber(row.revenue),
          secondary: row.average_temperature_c
            ? `${formatNumber(row.average_temperature_c)} °C átlag`
            : "Nincs hőmérséklet",
          meta: `Vezető kategória: ${row.top_category_name}`,
          tone: row.temperature_band,
        }))
      : activeView === "condition"
        ? conditionRows.map((row) => ({
            key: row.condition_band,
            label: formatWeatherConditionBand(row.condition_band),
            value: toNumber(row.revenue),
            secondary: `${formatNumber(row.precipitation_mm)} mm csapadék`,
            meta: `Vezető kategória: ${row.top_category_name}`,
            tone: row.condition_band,
          }))
        : forecastRows.map((row) => {
            const historical = toNumber(row.historical_average_revenue);
            const expected = toNumber(row.expected_revenue);
            const uplift =
              historical > 0 ? ((expected - historical) / historical) * 100 : 0;
            return {
              key: row.forecast_date,
              label: formatForecastDate(row.forecast_date),
              value: expected,
              secondary: `${uplift >= 0 ? "+" : ""}${formatNumber(uplift)}% várható eltérés`,
              meta: `${formatTemperatureBand(row.dominant_temperature_band)} · ${formatWeatherConditionBand(row.dominant_condition_band)}`,
              tone: row.confidence,
            };
          });
  const maxValue = Math.max(...visibleRows.map((row) => row.value), 1);
  const topCategoryLinks = [...categoryRows]
    .sort((left, right) => toNumber(right.revenue) - toNumber(left.revenue))
    .slice(0, 3);

  return (
    <Card
      hoverable
      tone="rainbow"
      className="weather-impact-card"
      eyebrow="Időjárási hatás"
      title="Kereslet, időjárás és előrejelzés"
      subtitle="Egy csempében a hőmérséklet, égbolt/csapadék és a várható forgalmi hatás"
      count={forecastRows.length > 0 ? `${forecastRows.length} nap forecast` : "Historikus"}
      actions={
        <div className="weather-impact-tabs">
          {[
            { value: "temperature", label: "Hőmérséklet" },
            { value: "condition", label: "Égbolt" },
            { value: "forecast", label: "Forecast" },
          ].map((option) => (
            <button
              key={option.value}
              type="button"
              className={
                activeView === option.value
                  ? "filter-chip filter-chip-active"
                  : "filter-chip"
              }
              onClick={() => setActiveView(option.value as WeatherImpactView)}
            >
              {option.label}
            </button>
          ))}
        </div>
      }
    >
      <div className="weather-impact-summary">
        <span>
          <strong>{formatMoney(totalHistoricalRevenue)}</strong>
          Historikus kapcsolt forgalom
        </span>
        <span>
          <strong>{formatMoney(totalForecastRevenue)}</strong>
          Várható forgalom
        </span>
        <span>
          <strong>
            {strongestTemperature
              ? formatTemperatureBand(strongestTemperature.temperature_band)
              : "-"}
          </strong>
          Legerősebb hősáv
        </span>
        <span>
          <strong>
            {strongestCondition
              ? formatWeatherConditionBand(strongestCondition.condition_band)
              : "-"}
          </strong>
          Legerősebb égbolt
        </span>
      </div>

      <div className="weather-impact-chart" aria-label="Időjárási hatás diagram">
        {visibleRows.slice(0, 7).map((row, index) => {
          const height = `${Math.max(10, (row.value / maxValue) * 100)}%`;
          return (
            <button
              type="button"
              className={`weather-impact-bar ${row.tone}`}
              key={row.key}
              title={`${row.label}: ${formatMoney(row.value)} · ${row.secondary}`}
            >
              <span className="weather-impact-column">
                <span style={{ height }} />
              </span>
              <strong>{formatMoney(row.value)}</strong>
              <small>{row.label}</small>
              <em>{row.secondary}</em>
            </button>
          );
        })}
      </div>

      <div className="weather-impact-context">
        {topCategoryLinks.map((row) => (
          <span key={`${row.category_name}-${row.weather_condition}`}>
            <strong>{row.category_name}</strong>
            {formatWeatherCondition(row.weather_condition)} · {formatMoney(row.revenue)}
          </span>
        ))}
        {visibleRows.length > 0 ? (
          <span>
            <strong>{visibleRows[0].label}</strong>
            {visibleRows[0].meta}
          </span>
        ) : null}
        {activeView === "forecast" && forecastRows[0] ? (
          <span>
            <strong>Javaslat</strong>
            {forecastRows[0].recommendation}
          </span>
        ) : null}
      </div>

      {visibleRows.length === 0 ? (
        <p className="empty-message">
          Nincs még elég időjárással összekapcsolt adat ehhez a nézethez.
        </p>
      ) : null}
    </Card>
  );
}

type WeatherImpactView = "temperature" | "condition" | "forecast";

type DemandForecastDisplayRow = {
  key: string;
  label: string;
  value: number;
  quantity: number;
  secondary: string;
  meta: string;
  signal: string;
  confidence: string;
  recommendation: string;
  topValue?: number;
};

export function DashboardDailyForecast({
  categoryRows,
  productRows,
  peakRows,
}: {
  categoryRows: DashboardForecastCategoryDemandRow[];
  productRows: DashboardForecastProductDemandRow[];
  peakRows: DashboardForecastPeakTimeRow[];
}) {
  const [selectedKey, setSelectedKey] = useState<string | null>(null);
  const rows = Object.values(
    categoryRows.reduce<Record<string, DemandForecastDisplayRow>>((acc, row) => {
      const current = acc[row.forecast_date] ?? {
        key: row.forecast_date,
        label: formatForecastDate(row.forecast_date),
        value: 0,
        quantity: 0,
        secondary: row.category_name,
        meta: `${formatTemperatureBand(row.dominant_temperature_band)} · ${formatWeatherConditionBand(row.dominant_condition_band)}`,
        signal: row.demand_signal,
        confidence: row.confidence,
        recommendation: row.recommendation,
        topValue: 0,
      };
      const rowRevenue = toNumber(row.expected_revenue);
      current.value += rowRevenue;
      current.quantity += toNumber(row.expected_quantity);
      if (rowRevenue > (current.topValue ?? 0)) {
        current.secondary = row.category_name;
        current.topValue = rowRevenue;
      }
      acc[row.forecast_date] = current;
      return acc;
    }, {}),
  ).sort((left, right) => left.key.localeCompare(right.key));
  const maxValue = Math.max(...rows.map((row) => row.value), 1);
  const selectedRow = rows.find((row) => row.key === selectedKey) ?? null;
  const selectedProducts = productRows
    .filter((row) => row.forecast_date === selectedKey)
    .sort((left, right) => toNumber(right.expected_revenue) - toNumber(left.expected_revenue))
    .slice(0, 4);
  const selectedPeaks = peakRows
    .filter((row) => row.forecast_date === selectedKey)
    .sort((left, right) => toNumber(right.expected_revenue) - toNumber(left.expected_revenue))
    .slice(0, 3);
  const totalForecastRevenue = rows.reduce((sum, row) => sum + row.value, 0);

  return (
    <Card
      hoverable
      tone="secondary"
      className="demand-forecast-card demand-forecast-daily-card"
      eyebrow="Gourmand előrejelzés"
      title="Várható kereslet"
      subtitle="Időrendi napi bevételi forecast, napokra kattintható részletekkel"
      count={rows.length > 0 ? `${rows.length} nap` : "Nincs forecast"}
    >
      <div className="demand-forecast-summary">
        <span>
          <strong>{formatMoney(totalForecastRevenue)}</strong>
          Forecast összesen
        </span>
        <span>
          <strong>{rows[0]?.label ?? "-"}</strong>
          Első forecast nap
        </span>
        <span>
          <strong>{rows[rows.length - 1]?.label ?? "-"}</strong>
          Utolsó forecast nap
        </span>
      </div>

      <div className="demand-forecast-chart demand-forecast-timeline">
        {rows.map((row) => {
          const height = `${Math.max(10, (row.value / maxValue) * 100)}%`;
          const isSelected = selectedKey === row.key;
          return (
            <button
              key={row.key}
              type="button"
              className={
                isSelected
                  ? `demand-forecast-row demand-forecast-row-active ${row.signal}`
                  : `demand-forecast-row ${row.signal}`
              }
              onClick={() => setSelectedKey(isSelected ? null : row.key)}
            >
              <span className="demand-forecast-content">
                <span className="demand-forecast-heading">
                  <strong>{row.label}</strong>
                  <small>Vezető kategória: {row.secondary || "-"}</small>
                </span>
                <span className="demand-forecast-track">
                  <span style={{ width: "100%", height }} />
                </span>
                <span className="demand-forecast-meta">
                  <span>{formatMoney(row.value)}</span>
                  <span>{formatNumber(row.quantity)} várható mennyiség</span>
                  <span>{formatDemandSignal(row.signal)}</span>
                </span>
              </span>
            </button>
          );
        })}
      </div>

      {selectedRow ? (
        <div className="demand-forecast-drilldown">
          <div>
            <strong>{selectedRow.label}</strong>
            <span>{selectedRow.meta}</span>
          </div>
          <div className="demand-forecast-drilldown-metrics">
            <span>
              <strong>{formatMoney(selectedRow.value)}</strong>
              Napi becsült bevétel
            </span>
            <span>
              <strong>{formatNumber(selectedRow.quantity)}</strong>
              Várható mennyiség
            </span>
            <span>
              <strong>{formatForecastConfidence(selectedRow.confidence)}</strong>
              Bizalom
            </span>
          </div>
          <div className="demand-forecast-day-detail">
            <div>
              <strong>Várható húzótermékek</strong>
              {selectedProducts.map((product) => (
                <span key={`${product.forecast_date}-${product.product_name}`}>
                  {product.product_name} · {formatMoney(product.expected_revenue)}
                </span>
              ))}
            </div>
            <div>
              <strong>Várható csúcssávok</strong>
              {selectedPeaks.map((peak) => (
                <span key={`${peak.forecast_date}-${peak.time_window}`}>
                  {peak.time_window} · {formatMoney(peak.expected_revenue)}
                </span>
              ))}
            </div>
          </div>
          <p>{selectedRow.recommendation}</p>
        </div>
      ) : null}

      {rows.length === 0 ? (
        <p className="empty-message">
          Nincs még elég forecast adat a Gourmand keresleti nézethez.
        </p>
      ) : null}
    </Card>
  );
}

