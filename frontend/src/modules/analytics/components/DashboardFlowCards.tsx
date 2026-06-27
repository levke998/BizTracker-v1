import { Card } from "../../../shared/components/ui/Card";
import type { EventPerformance, EventRecord } from "../../events/types/events";
import type {
  DashboardBreakdownRow,
  DashboardData,
  DashboardFlowForecastEventRow,
} from "../types/analytics";
import {
  formatBasketValueBand,
  formatEventDate,
  formatHeatmapHour,
  formatMoney,
  formatNumber,
  formatOptionalPercent,
  formatReadinessLevel,
  formatWeatherConditionBand,
  getStrongestHeatmapCell,
  getWeekdayLabel,
  toNumber,
} from "./dashboardView";
type BusinessSpecificMetric = {
  label: string;
  value: string;
  description: string;
  tone: "primary" | "success" | "warning" | "neutral";
  share?: number;
};

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

export function DashboardFlowConsumptionControl({ dashboard }: { dashboard: DashboardData }) {
  const categoryRows = buildGourmandCategoryMetrics(dashboard.category_breakdown);
  const totalRevenue = categoryRows.reduce((sum, row) => sum + row.revenue, 0);
  const leader = categoryRows[0] ?? null;
  const topThreeRevenue = categoryRows.slice(0, 3).reduce((sum, row) => sum + row.revenue, 0);
  const leaderShare = leader && totalRevenue > 0 ? (leader.revenue / totalRevenue) * 100 : 0;
  const topThreeShare = totalRevenue > 0 ? (topThreeRevenue / totalRevenue) * 100 : 0;
  const heatmapRevenue = dashboard.traffic_heatmap.reduce(
    (sum, cell) => sum + toNumber(cell.revenue),
    0,
  );
  const strongestSlot = getStrongestHeatmapCell(dashboard.traffic_heatmap);
  const strongestSlotShare =
    strongestSlot && heatmapRevenue > 0 ? (toNumber(strongestSlot.revenue) / heatmapRevenue) * 100 : 0;
  const averageBasket = dashboard.kpis.find((kpi) => kpi.code === "average_basket_value");
  const averageBasketQuantity = dashboard.kpis.find((kpi) => kpi.code === "average_basket_quantity");
  const leadingBasketBand = [...dashboard.basket_value_distribution].sort(
    (left, right) => toNumber(right.revenue) - toNumber(left.revenue),
  )[0];
  const growingCategories = dashboard.category_trends.filter(
    (row) => toNumber(row.revenue_change) > 0,
  ).length;
  const decliningCategories = dashboard.category_trends.filter(
    (row) => toNumber(row.revenue_change) < 0,
  ).length;
  const vatCoverage = toNumber(dashboard.vat_readiness.coverage_percent);
  const concentrationTone = leaderShare >= 55 ? "warning" : leaderShare >= 35 ? "neutral" : "success";
  const peakTone = strongestSlotShare >= 25 ? "warning" : strongestSlotShare > 0 ? "success" : "neutral";
  const vatTone = vatCoverage >= 98 ? "success" : vatCoverage > 0 ? "warning" : "neutral";

  const signals: BusinessSpecificMetric[] = [
    {
      label: "Vezető kategória",
      value: leader?.label ?? "-",
      description: leader
        ? `${formatMoney(leader.revenue)} bár/fogyasztási bevétel, ${formatOptionalPercent(leaderShare)} részesedés.`
        : "Nincs még kategóriaforgalom az aktuális időszakban.",
      tone: concentrationTone,
    },
    {
      label: "Top 3 koncentráció",
      value: formatOptionalPercent(topThreeShare),
      description:
        topThreeShare >= 75
          ? "A bevétel erősen néhány kategóriára támaszkodik, ezért készletben és pultban ez a fókusz."
          : "A fogyasztási bevétel több kategória között oszlik meg.",
      tone: topThreeShare >= 75 ? "warning" : "success",
    },
    {
      label: "Csúcsterhelés",
      value: strongestSlot
        ? `${getWeekdayLabel(strongestSlot.weekday)} ${formatHeatmapHour(strongestSlot.hour)}`
        : "-",
      description: strongestSlot
        ? `${formatMoney(strongestSlot.revenue)} forgalom ebben az órában, ${formatOptionalPercent(strongestSlotShare)} idősáv-súly.`
        : "Nincs még órás forgalmi hőtérkép adat.",
      tone: peakTone,
    },
    {
      label: "ÁFA readiness",
      value: formatOptionalPercent(vatCoverage),
      description:
        dashboard.vat_readiness.missing_row_count > 0
          ? `${dashboard.vat_readiness.missing_row_count} POS sorhoz hiányzik termék ÁFA kulcs.`
          : "A Flow POS bevétel ÁFA bontása a terméktörzs alapján lefedett.",
      tone: vatTone,
    },
  ];

  return (
    <Card
      tone="secondary"
      hoverable
      className="flow-consumption-control-card"
      eyebrow="Flow POS kontroll"
      title="Bárbevétel és fogyasztási viselkedés"
      subtitle="POS-only pénzügyi kép: jegyadat nélkül, event rangsor nélkül"
      count={totalRevenue > 0 ? formatMoney(totalRevenue) : "nincs forgalom"}
    >
      <div className="flow-consumption-grid">
        {signals.map((signal) => (
          <article className={`business-focus-item ${signal.tone}`} key={signal.label}>
            <span>{signal.label}</span>
            <strong>{signal.value}</strong>
            <small>{signal.description}</small>
          </article>
        ))}
      </div>

      <div className="flow-consumption-decision-list">
        <article className="flow-consumption-decision-row">
          <span>Kosárprofil</span>
          <strong>{averageBasket ? formatMoney(averageBasket.value) : "-"}</strong>
          <small>
            Átlagkosár, {averageBasketQuantity ? `${formatNumber(averageBasketQuantity.value)} tétel/nyugta` : "mennyiségi adat nélkül"}.
            Domináns sáv: {leadingBasketBand ? formatBasketValueBand(leadingBasketBand.label) : "-"}.
          </small>
        </article>
        <article className="flow-consumption-decision-row">
          <span>Kategóriamozgás</span>
          <strong>{growingCategories} nő / {decliningCategories} csökken</strong>
          <small>
            Előző azonos időszakhoz mért POS kategóriatrend. Ez a Flow üzleti dashboardban keresleti ritmus,
            nem event teljesítmény.
          </small>
        </article>
        <article className="flow-consumption-decision-row">
          <span>Adatértelmezés</span>
          <strong>Jegy nélkül</strong>
          <small>
            A fenti mutatók kizárólag kassza fogyasztási sorokból készülnek; a jegybevétel event ticket actualként kerül mellé.
          </small>
        </article>
      </div>
    </Card>
  );
}

