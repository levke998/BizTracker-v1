import type { Dispatch, SetStateAction } from "react";

import type { VatRate } from "../../masterData/types/masterData";
import type { RecipeCostSummary } from "../types/production";
import {
  formatMoney,
  formatNumber,
  formatQuantity,
  formatStockStatus,
  getStockStatusClass,
} from "./recipesPageView";

type RecipeIngredientsTableProps = {
  selectedRecipe: RecipeCostSummary;
  vatRates: VatRate[];
  quickCostInputs: Record<string, string>;
  setQuickCostInputs: Dispatch<SetStateAction<Record<string, string>>>;
  quickStockInputs: Record<string, string>;
  setQuickStockInputs: Dispatch<SetStateAction<Record<string, string>>>;
  quickVatInputs: Record<string, string>;
  setQuickVatInputs: Dispatch<SetStateAction<Record<string, string>>>;
  quickUpdatePending: boolean;
  onQuickUpdateIngredientCost: (inventoryItemId: string) => void;
  onQuickUpdateIngredientStock: (inventoryItemId: string) => void;
  onQuickUpdateIngredientVat: (inventoryItemId: string) => void;
};

export function RecipeIngredientsTable({
  selectedRecipe,
  vatRates,
  quickCostInputs,
  setQuickCostInputs,
  quickStockInputs,
  setQuickStockInputs,
  quickVatInputs,
  setQuickVatInputs,
  quickUpdatePending,
  onQuickUpdateIngredientCost,
  onQuickUpdateIngredientStock,
  onQuickUpdateIngredientVat,
}: RecipeIngredientsTableProps) {
  return (
    <div className="table-scroll">
      <table className="data-table details-table">
        <thead>
          <tr>
            <th>Osszetevo</th>
            <th>Mennyiseg</th>
            <th>Ar</th>
            <th>Koltseg</th>
            <th>AFA / brutto</th>
            <th>Keszlet</th>
          </tr>
        </thead>
        <tbody>
          {selectedRecipe.ingredients.map((ingredient) => (
            <tr key={ingredient.inventory_item_id}>
              <td>{ingredient.inventory_item_name}</td>
              <td>{formatQuantity(ingredient.quantity, ingredient.uom_code)}</td>
              <td>
                {formatMoney(ingredient.unit_cost)}
                {ingredient.unit_cost === null ? (
                  <div className="production-quick-fix">
                    <input
                      className="field-input"
                      type="number"
                      min="0"
                      step="0.01"
                      value={quickCostInputs[ingredient.inventory_item_id] ?? ""}
                      onChange={(event) =>
                        setQuickCostInputs((current) => ({
                          ...current,
                          [ingredient.inventory_item_id]: event.target.value,
                        }))
                      }
                      placeholder="Ft / egyseg"
                    />
                    <button
                      type="button"
                      className="text-button"
                      onClick={() => onQuickUpdateIngredientCost(ingredient.inventory_item_id)}
                      disabled={quickUpdatePending}
                    >
                      Ar mentese
                    </button>
                  </div>
                ) : null}
              </td>
              <td>{formatMoney(ingredient.estimated_cost)}</td>
              <td>
                <div className="metric-stack">
                  <span>
                    {ingredient.vat_rate_percent
                      ? `${formatNumber(ingredient.vat_rate_percent)}%`
                      : "AFA kulcs hianyzik"}
                  </span>
                  <span>AFA: {formatMoney(ingredient.estimated_vat_amount)}</span>
                  <span>Brutto: {formatMoney(ingredient.estimated_gross_cost)}</span>
                </div>
                {ingredient.vat_rate_percent === null ? (
                  <div className="production-quick-fix">
                    <select
                      className="field-input"
                      value={quickVatInputs[ingredient.inventory_item_id] ?? ""}
                      onChange={(event) =>
                        setQuickVatInputs((current) => ({
                          ...current,
                          [ingredient.inventory_item_id]: event.target.value,
                        }))
                      }
                    >
                      <option value="">AFA kulcs</option>
                      {vatRates.map((vatRate) => (
                        <option key={vatRate.id} value={vatRate.id}>
                          {vatRate.name}
                        </option>
                      ))}
                    </select>
                    <button
                      type="button"
                      className="text-button"
                      onClick={() => onQuickUpdateIngredientVat(ingredient.inventory_item_id)}
                      disabled={quickUpdatePending || vatRates.length === 0}
                    >
                      AFA mentese
                    </button>
                  </div>
                ) : null}
              </td>
              <td>
                <span className={getStockStatusClass(ingredient.stock_status)}>
                  {formatStockStatus(ingredient.stock_status)}
                </span>
                <div className="metric-stack">
                  <span>
                    Keszlet:{" "}
                    {formatQuantity(
                      ingredient.estimated_stock_quantity,
                      ingredient.item_uom_code,
                    )}
                  </span>
                </div>
                {ingredient.stock_status === "missing" ||
                ingredient.stock_status === "insufficient" ||
                ingredient.stock_status === "unknown" ? (
                  <div className="production-quick-fix">
                    <input
                      className="field-input"
                      type="number"
                      min="0"
                      step="0.001"
                      value={quickStockInputs[ingredient.inventory_item_id] ?? ""}
                      onChange={(event) =>
                        setQuickStockInputs((current) => ({
                          ...current,
                          [ingredient.inventory_item_id]: event.target.value,
                        }))
                      }
                      placeholder="Becsult menny."
                    />
                    <button
                      type="button"
                      className="text-button"
                      onClick={() => onQuickUpdateIngredientStock(ingredient.inventory_item_id)}
                      disabled={quickUpdatePending}
                    >
                      Keszlet mentese
                    </button>
                  </div>
                ) : null}
              </td>
            </tr>
          ))}
          {selectedRecipe.ingredients.length === 0 ? (
            <tr>
              <td colSpan={6}>Ehhez a termekhez meg nincs receptsor.</td>
            </tr>
          ) : null}
        </tbody>
      </table>
    </div>
  );
}
