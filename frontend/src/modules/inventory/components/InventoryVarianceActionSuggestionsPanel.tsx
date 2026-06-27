import { Link } from "react-router-dom";

import { routes } from "../../../shared/constants/routes";
import type { InventoryVarianceActionSuggestion } from "../types/inventory";

type InventoryVarianceActionSuggestionsPanelProps = {
  suggestions: InventoryVarianceActionSuggestion[];
  isLoading: boolean;
  error: Error | null;
  canUpdateReviews: boolean;
  updatingSuggestionId: string | null;
  focusedSuggestionId?: string;
  onSelectInventoryItem: (inventoryItemId: string) => void;
  onUpdateReview: (
    suggestion: InventoryVarianceActionSuggestion,
    status: "open" | "resolved",
  ) => void;
};

function formatMoney(value: string | null) {
  if (value === null) {
    return "-";
  }
  return new Intl.NumberFormat("hu-HU", {
    style: "currency",
    currency: "HUF",
    maximumFractionDigits: 0,
  }).format(Number(value));
}

function formatSeverity(value: InventoryVarianceActionSuggestion["severity"]) {
  const labels: Record<InventoryVarianceActionSuggestion["severity"], string> = {
    critical: "Kritikus",
    high: "Magas",
    medium: "Kozepes",
    low: "Alacsony",
    info: "Info",
  };
  return labels[value];
}

function getSeverityClass(value: InventoryVarianceActionSuggestion["severity"]) {
  if (value === "critical" || value === "high") {
    return "status-pill status-pill-danger";
  }
  if (value === "medium" || value === "low") {
    return "status-pill status-pill-warning";
  }
  return "status-pill status-pill-success";
}

function formatReviewStatus(value: InventoryVarianceActionSuggestion["review_status"]) {
  return value === "resolved" ? "Lezarva" : "Nyitott";
}

function getReviewStatusClass(value: InventoryVarianceActionSuggestion["review_status"]) {
  return value === "resolved"
    ? "status-pill status-pill-success"
    : "status-pill status-pill-warning";
}

function getActionTargetPath(
  suggestion: InventoryVarianceActionSuggestion,
) {
  const paths: Record<
    NonNullable<InventoryVarianceActionSuggestion["action_target_type"]>,
    string
  > = {
    catalog_ingredients: routes.catalogIngredients,
    production_recipes: routes.productionRecipes,
    imports: routes.imports,
    procurement_invoices: routes.procurementInvoices,
    inventory_theoretical_stock: routes.inventoryTheoreticalStock,
  };
  if (!suggestion.action_target_type) {
    return null;
  }
  const path = paths[suggestion.action_target_type];
  const params = new URLSearchParams(suggestion.action_target_params);
  const queryString = params.toString();
  return queryString ? `${path}?${queryString}` : path;
}

