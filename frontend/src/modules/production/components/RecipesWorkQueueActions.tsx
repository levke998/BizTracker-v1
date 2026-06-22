import type { RecipeFilter } from "./recipesPageView";

type RecipesWorkQueueActionsProps = {
  missingRecipeCount: number;
  missingCostCount: number;
  missingVatCount: number;
  stockSignalCount: number;
  emptyRecipeCount: number;
  onFocusIssue: (filter: RecipeFilter) => void;
};

export function RecipesWorkQueueActions({
  missingRecipeCount,
  missingCostCount,
  missingVatCount,
  stockSignalCount,
  emptyRecipeCount,
  onFocusIssue,
}: RecipesWorkQueueActionsProps) {
  return (
    <div className="production-work-queue-actions">
      <button
        type="button"
        className="text-button"
        onClick={() => onFocusIssue("missing_recipe")}
        disabled={missingRecipeCount === 0}
      >
        Recept hianyok ({missingRecipeCount})
      </button>
      <button
        type="button"
        className="text-button"
        onClick={() => onFocusIssue("missing_cost")}
        disabled={missingCostCount === 0}
      >
        Ar hianyok ({missingCostCount})
      </button>
      <button
        type="button"
        className="text-button"
        onClick={() => onFocusIssue("missing_vat")}
        disabled={missingVatCount === 0}
      >
        AFA hianyok ({missingVatCount})
      </button>
      <button
        type="button"
        className="text-button"
        onClick={() => onFocusIssue("missing_stock")}
        disabled={stockSignalCount === 0}
      >
        Keszletjelzesek ({stockSignalCount})
      </button>
      <button
        type="button"
        className="text-button"
        onClick={() => onFocusIssue("empty_recipe")}
        disabled={emptyRecipeCount === 0}
      >
        Ures receptek ({emptyRecipeCount})
      </button>
    </div>
  );
}
