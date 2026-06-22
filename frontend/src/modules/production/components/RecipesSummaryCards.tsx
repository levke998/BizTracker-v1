type RecipesSummaryCardsProps = {
  totalProducts: number;
  readyCount: number;
  missingRecipeCount: number;
  missingCostCount: number;
  stockSignalCount: number;
  missingVatCount: number;
};

export function RecipesSummaryCards({
  totalProducts,
  readyCount,
  missingRecipeCount,
  missingCostCount,
  stockSignalCount,
  missingVatCount,
}: RecipesSummaryCardsProps) {
  return (
    <div className="finance-summary-grid">
      <article className="finance-summary-card">
        <span>Termekek</span>
        <strong>{totalProducts}</strong>
      </article>
      <article className="finance-summary-card">
        <span>Rendben</span>
        <strong>{readyCount}</strong>
      </article>
      <article className="finance-summary-card">
        <span>Recept hianyzik</span>
        <strong>{missingRecipeCount}</strong>
      </article>
      <article className="finance-summary-card">
        <span>Ar / keszlet jelzes</span>
        <strong>{missingCostCount + stockSignalCount}</strong>
      </article>
      <article className="finance-summary-card">
        <span>AFA kulcs jelzes</span>
        <strong>{missingVatCount}</strong>
      </article>
    </div>
  );
}
