import { useEffect, useMemo, useState } from "react";
import type { FormEvent } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { useTopbarControls } from "../../../shared/components/layout/TopbarControlsContext";
import {
  listCatalogIngredients,
  updateCatalogIngredient,
} from "../../catalog/api/catalogApi";
import { listUnitsOfMeasure, listVatRates } from "../../masterData/api/masterDataApi";
import type {
  CatalogIngredient,
  CatalogIngredientPayload,
} from "../../catalog/types/catalog";
import type { BusinessUnit, UnitOfMeasure } from "../../masterData/types/masterData";
import { saveProductRecipe } from "../api/productionApi";
import { useRecipes } from "../hooks/useRecipes";
import type {
  IngredientStockStatus,
  RecipeCostStatus,
  RecipePayload,
  RecipeCostSummary,
  RecipeReadinessStatus,
} from "../types/production";

type RecipeFilter =
  | "all"
  | "missing_recipe"
  | "missing_cost"
  | "missing_vat"
  | "missing_stock"
  | "empty_recipe"
  | "ready";

type RecipeFormLine = {
  inventory_item_id: string;
  quantity: string;
  uom_id: string;
};

type RecipeFormState = {
  name: string;
  yield_quantity: string;
  yield_uom_id: string;
  ingredients: RecipeFormLine[];
};

function toNumber(value: string | number | null | undefined) {
  const parsed = Number(value ?? 0);
  return Number.isFinite(parsed) ? parsed : 0;
}

function formatMoney(value: string | number | null | undefined) {
  if (value === null || value === undefined || value === "") {
    return "-";
  }

  return new Intl.NumberFormat("hu-HU", {
    style: "currency",
    currency: "HUF",
    maximumFractionDigits: 0,
  }).format(toNumber(value));
}

function formatNumber(value: string | number | null | undefined) {
  if (value === null || value === undefined || value === "") {
    return "-";
  }

  return new Intl.NumberFormat("hu-HU", {
    maximumFractionDigits: 2,
  }).format(toNumber(value));
}

function formatQuantity(value: string | null, unit?: string | null) {
  if (value === null) {
    return "-";
  }
  return unit ? `${formatNumber(value)} ${unit}` : formatNumber(value);
}

function formatCostStatus(value: RecipeCostStatus) {
  const labels: Record<RecipeCostStatus, string> = {
    complete: "Teljes koltseg",
    missing_cost: "Hianyzo ar",
    no_recipe: "Nincs recept",
    empty_recipe: "Ures recept",
  };
  return labels[value] ?? value;
}

function formatTaxStatus(value: RecipeCostSummary["tax_status"]) {
  const labels: Record<string, string> = {
    product_vat_derived: "ÁFA számolt",
    missing_vat_rate: "ÁFA kulcs hiányzik",
    incomplete_cost: "ÁFA nem teljes",
    not_available: "ÁFA nincs",
  };
  return labels[value] ?? value;
}

function formatReadinessStatus(value: RecipeReadinessStatus) {
  const labels: Record<RecipeReadinessStatus, string> = {
    ready: "Rendben",
    missing_recipe: "Recept hianyzik",
    missing_cost: "Ar hianyzik",
    missing_stock: "Keszletjelzes",
    empty_recipe: "Ures recept",
  };
  return labels[value] ?? value;
}

function formatStockStatus(value: IngredientStockStatus) {
  const labels: Record<IngredientStockStatus, string> = {
    ok: "Rendben",
    missing: "Nincs keszlet",
    insufficient: "Keves keszlet",
    unknown: "Nincs keszletadat",
    not_tracked: "Nem kovetett",
  };
  return labels[value] ?? value;
}

function getReadinessClass(value: RecipeReadinessStatus) {
  if (value === "ready") {
    return "status-pill status-pill-success";
  }
  if (value === "missing_cost") {
    return "status-pill status-pill-danger";
  }
  return "status-pill status-pill-warning";
}

