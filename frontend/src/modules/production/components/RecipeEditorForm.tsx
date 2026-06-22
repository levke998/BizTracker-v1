import type { FormEventHandler } from "react";

import type { CatalogIngredient } from "../../catalog/types/catalog";
import type { UnitOfMeasure } from "../../masterData/types/masterData";
import type { RecipeCostSummary } from "../types/production";
import {
  formatNextVersion,
  ingredientDefaultUnitId,
  type RecipeFormLine,
  type RecipeFormState,
} from "./recipesPageView";

type RecipeEditorFormProps = {
  selectedRecipe: RecipeCostSummary;
  form: RecipeFormState;
  units: UnitOfMeasure[];
  ingredients: CatalogIngredient[];
  fallbackUnitId: string;
  savePending: boolean;
  onFormChange: (next: RecipeFormState) => void;
  onUpdateIngredientLine: (index: number, patch: Partial<RecipeFormLine>) => void;
  onAddIngredientLine: () => void;
  onRemoveIngredientLine: (index: number) => void;
  onCancel: () => void;
  onSubmit: FormEventHandler<HTMLFormElement>;
};

export function RecipeEditorForm({
  selectedRecipe,
  form,
  units,
  ingredients,
  fallbackUnitId,
  savePending,
  onFormChange,
  onUpdateIngredientLine,
  onAddIngredientLine,
  onRemoveIngredientLine,
  onCancel,
  onSubmit,
}: RecipeEditorFormProps) {
  return (
    <form className="production-recipe-form" onSubmit={onSubmit}>
      <div className="production-version-policy">
        <span>
          <small>Aktiv verzio</small>
          <strong>{selectedRecipe.version_no ? `v${selectedRecipe.version_no}` : "Nincs"}</strong>
        </span>
        <span>
          <small>Mentes utan</small>
          <strong>{formatNextVersion(selectedRecipe)}</strong>
        </span>
        <p>
          A mentes uj aktiv receptverziot hoz letre. A korabbi aktiv verzio archivalt
          marad, a POS eladast es importot ez nem blokkolja.
        </p>
      </div>
      <div className="production-recipe-form-grid">
        <label className="field">
          <span>Recept neve</span>
          <input
            className="field-input"
            value={form.name}
            onChange={(event) => onFormChange({ ...form, name: event.target.value })}
          />
        </label>
        <label className="field">
          <span>Kihozatal</span>
          <input
            className="field-input"
            type="number"
            min="0.001"
            step="0.001"
            value={form.yield_quantity}
            onChange={(event) =>
              onFormChange({ ...form, yield_quantity: event.target.value })
            }
          />
        </label>
        <label className="field">
          <span>Mertekegyseg</span>
          <select
            className="field-input"
            value={form.yield_uom_id}
            onChange={(event) => onFormChange({ ...form, yield_uom_id: event.target.value })}
          >
            {units.map((unit) => (
              <option key={unit.id} value={unit.id}>
                {unit.symbol ?? unit.code}
              </option>
            ))}
          </select>
        </label>
      </div>

      <div className="production-recipe-lines">
        {form.ingredients.map((line, index) => (
          <div className="production-recipe-line" key={`${line.inventory_item_id}-${index}`}>
            <select
              className="field-input"
              value={line.inventory_item_id}
              onChange={(event) => {
                const inventoryItemId = event.target.value;
                onUpdateIngredientLine(index, {
                  inventory_item_id: inventoryItemId,
                  uom_id: ingredientDefaultUnitId(ingredients, inventoryItemId, fallbackUnitId),
                });
              }}
            >
              {ingredients.map((ingredient) => (
                <option key={ingredient.id} value={ingredient.id}>
                  {ingredient.name}
                </option>
              ))}
            </select>
            <input
              className="field-input"
              type="number"
              min="0.001"
              step="0.001"
              value={line.quantity}
              onChange={(event) =>
                onUpdateIngredientLine(index, {
                  quantity: event.target.value,
                })
              }
            />
            <select
              className="field-input"
              value={line.uom_id}
              onChange={(event) =>
                onUpdateIngredientLine(index, {
                  uom_id: event.target.value,
                })
              }
            >
              {units.map((unit) => (
                <option key={unit.id} value={unit.id}>
                  {unit.symbol ?? unit.code}
                </option>
              ))}
            </select>
            <button
              type="button"
              className="text-button danger"
              onClick={() => onRemoveIngredientLine(index)}
            >
              Torles
            </button>
          </div>
        ))}
      </div>

      <div className="production-recipe-form-actions">
        <button
          type="button"
          className="text-button"
          onClick={onAddIngredientLine}
          disabled={ingredients.length === 0 || !fallbackUnitId}
        >
          Osszetevo hozzaadasa
        </button>
        <button type="button" className="text-button" onClick={onCancel}>
          Megse
        </button>
        <button type="submit" className="button" disabled={savePending}>
          {savePending
            ? "Mentes..."
            : `Uj verzio mentese (${formatNextVersion(selectedRecipe)})`}
        </button>
      </div>
    </form>
  );
}
