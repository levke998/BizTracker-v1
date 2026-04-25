import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";

import { Card } from "../../../shared/components/ui/Card";
import { routes } from "../../../shared/constants/routes";
import { listBusinessUnits } from "../../masterData/api/masterDataApi";
import { listCatalogProducts } from "../api/catalogApi";
import type { CatalogProduct } from "../types/catalog";

type ProductSort = "top" | "trending" | "abc" | "price";

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

export function CatalogProductsPage() {
  const [selectedBusinessUnitId, setSelectedBusinessUnitId] = useState("");
  const [selectedCategory, setSelectedCategory] = useState("all");
  const [search, setSearch] = useState("");
  const [sort, setSort] = useState<ProductSort>("top");
  const [expandedProductId, setExpandedProductId] = useState<string | null>(null);

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

  const products = productsQuery.data ?? [];
  const categories = useMemo(
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
          <input
            className="field-input"
            value={search}
            onChange={(event) => setSearch(event.target.value)}
            placeholder="Name or SKU"
          />
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
        <Link className="secondary-button" to={routes.catalogIngredients}>
          Ingredients
        </Link>
      </section>

      <div className="catalog-tabs">
        <button
          type="button"
          className={selectedCategory === "all" ? "active" : ""}
          onClick={() => setSelectedCategory("all")}
        >
          All
        </button>
        {categories.map((category) => (
          <button
            key={category}
            type="button"
            className={selectedCategory === category ? "active" : ""}
            onClick={() => setSelectedCategory(category)}
          >
            {category}
          </button>
        ))}
      </div>

      {productsQuery.isLoading ? <p className="info-message">Loading catalog...</p> : null}
      {productsQuery.error ? (
        <p className="error-message">{productsQuery.error.message}</p>
      ) : null}

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
                <span>
                  Cost <strong>{formatMoney(product.estimated_unit_cost)}</strong>
                </span>
                <span className={margin >= 0 ? "catalog-good" : "catalog-bad"}>
                  Margin <strong>{formatMoney(product.estimated_margin_amount)}</strong>
                </span>
                <span>
                  Unit <strong>{getUnitLabel(product)}</strong>
                </span>
              </div>

              {expanded ? (
                <div className="catalog-details">
                  <div className="details-grid">
                    <article className="detail-item">
                      <span>Margin percent</span>
                      <strong>{formatNumber(product.estimated_margin_percent)}%</strong>
                    </article>
                    <article className="detail-item">
                      <span>Recipe</span>
                      <strong>{product.has_recipe ? product.recipe_name : "No recipe"}</strong>
                    </article>
                    <article className="detail-item">
                      <span>Yield</span>
                      <strong>
                        {product.recipe_yield_quantity
                          ? `${formatNumber(product.recipe_yield_quantity)} ${product.recipe_yield_uom_code ?? ""}`
                          : "-"}
                      </strong>
                    </article>
                  </div>
                  {product.ingredients.length > 0 ? (
                    <table className="data-table">
                      <thead>
                        <tr>
                          <th>Ingredient</th>
                          <th>Qty</th>
                          <th>Unit cost</th>
                          <th>Line cost</th>
                        </tr>
                      </thead>
                      <tbody>
                        {product.ingredients.map((ingredient) => (
                          <tr key={ingredient.inventory_item_id}>
                            <td>{ingredient.name}</td>
                            <td>
                              {formatNumber(ingredient.quantity)} {ingredient.uom_code ?? ""}
                            </td>
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
