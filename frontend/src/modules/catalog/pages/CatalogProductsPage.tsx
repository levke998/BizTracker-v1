import { useEffect, useMemo, useState } from "react";
import type { FormEvent } from "react";
import { Link } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { useTopbarControls } from "../../../shared/components/layout/TopbarControlsContext";
import { Button } from "../../../shared/components/ui/Button";
import { Card } from "../../../shared/components/ui/Card";
import { routes } from "../../../shared/constants/routes";
import {
  listBusinessUnits,
  listCategories,
  listUnitsOfMeasure,
  listVatRates,
} from "../../masterData/api/masterDataApi";
import {
  createCatalogProduct,
  deleteCatalogProduct,
  listCatalogIngredients,
  listCatalogProducts,
  updateCatalogProduct,
} from "../api/catalogApi";
import { listInventoryStockLevels } from "../../inventory/api/inventoryApi";
import type { InventoryStockLevel } from "../../inventory/types/inventory";
import type {
  CatalogProduct,
  CatalogProductPayload,
  CatalogRecipeIngredientPayload,
} from "../types/catalog";

type ProductSort = "top" | "trending" | "abc" | "price";
type CatalogMode = "products" | "recipes";
type ProductRiskFilter = "all" | "attention" | "margin" | "recipe" | "stock";
type ProductRiskTone = "success" | "warning" | "danger" | "neutral";
type ProductRiskItem = {
  title: string;
  description: string;
  tone: ProductRiskTone;
};
type ProductDecisionSummary = {
  actionTitle: string;
  actionDescription: string;
  actionTone: ProductRiskTone;
  riskTitle: string;
  riskDescription: string;
  riskTone: ProductRiskTone;
  recipeTitle: string;
  recipeDescription: string;
  stockTitle: string;
  stockDescription: string;
  stockTone: ProductRiskTone;
};
type RecipeIngredientSummary = {
  totalCost: number;
  highestCostName: string;
  highestCostShare: number;
  emptyStockCount: number;
  missingStockCount: number;
};
type ProductFormState = {
  id?: string;
  category_id: string;
  sales_uom_id: string;
  default_vat_rate_id: string;
  sku: string;
  name: string;
  product_type: string;
  sale_price_gross: string;
  default_unit_cost: string;
  is_active: boolean;
  recipe_enabled: boolean;
  recipe_name: string;
  recipe_yield_quantity: string;
  recipe_yield_uom_id: string;
  recipe_ingredients: CatalogRecipeIngredientPayload[];
};

function toNumber(value: string | number | null | undefined) {
  const parsed = Number(value ?? 0);
  return Number.isFinite(parsed) ? parsed : 0;
}

function formatMoney(value: string | number | null | undefined) {
  return new Intl.NumberFormat("hu-HU", {
    style: "currency",
    currency: "HUF",
    maximumFractionDigits: 0,
  }).format(toNumber(value));
}

function formatNumber(value: string | number | null | undefined) {
  return new Intl.NumberFormat("hu-HU", {
    maximumFractionDigits: 1,
  }).format(toNumber(value));
}

function formatDateTime(value: string | null) {
  if (!value) {
    return "-";
  }

  return new Intl.DateTimeFormat("hu-HU", {
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  }).format(new Date(value));
}

function getUnitLabel(product: CatalogProduct) {
  return product.sales_uom_symbol ?? product.sales_uom_code ?? "egység";
}

function formatProductType(value: string) {
  const labels: Record<string, string> = {
    finished_good: "Késztermék",
    resale: "Továbbértékesített termék",
    service: "Szolgáltatás",
  };
  return labels[value] ?? value;
}

function getProductHealth(
  product: CatalogProduct,
  stockLevelByItemId: Map<string, InventoryStockLevel>,
) {
  const margin = toNumber(product.estimated_margin_amount);
  const marginPercent = toNumber(product.estimated_margin_percent);
  const lowStockIngredients = product.ingredients.filter((ingredient) => {
    const stockLevel = stockLevelByItemId.get(ingredient.inventory_item_id);
    return stockLevel !== undefined && toNumber(stockLevel.current_quantity) <= 0;
  });

  if (!product.is_active) {
    return { label: "Archivált", className: "status-pill" };
  }
  if (margin < 0) {
    return { label: "Negatív árrés", className: "status-pill status-pill-danger" };
  }
  if (product.has_recipe && lowStockIngredients.length > 0) {
    return { label: "Alapanyaghiány", className: "status-pill status-pill-danger" };
  }
  if (product.has_recipe && product.ingredients.length === 0) {
    return { label: "Hiányzó receptsor", className: "status-pill status-pill-warning" };
  }
  if (marginPercent >= 30) {
    return { label: "Erős árrés", className: "status-pill status-pill-success" };
  }
  if (!product.has_recipe) {
    return { label: "Direkt költség", className: "status-pill" };
  }
  return { label: "Rendben", className: "status-pill status-pill-success" };
}

function getProductRiskItems(
  product: CatalogProduct,
  stockLevelByItemId: Map<string, InventoryStockLevel>,
): ProductRiskItem[] {
  const margin = toNumber(product.estimated_margin_amount);
  const marginPercent = toNumber(product.estimated_margin_percent);
  const missingStockIngredients = product.ingredients.filter(
    (ingredient) => !stockLevelByItemId.has(ingredient.inventory_item_id),
  );
  const lowStockIngredients = product.ingredients.filter((ingredient) => {
    const stockLevel = stockLevelByItemId.get(ingredient.inventory_item_id);
    return stockLevel !== undefined && toNumber(stockLevel.current_quantity) <= 0;
  });
  const risks: ProductRiskItem[] = [];

  if (!product.is_active) {
    risks.push({
      title: "Archivált termék",
      description: "Nem aktív kínálati elem, értékesítéshez előbb vissza kell nyitni.",
      tone: "neutral",
    });
  }
  if (margin < 0) {
    risks.push({
      title: "Negatív árrés",
      description: "Az eladási ár nem fedezi a becsült egységköltséget.",
      tone: "danger",
    });
  } else if (marginPercent > 0 && marginPercent < 15) {
    risks.push({
      title: "Alacsony árrés",
      description: "Érdemes árat, receptet vagy beszerzési költséget ellenőrizni.",
      tone: "warning",
    });
  }
  if (product.has_recipe && product.ingredients.length === 0) {
    risks.push({
      title: "Hiányzó receptsor",
      description: "A termék receptes, de még nincs hozzárendelt alapanyag.",
      tone: "warning",
    });
  }
  if (product.has_recipe && lowStockIngredients.length > 0) {
    risks.push({
      title: "Alapanyaghiány",
      description: `${lowStockIngredients.length} receptösszetevő készlete nulla vagy negatív.`,
      tone: "danger",
    });
  }
  if (product.has_recipe && missingStockIngredients.length > 0) {
    risks.push({
      title: "Hiányzó készletadat",
      description: `${missingStockIngredients.length} receptösszetevőhöz még nincs aktuális készletszint.`,
      tone: "warning",
    });
  }
  if (!product.has_recipe) {
    risks.push({
      title: "Direkt költség alapú",
      description: "A margin a termékhez rögzített egységköltségből számolódik.",
      tone: "neutral",
    });
  }
  if (risks.length === 0) {
    risks.push({
      title: "Rendben",
      description: "A recept, készletadat és becsült árrés alapján nincs kiemelt kockázat.",
      tone: "success",
    });
  }

  return risks;
}

