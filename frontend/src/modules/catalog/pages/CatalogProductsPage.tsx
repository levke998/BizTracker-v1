import { useEffect, useMemo, useState } from "react";
import type { FormEvent } from "react";
import { Link } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { Button } from "../../../shared/components/ui/Button";
import { Card } from "../../../shared/components/ui/Card";
import { routes } from "../../../shared/constants/routes";
import {
  listBusinessUnits,
  listCategories,
  listUnitsOfMeasure,
} from "../../masterData/api/masterDataApi";
import {
  createCatalogProduct,
  listCatalogIngredients,
  listCatalogProducts,
  updateCatalogProduct,
} from "../api/catalogApi";
import type {
  CatalogProduct,
  CatalogProductPayload,
  CatalogRecipeIngredientPayload,
} from "../types/catalog";

type ProductSort = "top" | "trending" | "abc" | "price";
type ProductFormState = {
  id?: string;
  category_id: string;
  sales_uom_id: string;
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

function getUnitLabel(product: CatalogProduct) {
  return product.sales_uom_symbol ?? product.sales_uom_code ?? "unit";
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

function buildProductForm(product?: CatalogProduct, fallbackUomId = ""): ProductFormState {
  return {
    id: product?.id,
    category_id: product?.category_id ?? "",
    sales_uom_id: product?.sales_uom_id ?? fallbackUomId,
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

export function CatalogProductsPage() {
  const queryClient = useQueryClient();
  const [selectedBusinessUnitId, setSelectedBusinessUnitId] = useState("");
  const [selectedCategory, setSelectedCategory] = useState("all");
  const [search, setSearch] = useState("");
  const [sort, setSort] = useState<ProductSort>("top");
  const [expandedProductId, setExpandedProductId] = useState<string | null>(null);
  const [isCreating, setIsCreating] = useState(false);
  const [form, setForm] = useState<ProductFormState>(() => buildProductForm());

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
  const ingredientsQuery = useQuery({
    queryKey: ["catalog-ingredients", selectedBusinessUnitId],
    queryFn: () => listCatalogIngredients(selectedBusinessUnitId),
    enabled: Boolean(selectedBusinessUnitId),
  });

  const products = productsQuery.data ?? [];
  const categories = categoriesQuery.data ?? [];
  const units = unitsQuery.data ?? [];
  const ingredients = ingredientsQuery.data ?? [];
  const productCategories = useMemo(
    () => Array.from(new Set(products.map((product) => product.category_name ?? "Other"))),
    [products],
  );
  const visibleProducts = useMemo(() => {
    const normalizedSearch = search.trim().toLowerCase();
    const filtered = products.filter((product) => {
      const matchesCategory =
        selectedCategory === "all" || (product.category_name ?? "Other") === selectedCategory;
      const matchesSearch =
        normalizedSearch.length === 0 ||
        product.name.toLowerCase().includes(normalizedSearch) ||
        (product.sku ?? "").toLowerCase().includes(normalizedSearch);
      return matchesCategory && matchesSearch;
    });
    return sortProducts(filtered, sort);
  }, [products, search, selectedCategory, sort]);

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
      setForm(buildProductForm(product, product.sales_uom_id ?? ""));
      void queryClient.invalidateQueries({ queryKey: ["catalog-products", selectedBusinessUnitId] });
      void queryClient.invalidateQueries({ queryKey: ["dashboard"] });
    },
  });

  function startEdit(product: CatalogProduct) {
    const yieldUnit =
      units.find((unit) => unit.code === product.recipe_yield_uom_code)?.id ??
      product.sales_uom_id ??
      "";
    setForm({
      ...buildProductForm(product, product.sales_uom_id ?? ""),
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
    setIsCreating(false);
    setExpandedProductId(product.id);
  }

  function startCreate() {
    const fallbackUnit = units.find((unit) => unit.code === "pcs")?.id ?? units[0]?.id ?? "";
    setForm(buildProductForm(undefined, fallbackUnit));
    setIsCreating(true);
    setExpandedProductId(null);
  }

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
    saveMutation.mutate(buildPayload());
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
      eyebrow={isCreating ? "New product" : "Edit product"}
      title={isCreating ? "Create product" : form.name}
      subtitle="Price, category, sales unit and flexible recipe maintenance"
    >
      <form className="catalog-edit-form" onSubmit={submitProductForm}>
        <div className="form-grid">
          <label className="field">
            <span>Name</span>
            <input className="field-input" value={form.name} onChange={(event) => setForm({ ...form, name: event.target.value })} required />
          </label>
          <label className="field">
            <span>SKU</span>
            <input className="field-input" value={form.sku} onChange={(event) => setForm({ ...form, sku: event.target.value })} />
          </label>
          <label className="field">
            <span>Category</span>
            <select className="field-input" value={form.category_id} onChange={(event) => setForm({ ...form, category_id: event.target.value })}>
              <option value="">No category</option>
              {categories.map((category) => (
                <option key={category.id} value={category.id}>
                  {category.name}
                </option>
              ))}
            </select>
          </label>
          <label className="field">
            <span>Sales unit</span>
            <select className="field-input" value={form.sales_uom_id} onChange={(event) => setForm({ ...form, sales_uom_id: event.target.value })}>
              <option value="">No unit</option>
              {units.map((unit) => (
                <option key={unit.id} value={unit.id}>
                  {unit.name} ({unit.symbol ?? unit.code})
                </option>
              ))}
            </select>
          </label>
          <label className="field">
            <span>Type</span>
            <input className="field-input" value={form.product_type} onChange={(event) => setForm({ ...form, product_type: event.target.value })} required />
          </label>
          <label className="field">
            <span>Sale price</span>
            <input className="field-input" type="number" min="0" step="1" value={form.sale_price_gross} onChange={(event) => setForm({ ...form, sale_price_gross: event.target.value })} />
          </label>
          <label className="field">
            <span>Direct cost</span>
            <input className="field-input" type="number" min="0" step="0.01" value={form.default_unit_cost} disabled={form.recipe_enabled} onChange={(event) => setForm({ ...form, default_unit_cost: event.target.value })} />
          </label>
          <label className="checkbox-field">
            <input type="checkbox" checked={form.is_active} onChange={(event) => setForm({ ...form, is_active: event.target.checked })} />
            <span>Active</span>
          </label>
        </div>

        <label className="checkbox-field catalog-recipe-toggle">
          <input type="checkbox" checked={form.recipe_enabled} onChange={(event) => setForm({ ...form, recipe_enabled: event.target.checked })} />
          <span>Recipe product</span>
        </label>

        {form.recipe_enabled ? (
          <div className="catalog-recipe-editor">
            <div className="form-grid">
              <label className="field">
                <span>Recipe name</span>
                <input className="field-input" value={form.recipe_name} onChange={(event) => setForm({ ...form, recipe_name: event.target.value })} />
              </label>
              <label className="field">
                <span>Yield quantity</span>
                <input className="field-input" type="number" min="0.001" step="0.001" value={form.recipe_yield_quantity} onChange={(event) => setForm({ ...form, recipe_yield_quantity: event.target.value })} />
              </label>
              <label className="field">
                <span>Yield unit</span>
                <select className="field-input" value={form.recipe_yield_uom_id || form.sales_uom_id} onChange={(event) => setForm({ ...form, recipe_yield_uom_id: event.target.value })}>
                  {units.map((unit) => (
                    <option key={unit.id} value={unit.id}>
                      {unit.name} ({unit.symbol ?? unit.code})
                    </option>
                  ))}
                </select>
              </label>
            </div>

            <div className="catalog-recipe-lines">
              {form.recipe_ingredients.map((line, index) => (
                <div className="catalog-recipe-line" key={`${line.inventory_item_id}-${index}`}>
                  <select value={line.inventory_item_id} onChange={(event) => {
                    const ingredient = ingredients.find((item) => item.id === event.target.value);
                    updateRecipeIngredient(index, {
                      inventory_item_id: event.target.value,
                      uom_id: ingredient?.uom_id ?? line.uom_id,
                    });
                  }}>
                    <option value="">Ingredient</option>
                    {ingredients.map((ingredient) => (
                      <option key={ingredient.id} value={ingredient.id}>
                        {ingredient.name}
                      </option>
                    ))}
                  </select>
                  <input type="number" min="0.001" step="0.001" value={line.quantity} onChange={(event) => updateRecipeIngredient(index, { quantity: event.target.value })} />
                  <select value={line.uom_id} onChange={(event) => updateRecipeIngredient(index, { uom_id: event.target.value })}>
                    <option value="">Unit</option>
                    {units.map((unit) => (
                      <option key={unit.id} value={unit.id}>
                        {unit.symbol ?? unit.code}
                      </option>
                    ))}
                  </select>
                  <button type="button" onClick={() => setForm((current) => ({
                    ...current,
                    recipe_ingredients: current.recipe_ingredients.filter((_, itemIndex) => itemIndex !== index),
                  }))}>
                    Remove
                  </button>
                </div>
              ))}
            </div>
            <Button type="button" variant="secondary" onClick={() => setForm((current) => ({
              ...current,
              recipe_ingredients: [
                ...current.recipe_ingredients,
                { inventory_item_id: "", quantity: "1", uom_id: units[0]?.id ?? "" },
              ],
            }))}>
              Add ingredient
            </Button>
          </div>
        ) : null}

        {saveMutation.error ? <p className="error-message">{saveMutation.error.message}</p> : null}
        <div className="catalog-editor-actions">
          <Button type="submit">{saveMutation.isPending ? "Saving..." : "Save"}</Button>
          <Button type="button" variant="secondary" onClick={() => {
            setIsCreating(false);
            setForm(buildProductForm());
          }}>
            Cancel
          </Button>
        </div>
      </form>
    </Card>
  ) : null;

  return (
    <section className="page-section catalog-page">
      <section className="panel catalog-toolbar">
        <label className="field">
          <span>Business unit</span>
          <select
            className="field-input"
            value={selectedBusinessUnitId}
            onChange={(event) => {
              setSelectedBusinessUnitId(event.target.value);
              setExpandedProductId(null);
              setIsCreating(false);
            }}
          >
            {businessUnits.map((businessUnit) => (
              <option key={businessUnit.id} value={businessUnit.id}>
                {businessUnit.name}
              </option>
            ))}
          </select>
        </label>
        <label className="field">
          <span>Search</span>
          <input className="field-input" value={search} onChange={(event) => setSearch(event.target.value)} placeholder="Name or SKU" />
        </label>
        <label className="field">
          <span>Sort</span>
          <select className="field-input" value={sort} onChange={(event) => setSort(event.target.value as ProductSort)}>
            <option value="top">Top margin</option>
            <option value="trending">Trending ready</option>
            <option value="abc">ABC</option>
            <option value="price">Price</option>
          </select>
        </label>
        <Button type="button" onClick={startCreate}>New product</Button>
        <Link className="secondary-button" to={routes.catalogIngredients}>Ingredients</Link>
      </section>

      <div className="catalog-tabs">
        <button type="button" className={selectedCategory === "all" ? "active" : ""} onClick={() => setSelectedCategory("all")}>All</button>
        {productCategories.map((category) => (
          <button key={category} type="button" className={selectedCategory === category ? "active" : ""} onClick={() => setSelectedCategory(category)}>
            {category}
          </button>
        ))}
      </div>

      {formPanel}
      {productsQuery.isLoading ? <p className="info-message">Loading catalog...</p> : null}
      {productsQuery.error ? <p className="error-message">{productsQuery.error.message}</p> : null}

      <div className="catalog-card-grid">
        {visibleProducts.map((product) => {
          const expanded = expandedProductId === product.id;
          const margin = toNumber(product.estimated_margin_amount);
          return (
            <Card
              key={product.id}
              as="article"
              hoverable
              className={expanded ? "catalog-card catalog-card-open" : "catalog-card"}
              eyebrow={product.category_name ?? "Other"}
              title={product.name}
              subtitle={product.sku ?? product.product_type}
              count={formatMoney(product.sale_price_gross)}
              onClick={() => setExpandedProductId(expanded ? null : product.id)}
            >
              <div className="catalog-metrics">
                <span>Cost <strong>{formatMoney(product.estimated_unit_cost)}</strong></span>
                <span className={margin >= 0 ? "catalog-good" : "catalog-bad"}>Margin <strong>{formatMoney(product.estimated_margin_amount)}</strong></span>
                <span>Unit <strong>{getUnitLabel(product)}</strong></span>
              </div>

              {expanded ? (
                <div className="catalog-details" onClick={(event) => event.stopPropagation()}>
                  <div className="details-grid">
                    <article className="detail-item"><span>Margin percent</span><strong>{formatNumber(product.estimated_margin_percent)}%</strong></article>
                    <article className="detail-item"><span>Recipe</span><strong>{product.has_recipe ? product.recipe_name : "No recipe"}</strong></article>
                    <article className="detail-item"><span>Yield</span><strong>{product.recipe_yield_quantity ? `${formatNumber(product.recipe_yield_quantity)} ${product.recipe_yield_uom_code ?? ""}` : "-"}</strong></article>
                  </div>
                  <Button type="button" variant="secondary" onClick={() => startEdit(product)}>Edit product</Button>
                  {product.ingredients.length > 0 ? (
                    <table className="data-table">
                      <thead>
                        <tr><th>Ingredient</th><th>Qty</th><th>Unit cost</th><th>Line cost</th></tr>
                      </thead>
                      <tbody>
                        {product.ingredients.map((ingredient) => (
                          <tr key={ingredient.inventory_item_id}>
                            <td>{ingredient.name}</td>
                            <td>{formatNumber(ingredient.quantity)} {ingredient.uom_code ?? ""}</td>
                            <td>{formatMoney(ingredient.unit_cost)}</td>
                            <td>{formatMoney(ingredient.estimated_cost)}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  ) : (
                    <p className="section-note">Direct-cost product, no recipe attached.</p>
                  )}
                </div>
              ) : null}
            </Card>
          );
        })}
      </div>
    </section>
  );
}