function getCostStatusClass(value: RecipeCostStatus) {
  if (value === "complete") {
    return "status-pill status-pill-success";
  }
  if (value === "missing_cost") {
    return "status-pill status-pill-danger";
  }
  return "status-pill status-pill-warning";
}

function getStockStatusClass(value: IngredientStockStatus) {
  if (value === "ok" || value === "not_tracked") {
    return "status-pill status-pill-success";
  }
  if (value === "missing" || value === "insufficient") {
    return "status-pill status-pill-warning";
  }
  return "status-pill";
}

function getNextAction(row: RecipeCostSummary) {
  if (row.readiness_status === "missing_recipe") {
    return "Recept letrehozasa a katalogusban.";
  }
  if (row.readiness_status === "missing_cost") {
    return "Beszerzesi/default ar potlasa az erintett osszetevoknel.";
  }
  if (row.readiness_status === "missing_stock") {
    return "Keszletjelzes ellenorzese; az eladas ettol meg nem blokkolt.";
  }
  if (row.readiness_status === "empty_recipe") {
    return "Osszetevo sorok hozzaadasa a recepthez.";
  }
  if (row.tax_status === "missing_vat_rate") {
    return "ÁFA kulcs pótlása az érintett összetevőknél.";
  }
  return "Nincs surgos recept oldali teendo.";
}

function formatNextVersion(row: RecipeCostSummary) {
  return row.version_no === null ? "v1" : `v${row.version_no + 1}`;
}

function matchesFilter(row: RecipeCostSummary, filter: RecipeFilter) {
  if (filter === "all") {
    return true;
  }
  if (filter === "missing_vat") {
    return row.tax_status === "missing_vat_rate";
  }
  if (filter === "missing_stock") {
    return row.readiness_status === "missing_stock";
  }
  if (filter === "ready") {
    return row.readiness_status === "ready";
  }
  return row.cost_status === filter || row.readiness_status === filter;
}

function buildRecipeForm(
  row: RecipeCostSummary,
  fallbackUnitId: string,
): RecipeFormState {
  return {
    name: row.recipe_name ?? `${row.product_name} recept`,
    yield_quantity: row.yield_quantity ?? "1",
    yield_uom_id: row.yield_uom_id ?? fallbackUnitId,
    ingredients: row.ingredients.map((ingredient) => ({
      inventory_item_id: ingredient.inventory_item_id,
      quantity: ingredient.quantity,
      uom_id: ingredient.uom_id,
    })),
  };
}

function buildRecipePayload(form: RecipeFormState): RecipePayload {
  return {
    name: form.name.trim(),
    yield_quantity: form.yield_quantity,
    yield_uom_id: form.yield_uom_id,
    ingredients: form.ingredients
      .filter((ingredient) => ingredient.inventory_item_id && ingredient.uom_id)
      .map((ingredient) => ({
        inventory_item_id: ingredient.inventory_item_id,
        quantity: ingredient.quantity,
        uom_id: ingredient.uom_id,
      })),
  };
}

function ingredientDefaultUnitId(
  ingredients: CatalogIngredient[],
  inventoryItemId: string,
  fallbackUnitId: string,
) {
  return (
    ingredients.find((ingredient) => ingredient.id === inventoryItemId)?.uom_id ??
    fallbackUnitId
  );
}

function buildIngredientPayload(
  ingredient: CatalogIngredient,
  patch: Partial<CatalogIngredientPayload>,
): CatalogIngredientPayload {
  return {
    business_unit_id: ingredient.business_unit_id,
    name: ingredient.name,
    item_type: ingredient.item_type,
    uom_id: ingredient.uom_id,
    default_vat_rate_id: ingredient.default_vat_rate_id,
    track_stock: ingredient.track_stock,
    default_unit_cost: ingredient.default_unit_cost,
    estimated_stock_quantity: ingredient.estimated_stock_quantity,
    is_active: ingredient.is_active,
    ...patch,
  };
}

