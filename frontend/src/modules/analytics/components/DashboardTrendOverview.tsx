import { useMemo, useState } from "react";
import type { MouseEvent as ReactMouseEvent } from "react";

import { Card } from "../../../shared/components/ui/Card";
import type {
  DashboardForecastImpactRow,
  DashboardTrendPoint,
} from "../types/analytics";
import {
  formatForecastConfidence,
  formatForecastDate,
  formatGrain,
  formatMoney,
  formatTrendDate,
  toNumber,
} from "./dashboardView";

type TrendMetric = "revenue" | "cost" | "profit";
function buildNumericLinePath(
  values: number[],
  minValue: number,
  maxValue: number,
  offset: number,
  totalPoints: number,
) {
  if (values.length === 0) {
    return "";
  }

  const width = 680;
  const height = 260;
  const paddingLeft = 78;
  const paddingRight = 22;
  const paddingTop = 20;
  const paddingBottom = 38;
  const range = Math.max(maxValue - minValue, 1);
  const step =
    totalPoints > 1
      ? (width - paddingLeft - paddingRight) / (totalPoints - 1)
      : 0;

  return values
    .map((value, index) => {
      const x = paddingLeft + step * (offset + index);
      const normalized = (value - minValue) / range;
      const y =
        height -
        paddingBottom -
        normalized * (height - paddingTop - paddingBottom);
      return `${index === 0 ? "M" : "L"} ${x.toFixed(1)} ${y.toFixed(1)}`;
    })
    .join(" ");
}

const trendMetricConfig: Record<
  TrendMetric,
  { label: string; color: string; dash?: string; value: (point: DashboardTrendPoint) => number }
> = {
  revenue: {
    label: "Bevétel",
    color: "url(#businessRevenueGradient)",
    value: (point) => toNumber(point.revenue),
  },
  cost: {
    label: "Kiadás",
    color: "url(#businessCostGradient)",
    value: (point) => -toNumber(point.cost),
  },
  profit: {
    label: "Profit",
    color: "url(#businessProfitGradient)",
    value: (point) => toNumber(point.profit),
  },
};

