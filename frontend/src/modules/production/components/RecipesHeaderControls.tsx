import type { BusinessUnit } from "../../masterData/types/masterData";
import type { RecipeFilter } from "./recipesPageView";

type RecipesHeaderControlsProps = {
  businessUnits: BusinessUnit[];
  selectedBusinessUnitId: string;
  setSelectedBusinessUnitId: (value: string) => void;
  search: string;
  setSearch: (value: string) => void;
  filter: RecipeFilter;
  setFilter: (value: RecipeFilter) => void;
  activeOnly: boolean;
  setActiveOnly: (value: boolean) => void;
};

export function RecipesHeaderControls({
  businessUnits,
  selectedBusinessUnitId,
  setSelectedBusinessUnitId,
  search,
  setSearch,
  filter,
  setFilter,
  activeOnly,
  setActiveOnly,
}: RecipesHeaderControlsProps) {
  return (
    <div className="business-dashboard-filters topbar-dashboard-filters">
      <label className="field topbar-field">
        <span>Vallalkozas</span>
        <select
          className="field-input"
          value={selectedBusinessUnitId}
          onChange={(event) => setSelectedBusinessUnitId(event.target.value)}
        >
          {businessUnits.map((unit) => (
            <option key={unit.id} value={unit.id}>
              {unit.name}
            </option>
          ))}
        </select>
      </label>
      <label className="field topbar-field">
        <span>Kereses</span>
        <input
          className="field-input"
          value={search}
          onChange={(event) => setSearch(event.target.value)}
          placeholder="Termek vagy kategoria"
        />
      </label>
      <label className="field topbar-field">
        <span>Allapot</span>
        <select
          className="field-input"
          value={filter}
          onChange={(event) => setFilter(event.target.value as RecipeFilter)}
        >
          <option value="all">Osszes</option>
          <option value="missing_recipe">Recept hianyzik</option>
          <option value="missing_cost">Ar hianyzik</option>
          <option value="missing_vat">AFA kulcs hianyzik</option>
          <option value="missing_stock">Keszletjelzes</option>
          <option value="empty_recipe">Ures recept</option>
          <option value="ready">Rendben</option>
        </select>
      </label>
      <label className="checkbox-field topbar-checkbox">
        <input
          type="checkbox"
          checked={activeOnly}
          onChange={(event) => setActiveOnly(event.target.checked)}
        />
        <span>Csak aktiv</span>
      </label>
    </div>
  );
}