export function DashboardFlowFinancialEventImpact({
  events,
  performances,
  isLoading,
}: {
  events: EventRecord[];
  performances: EventPerformance[];
  isLoading: boolean;
}) {
  const eventById = new Map(events.map((event) => [event.id, event]));
  const eventRows = performances.filter(
    (performance) => eventById.get(performance.event_id)?.status !== "cancelled",
  );
  const summary = eventRows.reduce(
    (acc, performance) => ({
      ticketRevenue: acc.ticketRevenue + toNumber(performance.ticket_revenue_gross),
      barRevenue: acc.barRevenue + toNumber(performance.bar_revenue_gross),
      performerShare: acc.performerShare + toNumber(performance.performer_share_amount),
      ownRevenue: acc.ownRevenue + toNumber(performance.own_revenue),
      operatingCost: acc.operatingCost + toNumber(performance.operating_cost_gross),
      platformFee: acc.platformFee + toNumber(performance.platform_fee_gross),
      profit: acc.profit + toNumber(performance.event_profit_lite),
      actualTicketCount:
        acc.actualTicketCount + (performance.ticket_revenue_source === "ticket_actual" ? 1 : 0),
      missingTicketActualCount:
        acc.missingTicketActualCount + (performance.ticket_revenue_source !== "ticket_actual" ? 1 : 0),
      profitableCount:
        acc.profitableCount + (performance.profit_status === "profitable" ? 1 : 0),
      lossCount: acc.lossCount + (performance.profit_status === "loss" ? 1 : 0),
    }),
    {
      ticketRevenue: 0,
      barRevenue: 0,
      performerShare: 0,
      ownRevenue: 0,
      operatingCost: 0,
      platformFee: 0,
      profit: 0,
      actualTicketCount: 0,
      missingTicketActualCount: 0,
      profitableCount: 0,
      lossCount: 0,
    },
  );
  const averageProfit =
    eventRows.length > 0 ? summary.profit / eventRows.length : 0;
  const totalRevenue = summary.ticketRevenue + summary.barRevenue;
  const ticketShare = totalRevenue > 0 ? (summary.ticketRevenue / totalRevenue) * 100 : 0;
  const barShare = totalRevenue > 0 ? (summary.barRevenue / totalRevenue) * 100 : 0;
  const profitMargin = summary.ownRevenue > 0 ? (summary.profit / summary.ownRevenue) * 100 : 0;
  const costRatio = summary.ownRevenue > 0 ? (summary.operatingCost / summary.ownRevenue) * 100 : 0;
  const ticketActualShare =
    eventRows.length > 0 ? (summary.actualTicketCount / eventRows.length) * 100 : 0;

  return (
    <Card
      tone="rainbow"
      hoverable
      className="flow-event-performance-card"
      eyebrow="Flow pénzügyi event réteg"
      title="Event hatás a Flow eredményre"
      subtitle="Összesített ticket/bar bevételi mix, költségarány és ticket actual lefedettség"
      count={`${eventRows.length} event`}
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
          Event profit
        </span>
        <span>
          <strong>{formatMoney(summary.operatingCost)}</strong>
          Event költség
        </span>
      </div>

      <div className="flow-event-highlight">
        <article className="business-focus-item primary">
          <span>Saját event bevétel</span>
          <strong>{formatMoney(summary.ownRevenue)}</strong>
          <small>Megtartott jegybevétel plusz eventhez kapcsolt bárbevétel.</small>
        </article>
        <article className={averageProfit >= 0 ? "business-focus-item success" : "business-focus-item warning"}>
          <span>Átlagos event profit</span>
          <strong>{formatMoney(averageProfit)}</strong>
          <small>Összesített pénzügyi benchmark, nem eventenkénti rangsor.</small>
        </article>
        <article className={summary.lossCount > 0 ? "business-focus-item warning" : "business-focus-item success"}>
          <span>Nyereséges / veszteséges</span>
          <strong>{summary.profitableCount} / {summary.lossCount}</strong>
          <small>Az event dashboarddal azonos read-model profit státusz alapján.</small>
        </article>
        <article className={costRatio >= 50 ? "business-focus-item warning" : "business-focus-item neutral"}>
          <span>Költségarány</span>
          <strong>{formatOptionalPercent(costRatio)}</strong>
          <small>Event költség / saját event bevétel. Platform díj: {formatMoney(summary.platformFee)}.</small>
        </article>
      </div>

      {eventRows.length > 0 ? (
        <div className="flow-event-financial-mix">
          <div>
            <span>Jegy / bár pénzügyi mix</span>
            <strong>
              Jegy {formatOptionalPercent(ticketShare)} · Bár {formatOptionalPercent(barShare)}
            </strong>
            <span className="flow-event-split">
              <span style={{ width: `${ticketShare}%` }} />
              <span style={{ width: `${barShare}%` }} />
            </span>
          </div>
          <div>
            <span>Event profit margin</span>
            <strong>{formatOptionalPercent(profitMargin)}</strong>
            <small>Event profit / saját event bevétel.</small>
          </div>
          <div>
            <span>Ticket actual lefedettség</span>
            <strong>{formatOptionalPercent(ticketActualShare)}</strong>
            <small>{summary.actualTicketCount} actual · {summary.missingTicketActualCount} ticket actual hiányzik.</small>
          </div>
        </div>
      ) : (
        <p className="empty-message">
          Nincs eventhez kapcsolt pénzügyi réteg az időszakban. A Flow alapforgalmi KPI-k ettől még a POS
          actual adatokból számolódnak.
        </p>
      )}

    </Card>
  );
}

export function DashboardFlowForecastEvent({
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