function RecipesHeaderControls({
  businessUnits,
  selectedBusinessUnitId,
  setSelectedBusinessUnitId,
  search,
  setSearch,
  filter,
  setFilter,
  activeOnly,
  setActiveOnly,
}: {
  businessUnits: BusinessUnit[];
  selectedBusinessUnitId: string;
  setSelectedBusinessUnitId: (value: string) => void;
  search: string;
  setSearch: (value: string) => void;
  filter: RecipeFilter;
  setFilter: (value: RecipeFilter) => void;
  activeOnly: boolean;
  setActiveOnly: (value: boolean) => void;
}) {
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

export function RecipesPage() {
  const { setControls } = useTopbarControls();
  const queryClient = useQueryClient();
  const {
    businessUnits,
    recipes,
    overview,
    selectedBusinessUnitId,
    setSelectedBusinessUnitId,
    activeOnly,
    setActiveOnly,
    isLoading,
    errorMessage,
  } = useRecipes();
  const [search, setSearch] = useState("");
  const [filter, setFilter] = useState<RecipeFilter>("all");
  const [selectedProductId, setSelectedProductId] = useState<string | null>(null);
  const [editingProductId, setEditingProductId] = useState<string | null>(null);
  const [form, setForm] = useState<RecipeFormState | null>(null);
  const [formMessage, setFormMessage] = useState("");
  const [formError, setFormError] = useState("");
  const [quickCostInputs, setQuickCostInputs] = useState<Record<string, string>>({});
  const [quickStockInputs, setQuickStockInputs] = useState<Record<string, string>>({});
  const [quickVatInputs, setQuickVatInputs] = useState<Record<string, string>>({});
  const [selectedTemplateProductId, setSelectedTemplateProductId] = useState("");
  const [quickMessage, setQuickMessage] = useState("");
  const [quickError, setQuickError] = useState("");

  const unitsQuery = useQuery({
    queryKey: ["units-of-measure"],
    queryFn: listUnitsOfMeasure,
  });
  const units = unitsQuery.data ?? [];
  const fallbackUnitId =
    units.find((unit) => unit.code === "pcs")?.id ?? units[0]?.id ?? "";
  const vatRatesQuery = useQuery({
    queryKey: ["vat-rates"],
    queryFn: listVatRates,
  });
  const vatRates = vatRatesQuery.data ?? [];

  const ingredientsQuery = useQuery({
    queryKey: ["catalog-ingredients", selectedBusinessUnitId],
    queryFn: () => listCatalogIngredients(selectedBusinessUnitId),
    enabled: Boolean(selectedBusinessUnitId),
  });
  const ingredients = ingredientsQuery.data ?? [];
  const ingredientsById = useMemo(
    () => new Map(ingredients.map((ingredient) => [ingredient.id, ingredient])),
    [ingredients],
  );

  const saveRecipeMutation = useMutation({
    mutationFn: ({
      productId,
      payload,
    }: {
      productId: string;
      payload: RecipePayload;
    }) => saveProductRecipe(productId, payload),
    onSuccess: async (savedRecipe) => {
      setFormMessage("Recept mentve.");
      setFormError("");
      setEditingProductId(null);
      setForm(null);
      setSelectedProductId(savedRecipe.product_id);
      await queryClient.invalidateQueries({ queryKey: ["production-recipes"] });
      await queryClient.invalidateQueries({ queryKey: ["catalog-products"] });
    },
    onError: (error) => {
      setFormMessage("");
      setFormError(error instanceof Error ? error.message : "A recept mentese sikertelen.");
    },
  });

  const quickUpdateIngredientMutation = useMutation({
    mutationFn: ({
      inventoryItemId,
      payload,
    }: {
      inventoryItemId: string;
      payload: CatalogIngredientPayload;
    }) => updateCatalogIngredient(inventoryItemId, payload),
    onSuccess: async (updatedIngredient) => {
      setQuickMessage("Alapanyag adat frissitve.");
      setQuickError("");
      setQuickCostInputs((current) => {
        const next = { ...current };
        delete next[updatedIngredient.id];
        return next;
      });
      setQuickStockInputs((current) => {
        const next = { ...current };
        delete next[updatedIngredient.id];
        return next;
      });
      setQuickVatInputs((current) => {
        const next = { ...current };
        delete next[updatedIngredient.id];
        return next;
      });
      await queryClient.invalidateQueries({ queryKey: ["production-recipes"] });
      await queryClient.invalidateQueries({ queryKey: ["catalog-ingredients"] });
      await queryClient.invalidateQueries({ queryKey: ["catalog-products"] });
    },
    onError: (error) => {
      setQuickMessage("");
      setQuickError(
        error instanceof Error ? error.message : "Az alapanyag gyors javitasa sikertelen.",
      );
    },
  });

  const visibleRecipes = useMemo(() => {
    const normalizedSearch = search.trim().toLowerCase();
    return recipes.filter((row) => {
      const matchesSearch =
        normalizedSearch.length === 0 ||
        row.product_name.toLowerCase().includes(normalizedSearch) ||
        (row.category_name ?? "").toLowerCase().includes(normalizedSearch);
      return matchesSearch && matchesFilter(row, filter);
    });
  }, [filter, recipes, search]);

  const selectedRecipe =
    visibleRecipes.find((row) => row.product_id === selectedProductId) ??
    visibleRecipes[0] ??
    null;
  const templateRecipes = recipes.filter(
    (row) => row.recipe_id !== null && row.ingredients.length > 0,
  );
  const isEditingSelected =
    selectedRecipe !== null && editingProductId === selectedRecipe.product_id && form !== null;

  const readyCount =
    overview?.ready_count ?? recipes.filter((row) => row.readiness_status === "ready").length;
  const missingRecipeCount =
    overview?.readiness_counts.missing_recipe ??
    recipes.filter((row) => row.readiness_status === "missing_recipe").length;
  const missingCostCount =
    overview?.readiness_counts.missing_cost ??
    recipes.filter((row) => row.readiness_status === "missing_cost").length;
  const stockSignalCount =
    overview?.readiness_counts.missing_stock ??
    recipes.filter((row) => row.readiness_status === "missing_stock").length;
  const missingVatCount =
    overview?.tax_counts.missing_vat_rate ??
    recipes.filter((row) => row.tax_status === "missing_vat_rate").length;
  const emptyRecipeCount =
    overview?.readiness_counts.empty_recipe ??
    recipes.filter((row) => row.readiness_status === "empty_recipe").length;

  useEffect(() => {
    setControls(
      <RecipesHeaderControls
        businessUnits={businessUnits}
        selectedBusinessUnitId={selectedBusinessUnitId}
        setSelectedBusinessUnitId={(value) => {
          setSelectedBusinessUnitId(value);
          setSelectedProductId(null);
        }}
        search={search}
        setSearch={setSearch}
        filter={filter}
        setFilter={(value) => {
          setFilter(value);
          setSelectedProductId(null);
        }}
        activeOnly={activeOnly}
        setActiveOnly={setActiveOnly}
      />,
    );

    return () => setControls(null);
  }, [
    activeOnly,
    businessUnits,
    filter,
    search,
    selectedBusinessUnitId,
    setActiveOnly,
    setControls,
    setSelectedBusinessUnitId,
  ]);

  function startEditing(row: RecipeCostSummary) {
    setEditingProductId(row.product_id);
    setSelectedProductId(row.product_id);
    setForm(buildRecipeForm(row, fallbackUnitId));
    setFormMessage("");
    setFormError("");
  }

  function startFromTemplate(target: RecipeCostSummary, source: RecipeCostSummary) {
    setEditingProductId(target.product_id);
    setSelectedProductId(target.product_id);
    setForm({
      name: `${target.product_name} recept`,
      yield_quantity: source.yield_quantity ?? "1",
      yield_uom_id: source.yield_uom_id ?? fallbackUnitId,
      ingredients: source.ingredients.map((ingredient) => ({
        inventory_item_id: ingredient.inventory_item_id,
        quantity: ingredient.quantity,
        uom_id: ingredient.uom_id,
      })),
    });
    setFormMessage(`Sablon betoltve: ${source.product_name}. Mentes elott ellenorizd.`);
    setFormError("");
  }

  function loadSelectedTemplate(target: RecipeCostSummary) {
    const source =
      templateRecipes.find((row) => row.product_id === selectedTemplateProductId) ??
      templateRecipes.find((row) => row.product_id !== target.product_id);
    if (!source) {
      setFormError("Nincs betoltheto recept sablon.");
      return;
    }
    startFromTemplate(target, source);
  }

  function focusFirstIssue(nextFilter: RecipeFilter) {
    const firstMatch = recipes.find((row) => matchesFilter(row, nextFilter));
    setFilter(nextFilter);
    setSelectedProductId(firstMatch?.product_id ?? null);
    setEditingProductId(null);
    setForm(null);
    setFormError("");
  }

  function cancelEditing() {
    setEditingProductId(null);
    setForm(null);
    setFormError("");
  }

  function updateIngredientLine(index: number, patch: Partial<RecipeFormLine>) {
    setForm((current) => {
      if (current === null) {
        return current;
      }
      return {
        ...current,
        ingredients: current.ingredients.map((line, lineIndex) =>
          lineIndex === index ? { ...line, ...patch } : line,
        ),
      };
    });
  }

  function addIngredientLine() {
    const firstIngredient = ingredients[0];
    setForm((current) => {
      if (current === null) {
        return current;
      }
      return {
        ...current,
        ingredients: [
          ...current.ingredients,
          {
            inventory_item_id: firstIngredient?.id ?? "",
            quantity: "1",
            uom_id: firstIngredient?.uom_id ?? fallbackUnitId,
          },
        ],
      };
    });
  }

  function removeIngredientLine(index: number) {
    setForm((current) => {
      if (current === null) {
        return current;
      }
      return {
        ...current,
        ingredients: current.ingredients.filter((_, lineIndex) => lineIndex !== index),
      };
    });
  }

  function submitRecipeForm(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (selectedRecipe === null || form === null) {
      return;
    }
    if (!form.yield_uom_id) {
      setFormError("A kihozatal mertekegysege kotelezo.");
      return;
    }
    if (form.ingredients.length === 0) {
      setFormError("Legalabb egy osszetevo szukseges.");
      return;
    }
    saveRecipeMutation.mutate({
      productId: selectedRecipe.product_id,
      payload: buildRecipePayload(form),
    });
  }

  function quickUpdateIngredientCost(inventoryItemId: string) {
    const ingredient = ingredientsById.get(inventoryItemId);
    const value = quickCostInputs[inventoryItemId]?.trim();
    if (!ingredient || !value) {
      setQuickError("Adj meg beszerzesi/default arat.");
      return;
    }

    quickUpdateIngredientMutation.mutate({
      inventoryItemId,
      payload: buildIngredientPayload(ingredient, {
        default_unit_cost: value,
      }),
    });
  }

  function quickUpdateIngredientStock(inventoryItemId: string) {
    const ingredient = ingredientsById.get(inventoryItemId);
    const value = quickStockInputs[inventoryItemId]?.trim();
    if (!ingredient || !value) {
      setQuickError("Adj meg becsult keszletmennyiseget.");
      return;
    }

    quickUpdateIngredientMutation.mutate({
      inventoryItemId,
      payload: buildIngredientPayload(ingredient, {
        estimated_stock_quantity: value,
      }),
    });
  }

  function quickUpdateIngredientVat(inventoryItemId: string) {
    const ingredient = ingredientsById.get(inventoryItemId);
    const value = quickVatInputs[inventoryItemId]?.trim();
    if (!ingredient || !value) {
      setQuickError("Valassz AFA kulcsot.");
      return;
    }

    quickUpdateIngredientMutation.mutate({
      inventoryItemId,
      payload: buildIngredientPayload(ingredient, {
        default_vat_rate_id: value,
      }),
    });
  }

  return (
    <section className="page-section production-recipes-page">
      <div className="finance-summary-grid">
        <article className="finance-summary-card">
          <span>Termekek</span>
          <strong>{recipes.length}</strong>
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

      <div className="production-work-queue-actions">
        <button
          type="button"
          className="text-button"
          onClick={() => focusFirstIssue("missing_recipe")}
          disabled={missingRecipeCount === 0}
        >
          Recept hianyok ({missingRecipeCount})
        </button>
        <button
          type="button"
          className="text-button"
          onClick={() => focusFirstIssue("missing_cost")}
          disabled={missingCostCount === 0}
        >
          Ar hianyok ({missingCostCount})
        </button>
        <button
          type="button"
          className="text-button"
          onClick={() => focusFirstIssue("missing_vat")}
          disabled={missingVatCount === 0}
        >
          AFA hianyok ({missingVatCount})
        </button>
        <button
          type="button"
          className="text-button"
          onClick={() => focusFirstIssue("missing_stock")}
          disabled={stockSignalCount === 0}
        >
          Keszletjelzesek ({stockSignalCount})
        </button>
        <button
          type="button"
          className="text-button"
          onClick={() => focusFirstIssue("empty_recipe")}
          disabled={emptyRecipeCount === 0}
        >
          Ures receptek ({emptyRecipeCount})
        </button>
      </div>

      {errorMessage ? <div className="error-banner">{errorMessage}</div> : null}
      {isLoading ? <div className="loading-state">Receptek betoltese...</div> : null}
      {quickMessage ? <div className="success-banner">{quickMessage}</div> : null}
      {quickError ? <div className="error-banner">{quickError}</div> : null}

      <div className="production-recipes-layout">
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
                      selectedRecipe?.product_id === row.product_id
                        ? "production-recipe-row production-recipe-row-selected"
                        : "production-recipe-row"
                    }
                    onClick={() => setSelectedProductId(row.product_id)}
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
                        <span>Bruttó egys.: {formatMoney(row.unit_gross_cost)}</span>
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
                  <strong>
                    {selectedRecipe.version_no ? `v${selectedRecipe.version_no}` : "Nincs"}
                  </strong>
                </span>
                <span>
                  <small>Kihozatal</small>
                  <strong>
                    {formatQuantity(
                      selectedRecipe.yield_quantity,
                      selectedRecipe.yield_uom_code,
                    )}
                  </strong>
                </span>
                <span>
                  <small>Teljes koltseg</small>
                  <strong>{formatMoney(selectedRecipe.total_cost)}</strong>
                </span>
                <span>
                  <small>ÁFA</small>
                  <strong>{formatMoney(selectedRecipe.total_vat_amount)}</strong>
                </span>
                <span>
                  <small>Bruttó költség</small>
                  <strong>{formatMoney(selectedRecipe.total_gross_cost)}</strong>
                </span>
                <span>
                  <small>Egységkoltseg</small>
                  <strong>{formatMoney(selectedRecipe.unit_cost)}</strong>
                </span>
                <span>
                  <small>Bruttó egységköltség</small>
                  <strong>{formatMoney(selectedRecipe.unit_gross_cost)}</strong>
                </span>
                <span>
                  <small>ÁFA státusz</small>
                  <strong>{formatTaxStatus(selectedRecipe.tax_status)}</strong>
                </span>
              </div>

              <div className="production-recipe-action">
                <strong>{getNextAction(selectedRecipe)}</strong>
                <button
                  type="button"
                  className="text-button"
                  onClick={() => startEditing(selectedRecipe)}
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
                    onClick={() => loadSelectedTemplate(selectedRecipe)}
                  >
                    Sablon betoltese
                  </button>
                </div>
              ) : null}

              {formMessage ? <div className="success-banner">{formMessage}</div> : null}
              {formError ? <div className="error-banner">{formError}</div> : null}

              {isEditingSelected && form ? (
                <form className="production-recipe-form" onSubmit={submitRecipeForm}>
                  <div className="production-version-policy">
                    <span>
                      <small>Aktiv verzio</small>
                      <strong>
                        {selectedRecipe.version_no
                          ? `v${selectedRecipe.version_no}`
                          : "Nincs"}
                      </strong>
                    </span>
                    <span>
                      <small>Mentes utan</small>
                      <strong>{formatNextVersion(selectedRecipe)}</strong>
                    </span>
                    <p>
                      A mentes uj aktiv receptverziot hoz letre. A korabbi aktiv verzio
                      archivalt marad, a POS eladast es importot ez nem blokkolja.
                    </p>
                  </div>
                  <div className="production-recipe-form-grid">
                    <label className="field">
                      <span>Recept neve</span>
                      <input
                        className="field-input"
                        value={form.name}
                        onChange={(event) =>
                          setForm({ ...form, name: event.target.value })
                        }
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
                          setForm({ ...form, yield_quantity: event.target.value })
                        }
                      />
                    </label>
                    <label className="field">
                      <span>Mertekegyseg</span>
                      <select
                        className="field-input"
                        value={form.yield_uom_id}
                        onChange={(event) =>
                          setForm({ ...form, yield_uom_id: event.target.value })
                        }
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
                            updateIngredientLine(index, {
                              inventory_item_id: inventoryItemId,
                              uom_id: ingredientDefaultUnitId(
                                ingredients,
                                inventoryItemId,
                                fallbackUnitId,
                              ),
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
                            updateIngredientLine(index, {
                              quantity: event.target.value,
                            })
                          }
                        />
                        <select
                          className="field-input"
                          value={line.uom_id}
                          onChange={(event) =>
                            updateIngredientLine(index, {
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
                          onClick={() => removeIngredientLine(index)}
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
                      onClick={addIngredientLine}
                      disabled={ingredients.length === 0 || !fallbackUnitId}
                    >
                      Osszetevo hozzaadasa
                    </button>
                    <button
                      type="button"
                      className="text-button"
                      onClick={cancelEditing}
                    >
                      Megse
                    </button>
                    <button
                      type="submit"
                      className="button"
                      disabled={saveRecipeMutation.isPending}
                    >
                      {saveRecipeMutation.isPending
                        ? "Mentes..."
                        : `Uj verzio mentese (${formatNextVersion(selectedRecipe)})`}
                    </button>
                  </div>
                </form>
              ) : null}

              <div className="table-scroll">
                <table className="data-table details-table">
                  <thead>
                    <tr>
                      <th>Osszetevo</th>
                      <th>Mennyiseg</th>
                      <th>Ar</th>
                      <th>Koltseg</th>
                      <th>ÁFA / bruttó</th>
                      <th>Keszlet</th>
                    </tr>
                  </thead>
                  <tbody>
                    {selectedRecipe.ingredients.map((ingredient) => (
                      <tr key={ingredient.inventory_item_id}>
                        <td>{ingredient.inventory_item_name}</td>
                        <td>
                          {formatQuantity(ingredient.quantity, ingredient.uom_code)}
                        </td>
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
                                placeholder="Ft / egys."
                              />
                              <button
                                type="button"
                                className="text-button"
                                onClick={() =>
                                  quickUpdateIngredientCost(ingredient.inventory_item_id)
                                }
                                disabled={quickUpdateIngredientMutation.isPending}
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
                                : "ÁFA kulcs hiányzik"}
                            </span>
                            <span>ÁFA: {formatMoney(ingredient.estimated_vat_amount)}</span>
                            <span>Bruttó: {formatMoney(ingredient.estimated_gross_cost)}</span>
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
                                onClick={() =>
                                  quickUpdateIngredientVat(ingredient.inventory_item_id)
                                }
                                disabled={
                                  quickUpdateIngredientMutation.isPending ||
                                  vatRates.length === 0
                                }
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
                                onClick={() =>
                                  quickUpdateIngredientStock(ingredient.inventory_item_id)
                                }
                                disabled={quickUpdateIngredientMutation.isPending}
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
            </>
          ) : (
            <p className="muted-text">A szurok alapjan nincs megjelenitheto receptsor.</p>
          )}
        </aside>
      </div>
    </section>
  );
}