export function InventoryVarianceActionSuggestionsPanel({
  suggestions,
  isLoading,
  error,
  canUpdateReviews,
  updatingSuggestionId,
  focusedSuggestionId = "",
  onSelectInventoryItem,
  onUpdateReview,
}: InventoryVarianceActionSuggestionsPanelProps) {
  const criticalCount = suggestions.filter(
    (suggestion) => suggestion.severity === "critical",
  ).length;
  const actionableCount = suggestions.filter(
    (suggestion) =>
      suggestion.severity !== "info" && suggestion.review_status !== "resolved",
  ).length;
  const resolvedCount = suggestions.filter(
    (suggestion) => suggestion.review_status === "resolved",
  ).length;
  const totalEstimatedImpact = suggestions.reduce(
    (total, suggestion) => total + Number(suggestion.estimated_impact_value ?? 0),
    0,
  );

  return (
    <section className="panel">
      <div className="panel-header">
        <h2>Inventory akciojavaslatok</h2>
        <span className="panel-count">{suggestions.length}</span>
      </div>

      <div className="finance-summary-grid">
        <article className="finance-summary-card">
          <span>Nyitott akcio</span>
          <strong>{actionableCount}</strong>
        </article>
        <article className="finance-summary-card">
          <span>Kritikus jelzes</span>
          <strong>{criticalCount}</strong>
        </article>
        <article className="finance-summary-card">
          <span>Lezart akcio</span>
          <strong>{resolvedCount}</strong>
        </article>
        <article className="finance-summary-card">
          <span>Becsult erintett ertek</span>
          <strong>{formatMoney(String(totalEstimatedImpact))}</strong>
        </article>
      </div>

      <p className="info-message">
        A panel a periodus-osszehasonlitasbol, top vesztesegu tetelekbol es ok-kodokbol
        keszit priorizalt kovetkezo lepest. Nem import-forrasra epul, hanem a mar rogzitett
        keszletkorrekciokra.
      </p>
      {!canUpdateReviews ? (
        <p className="section-note">
          Lezarashoz valassz vallalkozast; osszesitett nezetben csak olvashatoak a
          javaslatok.
        </p>
      ) : null}

      {error ? <p className="error-message">{error.message}</p> : null}
      {isLoading ? <p className="info-message">Akciojavaslatok betoltese...</p> : null}
      {!isLoading && suggestions.length === 0 ? (
        <p className="empty-message">Nincs megjelenitheto inventory akciojavaslat.</p>
      ) : null}

      {suggestions.length > 0 ? (
        <div className="table-wrap">
          <table className="data-table">
            <thead>
              <tr>
                <th>Prioritas</th>
                <th>Javaslat</th>
                <th>Indoklas</th>
                <th>Kovetkezo lepes</th>
                <th>Keszletelem</th>
                <th>Becsult hatas</th>
                <th>Allapot</th>
                <th>Naplo</th>
                <th>Javitas</th>
                <th>Munkalista</th>
              </tr>
            </thead>
            <tbody>
              {suggestions.map((suggestion) => {
                const actionTargetPath = getActionTargetPath(suggestion);
                const isFocusedSuggestion = focusedSuggestionId === suggestion.id;

                return (
                  <tr
                    className={
                      isFocusedSuggestion ? "action-suggestion-focused-row" : undefined
                    }
                    key={suggestion.id}
                  >
                    <td>
                      <span className={getSeverityClass(suggestion.severity)}>
                        {formatSeverity(suggestion.severity)}
                      </span>
                    </td>
                    <td>{suggestion.title}</td>
                    <td>{suggestion.rationale}</td>
                    <td>{suggestion.recommended_action}</td>
                    <td>{suggestion.inventory_item_name ?? "-"}</td>
                    <td>{formatMoney(suggestion.estimated_impact_value)}</td>
                    <td>
                      <span className={getReviewStatusClass(suggestion.review_status)}>
                        {formatReviewStatus(suggestion.review_status)}
                      </span>
                    </td>
                    <td>
                      {suggestion.inventory_item_id ? (
                        <button
                          className="secondary-button inventory-audit-button"
                          type="button"
                          onClick={() => {
                            if (suggestion.inventory_item_id) {
                              onSelectInventoryItem(suggestion.inventory_item_id);
                            }
                          }}
                        >
                          Reszletek
                        </button>
                      ) : (
                        "-"
                      )}
                    </td>
                    <td>
                      {actionTargetPath ? (
                        <Link
                          className="secondary-button inventory-audit-button"
                          to={actionTargetPath}
                        >
                          {suggestion.action_target_label ?? "Megnyitas"}
                        </Link>
                      ) : (
                        "-"
                      )}
                    </td>
                    <td>
                      {suggestion.review_status === "resolved" ? (
                        <button
                          className="secondary-button inventory-audit-button"
                          type="button"
                          disabled={!canUpdateReviews || updatingSuggestionId === suggestion.id}
                          onClick={() => onUpdateReview(suggestion, "open")}
                        >
                          Ujranyitas
                        </button>
                      ) : (
                        <button
                          className="secondary-button inventory-audit-button"
                          type="button"
                          disabled={!canUpdateReviews || updatingSuggestionId === suggestion.id}
                          onClick={() => onUpdateReview(suggestion, "resolved")}
                        >
                          Lezaras
                        </button>
                      )}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      ) : null}
    </section>
  );
}
