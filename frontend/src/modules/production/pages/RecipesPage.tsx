import { useEffect, useMemo, useState } from "react";
import type { FormEvent } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Link, useSearchParams } from "react-router-dom";

import { useTopbarControls } from "../../../shared/components/layout/TopbarControlsContext";
import { routes } from "../../../shared/constants/routes";
import {
  listCatalogIngredients,
  updateCatalogIngredient,
} from "../../catalog/api/catalogApi";
import type {
  CatalogIngredientPayload,
} from "../../catalog/types/catalog";
import { listUnitsOfMeasure, listVatRates } from "../../masterData/api/masterDataApi";
import { saveProductRecipe } from "../api/productionApi";
import { RecipeDetailPanel } from "../components/RecipeDetailPanel";
import { RecipesHeaderControls } from "../components/RecipesHeaderControls";
import { RecipesListPanel } from "../components/RecipesListPanel";
import { RecipesSummaryCards } from "../components/RecipesSummaryCards";
import { RecipesWorkQueueActions } from "../components/RecipesWorkQueueActions";
import {
  buildIngredientPayload,
  buildRecipeForm,
  buildRecipePayload,
  matchesFilter,
  parseRecipeFilter,
  type RecipeFilter,
  type RecipeFormLine,
  type RecipeFormState,
} from "../components/recipesPageView";
import { useRecipes } from "../hooks/useRecipes";
import type { RecipeCostSummary, RecipePayload } from "../types/production";

