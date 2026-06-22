import type { Dispatch, SetStateAction } from "react";

import type { CatalogIngredient } from "../../catalog/types/catalog";
import type { UnitOfMeasure, VatRate } from "../../masterData/types/masterData";
import type { RecipeCostSummary } from "../types/production";
import { RecipeEditorForm } from "./RecipeEditorForm";
import { RecipeIngredientsTable } from "./RecipeIngredientsTable";
import {
  formatMoney,
  formatQuantity,
  formatReadinessStatus,
  formatTaxStatus,
  getNextAction,
  getReadinessClass,
  type RecipeFormLine,
  type RecipeFormState,
} from "./recipesPageView";

type RecipeDetailPanelProps = {
  selectedRecipe: RecipeCostSummary | null;
  templateRecipes: RecipeCostSummary[];
  selectedTemplateProductId: string;
  setSelectedTemplateProductId: Dispatch<SetStateAction<string>>;
  formMessage: string;
  formError: string;
  isEditingSelected: boolean;
  form: RecipeFormState | null;
  units: UnitOfMeasure[];
  ingredients: CatalogIngredient[];
  fallbackUnitId: string;
  saveRecipePending: boolean;
  vatRates: VatRate[];
  quickCostInputs: Record<string, string>;
  setQuickCostInputs: Dispatch<SetStateAction<Record<string, string>>>;
  quickStockInputs: Record<string, string>;
  setQuickStockInputs: Dispatch<SetStateAction<Record<string, string>>>;
  quickVatInputs: Record<string, string>;
  setQuickVatInputs: Dispatch<SetStateAction<Record<string, string>>>;
  quickUpdatePending: boolean;
  onStartEditing: (row: RecipeCostSummary) => void;
  onLoadSelectedTemplate: (target: RecipeCostSummary) => void;
  onFormChange: (next: RecipeFormState) => void;
  onSubmitRecipeForm: React.FormEventHandler<HTMLFormElement>;
  onUpdateIngredientLine: (index: number, patch: Partial<RecipeFormLine>) => void;
  onAddIngredientLine: () => void;
  onRemoveIngredientLine: (index: number) => void;
  onCancelEditing: () => void;
  onQuickUpdateIngredientCost: (inventoryItemId: string) => void;
  onQuickUpdateIngredientStock: (inventoryItemId: string) => void;
  onQuickUpdateIngredientVat: (inventoryItemId: string) => void;
};