function getProductDecisionSummary(
  product: CatalogProduct,
  stockLevelByItemId: Map<string, InventoryStockLevel>,
): ProductDecisionSummary {
  const margin = toNumber(product.estimated_margin_amount);
  const marginPercent = toNumber(product.estimated_margin_percent);
  const missingStockIngredients = product.ingredients.filter(
    (ingredient) => !stockLevelByItemId.has(ingredient.inventory_item_id),
  );
  const emptyStockIngredients = product.ingredients.filter((ingredient) => {
    const stockLevel = stockLevelByItemId.get(ingredient.inventory_item_id);
    return stockLevel !== undefined && toNumber(stockLevel.current_quantity) <= 0;
  });
  const lowStockIngredients = product.ingredients.filter((ingredient) => {
    const stockLevel = stockLevelByItemId.get(ingredient.inventory_item_id);
    return (
      stockLevel !== undefined &&
      toNumber(stockLevel.current_quantity) > 0 &&
      toNumber(stockLevel.current_quantity) <= toNumber(ingredient.quantity)
    );
  });
  const riskItems = getProductRiskItems(product, stockLevelByItemId);
  const dangerCount = riskItems.filter((risk) => risk.tone === "danger").length;
  const warningCount = riskItems.filter((risk) => risk.tone === "warning").length;
  const riskTone: ProductRiskTone =
    dangerCount > 0 ? "danger" : warningCount > 0 ? "warning" : "success";

  let actionTitle = "Értékesítésre kész";
  let actionDescription = "A termék árrése, receptje és készletkapcsolata alapján nincs sürgős teendő.";
  let actionTone: ProductRiskTone = "success";

  if (!product.is_active) {
    actionTitle = "Archivált termék";
    actionDescription = "Értékesítés előtt nyisd vissza, vagy hagyd archivált állapotban.";
    actionTone = "neutral";
  } else if (margin < 0) {
    actionTitle = "Árazás ellenőrzése";
    actionDescription = "Az eladási ár jelenleg nem fedezi a becsült egységköltséget.";
    actionTone = "danger";
  } else if (emptyStockIngredients.length > 0) {
    actionTitle = "Beszerzés indítása";
    actionDescription = `${emptyStockIngredients.length} alapanyag készlete nulla vagy negatív.`;
    actionTone = "danger";
  } else if (product.has_recipe && product.ingredients.length === 0) {
    actionTitle = "Recept kitöltése";
    actionDescription = "A termék receptes, de még nincs hozzárendelt alapanyag.";
    actionTone = "warning";
  } else if (missingStockIngredients.length > 0) {
    actionTitle = "Készletadat pótlása";
    actionDescription = `${missingStockIngredients.length} alapanyagnál még nincs tényleges készletszint.`;
    actionTone = "warning";
  } else if (marginPercent > 0 && marginPercent < 15) {
    actionTitle = "Fedezet vizsgálata";
    actionDescription = "Az árrés pozitív, de alacsony; érdemes árat vagy receptköltséget nézni.";
    actionTone = "warning";
  } else if (!product.has_recipe) {
    actionTitle = "Direkt költség kontroll";
    actionDescription = "A termék nem receptből, hanem kézzel rögzített egységköltségből számol.";
    actionTone = "neutral";
  }

  const recipeTitle = product.has_recipe
    ? product.ingredients.length > 0
      ? "Recept fedett"
      : "Recept hiányos"
    : "Direkt költség";
  const recipeDescription = product.has_recipe
    ? product.ingredients.length > 0
      ? `${product.ingredients.length} összetevő alapján számolt költség.`
      : "A recept bekapcsolt, de még nincs hozzá összetevő."
    : "Nincs recept, a termékköltség külön mezőből jön.";

  const stockTitle =
    emptyStockIngredients.length > 0
      ? "Készlethiány"
      : missingStockIngredients.length > 0
        ? "Hiányzó készletadat"
        : lowStockIngredients.length > 0
          ? "Alacsony készlet"
          : product.has_recipe
            ? "Készlet rendben"
            : "Nem receptes";
  const stockDescription =
    emptyStockIngredients.length > 0
      ? `${emptyStockIngredients.length} összetevő nem áll rendelkezésre.`
      : missingStockIngredients.length > 0
        ? `${missingStockIngredients.length} összetevőhöz nincs készletszint.`
        : lowStockIngredients.length > 0
          ? `${lowStockIngredients.length} összetevő közel van a receptigényhez.`
          : product.has_recipe
            ? "A kapcsolt alapanyagoknál nincs kiemelt készletjelzés."
            : "Készletkockázat csak recept vagy direkt készletkövetés mellett értelmezett.";
  const stockTone: ProductRiskTone =
    emptyStockIngredients.length > 0
      ? "danger"
      : missingStockIngredients.length > 0 || lowStockIngredients.length > 0
        ? "warning"
        : product.has_recipe
          ? "success"
          : "neutral";

  return {
    actionTitle,
    actionDescription,
    actionTone,
    riskTitle:
      dangerCount > 0
        ? `${dangerCount} kritikus jelzés`
        : warningCount > 0
          ? `${warningCount} figyelendő jelzés`
          : "Nincs kiemelt kockázat",
    riskDescription:
      dangerCount > 0
        ? "A termék üzletileg vagy készletoldalon azonnali figyelmet kér."
        : warningCount > 0
          ? "Nem blokkoló, de érdemes átnézni a kapcsolt adatokat."
          : "A jelenlegi adatok alapján stabil termékkártya.",
    riskTone,
    recipeTitle,
    recipeDescription,
    stockTitle,
    stockDescription,
    stockTone,
  };
}

function getIngredientStockStatus(
  ingredient: CatalogProduct["ingredients"][number],
  stockLevelByItemId: Map<string, InventoryStockLevel>,
) {
  const stockLevel = stockLevelByItemId.get(ingredient.inventory_item_id);
  if (!stockLevel) {
    return { label: "Nincs készletadat", className: "catalog-stock-pill neutral" };
  }

  const quantity = toNumber(stockLevel.current_quantity);
  if (quantity <= 0) {
    return { label: "Készlethiány", className: "catalog-stock-pill danger" };
  }
  if (quantity <= toNumber(ingredient.quantity)) {
    return { label: "Figyelendő", className: "catalog-stock-pill warning" };
  }
  return { label: "Rendben", className: "catalog-stock-pill success" };
}

function getLowestIngredientStock(
  product: CatalogProduct,
  stockLevelByItemId: Map<string, InventoryStockLevel>,
) {
  const levels = product.ingredients
    .map((ingredient) => {
      const stockLevel = stockLevelByItemId.get(ingredient.inventory_item_id);
      if (!stockLevel) {
        return null;
      }
      return {
        name: ingredient.name,
        quantity: toNumber(stockLevel.current_quantity),
        uom: ingredient.uom_code ?? "",
      };
    })
    .filter((item): item is { name: string; quantity: number; uom: string } =>
      Boolean(item),
    );

  if (levels.length === 0) {
    return "-";
  }

  const lowest = levels.sort((left, right) => left.quantity - right.quantity)[0];
  return `${lowest.name}: ${formatNumber(lowest.quantity)} ${lowest.uom}`;
}