export function RecipesPage() {
  const { setControls } = useTopbarControls();
  const queryClient = useQueryClient();
  const [searchParams, setSearchParams] = useSearchParams();
  const requestedBusinessUnitId = searchParams.get("business_unit_id") ?? "";
  const requestedProductId = searchParams.get("product_id") ?? "";
  const requestedEdit = searchParams.get("edit") === "1";
  const openedFromImports = searchParams.get("from") === "imports";
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
  const [search, setSearch] = useState(() => searchParams.get("search") ?? "");
  const [filter, setFilter] = useState<RecipeFilter>(() =>
    parseRecipeFilter(searchParams.get("filter")),
  );
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

  async function invalidateRecipeReadModels() {
    await queryClient.invalidateQueries({ queryKey: ["production-recipes"] });
    await queryClient.invalidateQueries({
      queryKey: ["production-recipes-readiness-overview"],
    });
    await queryClient.invalidateQueries({ queryKey: ["catalog-products"] });
  }

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
      await invalidateRecipeReadModels();
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
      await invalidateRecipeReadModels();
      await queryClient.invalidateQueries({ queryKey: ["catalog-ingredients"] });
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

  function updateRouteParameter(name: string, value: string) {
    setSearchParams(
      (current) => {
        const next = new URLSearchParams(current);
        if (value) {
          next.set(name, value);
        } else {
          next.delete(name);
        }
        return next;
      },
      { replace: true },
    );
  }

  useEffect(() => {
    if (
      requestedBusinessUnitId &&
      requestedBusinessUnitId !== selectedBusinessUnitId &&
      businessUnits.some((unit) => unit.id === requestedBusinessUnitId)
    ) {
      setSelectedBusinessUnitId(requestedBusinessUnitId);
    }
  }, [
    businessUnits,
    requestedBusinessUnitId,
    selectedBusinessUnitId,
    setSelectedBusinessUnitId,
  ]);

  useEffect(() => {
    if (
      selectedBusinessUnitId &&
      !businessUnits.some((unit) => unit.id === requestedBusinessUnitId)
    ) {
      updateRouteParameter("business_unit_id", selectedBusinessUnitId);
    }
  }, [businessUnits, requestedBusinessUnitId, selectedBusinessUnitId]);

  useEffect(() => {
    setControls(
      <RecipesHeaderControls
        businessUnits={businessUnits}
        selectedBusinessUnitId={selectedBusinessUnitId}
        setSelectedBusinessUnitId={(value) => {
          setSelectedBusinessUnitId(value);
          setSelectedProductId(null);
          setSearchParams(
            (current) => {
              const next = new URLSearchParams(current);
              next.set("business_unit_id", value);
              next.delete("product_id");
              next.delete("edit");
              return next;
            },
            { replace: true },
          );
        }}
        search={search}
        setSearch={(value) => {
          setSearch(value);
          updateRouteParameter("search", value);
        }}
        filter={filter}
        setFilter={(value) => {
          setFilter(value);
          setSelectedProductId(null);
          updateRouteParameter("filter", value === "all" ? "" : value);
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
    setSearchParams,
    setSelectedBusinessUnitId,
  ]);

  function startEditing(row: RecipeCostSummary) {
    setEditingProductId(row.product_id);
    setSelectedProductId(row.product_id);
    updateRouteParameter("product_id", row.product_id);
    setForm(buildRecipeForm(row, fallbackUnitId));
    setFormMessage("");
    setFormError("");
  }

  useEffect(() => {
    const requestedRecipe = recipes.find((row) => row.product_id === requestedProductId);
    if (!requestedRecipe) {
      return;
    }
    setSelectedProductId(requestedRecipe.product_id);
    if (requestedEdit && fallbackUnitId) {
      startEditing(requestedRecipe);
      updateRouteParameter("edit", "");
    }
  }, [fallbackUnitId, recipes, requestedEdit, requestedProductId]);

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
    setSearchParams(
      (current) => {
        const next = new URLSearchParams(current);
        next.set("filter", nextFilter);
        if (firstMatch) {
          next.set("product_id", firstMatch.product_id);
        } else {
          next.delete("product_id");
        }
        next.delete("edit");
        return next;
      },
      { replace: true },
    );
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
      <RecipesSummaryCards
        totalProducts={recipes.length}
        readyCount={readyCount}
        missingRecipeCount={missingRecipeCount}
        missingCostCount={missingCostCount}
        stockSignalCount={stockSignalCount}
        missingVatCount={missingVatCount}
      />

      <RecipesWorkQueueActions
        missingRecipeCount={missingRecipeCount}
        missingCostCount={missingCostCount}
        missingVatCount={missingVatCount}
        stockSignalCount={stockSignalCount}
        emptyRecipeCount={emptyRecipeCount}
        onFocusIssue={focusFirstIssue}
      />

      {errorMessage ? <div className="error-banner">{errorMessage}</div> : null}
      {isLoading ? <div className="loading-state">Receptek betoltese...</div> : null}
      {quickMessage ? <div className="success-banner">{quickMessage}</div> : null}
      {quickError ? <div className="error-banner">{quickError}</div> : null}
      {openedFromImports ? (
        <div className="production-return-banner">
          <span>Az Import kozpont recepthiany-munkalistajarol erkeztel.</span>
          <Link
            className="secondary-button"
            to={`${routes.imports}?${new URLSearchParams({
              business_unit_id: selectedBusinessUnitId,
            }).toString()}`}
          >
            Vissza az Import kozpontba
          </Link>
        </div>
      ) : null}

      <div className="production-recipes-layout">
        <RecipesListPanel
          visibleRecipes={visibleRecipes}
          selectedProductId={selectedRecipe?.product_id ?? null}
          onSelectProductId={(productId) => {
            setSelectedProductId(productId);
            updateRouteParameter("product_id", productId);
          }}
        />

        <RecipeDetailPanel
          selectedRecipe={selectedRecipe}
          templateRecipes={templateRecipes}
          selectedTemplateProductId={selectedTemplateProductId}
          setSelectedTemplateProductId={setSelectedTemplateProductId}
          formMessage={formMessage}
          formError={formError}
          isEditingSelected={isEditingSelected}
          form={form}
          units={units}
          ingredients={ingredients}
          fallbackUnitId={fallbackUnitId}
          saveRecipePending={saveRecipeMutation.isPending}
          vatRates={vatRates}
          quickCostInputs={quickCostInputs}
          setQuickCostInputs={setQuickCostInputs}
          quickStockInputs={quickStockInputs}
          setQuickStockInputs={setQuickStockInputs}
          quickVatInputs={quickVatInputs}
          setQuickVatInputs={setQuickVatInputs}
          quickUpdatePending={quickUpdateIngredientMutation.isPending}
          onStartEditing={startEditing}
          onLoadSelectedTemplate={loadSelectedTemplate}
          onFormChange={setForm}
          onSubmitRecipeForm={submitRecipeForm}
          onUpdateIngredientLine={updateIngredientLine}
          onAddIngredientLine={addIngredientLine}
          onRemoveIngredientLine={removeIngredientLine}
          onCancelEditing={cancelEditing}
          onQuickUpdateIngredientCost={quickUpdateIngredientCost}
          onQuickUpdateIngredientStock={quickUpdateIngredientStock}
          onQuickUpdateIngredientVat={quickUpdateIngredientVat}
        />
      </div>
    </section>
  );
}
