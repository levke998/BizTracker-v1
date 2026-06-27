import { useState } from "react";

import { Card } from "../../../shared/components/ui/Card";
import type {
  DashboardProductRiskRow,
  DashboardStockRiskRow,
} from "../types/analytics";
import { formatMoney, formatNumber, toNumber } from "./dashboardView";

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

function formatInventoryItemType(value: string) {
  const labels: Record<string, string> = {
    raw_material: "Alapanyag",
    packaging: "Csomagolóanyag",
    finished_good: "Késztermék",
    semi_finished: "Félkész termék",
  };
  return labels[value] ?? value;
}

export function DashboardRiskOverview({
  productRows,
  stockRows,
}: {
  productRows: DashboardProductRiskRow[];
  stockRows: DashboardStockRiskRow[];
}) {
  const [selectedRiskKey, setSelectedRiskKey] = useState<string | null>(null);
  const productDangerCount = productRows.filter(
    (row) => row.risk_level === "danger",
  ).length;
  const stockDangerCount = stockRows.filter(
    (row) => row.risk_level === "danger",
  ).length;
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
  const selectedRisk =
    riskItems.find((row) => row.key === selectedRiskKey) ?? null;

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
                  ? `risk-overview-row risk-overview-row-active ${
                      isDanger ? "danger" : "warning"
                    }`
                  : `risk-overview-row ${isDanger ? "danger" : "warning"}`
              }
              onClick={() => setSelectedRiskKey(isSelected ? null : row.key)}
            >
              <span
                className={
                  isDanger
                    ? "risk-overview-level danger"
                    : "risk-overview-level warning"
                }
              >
                {isDanger ? "!" : "?"}
              </span>
              <span className="risk-overview-content">
                <span className="risk-overview-heading">
                  <strong>{row.title}</strong>
                  <small>
                    {row.kind === "product" ? "Termék" : "Készlet"} ·{" "}
                    {row.subtitle}
                  </small>
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
        <p className="empty-message">
          Nincs kiemelt termék- vagy készletkockázat.
        </p>
      ) : null}
    </Card>
  );
}
