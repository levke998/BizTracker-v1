import { Button } from "../../../shared/components/ui/Button";
import type {
  DashboardPeriodPreset,
  DashboardScope,
} from "../types/analytics";
import { periodOptions, scopeOptions } from "./dashboardView";

export type DashboardViewMode = "overview" | "professional";

export function DashboardHeaderControls({
  scope,
  setScope,
  period,
  setPeriod,
  startDate,
  setStartDate,
  endDate,
  setEndDate,
  onExport,
  canExport,
  viewMode,
  setViewMode,
}: {
  scope: DashboardScope;
  setScope: (value: DashboardScope) => void;
  period: DashboardPeriodPreset;
  setPeriod: (value: DashboardPeriodPreset) => void;
  startDate: string;
  setStartDate: (value: string) => void;
  endDate: string;
  setEndDate: (value: string) => void;
  onExport: () => void;
  canExport: boolean;
  viewMode: DashboardViewMode;
  setViewMode: (value: DashboardViewMode) => void;
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

      <div className="business-segmented-control topbar-segmented-control">
        {[
          { value: "overview" as const, label: "Áttekintés" },
          { value: "professional" as const, label: "Professzionális" },
        ].map((option) => (
          <button
            key={option.value}
            type="button"
            className={
              viewMode === option.value
                ? "filter-chip filter-chip-active"
                : "filter-chip"
            }
            onClick={() => setViewMode(option.value)}
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

        <Button variant="secondary" onClick={onExport} disabled={!canExport}>
          Export
        </Button>
      </div>
    </>
  );
}
