import { Card } from "../../../shared/components/ui/Card";
import type { PosMappingReadiness } from "../../posIngestion/types/posIngestion";
import type {
  DashboardBreakdownRow,
  DashboardCategoryTrendRow,
  DashboardData,
  DashboardHeatmapCell,
  DashboardProductRiskRow,
  DashboardScope,
  DashboardStockRiskRow,
  DashboardVatReadiness,
  DashboardWeatherCategoryInsightRow,
} from "../types/analytics";
import {
  formatHeatmapHour,
  formatMoney,
  formatNumber,
  formatTaxBreakdownSource,
  formatVatReadinessStatus,
  formatWeatherCondition,
  getStrongestHeatmapCell,
  getTopCategory,
  getWeekdayLabel,
  mixPalette,
  toNumber,
} from "./dashboardView";
type BusinessInsight = {
  label: string;
  value: string;
  description: string;
  tone: "primary" | "success" | "warning" | "neutral";
};
type BusinessSpecificMetric = BusinessInsight & {
  share?: number;
};

function buildBusinessInsights(dashboard: {
  scope: DashboardScope;
  category_breakdown: DashboardBreakdownRow[];
  traffic_heatmap: DashboardHeatmapCell[];
  top_products: DashboardBreakdownRow[];
  category_trends: DashboardCategoryTrendRow[];
  weather_category_insights: DashboardWeatherCategoryInsightRow[];
  product_risks: DashboardProductRiskRow[];
  stock_risks: DashboardStockRiskRow[];
}): BusinessInsight[] {
  const topCategory = getTopCategory(dashboard.category_breakdown);
  const strongestSlot = getStrongestHeatmapCell(dashboard.traffic_heatmap);
  const topWeatherCategory = [...dashboard.weather_category_insights].sort(
    (left, right) => toNumber(right.revenue) - toNumber(left.revenue),
  )[0];
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
        label: "Ticket réteg",
        value: "Külön rendszer",
        description:
          "A Flow POS CSV nem tartalmaz jegyet; a ticket bevétel eventhez rögzített actualként kerül be.",
        tone: "neutral",
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
        value: topWeatherCategory
          ? `${topWeatherCategory.category_name} · ${formatWeatherCondition(topWeatherCategory.weather_condition)}`
          : "Nincs adat",
        description: topWeatherCategory
          ? `${formatMoney(topWeatherCategory.revenue)} forgalom időjárással összekapcsolt kasszasorokból.`
          : "A weather cache összekötés után itt jelenik meg a legerősebb kategória-időjárás kapcsolat.",
        tone: topWeatherCategory ? "success" : "neutral",
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
      label: "Ticket réteg",
      value: "Flow event actual",
      description:
        "A Flow jegybevétel külön ticket rendszerből érkezik, nem POS termékforgalomból.",
      tone: "neutral",
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

export function DashboardBusinessFocus({ dashboard }: { dashboard: DashboardData }) {
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

export function DashboardVatReadinessCard({ readiness }: { readiness: DashboardVatReadiness }) {
  const coverage = Math.min(100, Math.max(0, toNumber(readiness.coverage_percent)));
  const statusTone =
    readiness.status === "complete"
      ? "success"
      : readiness.status === "partial"
        ? "warning"
        : readiness.status === "missing"
          ? "danger"
          : "neutral";

  return (
    <Card
      hoverable
      className={`vat-readiness-card ${statusTone}`}
      eyebrow="ÁFA-lefedettség"
      title="POS bevétel nettó/bruttó készültség"
      subtitle={formatTaxBreakdownSource(readiness.tax_breakdown_source)}
      count={formatVatReadinessStatus(readiness.status)}
    >
      <div className="vat-readiness-summary">
        <span>
          <strong>{formatNumber(coverage)}%</strong>
          <small>Lefedett bruttó forgalom</small>
        </span>
        <span>
          <strong>{formatMoney(readiness.covered_gross_revenue)}</strong>
          <small>Számolható alap</small>
        </span>
        <span>
          <strong>{formatMoney(readiness.missing_gross_revenue)}</strong>
          <small>Hiányzó ÁFA-kulcs</small>
        </span>
      </div>
      <div className="vat-readiness-track" aria-hidden="true">
        <span style={{ width: `${coverage}%` }} />
      </div>
      <div className="vat-readiness-meta">
        <span>{readiness.covered_row_count} lefedett sor</span>
        <span>{readiness.missing_row_count} hiányos sor</span>
        <span>{readiness.total_row_count} összes POS sor</span>
      </div>
    </Card>
  );
}

export function DashboardMappingReadinessCard({
  readiness,
}: {
  readiness: PosMappingReadiness;
}) {
  const coverage = Math.min(
    100,
    Math.max(0, toNumber(readiness.gross_revenue_coverage_percent)),
  );
  const statusTone =
    readiness.status === "complete"
      ? "success"
      : readiness.status === "partial"
        ? "warning"
        : readiness.status === "missing"
          ? "danger"
          : "neutral";
  const statusLabel =
    readiness.status === "complete"
      ? "Teljes"
      : readiness.status === "partial"
        ? "Reszleges"
        : readiness.status === "missing"
          ? "Hianyzik"
          : "Nincs adat";

  return (
    <Card
      hoverable
      className={`vat-readiness-card ${statusTone}`}
      eyebrow="Mapping-lefedettseg"
      title="POS termekazonossag keszultseg"
      subtitle="Jovahagyott aliasokkal lefedett idoszaki forgalom"
      count={statusLabel}
    >
      <div className="vat-readiness-summary">
        <span>
          <strong>{formatNumber(coverage)}%</strong>
          <small>Jovahagyott brutto forgalom</small>
        </span>
        <span>
          <strong>{formatMoney(readiness.mapped_gross_revenue)}</strong>
          <small>Biztos mapping</small>
        </span>
        <span>
          <strong>{formatMoney(readiness.automatic_gross_revenue)}</strong>
          <small>Automatikus mapping</small>
        </span>
      </div>
      <div className="vat-readiness-track" aria-hidden="true">
        <span style={{ width: `${coverage}%` }} />
      </div>
      <div className="vat-readiness-meta">
        <span>{readiness.mapped_row_count} jovahagyott sor</span>
        <span>{readiness.automatic_row_count} ellenorzendo sor</span>
        <span>{readiness.missing_row_count} mapping nelkuli sor</span>
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

export function DashboardBusinessSpecificAnalytics({ dashboard }: { dashboard: DashboardData }) {
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
    const categoryRows = buildGourmandCategoryMetrics(dashboard.category_breakdown);
    const totalRevenue = categoryRows.reduce((sum, row) => sum + row.revenue, 0);
    const maxCategoryRevenue = Math.max(...categoryRows.map((row) => row.revenue), 1);
    const averageBasket = dashboard.kpis.find((kpi) => kpi.code === "average_basket_value");
    const metrics: BusinessSpecificMetric[] = [
      {
        label: "Ticket bevétel",
        value: "Külön actual",
        description:
          "Nincs helyszíni/POS jegyértékesítés. A jegyadat eventhez rögzített ticket actualként kerül be.",
        tone: "neutral",
      },
      {
        label: "Bár/fogyasztás",
        value: formatMoney(totalRevenue),
        description: "A Flow POS CSV teljes forgalmi rétege fogyasztási/bár truth source.",
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
      {
        label: "Átlagos kosárérték",
        value: averageBasket ? formatMoney(averageBasket.value) : "-",
        description:
          "Pénzügyi pultmutató: a fogyasztási viselkedés gyors összegzése, nem event rangsor.",
        tone: "success",
      },
    ];

    return (
      <Card
        tone="secondary"
        hoverable
        className="business-specific-card"
        eyebrow="Flow elemzés"
        title="Pénzügyi forgalmi mix"
        subtitle="A Flow üzleti dashboard POS-alapú pénzügyi képe; eventenkénti rangsor az Event nézetben marad"
        count={`${dashboard.category_breakdown.length} kategória`}
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
        <div className="flow-financial-mix-list">
          {categoryRows.map((row, index) => {
            const width = `${Math.max(5, (row.revenue / maxCategoryRevenue) * 100)}%`;
            const share = totalRevenue > 0 ? (row.revenue / totalRevenue) * 100 : 0;
            return (
              <article className="flow-financial-mix-row" key={row.label}>
                <div>
                  <strong>{row.label}</strong>
                  <span>Bár/fogyasztási réteg</span>
                </div>
                <span className="business-family-track">
                  <span
                    style={{
                      width,
                      background: `linear-gradient(135deg, ${mixPalette[index % mixPalette.length]}, ${
                        mixPalette[(index + 3) % mixPalette.length]
                      })`,
                    }}
                  />
                </span>
                <small>{formatMoney(row.revenue)} · {formatNumber(share)}% · {row.count} sor</small>
              </article>
            );
          })}
          {categoryRows.length === 0 ? (
            <p className="empty-message">Nincs még Flow kategóriaforgalom az aktuális időszakban.</p>
          ) : null}
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
        <article className="business-focus-item neutral">
          <span>Ticket réteg</span>
          <strong>Flow event actual</strong>
          <small>A jegybevétel nem POS termék, hanem külön Flow event réteg.</small>
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