function TrendChart({
  points,
  visibleMetrics,
  grain,
  forecastRows,
}: {
  points: DashboardTrendPoint[];
  visibleMetrics: TrendMetric[];
  grain: "hour" | "day" | "month";
  forecastRows: DashboardForecastImpactRow[];
}) {
  const [activeIndex, setActiveIndex] = useState<number | null>(null);
  const width = 680;
  const height = 260;
  const paddingLeft = 78;
  const paddingRight = 22;
  const paddingTop = 20;
  const paddingBottom = 38;
  const activeMetrics: TrendMetric[] =
    visibleMetrics.length > 0 ? visibleMetrics : ["revenue"];
  const forecastValues = forecastRows
    .slice()
    .sort((left, right) => left.forecast_date.localeCompare(right.forecast_date))
    .map((row) => toNumber(row.expected_revenue));
  const totalPointCount = points.length + forecastValues.length;
  const values = useMemo(
    () =>
      [
        ...points.flatMap((point) =>
          activeMetrics.map((metric) => trendMetricConfig[metric].value(point)),
        ),
        ...forecastValues,
      ],
    [activeMetrics, forecastValues, points],
  );
  const maxValue = Math.max(...values, 0, 1);
  const minValue = Math.min(...values, 0);
  const range = Math.max(maxValue - minValue, 1);
  const step =
    points.length > 1
      ? (width - paddingLeft - paddingRight) / (totalPointCount - 1)
      : 0;
  const toY = (value: number) => {
    const normalized = (value - minValue) / range;
    return (
      height -
      paddingBottom -
      normalized * (height - paddingTop - paddingBottom)
    );
  };
  const zeroY = toY(0);
  const paths: Record<TrendMetric, string> = {
    revenue: buildNumericLinePath(
      points.map((point) => toNumber(point.revenue)),
      minValue,
      maxValue,
      0,
      totalPointCount,
    ),
    cost: buildNumericLinePath(
      points.map((point) => -toNumber(point.cost)),
      minValue,
      maxValue,
      0,
      totalPointCount,
    ),
    profit: buildNumericLinePath(
      points.map((point) => toNumber(point.profit)),
      minValue,
      maxValue,
      0,
      totalPointCount,
    ),
  };
  const forecastPath = buildNumericLinePath(
    forecastValues,
    minValue,
    maxValue,
    points.length,
    totalPointCount,
  );
  const activePoint =
    activeIndex !== null && points[activeIndex] ? points[activeIndex] : null;
  const activeForecastRow =
    activeIndex !== null && activeIndex >= points.length
      ? forecastRows[activeIndex - points.length]
      : null;
  const axisLabels = [maxValue, (maxValue + minValue) / 2, minValue];
  const xAxisPoints =
    points.length <= 6
      ? points
      : points.filter((_, index) =>
          [0, Math.floor((points.length - 1) / 2), points.length - 1].includes(index),
        );
  const handleMouseMove = (event: ReactMouseEvent<SVGSVGElement>) => {
    if (points.length === 0) {
      return;
    }

    const bounds = event.currentTarget.getBoundingClientRect();
    const pointerX = ((event.clientX - bounds.left) / bounds.width) * width;
    const clampedX = Math.min(
      Math.max(pointerX, paddingLeft),
      width - paddingRight,
    );
    const nextIndex =
      totalPointCount > 1 ? Math.round((clampedX - paddingLeft) / step) : 0;
    setActiveIndex(Math.min(Math.max(nextIndex, 0), totalPointCount - 1));
  };

  return (
    <div className="business-chart-surface">
      <svg
        className="chart-svg"
        viewBox={`0 0 ${width} ${height}`}
        role="img"
        onMouseMove={handleMouseMove}
        onMouseLeave={() => setActiveIndex(null)}
      >
        <defs>
          <linearGradient id="businessRevenueGradient" x1="0%" x2="100%">
            <stop offset="0%" stopColor="#8b5cf6" />
            <stop offset="55%" stopColor="#d946ef" />
            <stop offset="100%" stopColor="#38bdf8" />
          </linearGradient>
          <linearGradient id="businessCostGradient" x1="0%" x2="100%">
            <stop offset="0%" stopColor="#fb7185" />
            <stop offset="58%" stopColor="#d946ef" />
            <stop offset="100%" stopColor="#8b5cf6" />
          </linearGradient>
          <linearGradient id="businessProfitGradient" x1="0%" x2="100%">
            <stop offset="0%" stopColor="#34d399" />
            <stop offset="58%" stopColor="#8b5cf6" />
            <stop offset="100%" stopColor="#38bdf8" />
          </linearGradient>
          <linearGradient id="businessForecastGradient" x1="0%" x2="100%">
            <stop offset="0%" stopColor="#fbbf24" />
            <stop offset="45%" stopColor="#d946ef" />
            <stop offset="100%" stopColor="#38bdf8" />
          </linearGradient>
        </defs>
        {axisLabels.map((label) => (
          <g key={label.toFixed(2)}>
            <line
              x1={paddingLeft}
              x2={width - paddingRight}
              y1={toY(label)}
              y2={toY(label)}
              stroke="rgba(148, 163, 184, 0.12)"
              strokeWidth="1"
            />
            <text
              x="10"
              y={toY(label) + 4}
              fill="rgba(226, 232, 240, 0.68)"
              fontSize="12"
            >
              {formatMoney(label)}
            </text>
            <line
              x1={paddingLeft - 5}
              x2={paddingLeft}
              y1={toY(label)}
              y2={toY(label)}
              stroke="rgba(226, 232, 240, 0.62)"
              strokeWidth="1.4"
            />
          </g>
        ))}
        <line
          x1={paddingLeft}
          x2={paddingLeft}
          y1={paddingTop}
          y2={height - paddingBottom}
          stroke="rgba(248, 250, 252, 0.86)"
          strokeWidth="2.2"
        />
        <line
          x1={paddingLeft}
          x2={width - paddingRight}
          y1={height - paddingBottom}
          y2={height - paddingBottom}
          stroke="rgba(226, 232, 240, 0.28)"
          strokeWidth="1"
        />
        <text
          x={paddingLeft + 8}
          y={paddingTop + 12}
          fill="rgba(226, 232, 240, 0.58)"
          fontSize="12"
        >
          Összeg
        </text>
        <line
          x1={paddingLeft}
          x2={width - paddingRight}
          y1={zeroY}
          y2={zeroY}
          stroke="rgba(248, 250, 252, 0.42)"
          strokeWidth="1.4"
        />
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
        {forecastPath ? (
          <path
            d={forecastPath}
            fill="none"
            stroke="url(#businessForecastGradient)"
            strokeWidth="3.5"
            strokeLinecap="round"
            strokeDasharray="8 7"
          />
        ) : null}
        {activePoint ? (
          <>
            <line
              x1={paddingLeft + step * (activeIndex ?? 0)}
              x2={paddingLeft + step * (activeIndex ?? 0)}
              y1={paddingTop}
              y2={height - paddingBottom}
              stroke="rgba(248, 250, 252, 0.36)"
              strokeWidth="1"
            />
            {visibleMetrics.map((metric) => (
              <circle
                key={metric}
                cx={paddingLeft + step * (activeIndex ?? 0)}
                cy={toY(trendMetricConfig[metric].value(activePoint))}
                r={metric === "revenue" ? "5" : "4"}
                fill="#0b1020"
                stroke={trendMetricConfig[metric].color}
                strokeWidth="2.4"
              />
            ))}
          </>
        ) : null}
        {activeForecastRow ? (
          <>
            <line
              x1={paddingLeft + step * (activeIndex ?? 0)}
              x2={paddingLeft + step * (activeIndex ?? 0)}
              y1={paddingTop}
              y2={height - paddingBottom}
              stroke="rgba(248, 250, 252, 0.36)"
              strokeWidth="1"
            />
            <circle
              cx={paddingLeft + step * (activeIndex ?? 0)}
              cy={toY(toNumber(activeForecastRow.expected_revenue))}
              r="5"
              fill="#0b1020"
              stroke="url(#businessForecastGradient)"
              strokeWidth="2.4"
            />
          </>
        ) : null}
        <rect
          x={paddingLeft}
          y={paddingTop}
          width={width - paddingLeft - paddingRight}
          height={height - paddingTop - paddingBottom}
          fill="transparent"
          pointerEvents="all"
        />
      </svg>
      <div className="business-chart-axis">
        {xAxisPoints.map((point) => (
          <span key={point.period_start}>
            {formatTrendDate(point.period_start, grain)}
          </span>
        ))}
        {forecastRows.length > 0 ? (
          <span className="business-chart-axis-forecast">
            Forecast {formatForecastDate(forecastRows[forecastRows.length - 1].forecast_date)}
          </span>
        ) : null}
      </div>
      {activePoint ? (
        <div className="business-chart-tooltip">
          <strong>{formatTrendDate(activePoint.period_start, grain, true)}</strong>
          {visibleMetrics.map((metric) => (
            <span key={metric}>
              {trendMetricConfig[metric].label}:{" "}
              {formatMoney(trendMetricConfig[metric].value(activePoint))}
            </span>
          ))}
        </div>
      ) : null}
      {activeForecastRow ? (
        <div className="business-chart-tooltip">
          <strong>{formatForecastDate(activeForecastRow.forecast_date)} forecast</strong>
          <span>Várható bevétel: {formatMoney(activeForecastRow.expected_revenue)}</span>
          <span>
            Historikus átlag: {formatMoney(activeForecastRow.historical_average_revenue)}
          </span>
          <span>{formatForecastConfidence(activeForecastRow.confidence)}</span>
        </div>
      ) : null}
    </div>
  );
}

export function DashboardTrendOverview({
  startDate,
  endDate,
  grain,
  points,
  forecastRows,
}: {
  startDate: string;
  endDate: string;
  grain: "hour" | "day" | "month";
  points: DashboardTrendPoint[];
  forecastRows: DashboardForecastImpactRow[];
}) {
  const [visibleTrendMetrics, setVisibleTrendMetrics] = useState<TrendMetric[]>([
    "revenue",
    "cost",
    "profit",
  ]);

  return (              <Card
                tone="rainbow"
                className="chart-card"
                hoverable
                eyebrow={`${startDate} - ${endDate}`}
                title="Forgalom, kiadás és profit"
                subtitle={formatGrain(grain)}
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
                                : metric === "cost"
                                  ? "linear-gradient(135deg, #fb7185, #8b5cf6)"
                                  : "linear-gradient(135deg, #34d399, #38bdf8)",
                          }}
                        />
                        {trendMetricConfig[metric].label}
                      </button>
                    ))}
                  </div>
                }
              >
                <TrendChart
                  points={points}
                  visibleMetrics={visibleTrendMetrics}
                  grain={grain}
                  forecastRows={forecastRows}
                />
              </Card>
  );
}