function getIngredientStockTone(
  ingredient: CatalogProduct["ingredients"][number],
  stockLevelByItemId: Map<string, InventoryStockLevel>,
): ProductRiskTone {
  const stockLevel = stockLevelByItemId.get(ingredient.inventory_item_id);
  if (!stockLevel) {
    return "neutral";
  }

  const quantity = toNumber(stockLevel.current_quantity);
  if (quantity <= 0) {
    return "danger";
  }
  if (quantity <= toNumber(ingredient.quantity)) {
    return "warning";
  }
  return "success";
}

function getIngredientCoverageLabel(
  ingredient: CatalogProduct["ingredients"][number],
  stockLevelByItemId: Map<string, InventoryStockLevel>,
) {
  const stockLevel = stockLevelByItemId.get(ingredient.inventory_item_id);
  if (!stockLevel) {
    return "-";
  }

  const recipeQuantity = toNumber(ingredient.quantity);
  if (recipeQuantity <= 0) {
    return "Nem számolható";
  }

  const coverage = toNumber(stockLevel.current_quantity) / recipeQuantity;
  if (coverage <= 0) {
    return "0 recept";
  }
  return `${formatNumber(coverage)} recept`;
}

function getRecipeIngredientSummary(
  product: CatalogProduct,
  stockLevelByItemId: Map<string, InventoryStockLevel>,
): RecipeIngredientSummary {
  const totalCost = product.ingredients.reduce(
    (total, ingredient) => total + toNumber(ingredient.estimated_cost),
    0,
  );
  const highestCostIngredient = [...product.ingredients].sort(
    (left, right) => toNumber(right.estimated_cost) - toNumber(left.estimated_cost),
  )[0];
  const emptyStockCount = product.ingredients.filter((ingredient) => {
    const stockLevel = stockLevelByItemId.get(ingredient.inventory_item_id);
    return stockLevel !== undefined && toNumber(stockLevel.current_quantity) <= 0;
  }).length;
  const missingStockCount = product.ingredients.filter(
    (ingredient) => !stockLevelByItemId.has(ingredient.inventory_item_id),
  ).length;

  return {
    totalCost,
    highestCostName: highestCostIngredient?.name ?? "-",
    highestCostShare:
      totalCost > 0 ? (toNumber(highestCostIngredient?.estimated_cost) / totalCost) * 100 : 0,
    emptyStockCount,
    missingStockCount,
  };
}

function sortIngredientsByRisk(
  ingredients: CatalogProduct["ingredients"],
  stockLevelByItemId: Map<string, InventoryStockLevel>,
) {
  const toneWeight: Record<ProductRiskTone, number> = {
    danger: 0,
    warning: 1,
    neutral: 2,
    success: 3,
  };

  return [...ingredients].sort((left, right) => {
    const toneDelta =
      toneWeight[getIngredientStockTone(left, stockLevelByItemId)] -
      toneWeight[getIngredientStockTone(right, stockLevelByItemId)];
    if (toneDelta !== 0) {
      return toneDelta;
    }
    return toNumber(right.estimated_cost) - toNumber(left.estimated_cost);
  });
}

function sortProducts(products: CatalogProduct[], sort: ProductSort) {
  const items = [...products];
  if (sort === "price") {
    return items.sort((a, b) => toNumber(b.sale_price_gross) - toNumber(a.sale_price_gross));
  }
  if (sort === "abc") {
    return items.sort((a, b) => a.name.localeCompare(b.name, "hu"));
  }
  return items.sort((a, b) => toNumber(b.estimated_margin_amount) - toNumber(a.estimated_margin_amount));
}

function productMatchesRiskFilter(
  product: CatalogProduct,
  stockLevelByItemId: Map<string, InventoryStockLevel>,
  riskFilter: ProductRiskFilter,
) {
  if (riskFilter === "all") {
    return true;
  }

  const risks = getProductRiskItems(product, stockLevelByItemId);
  const hasRealRisk = risks.some((risk) => risk.tone === "danger" || risk.tone === "warning");
  if (riskFilter === "attention") {
    return hasRealRisk;
  }
  if (riskFilter === "margin") {
    return risks.some((risk) => risk.title.includes("árrés"));
  }
  if (riskFilter === "recipe") {
    return risks.some((risk) => risk.title.includes("recept"));
  }
  if (riskFilter === "stock") {
    return risks.some((risk) => risk.title.includes("készlet") || risk.title.includes("Alapanyag"));
  }

  return true;
}

function buildProductForm(product?: CatalogProduct, fallbackUomId = ""): ProductFormState {
  return {
    id: product?.id,
    category_id: product?.category_id ?? "",
    sales_uom_id: product?.sales_uom_id ?? fallbackUomId,
    default_vat_rate_id: product?.default_vat_rate_id ?? "",
    sku: product?.sku ?? "",
    name: product?.name ?? "",
    product_type: product?.product_type ?? "finished_good",
    sale_price_gross: product?.sale_price_gross ?? "",
    default_unit_cost: product?.has_recipe ? "" : product?.estimated_unit_cost ?? "",
    is_active: product?.is_active ?? true,
    recipe_enabled: product?.has_recipe ?? false,
    recipe_name: product?.recipe_name ?? (product ? `${product.name} recipe` : ""),
    recipe_yield_quantity: product?.recipe_yield_quantity ?? "1",
    recipe_yield_uom_id: "",
    recipe_ingredients:
      product?.ingredients.map((ingredient) => ({
        inventory_item_id: ingredient.inventory_item_id,
        quantity: ingredient.quantity,
        uom_id: "",
      })) ?? [],
  };
}

function compactNullable(value: string) {
  return value.trim() === "" ? null : value.trim();
}

function validateProductForm(form: ProductFormState) {
  if (!form.recipe_enabled) {
    return null;
  }

  if (toNumber(form.recipe_yield_quantity) <= 0) {
    return "A recept kihozatalanak nagyobbnak kell lennie nullanal.";
  }

  const yieldUomId = form.recipe_yield_uom_id || form.sales_uom_id;
  if (!yieldUomId) {
    return "Valassz kihozatali egyseget a recepthez.";
  }

  const completeLines = form.recipe_ingredients.filter(
    (item) => item.inventory_item_id || item.quantity || item.uom_id,
  );
  if (completeLines.length === 0) {
    return "Receptes termekhez legalabb egy alapanyag sor szukseges.";
  }

  const seenIngredientIds = new Set<string>();
  for (const line of completeLines) {
    if (!line.inventory_item_id || !line.uom_id || toNumber(line.quantity) <= 0) {
      return "Minden receptsorhoz alapanyag, mennyiseg es egyseg szukseges.";
    }
    if (seenIngredientIds.has(line.inventory_item_id)) {
      return "Ugyanaz az alapanyag csak egyszer szerepelhet egy receptben.";
    }
    seenIngredientIds.add(line.inventory_item_id);
  }

  return null;
}

