import type { RecipeCostSummary } from "../types/production";
import {
  formatCostStatus,
  formatMoney,
  formatReadinessStatus,
  formatTaxStatus,
  getCostStatusClass,
  getNextAction,
  getReadinessClass,
} from "./recipesPageView";

type RecipesListPanelProps = {
  visibleRecipes: RecipeCostSummary[];
  selectedProductId: string | null;
  onSelectProductId: (productId: string) => void;
};

export function RecipesListPanel({
  visibleRecipes,
  selectedProductId,
  onSelectProductId,
}: RecipesListPanelProps) {
  return (
    <section className="panel production-recipes-list-panel">
      <div className="panel-header">
        <h2>Recept readiness</h2>
        <span className="panel-count">{visibleRecipes.length} sor</span>
      </div>
      <div className="table-scroll">
        <table className="data-table details-table">
          <thead>
            <tr>
              <th>Termek</th>
              <th>Readiness</th>
              <th>Koltseg</th>
              <th>Osszetevo</th>
              <th>Teendo</th>
            </tr>
          </thead>
          <tbody>
            {visibleRecipes.map((row) => (
              <tr
                key={row.product_id}
                className={
                  selectedProductId === row.product_id
                    ? "production-recipe-row production-recipe-row-selected"
                    : "production-recipe-row"
                }
                onClick={() => onSelectProductId(row.product_id)}
              >
                <td>
                  <strong>{row.product_name}</strong>
                  <div className="metric-stack">
                    <span>{row.category_name ?? "Kategoria nelkul"}</span>
                    <span>{row.recipe_name ?? "Nincs aktiv recept"}</span>
                  </div>
                </td>
                <td>
                  <span className={getReadinessClass(row.readiness_status)}>
                    {formatReadinessStatus(row.readiness_status)}
                  </span>
                </td>
                <td>
                  <span className={getCostStatusClass(row.cost_status)}>
                    {formatCostStatus(row.cost_status)}
                  </span>
                  <div className="metric-stack">
                    <span>Egys.: {formatMoney(row.unit_cost)}</span>
                    <span>Brutto egys.: {formatMoney(row.unit_gross_cost)}</span>
                    <span>Ismert: {formatMoney(row.known_total_cost)}</span>
                    <span>{formatTaxStatus(row.tax_status)}</span>
                  </div>
                </td>
                <td>{row.ingredients.length}</td>
                <td>{getNextAction(row)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}
