import { Fragment, useEffect, useMemo, useState } from "react";
import type { CSSProperties, MouseEvent as ReactMouseEvent } from "react";

import { Button } from "../../../shared/components/ui/Button";
import { Card } from "../../../shared/components/ui/Card";
import { useTopbarControls } from "../../../shared/components/layout/TopbarControlsContext";
import type { EventRecord } from "../../events/types/events";
import { useDashboard } from "../hooks/useDashboard";
import type { DashboardTopProductRow } from "../hooks/useDashboard";
import type {
  DashboardBasketPairRow,
  DashboardBasketReceipt,
  DashboardBreakdownRow,
  DashboardCategoryTrendRow,
  DashboardData,
  DashboardExpenseDetailRow,
  DashboardExpenseRow,
  DashboardExpenseSource,
  DashboardFlowForecastEventRow,
  DashboardForecastCategoryDemandRow,
  DashboardForecastImpactRow,
  DashboardForecastPeakTimeRow,
  DashboardForecastPreparationRow,
  DashboardForecastProductDemandRow,
  DashboardHeatmapCell,
  DashboardKpi,
  DashboardPeriodPreset,
  DashboardPosSourceRow,
  DashboardProductDetailRow,
  DashboardProductRiskRow,
  DashboardScope,
  DashboardStockRiskRow,
  DashboardTemperatureBandInsightRow,
  DashboardTrendPoint,
  DashboardWeatherCategoryInsightRow,
  DashboardWeatherConditionInsightRow,
} from "../types/analytics";

type TrendMetric = "revenue" | "cost" | "profit";
type MixMetric = "revenue" | "quantity";
type BusinessInsight = {
  label: string;
  value: string;
  description: string;
  tone: "primary" | "success" | "warning" | "neutral";
};
type BusinessSpecificMetric = BusinessInsight & {
  share?: number;
};

const scopeOptions: Array<{ value: DashboardScope; label: string }> = [
  { value: "overall", label: "Összesített" },
  { value: "flow", label: "Flow" },
  { value: "gourmand", label: "Gourmand" },
];