function CatalogProductsHeaderControls({
  businessUnits,
  selectedBusinessUnitId,
  setSelectedBusinessUnitId,
  search,
  setSearch,
  sort,
  setSort,
  riskFilter,
  setRiskFilter,
  startCreate,
}: {
  businessUnits: Array<{ id: string; name: string }>;
  selectedBusinessUnitId: string;
  setSelectedBusinessUnitId: (value: string) => void;
  search: string;
  setSearch: (value: string) => void;
  sort: ProductSort;
  setSort: (value: ProductSort) => void;
  riskFilter: ProductRiskFilter;
  setRiskFilter: (value: ProductRiskFilter) => void;
  startCreate: () => void;
}) {
  return (
    <div className="business-dashboard-filters topbar-dashboard-filters">
      <label className="field topbar-field">
        <span>Vállalkozás</span>
        <select
          className="field-input"
          value={selectedBusinessUnitId}
          onChange={(event) => setSelectedBusinessUnitId(event.target.value)}
        >
          {businessUnits.map((businessUnit) => (
            <option key={businessUnit.id} value={businessUnit.id}>
              {businessUnit.name}
            </option>
          ))}
        </select>
      </label>

      <label className="field topbar-field">
        <span>Keresés</span>
        <input
          className="field-input"
          value={search}
          onChange={(event) => setSearch(event.target.value)}
          placeholder="Név vagy SKU"
        />
      </label>

      <label className="field topbar-field">
        <span>Rendezés</span>
        <select
          className="field-input"
          value={sort}
          onChange={(event) => setSort(event.target.value as ProductSort)}
        >
          <option value="top">Legjobb árrés</option>
          <option value="trending">Elemzésre kész</option>
          <option value="abc">ABC</option>
          <option value="price">Ár</option>
        </select>
      </label>

      <label className="field topbar-field">
        <span>Kockázat</span>
        <select
          className="field-input"
          value={riskFilter}
          onChange={(event) => setRiskFilter(event.target.value as ProductRiskFilter)}
        >
          <option value="all">Minden termék</option>
          <option value="attention">Figyelendő</option>
          <option value="margin">Árrés kockázat</option>
          <option value="recipe">Recept kockázat</option>
          <option value="stock">Készlet kockázat</option>
        </select>
      </label>

      <Button type="button" onClick={startCreate}>
        Új termék
      </Button>
      <Link className="secondary-button" to={routes.catalogIngredients}>
        Alapanyagok
      </Link>
    </div>
  );
}

function CatalogModeTabs({
  mode,
  setMode,
  products,
}: {
  mode: CatalogMode;
  setMode: (mode: CatalogMode) => void;
  products: CatalogProduct[];
}) {
  const recipeCount = products.filter((product) => product.has_recipe).length;
  const missingRecipeCount = products.length - recipeCount;

  return (
    <div className="catalog-mode-tabs" role="tablist" aria-label="Katalogus nezet">
      <button
        type="button"
        className={mode === "products" ? "active" : ""}
        onClick={() => setMode("products")}
      >
        Termekek
        <strong>{products.length}</strong>
      </button>
      <button
        type="button"
        className={mode === "recipes" ? "active" : ""}
        onClick={() => setMode("recipes")}
      >
        Receptek
        <strong>{recipeCount}/{products.length}</strong>
      </button>
      {missingRecipeCount > 0 ? (
        <span>{missingRecipeCount} recept nelkul</span>
      ) : null}
    </div>
  );
}

