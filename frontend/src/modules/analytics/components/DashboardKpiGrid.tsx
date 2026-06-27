import { Card } from "../../../shared/components/ui/Card";
import type { DashboardKpi } from "../types/analytics";
import {
  formatAmountMarker,
  getKpiLabel,
  getKpiSecondary,
  getKpiTone,
  getKpiValue,
  getVisibleKpis,
  kpiHelp,
} from "./dashboardView";

export function DashboardKpiGrid({ kpis }: { kpis: DashboardKpi[] }) {
  return (
    <div className="kpi-grid">
      {getVisibleKpis(kpis).map((kpi) => {
        const marker = formatAmountMarker(kpi.amount_basis, kpi.amount_origin);
        const secondary = getKpiSecondary(kpi, kpis);
        return (
          <Card
            key={kpi.code}
            tone={getKpiTone(kpi.code)}
            className="kpi-card"
            hoverable
            eyebrow={getKpiLabel(kpi)}
            data-tooltip={kpiHelp[kpi.code] ?? kpi.label}
          >
            <span className="kpi-value">{getKpiValue(kpi)}</span>
            {marker ? <span className="kpi-caption">{marker}</span> : null}
            {secondary ? <span className="kpi-caption">{secondary}</span> : null}
          </Card>
        );
      })}
    </div>
  );
}