const periodOptions: Array<{ value: DashboardPeriodPreset; label: string }> = [
  { value: "last_1_hour", label: "1 óra" },
  { value: "last_6_hours", label: "6 óra" },
  { value: "last_12_hours", label: "12 óra" },
  { value: "today", label: "Ma" },
  { value: "week", label: "Ez a hét" },
  { value: "month", label: "Ez a hónap" },
  { value: "last_30_days", label: "Elmúlt 30 nap" },
  { value: "year", label: "Ez az év" },
  { value: "custom", label: "Egyedi" },
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

function formatTrendDate(
  value: string,
  grain: "hour" | "day" | "month",
  detail = false,
) {
  const date = new Date(value);
  if (grain === "hour") {
    return new Intl.DateTimeFormat("hu-HU", {
      month: "short",
      day: "2-digit",
      hour: "2-digit",
      minute: "2-digit",
    }).format(date);
  }
  if (grain === "month") {
    return new Intl.DateTimeFormat("hu-HU", {
      year: detail ? "numeric" : undefined,
      month: "short",
    }).format(date);
  }
  return new Intl.DateTimeFormat("hu-HU", {
    month: "short",
    day: "2-digit",
  }).format(date);
}

function formatGrain(value: string) {
  if (value === "hour") {
    return "Órás bontás";
  }
  if (value === "month") {
    return "Havi bontás";
  }
  if (value === "day") {
    return "Napi bontás";
  }
  return "Időszaki bontás";
}

function formatSourceLayer(value: string) {
  if (value === "weather_enriched_import") {
    return "Időjárással összekapcsolt eladási adat";
  }
  const labels: Record<string, string> = {
    financial_actual: "Rögzített pénzügyi adat",
    derived_actual: "Számított pénzügyi mutató",
    import_derived: "Importált eladási adat",
    recipe_or_unit_cost: "Becsült termékköltség",
    catalog_inventory_actual: "Katalógus és készletadat",
    inventory_actual: "Készletmozgásból számolt adat",
  };
  return labels[value] ?? "Adatbázisban rögzített adat";
}

function formatAmountBasis(value: string | null | undefined) {
  const labels: Record<string, string> = {
    gross: "Bruttó",
    net: "Nettó",
    vat: "ÁFA",
    mixed: "Vegyes alap",
  };
  return value ? labels[value] ?? value : null;
}

function formatAmountOrigin(value: string | null | undefined) {
  const labels: Record<string, string> = {
    actual: "tényleges",
    derived: "számított",
  };
  return value ? labels[value] ?? value : null;
}

function formatAmountMarker(
  basis: string | null | undefined,
  origin: string | null | undefined,
) {
  const basisLabel = formatAmountBasis(basis);
  const originLabel = formatAmountOrigin(origin);
  return [basisLabel, originLabel].filter(Boolean).join(" · ");
}

function formatTaxBreakdownSource(value: string | null | undefined) {
  const labels: Record<string, string> = {
    supplier_invoice_actual: "Számla alapján bontott",
    partial_supplier_invoice_actual: "Részben számla alapján bontott",
    not_available: "Nincs ÁFA-bontás",
  };
  return value ? labels[value] ?? value : "Nincs ÁFA-bontás";
}

function formatTransactionType(value: string) {
  const labels: Record<string, string> = {
    supplier_invoice: "Beszerzési számla",
    manual_expense: "Kézi költségrögzítés",
    pos_sale: "Kasszás értékesítés",
    expense: "Kiadás",
  };
  return labels[value] ?? value.replaceAll("_", " ");
}

function formatSourceType(value: string) {
  const labels: Record<string, string> = {
    supplier_invoice: "Beszerzési számla",
    supplier_invoice_line: "Beszerzési számlasor",
    import_row: "Importált kasszasor",
    manual_entry: "Kézi rögzítés",
  };
  return labels[value] ?? formatSourceLayer(value);
}

function formatPaymentMethod(value: string) {
  const labels: Record<string, string> = {
    cash: "Készpénz",
    card: "Bankkártya",
    szep: "SZÉP kártya",
    szep_card: "SZÉP kártya",
    transfer: "Átutalás",
    unknown: "Ismeretlen fizetés",
  };
  return labels[value.toLowerCase()] ?? value.replaceAll("_", " ");
}

function formatWeatherCondition(value: string) {
  const labels: Record<string, string> = {
    napos: "Napos",
    reszben_felhos: "Részben felhős",
    borult: "Borult",
    kodos: "Ködös",
    esos: "Esős",
    havas: "Havas",
    szeles: "Szeles",
    viharos: "Viharos",
    ismeretlen: "Ismeretlen",
  };
  return labels[value] ?? value.replaceAll("_", " ");
}

function formatTemperatureBand(value: string) {
  const labels: Record<string, string> = {
    hideg: "Hideg",
    enyhe: "Enyhe",
    meleg: "Meleg",
    kanikula: "Kánikula",
  };
  return labels[value] ?? value.replaceAll("_", " ");
}

function formatWeatherConditionBand(value: string) {
  const labels: Record<string, string> = {
    napos_szaraz: "Napos, száraz",
    reszben_felhos: "Részben felhős",
    borult: "Borult",
    csapadekos: "Csapadékos",
  };
  return labels[value] ?? value.replaceAll("_", " ");
}

function formatForecastDate(value: string) {
  return new Intl.DateTimeFormat("hu-HU", {
    weekday: "short",
    month: "short",
    day: "2-digit",
  }).format(new Date(`${value}T12:00:00`));
}

function formatForecastConfidence(value: string) {
  const labels: Record<string, string> = {
    magas: "Magas bizalom",
    kozepes: "Közepes bizalom",
    alacsony: "Alacsony bizalom",
  };
  return labels[value] ?? value;
}

function formatDemandSignal(value: string) {
  const labels: Record<string, string> = {
    emelkedo: "Emelkedő kereslet",
    normal: "Normál kereslet",
    visszafogott: "Visszafogott kereslet",
  };
  return labels[value] ?? value;
}

function formatReadinessLevel(value: string) {
  const labels: Record<string, string> = {
    rendben: "Rendben",
    figyelendo: "Figyelendő",
    kritikus: "Kritikus",
  };
  return labels[value] ?? value;
}

function formatBasketValueBand(value: string) {
  const labels: Record<string, string> = {
    "0-999": "0-999 Ft",
    "1000-2499": "1 000-2 499 Ft",
    "2500-4999": "2 500-4 999 Ft",
    "5000-9999": "5 000-9 999 Ft",
    "10000+": "10 000 Ft felett",
  };
  return labels[value] ?? value;
}

const heatmapWeekdays = ["Hét", "Ked", "Sze", "Csü", "Pén", "Szo", "Vas"];

function formatHeatmapHour(hour: number) {
  return `${String(hour).padStart(2, "0")}:00`;
}

function formatEventDate(value: string | null) {
  if (!value) {
    return "-";
  }
  return new Intl.DateTimeFormat("hu-HU", {
    month: "short",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  }).format(new Date(value));
}

function isTicketLikeLabel(value: string | null | undefined) {
  const normalized = (value ?? "").toLowerCase();
  return [
    "ticket",
    "jegy",
    "vip",
    "belépő",
    "belepo",
    "bérlet",
    "berlet",
    "pass",
  ].some((keyword) => normalized.includes(keyword));
}

function getTopCategory(rows: DashboardBreakdownRow[]) {
  return [...rows].sort((left, right) => toNumber(right.revenue) - toNumber(left.revenue))[0];
}

function getStrongestHeatmapCell(cells: DashboardHeatmapCell[]) {
  return [...cells].sort((left, right) => toNumber(right.revenue) - toNumber(left.revenue))[0];
}

function getWeekdayLabel(value: number) {
  return heatmapWeekdays[value] ?? "-";
}

function getKpiLabel(kpi: DashboardKpi) {
  return kpiLabels[kpi.code] ?? kpi.label;
}

function getVisibleKpis(kpis: DashboardKpi[]) {
  return visibleKpiCodes
    .map((code) => kpis.find((kpi) => kpi.code === code))
    .filter((kpi): kpi is DashboardKpi => Boolean(kpi));
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
  revenue: "Bruttó bevétel a kiválasztott időszak eladási tranzakcióiból.",
  cost: "Rögzített kiadások és költségoldali tranzakciók a kiválasztott időszakban.",
  profit: "Kontrolling profit: bevétel mínusz rögzített kiadás.",
  transaction_count: "A kiválasztott időszakban rögzített pénzügyi tranzakciók száma.",
  average_basket_value: "Átlagos nyugtaérték a rögzített eladások alapján.",
  average_basket_quantity: "Egy nyugtára jutó átlagos eladott mennyiség.",
};

const kpiLabels: Record<string, string> = {
  revenue: "Bevétel",
  cost: "Kiadás",
  profit: "Profit",
  transaction_count: "Tranzakciók",
  average_basket_value: "Átlagkosár érték",
  average_basket_quantity: "Átlagkosár mennyiség",
};

const visibleKpiCodes = [
  "revenue",
  "cost",
  "profit",
  "transaction_count",
  "average_basket_value",
  "average_basket_quantity",
];

const mixPalette = [
  "#8b5cf6",
  "#d946ef",
  "#38bdf8",
  "#34d399",
  "#f59e0b",
  "#fb7185",
  "#a78bfa",
  "#22d3ee",
];

function getKpiSecondary(kpi: DashboardKpi, allKpis: DashboardKpi[]) {
  if (kpi.code === "revenue") {
    const transactions = allKpis.find((item) => item.code === "transaction_count");
    return transactions ? `${formatNumber(transactions.value)} tranzakció` : null;
  }
  if (kpi.code === "cost") {
    const estimatedCogs = allKpis.find((item) => item.code === "estimated_cogs");
    return estimatedCogs
      ? `Becsült eladott áruk költsége: ${formatMoney(estimatedCogs.value)}`
      : null;
  }
  if (kpi.code === "profit") {
    const marginProfit = allKpis.find((item) => item.code === "profit_margin");
    const marginPercent = allKpis.find((item) => item.code === "gross_margin_percent");
    if (marginProfit && marginPercent) {
      return `Árrés profit: ${formatMoney(marginProfit.value)} · ${formatNumber(
        marginPercent.value,
      )}%`;
    }
    return marginProfit ? `Árrés profit: ${formatMoney(marginProfit.value)}` : null;
  }
  if (kpi.code === "transaction_count") {
    const basket = allKpis.find((item) => item.code === "average_basket_value");
    return basket ? `Átlagkosár: ${formatMoney(basket.value)}` : null;
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
  minValue: number,
  maxValue: number,
) {
  if (points.length === 0) {
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
    points.length > 1
      ? (width - paddingLeft - paddingRight) / (points.length - 1)
      : 0;

  return points
    .map((point, index) => {
      const x = paddingLeft + step * index;
      const normalized = (valueSelector(point) - minValue) / range;
      const y =
        height -
        paddingBottom -
        normalized * (height - paddingTop - paddingBottom);
      return `${index === 0 ? "M" : "L"} ${x.toFixed(1)} ${y.toFixed(1)}`;
    })
    .join(" ");
}

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

function buildBusinessInsights(dashboard: {
  scope: DashboardScope;
  category_breakdown: DashboardBreakdownRow[];
  traffic_heatmap: DashboardHeatmapCell[];
  top_products: DashboardBreakdownRow[];
  category_trends: DashboardCategoryTrendRow[];
  product_risks: DashboardProductRiskRow[];
  stock_risks: DashboardStockRiskRow[];
}): BusinessInsight[] {
  const topCategory = getTopCategory(dashboard.category_breakdown);
  const strongestSlot = getStrongestHeatmapCell(dashboard.traffic_heatmap);
  const ticketRows = dashboard.top_products.filter(
    (row) => isTicketLikeLabel(row.label),
  );
  const ticketRevenue = ticketRows.reduce((sum, row) => sum + toNumber(row.revenue), 0);
  const topProductsRevenue = dashboard.top_products.reduce(
    (sum, row) => sum + toNumber(row.revenue),
    0,
  );
  const ticketShare = topProductsRevenue > 0 ? (ticketRevenue / topProductsRevenue) * 100 : 0;
  const growingCategories = dashboard.category_trends.filter(
    (row) => toNumber(row.revenue_change) > 0,
  ).length;
  const criticalRisks = dashboard.product_risks.filter(
    (row) => row.risk_level === "danger",
  ).length + dashboard.stock_risks.filter((row) => row.risk_level === "danger").length;

  if (dashboard.scope === "flow") {
    return [
      {
        label: "Bevételi fókusz",
        value: topCategory?.label ?? "-",
        description:
          "A Flow dashboard itt a tényleges forgalmat, kategóriákat és bevételi mixet mutatja.",
        tone: "primary",
      },
      {
        label: "Jegyhatás",
        value: ticketRows.length > 0 ? `${formatNumber(ticketShare)}%` : "Nincs jelzés",
        description:
          ticketRows.length > 0
            ? "A top termék rangsorban jegy vagy VIP elem is megjelenik, ezt külön értékesítési rétegként kell majd kezelni."
            : "A jelenlegi top listában nem látszik jegy jellegű termék.",
        tone: ticketRows.length > 0 ? "warning" : "neutral",
      },
      {
        label: "Csúcsidő",
        value: strongestSlot
          ? `${getWeekdayLabel(strongestSlot.weekday)} ${formatHeatmapHour(strongestSlot.hour)}`
          : "-",
        description:
          "Flow-nál ez segíti a pult, személyzet, készlet és beléptetés időzítését.",
        tone: "success",
      },
      {
        label: "Fogyasztási kosár",
        value: topCategory?.label ?? "-",
        description:
          "A vezető kategória a bár- és fogyasztási oldal napi üzleti döntéseihez ad jelet.",
        tone: "primary",
      },
    ];
  }

  if (dashboard.scope === "gourmand") {
    return [
      {
        label: "Kategória fókusz",
        value: topCategory?.label ?? "-",
        description:
          "A kasszából érkező valós kategóriák aránya alapján érdemes gyártást és készletet tervezni.",
        tone: "primary",
      },
      {
        label: "Időjárás kapcsolat",
        value: "Előkészítve",
        description:
          "Fagyi, hideg ital és impulzusvásárlás esetén az időjárás később prediktív dimenzióként kerülhet be.",
        tone: "neutral",
      },
      {
        label: "Termelési ritmus",
        value: strongestSlot
          ? `${getWeekdayLabel(strongestSlot.weekday)} ${formatHeatmapHour(strongestSlot.hour)}`
          : "-",
        description:
          "A legerősebb idősáv segít előkészíteni a pultot, sütést, fagyi készletet és munkaerőt.",
        tone: "success",
      },
      {
        label: "Készletkockázat",
        value: `${criticalRisks}`,
        description:
          "A recept és alapanyag kockázatok közvetlenül hatnak arra, hogy mit lehet biztonságosan kínálni.",
        tone: criticalRisks > 0 ? "warning" : "success",
      },
    ];
  }

  return [
    {
      label: "Üzletágak",
      value: "Flow + Gourmand",
      description:
        "Az összesített nézet vezetői képet ad, de a Flow és Gourmand döntési logikája külön fejlődik tovább.",
      tone: "primary",
    },
    {
      label: "Jegy vs termék",
      value: ticketRows.length > 0 ? `${ticketRows.length} jelölt` : "Nincs jelzés",
      description:
        "Összesített rangsorban a jegyek bevételi hatása fontos, de nem ugyanaz, mint egy fogyasztási termék teljesítménye.",
      tone: ticketRows.length > 0 ? "warning" : "neutral",
    },
    {
      label: "Növekvő kategóriák",
      value: `${growingCategories}`,
      description:
        "A kategória trend jelzi, hol erősödik a kereslet az előző azonos időszakhoz képest.",
      tone: growingCategories > 0 ? "success" : "neutral",
    },
    {
      label: "Csúcsidő",
      value: strongestSlot
        ? `${getWeekdayLabel(strongestSlot.weekday)} ${formatHeatmapHour(strongestSlot.hour)}`
        : "-",
      description:
        "A legerősebb idősáv összüzleti kapacitástervezéshez használható.",
      tone: "success",
    },
  ];
}

function BusinessFocusCard({ dashboard }: { dashboard: DashboardData }) {
  const insights = buildBusinessInsights(dashboard);
  const title =
    dashboard.scope === "flow"
      ? "Flow üzleti fókusz"
      : dashboard.scope === "gourmand"
        ? "Gourmand üzleti fókusz"
        : "Vezetői fókusz";
  const subtitle =
    dashboard.scope === "flow"
      ? "Bevétel, jegyhatás, csúcsidő és fogyasztási mix"
      : dashboard.scope === "gourmand"
        ? "Kategória, időjárás, termelési ritmus és receptkockázat"
        : "Összesített kép, külön kezelendő üzletági logikákkal";

  return (
    <Card
      tone="rainbow"
      hoverable
      className="business-focus-card"
      eyebrow="Üzletág-specifikus nézet"
      title={title}
      subtitle={subtitle}
      count={dashboard.business_unit_name ?? "Összesített"}
    >
      <div className="business-focus-grid">
        {insights.map((insight) => (
          <article className={`business-focus-item ${insight.tone}`} key={insight.label}>
            <span>{insight.label}</span>
            <strong>{insight.value}</strong>
            <small>{insight.description}</small>
          </article>
        ))}
      </div>
    </Card>
  );
}

function getDaypart(hour: number) {
  if (hour < 10) {
    return "Reggeli nyitás";
  }
  if (hour < 14) {
    return "Délelőtti csúcs";
  }
  if (hour < 18) {
    return "Délutáni forgalom";
  }
  return "Esti zárásközeli sáv";
}

function buildGourmandCategoryMetrics(rows: DashboardBreakdownRow[]) {
  return rows
    .map((row) => ({
      label: row.label,
      revenue: toNumber(row.revenue),
      quantity: toNumber(row.quantity),
      count: row.transaction_count,
    }))
    .sort((left, right) => right.revenue - left.revenue);
}

function BusinessSpecificAnalyticsCard({ dashboard }: { dashboard: DashboardData }) {
  const topCategory = getTopCategory(dashboard.category_breakdown);
  const strongestSlot = getStrongestHeatmapCell(dashboard.traffic_heatmap);
  const topProduct = dashboard.top_products[0];

  if (dashboard.scope === "gourmand") {
    const categoryRows = buildGourmandCategoryMetrics(dashboard.category_breakdown);
    const totalRevenue = categoryRows.reduce((sum, row) => sum + row.revenue, 0);
    const maxCategoryRevenue = Math.max(...categoryRows.map((row) => row.revenue), 1);
    const leader = categoryRows[0] ?? null;
    const growingCategories = dashboard.category_trends.filter(
      (row) => toNumber(row.revenue_change) > 0,
    ).length;
    const metrics: BusinessSpecificMetric[] = [
      {
        label: "Vezető kategória",
        value: leader?.label ?? "-",
        description: leader
          ? `${formatMoney(leader.revenue)} forgalom, ${formatNumber(leader.quantity)} eladott mennyiség.`
          : "Nincs még elég kategóriaadat.",
        tone: "primary",
        share: leader && totalRevenue > 0 ? (leader.revenue / totalRevenue) * 100 : 0,
      },
      {
        label: "Csúcspont",
        value: strongestSlot
          ? `${getWeekdayLabel(strongestSlot.weekday)} ${formatHeatmapHour(strongestSlot.hour)}`
          : "-",
        description: strongestSlot
          ? `${getDaypart(strongestSlot.hour)}: pult, sütés, fagyi és személyzet ehhez igazítható.`
          : "Nincs még forgalmi hőtérkép adat.",
        tone: "success",
      },
      {
        label: "Trendben erősödik",
        value: `${growingCategories} kategória`,
        description:
          "Az előző azonos időszakhoz képest növekvő kategóriák mutatják, merre mozdul a kereslet.",
        tone: growingCategories > 0 ? "success" : "neutral",
      },
      {
        label: "Pult fókusz",
        value: topProduct?.label ?? topCategory?.label ?? "-",
        description:
          "A legerősebb termék vagy kategória adja a napi kihelyezés és készültség első jelzését.",
        tone: "warning",
      },
    ];

    return (
      <Card
        tone="secondary"
        hoverable
        className="business-specific-card"
        eyebrow="Gourmand elemzés"
        title="Valós kategóriák és termelési ritmus"
        subtitle="Az importált kasszakategóriák alapján, családosítás nélkül"
        count={`${categoryRows.length} kategória`}
      >
        <div className="business-specific-grid">
          {metrics.map((metric) => (
            <article className={`business-focus-item ${metric.tone}`} key={metric.label}>
              <span>{metric.label}</span>
              <strong>{metric.value}</strong>
              <small>{metric.description}</small>
            </article>
          ))}
        </div>

        <div className="business-family-list">
          {categoryRows.map((row, index) => {
            const width = `${Math.max(5, (row.revenue / maxCategoryRevenue) * 100)}%`;
            const share = totalRevenue > 0 ? (row.revenue / totalRevenue) * 100 : 0;
            return (
              <article className="business-family-row" key={row.label}>
                <div>
                  <strong>{row.label}</strong>
                  <span>{formatMoney(row.revenue)} · {formatNumber(share)}%</span>
                </div>
                <span className="business-family-track">
                  <span
                    style={{
                      width,
                      background: `linear-gradient(135deg, ${mixPalette[index % mixPalette.length]}, ${
                        mixPalette[(index + 2) % mixPalette.length]
                      })`,
                    }}
                  />
                </span>
                <small>{formatNumber(row.quantity)} mennyiség · {row.count} nyugtasor</small>
              </article>
            );
          })}
        </div>
      </Card>
    );
  }

  if (dashboard.scope === "flow") {
    const ticketRows = dashboard.top_products.filter((row) => isTicketLikeLabel(row.label));
    const ticketRevenue = ticketRows.reduce((sum, row) => sum + toNumber(row.revenue), 0);
    const topRevenue = dashboard.top_products.reduce((sum, row) => sum + toNumber(row.revenue), 0);
    const ticketShare = topRevenue > 0 ? (ticketRevenue / topRevenue) * 100 : 0;
    const metrics: BusinessSpecificMetric[] = [
      {
        label: "Jegybevétel jelzés",
        value: ticketRows.length > 0 ? `${formatNumber(ticketShare)}%` : "Nincs jelzés",
        description:
          "A jegybevétel üzleti logikája eltér a bárfogyasztástól, ezért külön bevételi rétegként kezeljük.",
        tone: ticketRows.length > 0 ? "warning" : "neutral",
      },
      {
        label: "Bárfogyasztás",
        value: topCategory?.label ?? "-",
        description:
          "A nem jegy jellegű kategóriák fogják mutatni, milyen koncert milyen pultforgalmat hoz.",
        tone: "primary",
      },
      {
        label: "Csúcspont",
        value: strongestSlot
          ? `${getWeekdayLabel(strongestSlot.weekday)} ${formatHeatmapHour(strongestSlot.hour)}`
          : "-",
        description:
          "Flow esetén ez a beléptetés, pult, pohárkészlet és személyzet egyik legfontosabb jelzése.",
        tone: "success",
      },
    ];

    return (
      <Card
        tone="secondary"
        hoverable
        className="business-specific-card"
        eyebrow="Flow elemzés"
        title="Jegy és bár bevételi mix"
        subtitle="A dashboard a Flow forgalmi oldalát mutatja, a POS-ból rögzített tényleges adatokból"
        count={`${dashboard.category_breakdown.length} kategória`}
      >
        <div className="business-specific-grid business-specific-grid-three">
          {metrics.map((metric) => (
            <article className={`business-focus-item ${metric.tone}`} key={metric.label}>
              <span>{metric.label}</span>
              <strong>{metric.value}</strong>
              <small>{metric.description}</small>
            </article>
          ))}
        </div>
      </Card>
    );
  }

  return (
    <Card
      tone="secondary"
      hoverable
      className="business-specific-card"
      eyebrow="Összesített elemzés"
      title="Külön logikák egy vezetői nézetben"
      subtitle="Az overall dashboard jelzi a teljes képet, de a döntéseket üzletáganként kell bontani"
      count="Flow + Gourmand"
    >
      <div className="business-specific-grid business-specific-grid-three">
        <article className="business-focus-item primary">
          <span>Vezető kategória</span>
          <strong>{topCategory?.label ?? "-"}</strong>
          <small>Az összesített képben ez a legnagyobb forgalmú kategória.</small>
        </article>
        <article className="business-focus-item warning">
          <span>Jegyhatás</span>
          <strong>
            {dashboard.top_products.some((row) => isTicketLikeLabel(row.label))
              ? "Külön bontandó"
              : "Nincs jelzés"}
          </strong>
          <small>A jegyek top termékként torzíthatják a fogyasztási toplistát.</small>
        </article>
        <article className="business-focus-item success">
          <span>Csúcspont</span>
          <strong>
            {strongestSlot
              ? `${getWeekdayLabel(strongestSlot.weekday)} ${formatHeatmapHour(strongestSlot.hour)}`
              : "-"}
          </strong>
          <small>A legerősebb idősáv kapacitás- és készlettervezési jelzés.</small>
        </article>
      </div>
    </Card>
  );
}

function FlowEventPerformanceCard({
  events,
  isLoading,
}: {
  events: EventRecord[];
  isLoading: boolean;
}) {
  const completedEvents = events.filter((event) => event.status !== "cancelled");
  const [selectedEventId, setSelectedEventId] = useState<string | null>(null);
  const summary = completedEvents.reduce(
    (acc, event) => ({
      ticketRevenue: acc.ticketRevenue + toNumber(event.ticket_revenue_gross),
      barRevenue: acc.barRevenue + toNumber(event.bar_revenue_gross),
      performerShare: acc.performerShare + toNumber(event.performer_share_amount),
      ownRevenue: acc.ownRevenue + toNumber(event.own_revenue),
      profit: acc.profit + toNumber(event.event_profit_lite),
    }),
    {
      ticketRevenue: 0,
      barRevenue: 0,
      performerShare: 0,
      ownRevenue: 0,
      profit: 0,
    },
  );
  const strongestEvent = [...completedEvents].sort(
    (left, right) => toNumber(right.event_profit_lite) - toNumber(left.event_profit_lite),
  )[0];
  const rankedEvents = [...completedEvents].sort(
    (left, right) => toNumber(right.event_profit_lite) - toNumber(left.event_profit_lite),
  );
  const selectedEvent =
    rankedEvents.find((event) => event.id === selectedEventId) ?? strongestEvent ?? null;
  const averageProfit =
    completedEvents.length > 0 ? summary.profit / completedEvents.length : 0;
  const selectedTicketRevenue = selectedEvent ? toNumber(selectedEvent.ticket_revenue_gross) : 0;
  const selectedBarRevenue = selectedEvent ? toNumber(selectedEvent.bar_revenue_gross) : 0;
  const selectedTotalRevenue = selectedTicketRevenue + selectedBarRevenue;
  const selectedTicketShare =
    selectedTotalRevenue > 0 ? (selectedTicketRevenue / selectedTotalRevenue) * 100 : 0;
  const selectedBarShare =
    selectedTotalRevenue > 0 ? (selectedBarRevenue / selectedTotalRevenue) * 100 : 0;

  return (
    <Card
      tone="rainbow"
      hoverable
      className="flow-event-performance-card"
      eyebrow="Flow event teljesítmény"
      title="Események összehasonlítása"
      subtitle="Jegybevétel, bárbevétel, előadói rész és saját eredmény"
      count={`${completedEvents.length} esemény`}
    >
      {isLoading ? <p className="info-message">Események betöltése...</p> : null}

      <div className="flow-event-summary-grid">
        <span>
          <strong>{formatMoney(summary.ticketRevenue)}</strong>
          Jegybevétel
        </span>
        <span>
          <strong>{formatMoney(summary.barRevenue)}</strong>
          Bárbevétel
        </span>
        <span>
          <strong>{formatMoney(summary.performerShare)}</strong>
          Előadói rész
        </span>
        <span>
          <strong>{formatMoney(summary.profit)}</strong>
          Gyors event profit
        </span>
      </div>

      <div className="flow-event-highlight">
        <article className="business-focus-item primary">
          <span>Flow saját bevétel</span>
          <strong>{formatMoney(summary.ownRevenue)}</strong>
          <small>Megtartott jegybevétel plusz bárbevétel a kiválasztott időszak eventjeiből.</small>
        </article>
        <article className={averageProfit >= 0 ? "business-focus-item success" : "business-focus-item warning"}>
          <span>Átlagos event profit</span>
          <strong>{formatMoney(averageProfit)}</strong>
          <small>Gyors benchmark, hogy egy koncert átlagosan mennyit hoz a jelenlegi adatokkal.</small>
        </article>
      </div>

      {strongestEvent ? (
        <div className="flow-event-top">
          <div>
            <span>Legerősebb event</span>
            <strong>{strongestEvent.title}</strong>
            <small>
              {formatEventDate(strongestEvent.starts_at)} ·{" "}
              {strongestEvent.performer_name ?? "fellépő nélkül"}
            </small>
          </div>
          <strong>{formatMoney(strongestEvent.event_profit_lite)}</strong>
        </div>
      ) : (
        <p className="empty-message">
          Nincs event az időszakban. Flow esetén ez nem hiba: téli vagy szüneteltetett hétvégén
          természetes lehet.
        </p>
      )}

      {rankedEvents.length > 0 ? (
        <div className="flow-event-drilldown">
          <div className="flow-event-ranking">
            <div className="flow-event-subheading">
              <span>Event rangsor</span>
              <strong>Profit szerint</strong>
            </div>
            {rankedEvents.slice(0, 8).map((event, index) => {
              const isSelected = selectedEvent?.id === event.id;
              const profit = toNumber(event.event_profit_lite);
              const maxProfit = Math.max(
                ...rankedEvents.map((item) => Math.max(0, toNumber(item.event_profit_lite))),
                1,
              );
              const width = `${Math.max(4, (Math.max(0, profit) / maxProfit) * 100)}%`;

              return (
                <button
                  className={isSelected ? "flow-event-rank-row active" : "flow-event-rank-row"}
                  key={event.id}
                  type="button"
                  onClick={() => setSelectedEventId(event.id)}
                >
                  <span className="flow-event-rank-number">{index + 1}</span>
                  <div>
                    <strong>{event.title}</strong>
                    <small>
                      {formatEventDate(event.starts_at)} ·{" "}
                      {event.performer_name ?? "fellépő nélkül"}
                    </small>
                    <span className="flow-event-rank-bar">
                      <span style={{ width }} />
                    </span>
                  </div>
                  <strong>{formatMoney(event.event_profit_lite)}</strong>
                </button>
              );
            })}
          </div>

          <div className="flow-event-detail-panel">
            {selectedEvent ? (
              <>
                <div className="flow-event-subheading">
                  <span>Kiválasztott event</span>
                  <strong>{selectedEvent.title}</strong>
                </div>
                <div className="flow-event-detail-metrics">
                  <span>Jegyarány <strong>{formatNumber(selectedTicketShare)}%</strong></span>
                  <span>Bárarány <strong>{formatNumber(selectedBarShare)}%</strong></span>
                  <span>Előadói rész <strong>{formatMoney(selectedEvent.performer_share_amount)}</strong></span>
                  <span>Saját bevétel <strong>{formatMoney(selectedEvent.own_revenue)}</strong></span>
                </div>
                <div className="flow-event-split">
                  <span style={{ width: `${selectedTicketShare}%` }} />
                  <span style={{ width: `${selectedBarShare}%` }} />
                </div>
                <div className="flow-event-detail-note">
                  <strong>{formatMoney(selectedEvent.event_profit_lite)}</strong>
                  <span>
                    Gyors event profit: megtartott jegybevétel + bárbevétel - fix fellépti díj - event költség.
                  </span>
                </div>
              </>
            ) : null}
          </div>
        </div>
      ) : null}

    </Card>
  );
}

function FlowForecastEventCard({
  rows,
}: {
  rows: DashboardFlowForecastEventRow[];
}) {
  const criticalCount = rows.filter((row) => row.preparation_level === "kritikus").length;
  const watchCount = rows.filter((row) => row.preparation_level === "figyelendo").length;
  const nextEvent = rows[0] ?? null;

  return (
    <Card
      tone="secondary"
      hoverable
      className="flow-forecast-event-card"
      eyebrow="Flow előkészítés"
      title="Közelgő event forecast"
      subtitle="Event naptár és Szolnok forecast cache alapján"
      count={criticalCount > 0 ? `${criticalCount} kritikus` : `${rows.length} event`}
    >
      <div className="flow-forecast-summary">
        <span>
          <strong>{criticalCount}</strong>
          Kritikus jelzés
        </span>
        <span>
          <strong>{watchCount}</strong>
          Figyelendő event
        </span>
        <span>
          <strong>{nextEvent ? formatEventDate(nextEvent.starts_at) : "-"}</strong>
          Következő event
        </span>
      </div>

      <div className="flow-forecast-list">
        {rows.map((row) => (
          <article
            className={`flow-forecast-row ${row.preparation_level}`}
            key={row.event_id}
          >
            <div className="flow-forecast-heading">
              <span>
                <strong>{row.title}</strong>
                <small>
                  {formatEventDate(row.starts_at)} · {row.performer_name ?? "fellépő nélkül"}
                </small>
              </span>
              <span>
                <strong>{formatReadinessLevel(row.preparation_level)}</strong>
                <small>{row.focus_area}</small>
              </span>
            </div>

            <div className="flow-forecast-metrics">
              <span>
                <strong>{row.expected_attendance ?? "-"}</strong>
                Várt létszám
              </span>
              <span>
                <strong>{row.forecast_hours}</strong>
                Forecast óra
              </span>
              <span>
                <strong>{formatWeatherConditionBand(row.dominant_condition_band)}</strong>
                Időjárás
              </span>
              <span>
                <strong>
                  {row.average_temperature_c ? `${formatNumber(row.average_temperature_c)} °C` : "-"}
                </strong>
                Átlaghő
              </span>
              <span>
                <strong>{formatNumber(row.precipitation_mm)} mm</strong>
                Csapadék
              </span>
              <span>
                <strong>
                  {row.average_wind_speed_kmh ? `${formatNumber(row.average_wind_speed_kmh)} km/h` : "-"}
                </strong>
                Szél
              </span>
            </div>
            <p>{row.recommendation}</p>
          </article>
        ))}
      </div>

      {rows.length === 0 ? (
        <p className="empty-message">
          Nincs közelgő, forecast horizonton belüli Flow event. A naptárba felvett eventek
          automatikusan megjelennek, amint van hozzájuk forecast cache.
        </p>
      ) : null}
    </Card>
  );
}

function TopProductsCard({
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
  const ticketRows = sortedRows.filter(
    (row) => isTicketLikeLabel(row.label) || isTicketLikeLabel(row.category_name),
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
      </div>

      {isLoading ? <p className="info-message">Terméklista betöltése...</p> : null}

      {ticketRows.length > 0 && (scope === "overall" || scope === "flow") ? (
        <div className="top-products-ticket-note">
          <strong>Jegy jellegű tétel a rangsorban</strong>
          <span>
            A jegy vagy VIP belépő bevételi adatként fontos, de fogyasztási termékként
            torzíthatja a top termék képet. Külön ticket/event bontás szükséges lesz.
          </span>
        </div>
      ) : null}

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
                  {isTicketLikeLabel(row.label) || isTicketLikeLabel(row.category_name) ? (
                    <span className="top-product-ticket-badge">Jegy</span>
                  ) : null}
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
                <span>
                  <strong>{row.category_name ?? "-"}</strong>
                  Kategória
                </span>
                <span>
                  <strong>{row.transaction_count}</strong>
                  Érintett nyugtasor
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

function BasketAnalysisCard({
  pairs,
  selectedPair,
  setSelectedPair,
  receipts,
  isLoading,
}: {
  pairs: DashboardBasketPairRow[];
  selectedPair: DashboardBasketPairRow | null;
  setSelectedPair: (value: DashboardBasketPairRow | null) => void;
  receipts: DashboardBasketReceipt[];
  isLoading: boolean;
}) {
  const maxRevenue = Math.max(
    ...pairs.map((row) => toNumber(row.total_gross_amount)),
    1,
  );
  const selectedPairKey = selectedPair
    ? `${selectedPair.product_a}-${selectedPair.product_b}`
    : "";

  return (
    <Card
      hoverable
      className="basket-analysis-card"
      eyebrow="Kosárelemzés"
      title="Együtt vásárolt termékek"
      subtitle="Gyakori termékpárok nyugták alapján"
      count={pairs.length}
    >
      <div className="basket-analysis-layout">
        <div className="basket-pair-list">
          {pairs.map((row, index) => {
            const pairKey = `${row.product_a}-${row.product_b}`;
            const revenue = toNumber(row.total_gross_amount);
            const width = `${Math.max(4, (revenue / maxRevenue) * 100)}%`;
            const isSelected = selectedPairKey === pairKey;

            return (
              <Fragment key={pairKey}>
              <button
                type="button"
                className={
                  isSelected
                    ? "basket-pair-row basket-pair-row-active"
                    : "basket-pair-row"
                }
                onClick={() => setSelectedPair(isSelected ? null : row)}
              >
                <span className="basket-pair-rank">{index + 1}</span>
                <span className="basket-pair-content">
                  <span className="basket-pair-title">
                    <strong>{row.product_a}</strong>
                    <span>+</span>
                    <strong>{row.product_b}</strong>
                  </span>
                  <span className="basket-pair-bar">
                    <span style={{ width }} />
                  </span>
                  <span className="basket-pair-meta">
                    <span>{row.basket_count} közös kosár</span>
                    <span>{formatMoney(row.total_gross_amount)}</span>
                  </span>
                </span>
              </button>
              {isSelected ? (
                <div className="basket-inline-detail">
                  <div className="basket-inline-summary">
                    <span>
                      <strong>{row.basket_count}</strong>
                      Közös kosár
                    </span>
                    <span>
                      <strong>{formatMoney(row.total_gross_amount)}</strong>
                      Bruttó összeg
                    </span>
                    <span>
                      <strong>{receipts.length}</strong>
                      Kapcsolódó nyugta
                    </span>
                  </div>

                  {isLoading ? (
                    <p className="info-message">Nyugták betöltése...</p>
                  ) : null}

                  <div className="basket-inline-receipts">
                    {receipts.slice(0, 4).map((receipt) => (
                      <article className="basket-inline-receipt" key={receipt.receipt_no}>
                        <span>
                          <strong>{receipt.receipt_no}</strong>
                          {receipt.date ?? "-"}
                        </span>
                        <span>{formatMoney(receipt.gross_amount)}</span>
                        <small>{formatNumber(receipt.quantity)} tétel</small>
                      </article>
                    ))}
                  </div>

                  {receipts.length > 4 ? (
                    <p className="section-note">
                      További {receipts.length - 4} nyugta tartozik ehhez a termékpárhoz.
                    </p>
                  ) : null}

                  {receipts.length === 0 && !isLoading ? (
                    <p className="empty-message">
                      Ehhez a termékpárhoz nincs részletezhető nyugta.
                    </p>
                  ) : null}
                </div>
              ) : null}
              </Fragment>
            );
          })}
          {pairs.length === 0 ? (
            <p className="info-message">Nincs kosárpár ebben az időszakban.</p>
          ) : null}
        </div>

        <aside className="basket-detail-card">
          {selectedPair ? (
            <>
              <div className="section-heading-row">
                <div>
                  <h3>
                    {selectedPair.product_a} + {selectedPair.product_b}
                  </h3>
                  <p className="section-note">Kapcsolódó nyugták és tételek</p>
                </div>
                <span className="status-pill">{receipts.length} nyugta</span>
              </div>

              <div className="basket-detail-metrics">
                <span>
                  <strong>{selectedPair.basket_count}</strong>
                  Közös kosár
                </span>
                <span>
                  <strong>{formatMoney(selectedPair.total_gross_amount)}</strong>
                  Bruttó összeg
                </span>
              </div>

              {isLoading ? (
                <p className="info-message">Nyugták betöltése...</p>
              ) : null}

              <div className="basket-receipt-list">
                {receipts.map((receipt) => (
                  <article className="basket-receipt-card" key={receipt.receipt_no}>
                    <div className="activity-meta">
                      <strong>{receipt.receipt_no}</strong>
                      <span>{receipt.date ?? "-"}</span>
                    </div>
                    <p>
                      {formatMoney(receipt.gross_amount)} ·{" "}
                      {formatNumber(receipt.quantity)} tétel
                    </p>
                    <div className="table-wrap basket-receipt-table">
                      <table className="data-table">
                        <thead>
                          <tr>
                            <th>Termék</th>
                            <th>Kategória</th>
                            <th>Mennyiség</th>
                            <th>Bruttó összeg</th>
                            <th>Fizetés</th>
                          </tr>
                        </thead>
                        <tbody>
                          {receipt.lines.map((line) => (
                            <tr key={line.row_id}>
                              <td>{line.product_name}</td>
                              <td>{line.category_name}</td>
                              <td>{formatNumber(line.quantity)}</td>
                              <td>{formatMoney(line.gross_amount)}</td>
                              <td>{line.payment_method ? formatPaymentMethod(line.payment_method) : "-"}</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </article>
                ))}
              </div>

              {receipts.length === 0 && !isLoading ? (
                <p className="empty-message">Ehhez a termékpárhoz nincs részletezhető nyugta.</p>
              ) : null}
            </>
          ) : (
            <div className="basket-detail-empty">
              <strong>Válassz egy termékpárt</strong>
              <span>A kapcsolódó nyugták itt, külön részletező panelben jelennek meg.</span>
            </div>
          )}
        </aside>
      </div>
    </Card>
  );
}

function ExpenseBreakdownCard({
  rows,
  activeType,
  openExpenseType,
}: {
  rows: DashboardExpenseRow[];
  activeType: string | null;
  openExpenseType: (type: string) => void;
}) {
  const total = rows.reduce((sum, row) => sum + toNumber(row.gross_amount), 0);
  const totalNet = rows.reduce((sum, row) => sum + toNumber(row.net_amount ?? "0"), 0);
  const totalVat = rows.reduce((sum, row) => sum + toNumber(row.vat_amount ?? "0"), 0);
  const hasTaxBreakdown = rows.some((row) => row.net_amount !== null || row.vat_amount !== null);
  const maxAmount = Math.max(...rows.map((row) => toNumber(row.gross_amount)), 1);

  return (
    <Card
      tone="highlight"
      hoverable
      eyebrow="Költségkontroll"
      title="Kiadások bontása"
      subtitle="Rögzített kiadások tranzakciótípus szerint"
      count={rows.length}
    >
      <div className="expense-summary-strip">
        <span>
          <strong>{formatMoney(total)}</strong>
          <small>Bruttó tényleges</small>
          Összes kiadás
        </span>
        {hasTaxBreakdown ? (
          <>
            <span>
              <strong>{formatMoney(totalNet)}</strong>
              Nettó
            </span>
            <span>
              <strong>{formatMoney(totalVat)}</strong>
              ÁFA
            </span>
          </>
        ) : null}
        <span>
          <strong>{rows.reduce((sum, row) => sum + row.transaction_count, 0)}</strong>
          Tranzakció
        </span>
      </div>

      <div className="expense-breakdown-list">
        {rows.map((row) => {
          const amount = toNumber(row.gross_amount);
          const width = `${Math.max(4, (amount / maxAmount) * 100)}%`;
          const isActive = activeType === row.label;

          return (
            <button
              key={row.label}
              type="button"
              className={
                isActive
                  ? "expense-breakdown-row expense-breakdown-row-active"
                  : "expense-breakdown-row"
              }
              onClick={() => openExpenseType(row.label)}
            >
              <span className="expense-breakdown-top">
                <strong>{formatTransactionType(row.label)}</strong>
                <strong>{formatMoney(row.gross_amount)}</strong>
              </span>
              <span className="expense-breakdown-bar">
                <span style={{ width }} />
              </span>
              <span className="expense-breakdown-meta">
                <span>{row.transaction_count} tranzakció</span>
                <span>
                  {formatAmountBasis(row.amount_basis)} ·{" "}
                  {formatTaxBreakdownSource(row.tax_breakdown_source)}
                </span>
              </span>
              {row.net_amount !== null || row.vat_amount !== null ? (
                <span className="expense-breakdown-meta">
                  <span>Nettó: {formatMoney(row.net_amount ?? 0)}</span>
                  <span>ÁFA: {formatMoney(row.vat_amount ?? 0)}</span>
                </span>
              ) : null}
            </button>
          );
        })}
        {rows.length === 0 ? (
          <p className="empty-message">Nincs rögzített kiadás ebben az időszakban.</p>
        ) : null}
      </div>
    </Card>
  );
}

function ExpenseDrilldownCard({
  type,
  rows,
  selectedExpense,
  setSelectedExpense,
  source,
  isLoading,
  close,
}: {
  type: string;
  rows: DashboardExpenseDetailRow[];
  selectedExpense: DashboardExpenseDetailRow | null;
  setSelectedExpense: (value: DashboardExpenseDetailRow) => void;
  source: DashboardExpenseSource | null;
  isLoading: boolean;
  close: () => void;
}) {
  return (
    <Card
      hoverable
      className="expense-detail-card"
      eyebrow="Költségrészletek"
      title={formatTransactionType(type)}
      subtitle="Kiadási tranzakciók és forrásadatok"
      actions={
        <Button variant="secondary" onClick={close}>
          Bezárás
        </Button>
      }
    >
      {isLoading ? <p className="info-message">Részletek betöltése...</p> : null}

      <div className="expense-detail-layout">
        <div className="expense-transaction-list">
          {rows.map((row) => {
            const isSelected =
              selectedExpense?.transaction_id === row.transaction_id;

            return (
              <button
                key={row.transaction_id}
                type="button"
                className={
                  isSelected
                    ? "expense-transaction-row expense-transaction-row-active"
                    : "expense-transaction-row"
                }
                onClick={() => setSelectedExpense(row)}
              >
                <span>
                  <strong>{formatMoney(row.gross_amount)}</strong>
                  <small>{row.occurred_at}</small>
                </span>
                <span>{row.description || formatTransactionType(row.transaction_type)}</span>
                <small>
                  {formatSourceType(row.source_type)} ·{" "}
                  {formatTaxBreakdownSource(row.tax_breakdown_source)}
                </small>
              </button>
            );
          })}
          {rows.length === 0 && !isLoading ? (
            <p className="empty-message">Nincs részletezhető tranzakció.</p>
          ) : null}
        </div>

        <aside className="expense-source-card">
          {selectedExpense && source ? (
            <>
              <div className="section-heading-row">
                <div>
                  <h3>{source.invoice_number ?? formatSourceType(source.source_type)}</h3>
                  <p className="section-note">
                    {source.supplier_name ?? "Forrásrekord"} ·{" "}
                    {source.invoice_date ?? source.occurred_at}
                  </p>
                </div>
                <span className="status-pill">{source.lines.length} sor</span>
              </div>

              <div className="expense-source-metrics">
                <article className="detail-item">
                  <span>Bruttó összeg</span>
                  <strong>
                    {source.gross_total
                      ? formatMoney(source.gross_total)
                      : formatMoney(source.gross_amount)}
                  </strong>
                </article>
                <article className="detail-item">
                  <span>Nettó</span>
                  <strong>{source.net_total ? formatMoney(source.net_total) : "-"}</strong>
                </article>
                <article className="detail-item">
                  <span>ÁFA</span>
                  <strong>{source.vat_total ? formatMoney(source.vat_total) : "-"}</strong>
                </article>
                <article className="detail-item">
                  <span>Forrás</span>
                  <strong>{formatTaxBreakdownSource(source.tax_breakdown_source)}</strong>
                </article>
              </div>

              {source.lines.length > 0 ? (
                <div className="table-wrap expense-source-table">
                  <table className="data-table">
                    <thead>
                      <tr>
                        <th>Leírás</th>
                        <th>Mennyiség</th>
                        <th>Nettó egységár</th>
                        <th>Nettó sorösszeg</th>
                        <th>Készletelem</th>
                      </tr>
                    </thead>
                    <tbody>
                      {source.lines.map((line) => (
                        <tr key={line.line_id}>
                          <td>{line.description}</td>
                          <td>{formatNumber(line.quantity)}</td>
                          <td>{formatMoney(line.unit_net_amount)}</td>
                          <td>{formatMoney(line.line_net_amount)}</td>
                          <td>{line.inventory_item_id ?? "-"}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              ) : (
                <p className="info-message">
                  Ehhez a tranzakcióhoz nincs strukturált forrássor.
                </p>
              )}
            </>
          ) : (
            <div className="expense-source-empty">
              <strong>Válassz egy tranzakciót</strong>
              <span>A forrásrekord és a számlasorok itt jelennek meg.</span>
            </div>
          )}
        </aside>
      </div>
    </Card>
  );
}

function PaymentMethodCard({ rows }: { rows: DashboardBreakdownRow[] }) {
  const total = rows.reduce((sum, row) => sum + toNumber(row.revenue), 0);

  return (
    <Card
      hoverable
      tone="secondary"
      eyebrow="Fizetési módok"
      title="Bevétel fizetési mód szerint"
      subtitle="Kasszából/importból rögzített nyugtasorok alapján"
      count={rows.length}
    >
      <div className="payment-mix-layout">
        <div className="dashboard-donut-wrap">
          <div
            className="dashboard-donut dashboard-donut-compact"
            style={{ background: buildDonutGradient(rows, "revenue") }}
            aria-label="Fizetési mód megoszlás diagram"
          >
            <div className="dashboard-donut-center">
              <span>Összes bevétel</span>
              <strong>{formatMoney(total)}</strong>
            </div>
          </div>
        </div>

        <div className="payment-mix-list">
          {rows.map((row, index) => {
            const revenue = toNumber(row.revenue);
            const percentage = total > 0 ? (revenue / total) * 100 : 0;

            return (
              <article className="payment-mix-row" key={row.label}>
                <span
                  className="dashboard-mix-swatch"
                  style={{ background: mixPalette[index % mixPalette.length] }}
                />
                <span>
                  <strong>{formatPaymentMethod(row.label)}</strong>
                  <small>{row.transaction_count} nyugtasor</small>
                </span>
                <span className="payment-mix-value">
                  {formatMoney(row.revenue)}
                  <small>{percentage.toFixed(1)}%</small>
                </span>
              </article>
            );
          })}
        </div>
      </div>

      {rows.length === 0 ? (
        <p className="empty-message">Nincs fizetési mód adat ebben az időszakban.</p>
      ) : null}
    </Card>
  );
}

function BasketValueDistributionCard({ rows }: { rows: DashboardBreakdownRow[] }) {
  const totalBaskets = rows.reduce((sum, row) => sum + row.transaction_count, 0);
  const totalRevenue = rows.reduce((sum, row) => sum + toNumber(row.revenue), 0);
  const maxCount = Math.max(...rows.map((row) => row.transaction_count), 1);

  return (
    <Card
      hoverable
      eyebrow="Kosárérték eloszlás"
      title="Vásárlási sávok"
      subtitle="Nyugták teljes bruttó értéke alapján"
      count={totalBaskets}
    >
      <div className="basket-value-summary">
        <span>
          <strong>{totalBaskets}</strong>
          Kosár
        </span>
        <span>
          <strong>{formatMoney(totalRevenue)}</strong>
          Összes bruttó érték
        </span>
      </div>

      <div className="basket-value-bars">
        {rows.map((row, index) => {
          const width = `${Math.max(row.transaction_count > 0 ? 5 : 0, (row.transaction_count / maxCount) * 100)}%`;
          const percentage =
            totalBaskets > 0 ? (row.transaction_count / totalBaskets) * 100 : 0;

          return (
            <article className="basket-value-row" key={row.label}>
              <div className="basket-value-row-top">
                <strong>{formatBasketValueBand(row.label)}</strong>
                <span>
                  {row.transaction_count} kosár · {percentage.toFixed(1)}%
                </span>
              </div>
              <div className="basket-value-track">
                <span
                  style={{
                    width,
                    background: `linear-gradient(135deg, ${
                      mixPalette[index % mixPalette.length]
                    }, ${mixPalette[(index + 2) % mixPalette.length]})`,
                  }}
                />
              </div>
              <p>{formatMoney(row.revenue)} bruttó érték ebben a sávban</p>
            </article>
          );
        })}
      </div>

      {totalBaskets === 0 ? (
        <p className="empty-message">Nincs kosárérték adat ebben az időszakban.</p>
      ) : null}
    </Card>
  );
}

function TrafficHeatmapCard({
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

function CategoryTrendCard({ rows }: { rows: DashboardCategoryTrendRow[] }) {
  const totalChange = rows.reduce(
    (sum, row) => sum + toNumber(row.revenue_change),
    0,
  );
  const growingCount = rows.filter((row) => toNumber(row.revenue_change) > 0).length;
  const decliningCount = rows.filter((row) => toNumber(row.revenue_change) < 0).length;
  const maxAbsChange = Math.max(
    ...rows.map((row) => Math.abs(toNumber(row.revenue_change))),
    1,
  );

  return (
    <Card
      hoverable
      tone="secondary"
      eyebrow="Kategória trend"
      title="Mi nő, mi esik?"
      subtitle="Aktuális időszak összevetése az előző azonos időszakkal"
      count={rows.length}
    >
      <div className="category-trend-summary">
        <span>
          <strong>{formatMoney(totalChange)}</strong>
          Nettó változás
        </span>
        <span>
          <strong>{growingCount}</strong>
          Növekvő kategória
        </span>
        <span>
          <strong>{decliningCount}</strong>
          Csökkenő kategória
        </span>
      </div>

      <div className="category-trend-list">
        {rows.map((row, index) => {
          const change = toNumber(row.revenue_change);
          const percent = toNumber(row.revenue_change_percent);
          const isGrowing = change > 0;
          const isFlat = change === 0;
          const width = `${Math.max(6, (Math.abs(change) / maxAbsChange) * 100)}%`;
          const trendLabel = isFlat ? "Stabil" : isGrowing ? "Növekedés" : "Csökkenés";

          return (
            <article className="category-trend-row" key={row.label}>
              <div className="category-trend-heading">
                <span
                  className={
                    isFlat
                      ? "category-trend-rank neutral"
                      : isGrowing
                        ? "category-trend-rank positive"
                        : "category-trend-rank negative"
                  }
                >
                  {index + 1}
                </span>
                <span>
                  <strong>{row.label}</strong>
                  <small>
                    {formatMoney(row.current_revenue)} most · {formatMoney(
                      row.previous_revenue,
                    )} előző időszak
                  </small>
                </span>
                <span
                  className={
                    isFlat
                      ? "category-trend-change neutral"
                      : isGrowing
                        ? "category-trend-change positive"
                        : "category-trend-change negative"
                  }
                >
                  {isGrowing ? "+" : ""}
                  {formatMoney(change)}
                  <small>
                    {isGrowing ? "+" : ""}
                    {formatNumber(percent)}%
                  </small>
                </span>
              </div>

              <div className="category-trend-track">
                <span
                  className={
                    isFlat
                      ? "neutral"
                      : isGrowing
                        ? "positive"
                        : "negative"
                  }
                  style={{ width }}
                />
              </div>

              <div className="category-trend-meta">
                <span>{trendLabel}</span>
                <span>
                  {row.current_transaction_count} most ·{" "}
                  {row.previous_transaction_count} előző
                </span>
              </div>
            </article>
          );
        })}
      </div>

      {rows.length === 0 ? (
        <p className="empty-message">Nincs kategória trend adat ebben az időszakban.</p>
      ) : null}
    </Card>
  );
}

function WeatherCategoryInsightCard({
  rows,
}: {
  rows: DashboardWeatherCategoryInsightRow[];
}) {
  const totalRevenue = rows.reduce((sum, row) => sum + toNumber(row.revenue), 0);
  const totalTransactions = rows.reduce(
    (sum, row) => sum + row.transaction_count,
    0,
  );
  const maxRevenue = Math.max(...rows.map((row) => toNumber(row.revenue)), 1);

  return (
    <Card
      hoverable
      tone="secondary"
      eyebrow="Időjárás és kategória"
      title="Milyen időben mit vesznek?"
      subtitle="Közös szolnoki órás időjárásadat és kasszasor kapcsolat"
      count={rows.length}
    >
      <div className="weather-category-summary">
        <span>
          <strong>{formatMoney(totalRevenue)}</strong>
          Összekapcsolt bevétel
        </span>
        <span>
          <strong>{totalTransactions}</strong>
          Nyugtasor
        </span>
      </div>

      <div className="weather-category-list">
        {rows.map((row) => {
          const revenue = toNumber(row.revenue);
          const width = `${Math.max(8, (revenue / maxRevenue) * 100)}%`;

          return (
            <article
              className="weather-category-row"
              key={`${row.category_name}-${row.weather_condition}`}
            >
              <div className="weather-category-heading">
                <span>
                  <strong>{row.category_name}</strong>
                  <small>{formatWeatherCondition(row.weather_condition)}</small>
                </span>
                <span>
                  <strong>{formatMoney(row.revenue)}</strong>
                  <small>
                    {formatNumber(row.quantity)} mennyiség ·{" "}
                    {row.transaction_count} sor
                  </small>
                </span>
              </div>
              <div className="weather-category-track">
                <span style={{ width }} />
              </div>
              <div className="weather-category-meta">
                <span>{formatSourceLayer(row.source_layer)}</span>
                <span>
                  {row.average_temperature_c
                    ? `${formatNumber(row.average_temperature_c)} °C átlag`
                    : "Nincs hőmérséklet"}
                </span>
              </div>
            </article>
          );
        })}
      </div>

      {rows.length === 0 ? (
        <p className="empty-message">
          Nincs még összekapcsolt időjárásadat ehhez az időszakhoz.
        </p>
      ) : null}
    </Card>
  );
}

function TemperatureBandInsightCard({
  rows,
}: {
  rows: DashboardTemperatureBandInsightRow[];
}) {
  const totalRevenue = rows.reduce((sum, row) => sum + toNumber(row.revenue), 0);
  const maxRevenue = Math.max(...rows.map((row) => toNumber(row.revenue)), 1);

  return (
    <Card
      hoverable
      tone="secondary"
      eyebrow="Hőmérséklet-hatás"
      title="Mit jelent a meleg a pultnál?"
      subtitle="Eladás hőmérsékleti sávok szerint, órás időjárás-cache alapján"
      count={rows.length}
    >
      <div className="temperature-band-summary">
        <span>
          <strong>{formatMoney(totalRevenue)}</strong>
          Összekapcsolt bevétel
        </span>
        <span>
          <strong>{rows.length}</strong>
          Aktív sáv
        </span>
      </div>

      <div className="temperature-band-list">
        {rows.map((row) => {
          const revenue = toNumber(row.revenue);
          const width = `${Math.max(8, (revenue / maxRevenue) * 100)}%`;
          const share = totalRevenue > 0 ? (revenue / totalRevenue) * 100 : 0;

          return (
            <article
              className={`temperature-band-row ${row.temperature_band}`}
              key={row.temperature_band}
            >
              <div className="temperature-band-heading">
                <span>
                  <strong>{formatTemperatureBand(row.temperature_band)}</strong>
                  <small>
                    {row.average_temperature_c
                      ? `${formatNumber(row.average_temperature_c)} °C átlag`
                      : "Nincs hőmérséklet"}
                  </small>
                </span>
                <span>
                  <strong>{formatMoney(row.revenue)}</strong>
                  <small>{formatNumber(share)}% arány</small>
                </span>
              </div>
              <div className="temperature-band-track">
                <span style={{ width }} />
              </div>
              <div className="temperature-band-metrics">
                <span>
                  <strong>{formatNumber(row.quantity)}</strong>
                  Mennyiség
                </span>
                <span>
                  <strong>{row.transaction_count}</strong>
                  Nyugtasor
                </span>
                <span>
                  <strong>{formatMoney(row.average_basket_value)}</strong>
                  Átlagkosár
                </span>
              </div>
              <div className="temperature-band-meta">
                <span>Vezető kategória: {row.top_category_name}</span>
                <span>{formatMoney(row.top_category_revenue)}</span>
              </div>
            </article>
          );
        })}
      </div>

      {rows.length === 0 ? (
        <p className="empty-message">
          Nincs még hőmérséklettel összekapcsolt eladási adat ehhez az időszakhoz.
        </p>
      ) : null}
    </Card>
  );
}

function WeatherConditionInsightCard({
  rows,
}: {
  rows: DashboardWeatherConditionInsightRow[];
}) {
  const totalRevenue = rows.reduce((sum, row) => sum + toNumber(row.revenue), 0);
  const totalPrecipitation = rows.reduce(
    (sum, row) => sum + toNumber(row.precipitation_mm),
    0,
  );
  const maxRevenue = Math.max(...rows.map((row) => toNumber(row.revenue)), 1);

  return (
    <Card
      hoverable
      tone="secondary"
      eyebrow="Csapadék és felhőzet"
      title="Milyen ég alatt vásárolnak?"
      subtitle="Napsütés, felhőzet és csapadék kapcsolata a kasszaadatokkal"
      count={rows.length}
    >
      <div className="weather-condition-summary">
        <span>
          <strong>{formatMoney(totalRevenue)}</strong>
          Összekapcsolt bevétel
        </span>
        <span>
          <strong>{formatNumber(totalPrecipitation)} mm</strong>
          Csapadékösszeg
        </span>
      </div>

      <div className="weather-condition-list">
        {rows.map((row) => {
          const revenue = toNumber(row.revenue);
          const width = `${Math.max(8, (revenue / maxRevenue) * 100)}%`;
          const share = totalRevenue > 0 ? (revenue / totalRevenue) * 100 : 0;

          return (
            <article
              className={`weather-condition-row ${row.condition_band}`}
              key={row.condition_band}
            >
              <div className="weather-condition-heading">
                <span>
                  <strong>{formatWeatherConditionBand(row.condition_band)}</strong>
                  <small>
                    {row.average_cloud_cover_percent
                      ? `${formatNumber(row.average_cloud_cover_percent)}% felhőzet`
                      : "Nincs felhőzetadat"}
                  </small>
                </span>
                <span>
                  <strong>{formatMoney(row.revenue)}</strong>
                  <small>{formatNumber(share)}% arány</small>
                </span>
              </div>
              <div className="weather-condition-track">
                <span style={{ width }} />
              </div>
              <div className="weather-condition-metrics">
                <span>
                  <strong>{formatNumber(row.quantity)}</strong>
                  Mennyiség
                </span>
                <span>
                  <strong>{row.transaction_count}</strong>
                  Nyugtasor
                </span>
                <span>
                  <strong>{formatMoney(row.average_basket_value)}</strong>
                  Átlagkosár
                </span>
              </div>
              <div className="weather-condition-meta">
                <span>Vezető kategória: {row.top_category_name}</span>
                <span>{formatMoney(row.top_category_revenue)}</span>
              </div>
            </article>
          );
        })}
      </div>

      {rows.length === 0 ? (
        <p className="empty-message">
          Nincs még csapadék/felhőzet adattal összekapcsolt eladási adat ehhez az időszakhoz.
        </p>
      ) : null}
    </Card>
  );
}

function ForecastImpactCard({ rows }: { rows: DashboardForecastImpactRow[] }) {
  const totalExpectedRevenue = rows.reduce(
    (sum, row) => sum + toNumber(row.expected_revenue),
    0,
  );
  const maxRevenue = Math.max(...rows.map((row) => toNumber(row.expected_revenue)), 1);
  const latestUpdate = rows
    .map((row) => row.forecast_updated_at)
    .filter((value): value is string => Boolean(value))
    .sort()
    .at(-1);

  return (
    <Card
      hoverable
      tone="rainbow"
      eyebrow="Előrejelzés"
      title="Várható időjárási hatás"
      subtitle="A forecast cache és a historikus időjárás-forgalom kapcsolat első becslése"
      count={latestUpdate ? `Frissítve: ${formatTrendDate(latestUpdate, "hour", true)}` : rows.length}
    >
      <div className="forecast-impact-summary">
        <span>
          <strong>{formatMoney(totalExpectedRevenue)}</strong>
          Várható összforgalom
        </span>
        <span>
          <strong>{rows.length}</strong>
          Előrejelzett nap
        </span>
      </div>

      <div className="forecast-impact-list">
        {rows.map((row) => {
          const revenue = toNumber(row.expected_revenue);
          const width = `${Math.max(8, (revenue / maxRevenue) * 100)}%`;
          const delta =
            toNumber(row.historical_average_revenue) > 0
              ? ((revenue - toNumber(row.historical_average_revenue)) /
                  toNumber(row.historical_average_revenue)) *
                100
              : 0;

          return (
            <article className={`forecast-impact-row ${row.confidence}`} key={row.forecast_date}>
              <div className="forecast-impact-heading">
                <span>
                  <strong>{formatForecastDate(row.forecast_date)}</strong>
                  <small>
                    {formatTemperatureBand(row.dominant_temperature_band)} ·{" "}
                    {formatWeatherConditionBand(row.dominant_condition_band)}
                  </small>
                </span>
                <span>
                  <strong>{formatMoney(row.expected_revenue)}</strong>
                  <small>{formatForecastConfidence(row.confidence)}</small>
                </span>
              </div>
              <div className="forecast-impact-track">
                <span style={{ width }} />
              </div>
              <div className="forecast-impact-metrics">
                <span>
                  <strong>
                    {row.average_temperature_c
                      ? `${formatNumber(row.average_temperature_c)} °C`
                      : "-"}
                  </strong>
                  Átlaghő
                </span>
                <span>
                  <strong>{formatNumber(row.precipitation_mm)} mm</strong>
                  Csapadék
                </span>
                <span>
                  <strong>{delta >= 0 ? "+" : ""}{formatNumber(delta)}%</strong>
                  Normálhoz képest
                </span>
              </div>
              <p>{row.recommendation}</p>
            </article>
          );
        })}
      </div>

      {rows.length === 0 ? (
        <p className="empty-message">
          Nincs még forecast cache vagy nincs elég historikus, időjárással összekapcsolt
          forgalmi adat a becsléshez.
        </p>
      ) : null}
    </Card>
  );
}

type WeatherImpactView = "temperature" | "condition" | "forecast";
type DemandForecastView = "category" | "product" | "peak";

function WeatherImpactDashboardCard({
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

function GourmandDailyForecastCard({
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

function GourmandDemandForecastCard({
  categoryRows,
  productRows,
  peakRows,
}: {
  categoryRows: DashboardForecastCategoryDemandRow[];
  productRows: DashboardForecastProductDemandRow[];
  peakRows: DashboardForecastPeakTimeRow[];
}) {
  const [activeView, setActiveView] = useState<DemandForecastView>("category");
  const [selectedKey, setSelectedKey] = useState<string | null>(null);
  const strongestCategory = [...categoryRows].sort(
    (left, right) => toNumber(right.expected_revenue) - toNumber(left.expected_revenue),
  )[0];
  const strongestProduct = [...productRows].sort(
    (left, right) => toNumber(right.expected_revenue) - toNumber(left.expected_revenue),
  )[0];
  const strongestPeak = [...peakRows].sort(
    (left, right) => toNumber(right.expected_revenue) - toNumber(left.expected_revenue),
  )[0];
  const rows: DemandForecastDisplayRow[] =
    activeView === "category"
      ? categoryRows.map((row) => ({
          key: `${row.forecast_date}-${row.category_name}`,
          label: row.category_name,
          value: toNumber(row.expected_revenue),
          quantity: toNumber(row.expected_quantity),
          secondary: formatForecastDate(row.forecast_date),
          meta: `${formatTemperatureBand(row.dominant_temperature_band)} · ${formatWeatherConditionBand(row.dominant_condition_band)}`,
          signal: row.demand_signal,
          confidence: row.confidence,
          recommendation: row.recommendation,
        }))
      : activeView === "product"
        ? productRows.map((row) => ({
            key: `${row.forecast_date}-${row.product_name}`,
            label: row.product_name,
            value: toNumber(row.expected_revenue),
            quantity: toNumber(row.expected_quantity),
            secondary: `${formatForecastDate(row.forecast_date)} · ${row.category_name}`,
            meta: `${formatTemperatureBand(row.dominant_temperature_band)} · ${formatWeatherConditionBand(row.dominant_condition_band)}`,
            signal: row.demand_signal,
            confidence: row.confidence,
            recommendation: row.recommendation,
          }))
        : peakRows.map((row) => ({
            key: `${row.forecast_date}-${row.time_window}`,
            label: row.time_window,
            value: toNumber(row.expected_revenue),
            quantity: toNumber(row.expected_quantity),
            secondary: formatForecastDate(row.forecast_date),
            meta: `${row.expected_transaction_count} várható nyugtasor · ${formatTemperatureBand(row.dominant_temperature_band)}`,
            signal: row.demand_signal,
            confidence: row.confidence,
            recommendation: row.recommendation,
          }));
  const sortedRows = [...rows].sort((left, right) => right.value - left.value).slice(0, 8);
  const maxValue = Math.max(...sortedRows.map((row) => row.value), 1);
  const selectedRow = sortedRows.find((row) => row.key === selectedKey) ?? null;

  return (
    <Card
      hoverable
      tone="secondary"
      className="demand-forecast-card"
      eyebrow="Gourmand előrejelzés"
      title="Várható kereslet"
      subtitle="Kategóriák, húzótermékek és csúcsidősávok egy helyen"
      count={
        strongestCategory
          ? `${strongestCategory.category_name} · ${formatMoney(strongestCategory.expected_revenue)}`
          : rows.length
      }
      actions={
        <div className="demand-forecast-tabs">
          {[
            { value: "category", label: "Kategória" },
            { value: "product", label: "Termék" },
            { value: "peak", label: "Csúcsidő" },
          ].map((option) => (
            <button
              key={option.value}
              type="button"
              className={
                activeView === option.value
                  ? "filter-chip filter-chip-active"
                  : "filter-chip"
              }
              onClick={() => {
                setActiveView(option.value as DemandForecastView);
                setSelectedKey(null);
              }}
            >
              {option.label}
            </button>
          ))}
        </div>
      }
    >
      <div className="demand-forecast-summary">
        <span>
          <strong>{strongestCategory?.category_name ?? "-"}</strong>
          Várható vezető kategória
        </span>
        <span>
          <strong>{strongestProduct?.product_name ?? "-"}</strong>
          Várható húzótermék
        </span>
        <span>
          <strong>
            {strongestPeak
              ? `${formatForecastDate(strongestPeak.forecast_date)} · ${strongestPeak.time_window}`
              : "-"}
          </strong>
          Várható csúcsidő
        </span>
      </div>

      <div className="demand-forecast-chart">
        {sortedRows.map((row, index) => {
          const width = `${Math.max(6, (row.value / maxValue) * 100)}%`;
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
              <span className="demand-forecast-rank">{index + 1}</span>
              <span className="demand-forecast-content">
                <span className="demand-forecast-heading">
                  <strong>{row.label}</strong>
                  <small>{row.secondary}</small>
                </span>
                <span className="demand-forecast-track">
                  <span style={{ width }} />
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
              Becsült forgalom
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

function ForecastCategoryDemandCard({
  rows,
}: {
  rows: DashboardForecastCategoryDemandRow[];
}) {
  const groupedRows = rows.reduce<Record<string, DashboardForecastCategoryDemandRow[]>>(
    (acc, row) => {
      acc[row.forecast_date] = [...(acc[row.forecast_date] ?? []), row];
      return acc;
    },
    {},
  );
  const dates = Object.keys(groupedRows).sort();
  const strongestRow = [...rows].sort(
    (left, right) => toNumber(right.expected_revenue) - toNumber(left.expected_revenue),
  )[0];

  return (
    <Card
      hoverable
      tone="secondary"
      eyebrow="Gourmand előrejelzés"
      title="Kategória keresleti jelzés"
      subtitle="Forecast időjárás és historikus kategóriaforgalom alapján"
      count={strongestRow ? strongestRow.category_name : rows.length}
    >
      <div className="forecast-demand-summary">
        <span>
          <strong>{strongestRow?.category_name ?? "-"}</strong>
          Legerősebb várható kategória
        </span>
        <span>
          <strong>{strongestRow ? formatMoney(strongestRow.expected_revenue) : "-"}</strong>
          Becsült kategóriaforgalom
        </span>
      </div>

      <div className="forecast-demand-list">
        {dates.map((forecastDate) => (
          <section className="forecast-demand-day" key={forecastDate}>
            <div className="forecast-demand-date">
              <strong>{formatForecastDate(forecastDate)}</strong>
              <span>{groupedRows[forecastDate].length} kategóriajelzés</span>
            </div>
            {groupedRows[forecastDate].map((row) => {
              const uplift = toNumber(row.revenue_uplift_percent);
              return (
                <article className={`forecast-demand-row ${row.demand_signal}`} key={`${row.forecast_date}-${row.category_name}`}>
                  <div className="forecast-demand-heading">
                    <span>
                      <strong>{row.category_name}</strong>
                      <small>
                        {formatTemperatureBand(row.dominant_temperature_band)} ·{" "}
                        {formatWeatherConditionBand(row.dominant_condition_band)}
                      </small>
                    </span>
                    <span>
                      <strong>{formatMoney(row.expected_revenue)}</strong>
                      <small>{formatDemandSignal(row.demand_signal)}</small>
                    </span>
                  </div>
                  <div className="forecast-demand-metrics">
                    <span>
                      <strong>{formatNumber(row.expected_quantity)}</strong>
                      Várható mennyiség
                    </span>
                    <span>
                      <strong>{uplift >= 0 ? "+" : ""}{formatNumber(uplift)}%</strong>
                      Kategóriaátlaghoz
                    </span>
                    <span>
                      <strong>{formatForecastConfidence(row.confidence)}</strong>
                      Bizalom
                    </span>
                  </div>
                  <p>{row.recommendation}</p>
                </article>
              );
            })}
          </section>
        ))}
      </div>

      {rows.length === 0 ? (
        <p className="empty-message">
          Nincs még elég forecast és historikus kategória-időjárás kapcsolat a Gourmand
          keresleti becsléshez.
        </p>
      ) : null}
    </Card>
  );
}

function ForecastPreparationCard({
  rows,
}: {
  rows: DashboardForecastPreparationRow[];
}) {
  const criticalCount = rows.filter((row) => row.readiness_level === "kritikus").length;
  const watchCount = rows.filter((row) => row.readiness_level === "figyelendo").length;
  const strongestRow = [...rows].sort(
    (left, right) => toNumber(right.expected_revenue) - toNumber(left.expected_revenue),
  )[0];

  return (
    <Card
      hoverable
      tone="secondary"
      eyebrow="Gourmand előkészítés"
      title="Termelési és készlet ajánló"
      subtitle="Forecast kereslet, katalógus, recept és aktuális készlet alapján"
      count={criticalCount > 0 ? `${criticalCount} kritikus` : strongestRow?.category_name ?? rows.length}
    >
      <div className="forecast-preparation-summary">
        <span>
          <strong>{criticalCount}</strong>
          Kritikus előkészítés
        </span>
        <span>
          <strong>{watchCount}</strong>
          Figyelendő jelzés
        </span>
        <span>
          <strong>{strongestRow ? formatMoney(strongestRow.expected_revenue) : "-"}</strong>
          Legnagyobb várható kategória
        </span>
      </div>

      <div className="forecast-preparation-list">
        {rows.map((row) => (
          <article
            className={`forecast-preparation-row ${row.readiness_level}`}
            key={`${row.forecast_date}-${row.category_name}`}
          >
            <div className="forecast-preparation-heading">
              <span>
                <strong>{row.category_name}</strong>
                <small>
                  {formatForecastDate(row.forecast_date)} · {formatDemandSignal(row.demand_signal)}
                </small>
              </span>
              <span>
                <strong>{formatReadinessLevel(row.readiness_level)}</strong>
                <small>{formatForecastConfidence(row.confidence)}</small>
              </span>
            </div>

            <div className="forecast-preparation-metrics">
              <span>
                <strong>{formatMoney(row.expected_revenue)}</strong>
                Várható forgalom
              </span>
              <span>
                <strong>{formatNumber(row.expected_quantity)}</strong>
                Becsült mennyiség
              </span>
              <span>
                <strong>{row.product_count}</strong>
                Katalógus termék
              </span>
              <span>
                <strong>{row.risky_product_count}</strong>
                Érintett termék
              </span>
              <span>
                <strong>{row.missing_stock_ingredient_count}</strong>
                Hiányzó készlet
              </span>
              <span>
                <strong>{row.low_stock_ingredient_count}</strong>
                Alacsony készlet
              </span>
            </div>
            <p>{row.recommendation}</p>
          </article>
        ))}
      </div>

      {rows.length === 0 ? (
        <p className="empty-message">
          Nincs még olyan Gourmand forecast jelzés, ami katalógus és készlet ajánlóvá alakítható.
        </p>
      ) : null}
    </Card>
  );
}

function ForecastProductDemandCard({
  rows,
}: {
  rows: DashboardForecastProductDemandRow[];
}) {
  const strongestRow = [...rows].sort(
    (left, right) => toNumber(right.expected_revenue) - toNumber(left.expected_revenue),
  )[0];
  const groupedRows = rows.reduce<Record<string, DashboardForecastProductDemandRow[]>>(
    (acc, row) => {
      acc[row.forecast_date] = [...(acc[row.forecast_date] ?? []), row];
      return acc;
    },
    {},
  );
  const dates = Object.keys(groupedRows).sort();

  return (
    <Card
      hoverable
      tone="secondary"
      eyebrow="Gourmand termék forecast"
      title="Várható húzótermékek"
      subtitle="Forecast időjárás, historikus termékforgalom és kategória alapján"
      count={strongestRow?.product_name ?? rows.length}
    >
      <div className="forecast-product-summary">
        <span>
          <strong>{strongestRow?.product_name ?? "-"}</strong>
          Legerősebb várható termék
        </span>
        <span>
          <strong>{strongestRow ? formatMoney(strongestRow.expected_revenue) : "-"}</strong>
          Becsült termékforgalom
        </span>
      </div>

      <div className="forecast-product-list">
        {dates.map((forecastDate) => (
          <section className="forecast-product-day" key={forecastDate}>
            <div className="forecast-demand-date">
              <strong>{formatForecastDate(forecastDate)}</strong>
              <span>{groupedRows[forecastDate].length} termékjelzés</span>
            </div>
            {groupedRows[forecastDate].map((row) => {
              const uplift = toNumber(row.revenue_uplift_percent);
              return (
                <article className={`forecast-product-row ${row.demand_signal}`} key={`${row.forecast_date}-${row.product_name}`}>
                  <div className="forecast-product-heading">
                    <span>
                      <strong>{row.product_name}</strong>
                      <small>
                        {row.category_name} · {formatTemperatureBand(row.dominant_temperature_band)}
                      </small>
                    </span>
                    <span>
                      <strong>{formatMoney(row.expected_revenue)}</strong>
                      <small>{formatDemandSignal(row.demand_signal)}</small>
                    </span>
                  </div>
                  <div className="forecast-product-metrics">
                    <span>
                      <strong>{formatNumber(row.expected_quantity)}</strong>
                      Várható mennyiség
                    </span>
                    <span>
                      <strong>{uplift >= 0 ? "+" : ""}{formatNumber(uplift)}%</strong>
                      Termékátlaghoz
                    </span>
                    <span>
                      <strong>{formatForecastConfidence(row.confidence)}</strong>
                      Bizalom
                    </span>
                  </div>
                  <p>{row.recommendation}</p>
                </article>
              );
            })}
          </section>
        ))}
      </div>

      {rows.length === 0 ? (
        <p className="empty-message">
          Nincs még elég forecast és historikus termék-időjárás kapcsolat a termékszintű becsléshez.
        </p>
      ) : null}
    </Card>
  );
}

function ForecastPeakTimeCard({
  rows,
}: {
  rows: DashboardForecastPeakTimeRow[];
}) {
  const strongestRow = [...rows].sort(
    (left, right) => toNumber(right.expected_revenue) - toNumber(left.expected_revenue),
  )[0];
  const maxRevenue = Math.max(...rows.map((row) => toNumber(row.expected_revenue)), 1);

  return (
    <Card
      hoverable
      tone="secondary"
      eyebrow="Gourmand csúcsidő forecast"
      title="Várható forgalmi idősávok"
      subtitle="Napszakos forecast jelzés historikus kassza- és időjárásmintából"
      count={strongestRow ? `${formatForecastDate(strongestRow.forecast_date)} ${strongestRow.time_window}` : rows.length}
    >
      <div className="forecast-peak-summary">
        <span>
          <strong>{strongestRow?.time_window ?? "-"}</strong>
          Legerősebb várható idősáv
        </span>
        <span>
          <strong>{strongestRow ? formatMoney(strongestRow.expected_revenue) : "-"}</strong>
          Becsült idősávforgalom
        </span>
        <span>
          <strong>{strongestRow?.expected_transaction_count ?? "-"}</strong>
          Várható nyugta
        </span>
      </div>

      <div className="forecast-peak-list">
        {rows.map((row) => {
          const width = `${Math.max(6, (toNumber(row.expected_revenue) / maxRevenue) * 100)}%`;
          const uplift = toNumber(row.revenue_uplift_percent);
          return (
            <article className={`forecast-peak-row ${row.demand_signal}`} key={`${row.forecast_date}-${row.time_window}`}>
              <div className="forecast-peak-heading">
                <span>
                  <strong>{formatForecastDate(row.forecast_date)} · {row.time_window}</strong>
                  <small>
                    {row.start_hour}:00-{row.end_hour}:00 · {formatWeatherConditionBand(row.dominant_condition_band)}
                  </small>
                </span>
                <span>
                  <strong>{formatMoney(row.expected_revenue)}</strong>
                  <small>{formatDemandSignal(row.demand_signal)}</small>
                </span>
              </div>
              <div className="forecast-peak-track">
                <span style={{ width }} />
              </div>
              <div className="forecast-peak-metrics">
                <span>
                  <strong>{formatNumber(row.expected_quantity)}</strong>
                  Mennyiség
                </span>
                <span>
                  <strong>{row.expected_transaction_count}</strong>
                  Várható nyugta
                </span>
                <span>
                  <strong>{uplift >= 0 ? "+" : ""}{formatNumber(uplift)}%</strong>
                  Idősávátlaghoz
                </span>
              </div>
              <p>{row.recommendation}</p>
            </article>
          );
        })}
      </div>

      {rows.length === 0 ? (
        <p className="empty-message">
          Nincs még elég forecast és historikus napszakos adat a csúcsidő becsléshez.
        </p>
      ) : null}
    </Card>
  );
}

function ProductRiskCard({ rows }: { rows: DashboardProductRiskRow[] }) {
  const dangerCount = rows.filter((row) => row.risk_level === "danger").length;
  const warningCount = rows.filter((row) => row.risk_level !== "danger").length;
  const totalMarginRisk = rows.reduce(
    (sum, row) => sum + Math.min(toNumber(row.estimated_margin_amount), 0),
    0,
  );

  return (
    <Card
      hoverable
      tone="secondary"
      eyebrow="Figyelendő termékek"
      title="Árrés, recept és készlet kockázatok"
      subtitle="Aktuális katalógus és mozgásalapú készlet alapján"
      count={rows.length}
    >
      <div className="product-risk-summary">
        <span>
          <strong>{dangerCount}</strong>
          Kritikus jelzés
        </span>
        <span>
          <strong>{warningCount}</strong>
          Figyelendő jelzés
        </span>
        <span>
          <strong>{formatMoney(totalMarginRisk)}</strong>
          Negatív árrés összesen
        </span>
      </div>

      <div className="product-risk-list">
        {rows.map((row) => {
          const isDanger = row.risk_level === "danger";
          return (
            <article
              className={isDanger ? "product-risk-row danger" : "product-risk-row warning"}
              key={row.product_id}
            >
              <div className="product-risk-heading">
                <span className={isDanger ? "product-risk-level danger" : "product-risk-level warning"}>
                  {isDanger ? "!" : "?"}
                </span>
                <span>
                  <strong>{row.product_name}</strong>
                  <small>{row.category_name}</small>
                </span>
                <span className={toNumber(row.estimated_margin_amount) < 0 ? "product-risk-margin negative" : "product-risk-margin"}>
                  {formatMoney(row.estimated_margin_amount)}
                  <small>{formatNumber(row.estimated_margin_percent)}%</small>
                </span>
              </div>

              <div className="product-risk-tags">
                {row.risk_reasons.map((reason) => (
                  <span key={reason}>{reason}</span>
                ))}
              </div>

              <div className="product-risk-meta">
                <span>Ár: {formatMoney(row.sale_price_gross)}</span>
                <span>Költség: {formatMoney(row.estimated_unit_cost)}</span>
                <span>Hiány: {row.low_stock_ingredient_count}</span>
                <span>Nincs készletadat: {row.missing_stock_ingredient_count}</span>
              </div>
            </article>
          );
        })}
      </div>

      {rows.length === 0 ? (
        <p className="empty-message">Nincs kiemelt termékkockázat.</p>
      ) : null}
    </Card>
  );
}

function formatInventoryItemType(value: string) {
  const labels: Record<string, string> = {
    raw_material: "Alapanyag",
    packaging: "Csomagolóanyag",
    finished_good: "Késztermék",
    semi_finished: "Félkész termék",
  };
  return labels[value] ?? value;
}

function StockRiskCard({ rows }: { rows: DashboardStockRiskRow[] }) {
  const dangerCount = rows.filter((row) => row.risk_level === "danger").length;
  const warningCount = rows.filter((row) => row.risk_level !== "danger").length;
  const impactedProducts = rows.reduce(
    (sum, row) => sum + row.used_by_product_count,
    0,
  );

  return (
    <Card
      hoverable
      eyebrow="Készletkockázat"
      title="Mi veszélyeztetheti az értékesítést?"
      subtitle="Mozgásalapú készlet és recept-használat alapján"
      count={rows.length}
    >
      <div className="stock-risk-summary">
        <span>
          <strong>{dangerCount}</strong>
          Kritikus készlet
        </span>
        <span>
          <strong>{warningCount}</strong>
          Figyelendő készlet
        </span>
        <span>
          <strong>{impactedProducts}</strong>
          Érintett termék
        </span>
      </div>

      <div className="stock-risk-list">
        {rows.map((row) => {
          const isDanger = row.risk_level === "danger";
          return (
            <article
              className={isDanger ? "stock-risk-row danger" : "stock-risk-row warning"}
              key={row.inventory_item_id}
            >
              <div className="stock-risk-heading">
                <span className={isDanger ? "stock-risk-level danger" : "stock-risk-level warning"}>
                  {isDanger ? "!" : "?"}
                </span>
                <span>
                  <strong>{row.item_name}</strong>
                  <small>{formatInventoryItemType(row.item_type)}</small>
                </span>
                <span className="stock-risk-quantity">
                  {formatNumber(row.current_quantity)}
                  <small>aktuális készlet</small>
                </span>
              </div>

              <div className="stock-risk-tags">
                {row.risk_reasons.map((reason) => (
                  <span key={reason}>{reason}</span>
                ))}
              </div>

              <div className="stock-risk-meta">
                <span>{row.used_by_product_count} termék használja</span>
                <span>{row.movement_count} készletmozgás</span>
                <span>
                  Eltérés:{" "}
                  {row.variance_quantity === null
                    ? "nincs theoretical adat"
                    : formatNumber(row.variance_quantity)}
                </span>
              </div>
            </article>
          );
        })}
      </div>

      {rows.length === 0 ? (
        <p className="empty-message">Nincs kiemelt készletkockázat.</p>
      ) : null}
    </Card>
  );
}

type DashboardRiskItem = {
  key: string;
  kind: "product" | "stock";
  title: string;
  subtitle: string;
  level: string;
  primaryValue: string;
  primaryLabel: string;
  meta: string[];
  reasons: string[];
};

function RiskOverviewCard({
  productRows,
  stockRows,
}: {
  productRows: DashboardProductRiskRow[];
  stockRows: DashboardStockRiskRow[];
}) {
  const [selectedRiskKey, setSelectedRiskKey] = useState<string | null>(null);
  const productDangerCount = productRows.filter((row) => row.risk_level === "danger").length;
  const stockDangerCount = stockRows.filter((row) => row.risk_level === "danger").length;
  const productWarningCount = productRows.length - productDangerCount;
  const stockWarningCount = stockRows.length - stockDangerCount;
  const totalMarginRisk = productRows.reduce(
    (sum, row) => sum + Math.min(toNumber(row.estimated_margin_amount), 0),
    0,
  );
  const riskItems: DashboardRiskItem[] = [
    ...productRows.map((row) => ({
      key: `product-${row.product_id}`,
      kind: "product" as const,
      title: row.product_name,
      subtitle: row.category_name,
      level: row.risk_level,
      primaryValue: formatMoney(row.estimated_margin_amount),
      primaryLabel: `${formatNumber(row.estimated_margin_percent)}% árrés`,
      meta: [
        `Ár: ${formatMoney(row.sale_price_gross)}`,
        `Költség: ${formatMoney(row.estimated_unit_cost)}`,
        `Hiány: ${row.low_stock_ingredient_count}`,
        `Nincs készletadat: ${row.missing_stock_ingredient_count}`,
      ],
      reasons: row.risk_reasons,
    })),
    ...stockRows.map((row) => ({
      key: `stock-${row.inventory_item_id}`,
      kind: "stock" as const,
      title: row.item_name,
      subtitle: formatInventoryItemType(row.item_type),
      level: row.risk_level,
      primaryValue: formatNumber(row.current_quantity),
      primaryLabel: "aktuális készlet",
      meta: [
        `${row.used_by_product_count} termék használja`,
        `${row.movement_count} készletmozgás`,
        row.variance_quantity === null
          ? "Eltérés: nincs theoretical adat"
          : `Eltérés: ${formatNumber(row.variance_quantity)}`,
      ],
      reasons: row.risk_reasons,
    })),
  ]
    .sort((left, right) => {
      if (left.level === right.level) {
        return left.title.localeCompare(right.title, "hu-HU");
      }
      return left.level === "danger" ? -1 : 1;
    })
    .slice(0, 8);
  const selectedRisk = riskItems.find((row) => row.key === selectedRiskKey) ?? null;

  return (
    <Card
      hoverable
      tone="secondary"
      className="risk-overview-card"
      eyebrow="Kockázati jelzések"
      title="Termék, recept és készlet fókusz"
      subtitle="Dashboardon csak a vezetői riasztás; részletes munka Katalógus/Inventory irányban"
      count={riskItems.length}
    >
      <div className="risk-overview-summary">
        <span>
          <strong>{productDangerCount + stockDangerCount}</strong>
          Kritikus jelzés
        </span>
        <span>
          <strong>{productWarningCount + stockWarningCount}</strong>
          Figyelendő jelzés
        </span>
        <span>
          <strong>{formatMoney(totalMarginRisk)}</strong>
          Negatív árrés összesen
        </span>
      </div>

      <div className="risk-overview-list">
        {riskItems.map((row) => {
          const isDanger = row.level === "danger";
          const isSelected = selectedRiskKey === row.key;

          return (
            <button
              key={row.key}
              type="button"
              className={
                isSelected
                  ? `risk-overview-row risk-overview-row-active ${isDanger ? "danger" : "warning"}`
                  : `risk-overview-row ${isDanger ? "danger" : "warning"}`
              }
              onClick={() => setSelectedRiskKey(isSelected ? null : row.key)}
            >
              <span className={isDanger ? "risk-overview-level danger" : "risk-overview-level warning"}>
                {isDanger ? "!" : "?"}
              </span>
              <span className="risk-overview-content">
                <span className="risk-overview-heading">
                  <strong>{row.title}</strong>
                  <small>{row.kind === "product" ? "Termék" : "Készlet"} · {row.subtitle}</small>
                </span>
                <span className="risk-overview-meta">
                  <span>{row.primaryValue}</span>
                  <span>{row.primaryLabel}</span>
                  <span>{row.reasons[0] ?? "Részletezés szükséges"}</span>
                </span>
              </span>
            </button>
          );
        })}
      </div>

      {selectedRisk ? (
        <div className="risk-overview-drilldown">
          <div>
            <strong>{selectedRisk.title}</strong>
            <span>{selectedRisk.subtitle}</span>
          </div>
          <div className="risk-overview-tags">
            {selectedRisk.reasons.map((reason) => (
              <span key={reason}>{reason}</span>
            ))}
          </div>
          <div className="risk-overview-drilldown-meta">
            {selectedRisk.meta.map((item) => (
              <span key={item}>{item}</span>
            ))}
          </div>
        </div>
      ) : null}

      {riskItems.length === 0 ? (
        <p className="empty-message">Nincs kiemelt termék- vagy készletkockázat.</p>
      ) : null}
    </Card>
  );
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

function CategoryMixCard({
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
          <div className="table-wrap dashboard-embedded-table">
            <table className="data-table details-table">
              <thead>
                <tr>
                  <th>Dátum</th>
                  <th>Nyugta</th>
                  <th>Mennyiség</th>
                  <th>Bruttó összeg</th>
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

function DashboardHeaderControls({
  scope,
  setScope,
  period,
  setPeriod,
  startDate,
  setStartDate,
  endDate,
  setEndDate,
}: {
  scope: DashboardScope;
  setScope: (value: DashboardScope) => void;
  period: DashboardPeriodPreset;
  setPeriod: (value: DashboardPeriodPreset) => void;
  startDate: string;
  setStartDate: (value: string) => void;
  endDate: string;
  setEndDate: (value: string) => void;
}) {
  return (
    <>
      <div className="business-segmented-control topbar-segmented-control">
        {scopeOptions.map((option) => (
          <button
            key={option.value}
            type="button"
            className={
              scope === option.value ? "filter-chip filter-chip-active" : "filter-chip"
            }
            onClick={() => setScope(option.value)}
          >
            {option.label}
          </button>
        ))}
      </div>

      <div className="business-dashboard-filters topbar-dashboard-filters">
        <label className="field topbar-field">
          <span>Időszak</span>
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
            <label className="field topbar-field">
              <span>Kezdő dátum</span>
              <input
                className="field-input"
                type="date"
                value={startDate}
                onChange={(event) => setStartDate(event.target.value)}
              />
            </label>
            <label className="field topbar-field">
              <span>Záró dátum</span>
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
    </>
  );
}

export function DashboardPage() {
  const { setControls } = useTopbarControls();
  const [visibleTrendMetrics, setVisibleTrendMetrics] = useState<TrendMetric[]>([
    "revenue",
    "cost",
    "profit",
  ]);
  const [categoryMixMetric, setCategoryMixMetric] = useState<MixMetric>("revenue");
  const {
    dashboard,
    basketPairs,
    basketReceipts,
    topProducts,
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
    topProductCategory,
    setTopProductCategory,
    isLoading,
    isDrilldownLoading,
    isTopProductsLoading,
    isBasketReceiptsLoading,
    errorMessage,
  } = useDashboard();
  useEffect(() => {
    setControls(
      <DashboardHeaderControls
        scope={scope}
        setScope={setScope}
        period={period}
        setPeriod={setPeriod}
        startDate={startDate}
        setStartDate={setStartDate}
        endDate={endDate}
        setEndDate={setEndDate}
      />,
    );

    return () => setControls(null);
  }, [
    endDate,
    period,
    scope,
    setControls,
    setEndDate,
    setPeriod,
    setScope,
    setStartDate,
    startDate,
  ]);

  return (
    <section className="page-section">
      {errorMessage ? <p className="error-message">{errorMessage}</p> : null}
      {isLoading ? <p className="info-message">Dashboard betöltése...</p> : null}

      {dashboard ? (
        <>
          <div className="kpi-grid">
            {getVisibleKpis(dashboard.kpis).map((kpi) => (
              <Card
                key={kpi.code}
                tone={getKpiTone(kpi.code)}
                className="kpi-card"
                hoverable
                eyebrow={getKpiLabel(kpi)}
                data-tooltip={kpiHelp[kpi.code] ?? kpi.label}
              >
                <span className="kpi-value">{getKpiValue(kpi)}</span>
                {formatAmountMarker(kpi.amount_basis, kpi.amount_origin) ? (
                  <span className="kpi-caption">
                    {formatAmountMarker(kpi.amount_basis, kpi.amount_origin)}
                  </span>
                ) : null}
                {getKpiSecondary(kpi, dashboard.kpis) ? (
                  <span className="kpi-caption">
                    {getKpiSecondary(kpi, dashboard.kpis)}
                  </span>
                ) : null}
              </Card>
            ))}
          </div>

          <div className="dashboard-main dashboard-main-compact">
            <div className="dashboard-stack dashboard-stack-primary">
              <section className="dashboard-section dashboard-section-primary">
                <div className="dashboard-section-heading">
                  <span>Üzleti pulzus</span>
                  <strong>Bevétel, trend és kategóriaarány</strong>
                </div>

              <Card
                tone="rainbow"
                className="chart-card"
                hoverable
                eyebrow={`${dashboard.period.start_date} - ${dashboard.period.end_date}`}
                title="Forgalom, kiadás és profit"
                subtitle={formatGrain(dashboard.period.grain)}
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
                  points={dashboard.revenue_trend}
                  visibleMetrics={visibleTrendMetrics}
                  grain={dashboard.period.grain}
                  forecastRows={dashboard.forecast_impact_insights}
                />
              </Card>

              <BusinessFocusCard dashboard={dashboard} />
              <BusinessSpecificAnalyticsCard dashboard={dashboard} />

              <CategoryMixCard
                categories={dashboard.category_breakdown}
                activeCategory={drilldown?.type === "category" ? drilldown.label : null}
                productDetails={productDetails}
                selectedProduct={selectedProduct}
                productSourceRows={productSourceRows}
                isLoading={drilldown?.type === "category" && isDrilldownLoading}
                metric={categoryMixMetric}
                setMetric={setCategoryMixMetric}
                openCategory={(category) => {
                  setSelectedProduct(null);
                  setDrilldown({ type: "category", label: category });
                }}
                closeCategory={() => {
                  setSelectedProduct(null);
                  setDrilldown(null);
                }}
                selectProduct={setSelectedProduct}
              />

              <TrafficHeatmapCard
                cells={dashboard.traffic_heatmap}
                scope={scope}
                basketRows={dashboard.basket_value_distribution}
              />
              {dashboard.scope !== "flow" ? (
                <WeatherImpactDashboardCard
                  temperatureRows={dashboard.temperature_band_insights}
                  conditionRows={dashboard.weather_condition_insights}
                  categoryRows={dashboard.weather_category_insights}
                  forecastRows={dashboard.forecast_impact_insights}
                />
              ) : null}
              {dashboard.scope !== "flow" ? (
                <GourmandDailyForecastCard
                  categoryRows={dashboard.forecast_category_demand_insights}
                  productRows={dashboard.forecast_product_demand_insights}
                  peakRows={dashboard.forecast_peak_time_insights}
                />
              ) : null}
              </section>

              <section className="dashboard-section">
                <div className="dashboard-section-heading">
                  <span>Forgalmi ritmus</span>
                  <strong>Idősávok, fizetés és kosárérték</strong>
                </div>

              </section>

            </div>

            <div className="dashboard-stack">
              <section className="dashboard-section">
                <div className="dashboard-section-heading">
                  <span>Termék és készlet figyelő</span>
                  <strong>Top teljesítmény és kockázatok</strong>
                </div>

                <TopProductsCard
                  rows={topProducts}
                  categories={dashboard.category_breakdown}
                  selectedCategory={topProductCategory}
                  setSelectedCategory={setTopProductCategory}
                  isLoading={isTopProductsLoading}
                  scope={scope}
                />

                <RiskOverviewCard
                  productRows={dashboard.product_risks}
                  stockRows={dashboard.stock_risks}
                />
              </section>

              <section className="dashboard-section">
                <div className="dashboard-section-heading">
                  <span>Kosár és költség mélyítés</span>
                  <strong>Együttvásárlás és kiadáskontroll</strong>
                </div>

                <BasketAnalysisCard
                  pairs={basketPairs}
                  selectedPair={selectedBasketPair}
                  setSelectedPair={setSelectedBasketPair}
                  receipts={basketReceipts}
                  isLoading={isBasketReceiptsLoading}
                />

                <ExpenseBreakdownCard
                  rows={dashboard.expense_breakdown}
                  activeType={drilldown?.type === "expense" ? drilldown.label : null}
                  openExpenseType={(type) => {
                    setSelectedExpense(null);
                    setDrilldown({ type: "expense", label: type });
                  }}
                />
              </section>

            </div>
          </div>

          {drilldown?.type === "expense" ? (
            <ExpenseDrilldownCard
              type={drilldown.label}
              rows={expenseDetails}
              selectedExpense={selectedExpense}
              setSelectedExpense={setSelectedExpense}
              source={expenseSource}
              isLoading={isDrilldownLoading}
              close={() => {
                setSelectedProduct(null);
                setSelectedExpense(null);
                setSelectedBasketPair(null);
                setDrilldown(null);
              }}
            />
          ) : null}
        </>
      ) : null}
    </section>
  );
}