function CatalogRecipesPanel({
  products,
  stockLevelByItemId,
  onEditRecipe,
}: {
  products: CatalogProduct[];
  stockLevelByItemId: Map<string, InventoryStockLevel>;
  onEditRecipe: (product: CatalogProduct) => void;
}) {
  const recipeProducts = [...products].sort((left, right) => {
    if (left.has_recipe !== right.has_recipe) {
      return left.has_recipe ? 1 : -1;
    }
    return left.name.localeCompare(right.name, "hu-HU");
  });

  if (recipeProducts.length === 0) {
    return <p className="empty-message">Nincs megjelenitheto termek.</p>;
  }

  return (
    <section className="panel catalog-recipes-panel">
      <div className="panel-header">
        <h2>Receptek</h2>
        <span className="panel-count">
          {recipeProducts.filter((product) => product.has_recipe).length} aktiv
        </span>
      </div>

      <div className="table-wrap">
        <table className="data-table details-table catalog-recipes-table">
          <thead>
            <tr>
              <th>Termek</th>
              <th>Recept</th>
              <th>Kihozatal</th>
              <th>Osszetevok</th>
              <th>Koltseg es arres</th>
              <th>Keszlet jelzes</th>
              <th>Muvelet</th>
            </tr>
          </thead>
          <tbody>
            {recipeProducts.map((product) => {
              const ingredientSummary = getRecipeIngredientSummary(
                product,
                stockLevelByItemId,
              );
              const productHealth = getProductHealth(product, stockLevelByItemId);
              const yieldLabel = product.recipe_yield_quantity
                ? `${formatNumber(product.recipe_yield_quantity)} ${
                    product.recipe_yield_uom_code ?? ""
                  }`
                : "-";

              return (
                <tr key={product.id}>
                  <td>
                    <strong>{product.name}</strong>
                    <div className="metric-stack">
                      <span>{product.category_name ?? "Egyeb"}</span>
                      <span>{formatMoney(product.sale_price_gross)}</span>
                    </div>
                  </td>
                  <td>
                    <span
                      className={
                        product.has_recipe
                          ? "status-pill status-pill-success"
                          : "status-pill status-pill-warning"
                      }
                    >
                      {product.has_recipe ? product.recipe_name : "Recept hianyzik"}
                    </span>
                  </td>
                  <td>{yieldLabel}</td>
                  <td>
                    <div className="metric-stack">
                      <span>{product.ingredients.length} sor</span>
                      <span>{ingredientSummary.highestCostName}</span>
                    </div>
                  </td>
                  <td>
                    <div className="metric-stack">
                      <span>Koltseg: {formatMoney(product.estimated_unit_cost)}</span>
                      <span>Arres: {formatMoney(product.estimated_margin_amount)}</span>
                    </div>
                  </td>
                  <td>
                    <span className={productHealth.className}>
                      {productHealth.label}
                    </span>
                  </td>
                  <td>
                    <Button
                      type="button"
                      variant="secondary"
                      onClick={() => onEditRecipe(product)}
                    >
                      {product.has_recipe ? "Recept szerkesztese" : "Recept letrehozasa"}
                    </Button>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </section>
  );
}

export function CatalogProductsPage() {
  const { setControls } = useTopbarControls();
  const queryClient = useQueryClient();
  const [selectedBusinessUnitId, setSelectedBusinessUnitId] = useState("");
  const [catalogMode, setCatalogMode] = useState<CatalogMode>("products");
  const [selectedCategory, setSelectedCategory] = useState("all");
  const [search, setSearch] = useState("");
  const [sort, setSort] = useState<ProductSort>("top");
  const [riskFilter, setRiskFilter] = useState<ProductRiskFilter>("all");
  const [expandedProductId, setExpandedProductId] = useState<string | null>(null);
  const [isCreating, setIsCreating] = useState(false);
  const [form, setForm] = useState<ProductFormState>(() => buildProductForm());
  const [formValidationError, setFormValidationError] = useState("");
  const [recipeIngredientSearch, setRecipeIngredientSearch] = useState("");

  const businessUnitsQuery = useQuery({
    queryKey: ["business-units"],
    queryFn: listBusinessUnits,
  });
  const businessUnits = businessUnitsQuery.data ?? [];

  useEffect(() => {
    if (!selectedBusinessUnitId && businessUnits.length > 0) {
      setSelectedBusinessUnitId(businessUnits[0].id);
    }
  }, [businessUnits, selectedBusinessUnitId]);

  const productsQuery = useQuery({
    queryKey: ["catalog-products", selectedBusinessUnitId],
    queryFn: () => listCatalogProducts(selectedBusinessUnitId),
    enabled: Boolean(selectedBusinessUnitId),
  });
  const categoriesQuery = useQuery({
    queryKey: ["catalog-categories", selectedBusinessUnitId],
    queryFn: () => listCategories(selectedBusinessUnitId),
    enabled: Boolean(selectedBusinessUnitId),
  });
  const unitsQuery = useQuery({
    queryKey: ["units-of-measure"],
    queryFn: listUnitsOfMeasure,
  });
  const vatRatesQuery = useQuery({
    queryKey: ["vat-rates"],
    queryFn: listVatRates,
  });
  const ingredientsQuery = useQuery({
    queryKey: ["catalog-ingredients", selectedBusinessUnitId],
    queryFn: () => listCatalogIngredients(selectedBusinessUnitId),
    enabled: Boolean(selectedBusinessUnitId),
  });
  const stockLevelsQuery = useQuery({
    queryKey: ["catalog-stock-levels", selectedBusinessUnitId],
    queryFn: () => listInventoryStockLevels({ business_unit_id: selectedBusinessUnitId }),
    enabled: Boolean(selectedBusinessUnitId),
  });

  const products = productsQuery.data ?? [];
  const categories = categoriesQuery.data ?? [];
  const units = unitsQuery.data ?? [];
  const vatRates = vatRatesQuery.data ?? [];
  const ingredients = ingredientsQuery.data ?? [];
  const stockLevelByItemId = useMemo(
    () =>
      new Map(
        (stockLevelsQuery.data ?? []).map((stockLevel) => [
          stockLevel.inventory_item_id,
          stockLevel,
        ]),
      ),
    [stockLevelsQuery.data],
  );
  const productCategories = useMemo(
    () => Array.from(new Set(products.map((product) => product.category_name ?? "Egyéb"))),
    [products],
  );
  const visibleProducts = useMemo(() => {
    const normalizedSearch = search.trim().toLowerCase();
    const filtered = products.filter((product) => {
      const matchesCategory =
        selectedCategory === "all" || (product.category_name ?? "Egyéb") === selectedCategory;
      const matchesSearch =
        normalizedSearch.length === 0 ||
        product.name.toLowerCase().includes(normalizedSearch) ||
        (product.sku ?? "").toLowerCase().includes(normalizedSearch);
      const matchesRisk = productMatchesRiskFilter(
        product,
        stockLevelByItemId,
        riskFilter,
      );
      return matchesCategory && matchesSearch && matchesRisk;
    });
    return sortProducts(filtered, sort);
  }, [products, riskFilter, search, selectedCategory, sort, stockLevelByItemId]);
  const recipeIngredientSearchNormalized = recipeIngredientSearch.trim().toLowerCase();
  const selectedRecipeIngredientIds = useMemo(
    () =>
      new Set(
        form.recipe_ingredients
          .map((ingredient) => ingredient.inventory_item_id)
          .filter(Boolean),
      ),
    [form.recipe_ingredients],
  );
  const recipeFormEstimatedCost = useMemo(() => {
    return form.recipe_ingredients.reduce((total, line) => {
      const ingredient = ingredients.find((item) => item.id === line.inventory_item_id);
      return total + toNumber(line.quantity) * toNumber(ingredient?.default_unit_cost);
    }, 0);
  }, [form.recipe_ingredients, ingredients]);

  const saveMutation = useMutation({
    mutationFn: (payload: CatalogProductPayload & { id?: string }) => {
      if (payload.id) {
        const { id, business_unit_id: _businessUnitId, ...body } = payload;
        return updateCatalogProduct(id, body);
      }
      return createCatalogProduct(payload);
    },
    onSuccess: (product) => {
      setExpandedProductId(product.id);
      setIsCreating(false);
      setFormValidationError("");
      setForm(buildProductForm(product, product.sales_uom_id ?? ""));
      void queryClient.invalidateQueries({ queryKey: ["catalog-products", selectedBusinessUnitId] });
      void queryClient.invalidateQueries({ queryKey: ["demo-pos-catalog", selectedBusinessUnitId] });
      void queryClient.invalidateQueries({ queryKey: ["dashboard"] });
    },
  });
  const deleteMutation = useMutation({
    mutationFn: deleteCatalogProduct,
    onSuccess: () => {
      setExpandedProductId(null);
      setIsCreating(false);
      setForm(buildProductForm());
      void queryClient.invalidateQueries({ queryKey: ["catalog-products", selectedBusinessUnitId] });
      void queryClient.invalidateQueries({ queryKey: ["demo-pos-catalog", selectedBusinessUnitId] });
      void queryClient.invalidateQueries({ queryKey: ["dashboard"] });
    },
  });

  function startEdit(product: CatalogProduct, forceRecipe = false) {
    const yieldUnit =
      units.find((unit) => unit.code === product.recipe_yield_uom_code)?.id ??
      product.sales_uom_id ??
      units.find((unit) => unit.code === "pcs")?.id ??
      units[0]?.id ??
      "";
    const nextForm = buildProductForm(product, product.sales_uom_id ?? "");
    setForm({
      ...nextForm,
      recipe_enabled: forceRecipe ? true : nextForm.recipe_enabled,
      recipe_yield_uom_id: yieldUnit,
      recipe_ingredients: product.ingredients.map((ingredient) => {
        const inventoryItem = ingredients.find((item) => item.id === ingredient.inventory_item_id);
        const ingredientUnit = units.find((unit) => unit.code === ingredient.uom_code);
        return {
          inventory_item_id: ingredient.inventory_item_id,
          quantity: ingredient.quantity,
          uom_id: ingredientUnit?.id ?? inventoryItem?.uom_id ?? "",
        };
      }),
    });
    setFormValidationError("");
    setIsCreating(false);
    setExpandedProductId(product.id);
  }

  function startRecipeEdit(product: CatalogProduct) {
    setCatalogMode("recipes");
    startEdit(product, true);
  }

  function startCreate() {
    const fallbackUnit = units.find((unit) => unit.code === "pcs")?.id ?? units[0]?.id ?? "";
    setForm(buildProductForm(undefined, fallbackUnit));
    setFormValidationError("");
    setIsCreating(true);
    setExpandedProductId(null);
  }

  useEffect(() => {
    setControls(
      <CatalogProductsHeaderControls
        businessUnits={businessUnits}
        selectedBusinessUnitId={selectedBusinessUnitId}
        setSelectedBusinessUnitId={(value) => {
          setSelectedBusinessUnitId(value);
          setExpandedProductId(null);
          setIsCreating(false);
        }}
        search={search}
        setSearch={setSearch}
        sort={sort}
        setSort={setSort}
        riskFilter={riskFilter}
        setRiskFilter={setRiskFilter}
        startCreate={startCreate}
      />,
    );

    return () => setControls(null);
  }, [businessUnits, riskFilter, search, selectedBusinessUnitId, setControls, sort]);

  function buildPayload(): CatalogProductPayload & { id?: string } {
    const recipe =
      form.recipe_enabled
        ? {
            name: form.recipe_name.trim() || `${form.name.trim()} recipe`,
            yield_quantity: form.recipe_yield_quantity || "1",
            yield_uom_id: form.recipe_yield_uom_id || form.sales_uom_id,
            ingredients: form.recipe_ingredients.filter(
              (item) => item.inventory_item_id && item.quantity && item.uom_id,
            ),
          }
        : null;
    return {
      id: form.id,
      business_unit_id: form.id ? undefined : selectedBusinessUnitId,
      category_id: compactNullable(form.category_id),
      sales_uom_id: compactNullable(form.sales_uom_id),
      default_vat_rate_id: compactNullable(form.default_vat_rate_id),
      sku: compactNullable(form.sku),
      name: form.name,
      product_type: form.product_type,
      sale_price_gross: compactNullable(form.sale_price_gross),
      default_unit_cost: form.recipe_enabled ? null : compactNullable(form.default_unit_cost),
      currency: "HUF",
      is_active: form.is_active,
      recipe,
    };
  }

  function submitProductForm(event: FormEvent) {
    event.preventDefault();
    const validationError = validateProductForm(form);
    if (validationError) {
      setFormValidationError(validationError);
      return;
    }
    setFormValidationError("");
    saveMutation.mutate(buildPayload());
  }

  function archiveProduct(product: CatalogProduct) {
    if (!window.confirm(`Archiválod ezt a terméket: ${product.name}?`)) {
      return;
    }
    deleteMutation.mutate(product.id);
  }

  function updateRecipeIngredient(index: number, patch: Partial<CatalogRecipeIngredientPayload>) {
    setForm((current) => ({
      ...current,
      recipe_ingredients: current.recipe_ingredients.map((item, itemIndex) =>
        itemIndex === index ? { ...item, ...patch } : item,
      ),
    }));
  }

  const formPanel = isCreating || form.id ? (
    <Card
      className="catalog-editor-card"
      eyebrow={isCreating ? "Új termék" : "Termék szerkesztése"}
      title={isCreating ? "Termék létrehozása" : form.name}
      subtitle="Ár, kategória, értékesítési egység és recept karbantartása"
    >
      <form className="catalog-edit-form" onSubmit={submitProductForm}>
        <div className="form-grid">
          <label className="field">
            <span>Név</span>
            <input className="field-input" value={form.name} onChange={(event) => setForm({ ...form, name: event.target.value })} required />
          </label>
          <label className="field">
            <span>SKU</span>
            <input className="field-input" value={form.sku} onChange={(event) => setForm({ ...form, sku: event.target.value })} />
          </label>
          <label className="field">
            <span>Kategória</span>
            <select className="field-input" value={form.category_id} onChange={(event) => setForm({ ...form, category_id: event.target.value })}>
              <option value="">Nincs kategória</option>
              {categories.map((category) => (
                <option key={category.id} value={category.id}>
                  {category.name}
                </option>
              ))}
            </select>
          </label>
          <label className="field">
            <span>Értékesítési egység</span>
            <select className="field-input" value={form.sales_uom_id} onChange={(event) => setForm({ ...form, sales_uom_id: event.target.value })}>
              <option value="">Nincs egység</option>
              {units.map((unit) => (
                <option key={unit.id} value={unit.id}>
                  {unit.name} ({unit.symbol ?? unit.code})
                </option>
              ))}
            </select>
          </label>
          <label className="field">
            <span>Típus</span>
            <select className="field-input" value={form.product_type} onChange={(event) => setForm({ ...form, product_type: event.target.value })} required>
              <option value="finished_good">Késztermék</option>
              <option value="resale">Továbbértékesített termék</option>
              <option value="service">Szolgáltatás</option>
            </select>
          </label>
          <label className="field">
            <span>Eladási ár</span>
            <input className="field-input" type="number" min="0" step="1" value={form.sale_price_gross} onChange={(event) => setForm({ ...form, sale_price_gross: event.target.value })} />
          </label>
          <label className="field">
            <span>ÁFA kulcs</span>
            <select className="field-input" value={form.default_vat_rate_id} onChange={(event) => setForm({ ...form, default_vat_rate_id: event.target.value })}>
              <option value="">Nincs beállítva</option>
              {vatRates.map((vatRate) => (
                <option key={vatRate.id} value={vatRate.id}>
                  {vatRate.name}
                </option>
              ))}
            </select>
          </label>
          <label className="field">
            <span>Direkt költség</span>
            <input className="field-input" type="number" min="0" step="0.01" value={form.default_unit_cost} disabled={form.recipe_enabled} onChange={(event) => setForm({ ...form, default_unit_cost: event.target.value })} />
          </label>
          <label className="checkbox-field">
            <input type="checkbox" checked={form.is_active} onChange={(event) => setForm({ ...form, is_active: event.target.checked })} />
            <span>Aktív</span>
          </label>
        </div>

        <label className="checkbox-field catalog-recipe-toggle">
          <input type="checkbox" checked={form.recipe_enabled} onChange={(event) => setForm({ ...form, recipe_enabled: event.target.checked })} />
          <span>Receptes termék</span>
        </label>

        {form.recipe_enabled ? (
          <div className="catalog-recipe-editor">
            <div className="catalog-recipe-editor-summary">
              <span>
                <strong>{form.recipe_ingredients.length}</strong>
                receptsor
              </span>
              <span>
                <strong>{formatMoney(recipeFormEstimatedCost)}</strong>
                becsult receptkoltseg
              </span>
            </div>
            <div className="form-grid">
              <label className="field">
                <span>Recept neve</span>
                <input className="field-input" value={form.recipe_name} onChange={(event) => setForm({ ...form, recipe_name: event.target.value })} />
              </label>
              <label className="field">
                <span>Kihozatal mennyisége</span>
                <input className="field-input" type="number" min="0.001" step="0.001" value={form.recipe_yield_quantity} onChange={(event) => setForm({ ...form, recipe_yield_quantity: event.target.value })} />
              </label>
              <label className="field">
                <span>Kihozatal egysége</span>
                <select className="field-input" value={form.recipe_yield_uom_id || form.sales_uom_id} onChange={(event) => setForm({ ...form, recipe_yield_uom_id: event.target.value })}>
                  {units.map((unit) => (
                    <option key={unit.id} value={unit.id}>
                      {unit.name} ({unit.symbol ?? unit.code})
                    </option>
                  ))}
                </select>
              </label>
            </div>

            <label className="field catalog-recipe-search">
              <span>Alapanyag kereses</span>
              <input
                className="field-input"
                value={recipeIngredientSearch}
                onChange={(event) => setRecipeIngredientSearch(event.target.value)}
                placeholder="Liszt, tojas, cukor..."
              />
            </label>

            <div className="catalog-recipe-lines">
              {form.recipe_ingredients.map((line, index) => {
                const lineIngredient = ingredients.find((item) => item.id === line.inventory_item_id);
                const lineCost = toNumber(line.quantity) * toNumber(lineIngredient?.default_unit_cost);
                const ingredientOptions = ingredients.filter((ingredient) => {
                  const alreadySelected =
                    selectedRecipeIngredientIds.has(ingredient.id) &&
                    ingredient.id !== line.inventory_item_id;
                  const matchesSearch =
                    recipeIngredientSearchNormalized.length === 0 ||
                    ingredient.name.toLowerCase().includes(recipeIngredientSearchNormalized);
                  return !alreadySelected && (matchesSearch || ingredient.id === line.inventory_item_id);
                });

                return (
                  <div className="catalog-recipe-line" key={`${line.inventory_item_id}-${index}`}>
                  <select value={line.inventory_item_id} onChange={(event) => {
                    const ingredient = ingredients.find((item) => item.id === event.target.value);
                    updateRecipeIngredient(index, {
                      inventory_item_id: event.target.value,
                      uom_id: ingredient?.uom_id ?? line.uom_id,
                    });
                  }}>
                    <option value="">Alapanyag</option>
                    {ingredientOptions.map((ingredient) => (
                      <option key={ingredient.id} value={ingredient.id}>
                        {ingredient.name}
                      </option>
                    ))}
                  </select>
                  <input type="number" min="0.001" step="0.001" value={line.quantity} onChange={(event) => updateRecipeIngredient(index, { quantity: event.target.value })} />
                  <select value={line.uom_id} onChange={(event) => updateRecipeIngredient(index, { uom_id: event.target.value })}>
                    <option value="">Egység</option>
                    {units.map((unit) => (
                      <option key={unit.id} value={unit.id}>
                        {unit.symbol ?? unit.code}
                      </option>
                    ))}
                  </select>
                  <span className="catalog-recipe-line-cost">
                    {formatMoney(lineCost)}
                  </span>
                  <button type="button" onClick={() => setForm((current) => ({
                    ...current,
                    recipe_ingredients: current.recipe_ingredients.filter((_, itemIndex) => itemIndex !== index),
                  }))}>
                    Eltávolítás
                  </button>
                </div>
                );
              })}
            </div>
            <Button type="button" variant="secondary" onClick={() => setForm((current) => ({
              ...current,
              recipe_ingredients: [
                ...current.recipe_ingredients,
                { inventory_item_id: "", quantity: "1", uom_id: units[0]?.id ?? "" },
              ],
            }))}>
              Alapanyag hozzáadása
            </Button>
          </div>
        ) : null}

        {formValidationError ? <p className="error-message">{formValidationError}</p> : null}
        {saveMutation.error ? <p className="error-message">{saveMutation.error.message}</p> : null}
        <div className="catalog-editor-actions">
          <Button type="submit">{saveMutation.isPending ? "Mentés..." : "Mentés"}</Button>
          <Button type="button" variant="secondary" onClick={() => {
            setIsCreating(false);
            setFormValidationError("");
            setForm(buildProductForm());
          }}>
            Mégsem
          </Button>
        </div>
      </form>
    </Card>
  ) : null;

  return (
    <section className="page-section catalog-page">
      <div className="finance-summary-grid">
        <article className="finance-summary-card">
          <span>Termékek</span>
          <strong>{visibleProducts.length}</strong>
        </article>
        <article className="finance-summary-card">
          <span>Receptes termékek</span>
          <strong>{products.filter((product) => product.has_recipe).length}</strong>
        </article>
        <article className="finance-summary-card">
          <span>Átlagos árrés</span>
          <strong>
            {formatMoney(
              visibleProducts.length > 0
                ? visibleProducts.reduce(
                    (total, product) => total + toNumber(product.estimated_margin_amount),
                    0,
                  ) / visibleProducts.length
                : 0,
            )}
          </strong>
        </article>
      </div>

      <CatalogModeTabs
        mode={catalogMode}
        setMode={(mode) => {
          setCatalogMode(mode);
          setExpandedProductId(null);
          setIsCreating(false);
        }}
        products={products}
      />

      <div className="catalog-tabs">
        <button type="button" className={selectedCategory === "all" ? "active" : ""} onClick={() => setSelectedCategory("all")}>Összes</button>
        {productCategories.map((category) => (
          <button key={category} type="button" className={selectedCategory === category ? "active" : ""} onClick={() => setSelectedCategory(category)}>
            {category}
          </button>
        ))}
      </div>

      {formPanel}
      {productsQuery.isLoading ? <p className="info-message">Katalógus betöltése...</p> : null}
      {stockLevelsQuery.isLoading ? <p className="info-message">Készletszintek betöltése...</p> : null}
      {productsQuery.error ? <p className="error-message">{productsQuery.error.message}</p> : null}

      {catalogMode === "recipes" ? (
        <CatalogRecipesPanel
          products={visibleProducts}
          stockLevelByItemId={stockLevelByItemId}
          onEditRecipe={startRecipeEdit}
        />
      ) : (
      <div className="catalog-card-grid">
        {visibleProducts.map((product) => {
          const expanded = expandedProductId === product.id;
          const margin = toNumber(product.estimated_margin_amount);
          const productHealth = getProductHealth(product, stockLevelByItemId);
          const productRisks = getProductRiskItems(product, stockLevelByItemId);
          const decisionSummary = getProductDecisionSummary(product, stockLevelByItemId);
          const lowestIngredientStock = getLowestIngredientStock(product, stockLevelByItemId);
          const ingredientSummary = getRecipeIngredientSummary(product, stockLevelByItemId);
          const sortedIngredients = sortIngredientsByRisk(product.ingredients, stockLevelByItemId);
          return (
            <Card
              key={product.id}
              as="article"
              hoverable
              className={expanded ? "catalog-card catalog-card-open" : "catalog-card"}
              eyebrow={product.category_name ?? "Egyéb"}
              title={product.name}
              subtitle={product.sku ?? formatProductType(product.product_type)}
              count={formatMoney(product.sale_price_gross)}
              onClick={() => setExpandedProductId(expanded ? null : product.id)}
            >
              <div className="catalog-card-status-row">
                <span className={productHealth.className}>{productHealth.label}</span>
              </div>

              <div className="catalog-metrics">
                <span>Költség <strong>{formatMoney(product.estimated_unit_cost)}</strong></span>
                <span className={margin >= 0 ? "catalog-good" : "catalog-bad"}>Árrés <strong>{formatMoney(product.estimated_margin_amount)}</strong></span>
                <span>Egység <strong>{getUnitLabel(product)}</strong></span>
              </div>

              {expanded ? (
                <div className="catalog-details" onClick={(event) => event.stopPropagation()}>
                  <div className="catalog-decision-strip">
                    <article className={`catalog-decision-card ${decisionSummary.actionTone}`}>
                      <span>Teendő</span>
                      <strong>{decisionSummary.actionTitle}</strong>
                      <small>{decisionSummary.actionDescription}</small>
                    </article>
                    <article className={`catalog-decision-card ${decisionSummary.riskTone}`}>
                      <span>Kockázati szint</span>
                      <strong>{decisionSummary.riskTitle}</strong>
                      <small>{decisionSummary.riskDescription}</small>
                    </article>
                    <article className="catalog-decision-card neutral">
                      <span>Receptfedettség</span>
                      <strong>{decisionSummary.recipeTitle}</strong>
                      <small>{decisionSummary.recipeDescription}</small>
                    </article>
                    <article className={`catalog-decision-card ${decisionSummary.stockTone}`}>
                      <span>Készletjelzés</span>
                      <strong>{decisionSummary.stockTitle}</strong>
                      <small>{decisionSummary.stockDescription}</small>
                    </article>
                  </div>

                  <div className="catalog-product-action-bar">
                    <div>
                      <span>Termékkártya műveletek</span>
                      <strong>{decisionSummary.actionTitle}</strong>
                    </div>
                    <div className="catalog-editor-actions">
                      <Button type="button" variant="secondary" onClick={() => startEdit(product)}>Szerkesztés</Button>
                      <Button type="button" variant="secondary" onClick={() => archiveProduct(product)} disabled={deleteMutation.isPending}>Archiválás</Button>
                    </div>
                  </div>

                  <div className="catalog-health-row">
                    <article className="catalog-health-card">
                      <span>Állapot</span>
                      <strong>{productHealth.label}</strong>
                    </article>
                    <article className="catalog-health-card">
                      <span>Típus</span>
                      <strong>{formatProductType(product.product_type)}</strong>
                    </article>
                    <article className="catalog-health-card">
                      <span>Recept sorok</span>
                      <strong>{product.ingredients.length}</strong>
                    </article>
                    <article className="catalog-health-card">
                      <span>Legalacsonyabb készlet</span>
                      <strong>{lowestIngredientStock}</strong>
                    </article>
                  </div>

                  <div className="catalog-product-detail-layout">
                    <article className="catalog-product-panel">
                      <div className="catalog-panel-heading">
                        <span>Pénzügyi kép</span>
                        <strong>{margin >= 0 ? "Pozitív fedezet" : "Veszteséges"}</strong>
                      </div>
                      <div className="catalog-mini-metrics">
                        <span>Eladási ár <strong>{formatMoney(product.sale_price_gross)}</strong></span>
                        <span>ÁFA <strong>{product.vat_rate_name ?? "Nincs beállítva"}</strong></span>
                        <span>Költség <strong>{formatMoney(product.estimated_unit_cost)}</strong></span>
                        <span className={margin >= 0 ? "catalog-good" : "catalog-bad"}>Árrés <strong>{formatMoney(product.estimated_margin_amount)}</strong></span>
                        <span className={margin >= 0 ? "catalog-good" : "catalog-bad"}>Árrés % <strong>{formatNumber(product.estimated_margin_percent)}%</strong></span>
                      </div>
                    </article>

                    <article className="catalog-product-panel">
                      <div className="catalog-panel-heading">
                        <span>Recept és készlet</span>
                        <strong>{product.has_recipe ? product.recipe_name : "Direkt költség"}</strong>
                      </div>
                      <div className="catalog-mini-metrics">
                        <span>Kihozatal <strong>{product.recipe_yield_quantity ? `${formatNumber(product.recipe_yield_quantity)} ${product.recipe_yield_uom_code ?? ""}` : "-"}</strong></span>
                        <span>Receptsor <strong>{product.ingredients.length}</strong></span>
                        <span>Egység <strong>{getUnitLabel(product)}</strong></span>
                        <span>Minimum készlet <strong>{lowestIngredientStock}</strong></span>
                      </div>
                    </article>

                    <article className="catalog-product-panel catalog-product-panel-wide">
                      <div className="catalog-panel-heading">
                        <span>Kockázati jelzések</span>
                        <strong>{productRisks.length}</strong>
                      </div>
                      <div className="catalog-risk-list">
                        {productRisks.map((risk) => (
                          <div className={`catalog-risk-card ${risk.tone}`} key={risk.title}>
                            <strong>{risk.title}</strong>
                            <span>{risk.description}</span>
                          </div>
                        ))}
                      </div>
                    </article>
                  </div>
                  {product.ingredients.length > 0 ? (
                    <div className="catalog-product-panel catalog-product-panel-wide">
                      <div className="catalog-panel-heading">
                        <span>Receptösszetevők</span>
                        <strong>{formatMoney(product.estimated_unit_cost)}</strong>
                      </div>
                      <div className="catalog-ingredient-summary">
                        <span>Receptköltség <strong>{formatMoney(ingredientSummary.totalCost)}</strong></span>
                        <span>Legdrágább összetevő <strong>{ingredientSummary.highestCostName}</strong></span>
                        <span>Költségarány <strong>{formatNumber(ingredientSummary.highestCostShare)}%</strong></span>
                        <span>Készletjelzés <strong>{ingredientSummary.emptyStockCount + ingredientSummary.missingStockCount}</strong></span>
                      </div>
                      <div className="catalog-ingredient-table-wrap">
                        <table className="data-table catalog-ingredient-table">
                          <thead>
                            <tr><th>Alapanyag</th><th>Mennyiség</th><th>Egységköltség</th><th>Sorköltség</th><th>Költségarány</th><th>Aktuális készlet</th><th>Fedés</th><th>Állapot</th><th>Utolsó mozgás</th></tr>
                          </thead>
                          <tbody>
                            {sortedIngredients.map((ingredient) => {
                              const stockLevel = stockLevelByItemId.get(ingredient.inventory_item_id);
                              const stockStatus = getIngredientStockStatus(
                                ingredient,
                                stockLevelByItemId,
                              );
                              const stockTone = getIngredientStockTone(
                                ingredient,
                                stockLevelByItemId,
                              );
                              const costShare =
                                ingredientSummary.totalCost > 0
                                  ? (toNumber(ingredient.estimated_cost) / ingredientSummary.totalCost) * 100
                                  : 0;
                              return (
                                <tr className={`catalog-ingredient-row ${stockTone}`} key={ingredient.inventory_item_id}>
                                  <td>{ingredient.name}</td>
                                  <td>{formatNumber(ingredient.quantity)} {ingredient.uom_code ?? ""}</td>
                                  <td>{formatMoney(ingredient.unit_cost)}</td>
                                  <td>{formatMoney(ingredient.estimated_cost)}</td>
                                  <td>{formatNumber(costShare)}%</td>
                                  <td>
                                    {stockLevel
                                      ? `${formatNumber(stockLevel.current_quantity)} ${ingredient.uom_code ?? ""}`
                                      : "-"}
                                  </td>
                                  <td>{getIngredientCoverageLabel(ingredient, stockLevelByItemId)}</td>
                                  <td><span className={stockStatus.className}>{stockStatus.label}</span></td>
                                  <td>{formatDateTime(stockLevel?.last_movement_at ?? null)}</td>
                                </tr>
                              );
                            })}
                          </tbody>
                        </table>
                      </div>
                    </div>
                  ) : (
                    <p className="section-note">Direkt költségű termék, nincs hozzárendelt recept.</p>
                  )}
                </div>
              ) : null}
            </Card>
          );
        })}
      </div>
      )}
    </section>
  );
}