export function RecipeDetailPanel({
  selectedRecipe,
  templateRecipes,
  selectedTemplateProductId,
  setSelectedTemplateProductId,
  formMessage,
  formError,
  isEditingSelected,
  form,
  units,
  ingredients,
  fallbackUnitId,
  saveRecipePending,
  vatRates,
  quickCostInputs,
  setQuickCostInputs,
  quickStockInputs,
  setQuickStockInputs,
  quickVatInputs,
  setQuickVatInputs,
  quickUpdatePending,
  onStartEditing,
  onLoadSelectedTemplate,
  onFormChange,
  onSubmitRecipeForm,
  onUpdateIngredientLine,
  onAddIngredientLine,
  onRemoveIngredientLine,
  onCancelEditing,
  onQuickUpdateIngredientCost,
  onQuickUpdateIngredientStock,
  onQuickUpdateIngredientVat,
}: RecipeDetailPanelProps) {
  return (
    <aside className="panel production-recipe-detail-panel">
      <div className="panel-header">
        <h2>{selectedRecipe?.product_name ?? "Nincs kivalasztott termek"}</h2>
        {selectedRecipe ? (
          <span className={getReadinessClass(selectedRecipe.readiness_status)}>
            {formatReadinessStatus(selectedRecipe.readiness_status)}
          </span>
        ) : null}
      </div>

      {selectedRecipe ? (
        <>
          <div className="production-recipe-facts">
            <span>
              <small>Recept</small>
              <strong>{selectedRecipe.recipe_name ?? "Hianyzik"}</strong>
            </span>
            <span>
              <small>Aktiv verzio</small>
              <strong>{selectedRecipe.version_no ? `v${selectedRecipe.version_no}` : "Nincs"}</strong>
            </span>
            <span>
              <small>Kihozatal</small>
              <strong>
                {formatQuantity(selectedRecipe.yield_quantity, selectedRecipe.yield_uom_code)}
              </strong>
            </span>
            <span>
              <small>Teljes koltseg</small>
              <strong>{formatMoney(selectedRecipe.total_cost)}</strong>
            </span>
            <span>
              <small>AFA</small>
              <strong>{formatMoney(selectedRecipe.total_vat_amount)}</strong>
            </span>
            <span>
              <small>Brutto koltseg</small>
              <strong>{formatMoney(selectedRecipe.total_gross_cost)}</strong>
            </span>
            <span>
              <small>Egysegkoltseg</small>
              <strong>{formatMoney(selectedRecipe.unit_cost)}</strong>
            </span>
            <span>
              <small>Brutto egysegkoltseg</small>
              <strong>{formatMoney(selectedRecipe.unit_gross_cost)}</strong>
            </span>
            <span>
              <small>AFA statusz</small>
              <strong>{formatTaxStatus(selectedRecipe.tax_status)}</strong>
            </span>
          </div>

          <div className="production-recipe-action">
            <strong>{getNextAction(selectedRecipe)}</strong>
            <button
              type="button"
              className="text-button"
              onClick={() => onStartEditing(selectedRecipe)}
            >
              Recept szerkesztese
            </button>
          </div>

          {(selectedRecipe.readiness_status === "missing_recipe" ||
            selectedRecipe.readiness_status === "empty_recipe") &&
          templateRecipes.some((row) => row.product_id !== selectedRecipe.product_id) ? (
            <div className="production-template-starter">
              <label className="field">
                <span>Sablon recept</span>
                <select
                  className="field-input"
                  value={selectedTemplateProductId}
                  onChange={(event) => setSelectedTemplateProductId(event.target.value)}
                >
                  <option value="">Valassz sablont</option>
                  {templateRecipes
                    .filter((row) => row.product_id !== selectedRecipe.product_id)
                    .map((row) => (
                      <option key={row.product_id} value={row.product_id}>
                        {row.product_name} ({row.ingredients.length} osszetevo)
                      </option>
                    ))}
                </select>
              </label>
              <button
                type="button"
                className="text-button"
                onClick={() => onLoadSelectedTemplate(selectedRecipe)}
              >
                Sablon betoltese
              </button>
            </div>
          ) : null}

          {formMessage ? <div className="success-banner">{formMessage}</div> : null}
          {formError ? <div className="error-banner">{formError}</div> : null}

          {isEditingSelected && form ? (
            <RecipeEditorForm
              selectedRecipe={selectedRecipe}
              form={form}
              units={units}
              ingredients={ingredients}
              fallbackUnitId={fallbackUnitId}
              savePending={saveRecipePending}
              onFormChange={onFormChange}
              onUpdateIngredientLine={onUpdateIngredientLine}
              onAddIngredientLine={onAddIngredientLine}
              onRemoveIngredientLine={onRemoveIngredientLine}
              onCancel={onCancelEditing}
              onSubmit={onSubmitRecipeForm}
            />
          ) : null}

          <RecipeIngredientsTable
            selectedRecipe={selectedRecipe}
            vatRates={vatRates}
            quickCostInputs={quickCostInputs}
            setQuickCostInputs={setQuickCostInputs}
            quickStockInputs={quickStockInputs}
            setQuickStockInputs={setQuickStockInputs}
            quickVatInputs={quickVatInputs}
            setQuickVatInputs={setQuickVatInputs}
            quickUpdatePending={quickUpdatePending}
            onQuickUpdateIngredientCost={onQuickUpdateIngredientCost}
            onQuickUpdateIngredientStock={onQuickUpdateIngredientStock}
            onQuickUpdateIngredientVat={onQuickUpdateIngredientVat}
          />
        </>
      ) : (
        <p className="muted-text">A szurok alapjan nincs megjelenitheto receptsor.</p>
      )}
    </aside>
  );
}
